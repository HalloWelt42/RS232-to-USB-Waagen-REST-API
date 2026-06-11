"""Connect-Modul: konfigurierbare Messwert-Weiterleitung an Drittsysteme.

Pusht den jeweils letzten Reading periodisch per HTTP-POST an einen
frei konfigurierbaren Endpoint -- z.B. eine Inventar-App, ein ERP oder
ein eigenes Dashboard. Payload ist bewusst schlicht gehalten:

    {
      "weight_g": 123.4,      Brutto- oder Netto-Gewicht (s. send_netto)
      "unit": "g",
      "stable": true,
      "count": 42             nur wenn Stueckgewicht kalibriert ist
    }

Eigenschaften:
  - Auth ueber frei benennbaren Header (z.B. 'X-Device-Token')
  - Intervall, Nur-Stabil-Filter und Netto/Brutto-Wahl konfigurierbar
  - extra_fields werden unveraendert in den Payload gemischt (z.B.
    {"device": "werkstatt"})
  - Status fuer die UI: zuletzt gesendet, letzter Fehler, Zaehler
  - Konfig wandert in die bestehende config.json-Persistenz

Kein Versand-Puffer: ein Live-Gewicht ist fluechtig, verpasste Pushes
sind egal. Wer Messreihen braucht, nutzt das Messlog/Samples-Modul.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx

log = logging.getLogger(__name__)


@dataclass
class ConnectConfig:
    enabled: bool = False
    url: str = ""
    auth_header: str = "X-Device-Token"
    auth_token: str = ""
    interval_s: float = 1.0
    only_stable: bool = True
    send_netto: bool = False
    extra_fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "url": self.url,
            "auth_header": self.auth_header,
            "auth_token": self.auth_token,
            "interval_s": self.interval_s,
            "only_stable": self.only_stable,
            "send_netto": self.send_netto,
            "extra_fields": dict(self.extra_fields),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConnectConfig":
        cfg = cls()
        cfg.enabled = bool(data.get("enabled", False))
        cfg.url = str(data.get("url", ""))
        cfg.auth_header = str(data.get("auth_header") or "X-Device-Token")
        cfg.auth_token = str(data.get("auth_token", ""))
        try:
            cfg.interval_s = max(0.2, float(data.get("interval_s", 1.0)))
        except (TypeError, ValueError):
            cfg.interval_s = 1.0
        cfg.only_stable = bool(data.get("only_stable", True))
        cfg.send_netto = bool(data.get("send_netto", False))
        extra = data.get("extra_fields")
        cfg.extra_fields = dict(extra) if isinstance(extra, dict) else {}
        return cfg


@dataclass
class ConnectStatus:
    running: bool = False
    last_sent_at: Optional[str] = None
    last_http_status: Optional[int] = None
    last_error: Optional[str] = None
    sent_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "last_sent_at": self.last_sent_at,
            "last_http_status": self.last_http_status,
            "last_error": self.last_error,
            "sent_count": self.sent_count,
        }


class ConnectForwarder:
    """Hintergrund-Task: liest state.latest im Intervall und pusht.

    Der Task laeuft dauerhaft und prueft selbst ob enabled -- so kann
    die UI an/aus schalten ohne Task-Lifecycle-Gefrickel.
    """

    def __init__(self, state: Any) -> None:
        # 'Any' statt AppState um Import-Zyklus zu vermeiden (state.py
        # importiert connect.py fuer die Config-Persistenz).
        self._state = state
        self.config = ConnectConfig()
        self.status = ConnectStatus()
        self._task: Optional[asyncio.Task[None]] = None
        self._client: Optional[httpx.AsyncClient] = None

    # -- Lifecycle ------------------------------------------------------
    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.get_event_loop().create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
            self._task = None
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self.status.running = False

    # -- Versand --------------------------------------------------------
    def _build_payload(self) -> Optional[dict[str, Any]]:
        reading = getattr(self._state, "latest", None)
        if reading is None:
            return None
        if self.config.only_stable and not reading.stable:
            return None
        weight = float(reading.weight)
        if self.config.send_netto:
            tare = getattr(self._state, "tare_g", None)
            if tare:
                weight = max(0.0, weight - float(tare))
        payload: dict[str, Any] = {
            "weight_g": round(weight, 4),
            "unit": reading.unit,
            "stable": bool(reading.stable),
        }
        # Stueckzahl wie /app/count: nur wenn Stueckgewicht kalibriert.
        piece_weight = getattr(self._state, "piece_weight_g", None)
        if piece_weight and piece_weight > 0:
            payload["count"] = int(round(weight / float(piece_weight)))
        if self.config.extra_fields:
            payload.update(self.config.extra_fields)
        return payload

    async def send_once(self) -> tuple[bool, str]:
        """Einmal-Push (Test-Knopf). Returns (ok, beschreibung)."""
        if not self.config.url:
            return False, "Keine Ziel-URL konfiguriert."
        payload = self._build_payload()
        if payload is None:
            return False, "Kein (stabiler) Messwert vorhanden."
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=5.0)
        headers = {}
        if self.config.auth_header and self.config.auth_token:
            headers[self.config.auth_header] = self.config.auth_token
        try:
            resp = await self._client.post(
                self.config.url, json=payload, headers=headers
            )
            self.status.last_http_status = resp.status_code
            self.status.last_sent_at = datetime.now().isoformat(
                timespec="seconds"
            )
            if 200 <= resp.status_code < 300:
                self.status.sent_count += 1
                self.status.last_error = None
                return True, f"HTTP {resp.status_code}"
            self.status.last_error = f"HTTP {resp.status_code}"
            return False, f"HTTP {resp.status_code}: {resp.text[:120]}"
        except httpx.HTTPError as exc:
            self.status.last_error = str(exc)
            self.status.last_http_status = None
            return False, str(exc)

    async def _run(self) -> None:
        log.info("Connect-Forwarder gestartet")
        backoff = 0.0
        while True:
            try:
                await asyncio.sleep(max(self.config.interval_s, 0.2) + backoff)
                if not self.config.enabled or not self.config.url:
                    self.status.running = False
                    continue
                self.status.running = True
                ok, _ = await self.send_once()
                # Sanfter Backoff bei Fehlern, damit ein totes Ziel das
                # Log nicht flutet: +2 s pro Fehlschlag, max 30 s.
                backoff = 0.0 if ok else min(backoff + 2.0, 30.0)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                log.exception("Connect-Forwarder Fehler")
                backoff = min(backoff + 2.0, 30.0)
