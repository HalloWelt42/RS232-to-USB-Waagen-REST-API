"""Gemeinsamer App-State zwischen Reader-Loop und HTTP-Handlern.

Hält den letzten ``Reading``, den Ringpuffer der History, die
WS-Subscriber, alle Toolmodi-Stati (Toleranz, Netto, Count) und die
Backend-Konfiguration (aktives Modell, Polling-Intervall, Sample-Pfad).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import deque
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .containers import ContainerStore
from .count_templates import CountTemplateStore
from .differenz import DifferenzStore
from .messlog import MesslogStore
from .models import DEFAULT_MODEL_ID
from .parser import Reading
from .reader import Waage
from .samples import SampleStore

log = logging.getLogger(__name__)

CONFIG_FILE_NAME = "config.json"


class AppState:
    """Zentraler reaktiver Zustand der laufenden App."""

    def __init__(
        self,
        history_size: int,
        port: str,
        baudrate: int,
        resolved_port: str,
        samples_path: Optional[str],
        messlog_path: Optional[str],
        config_dir: Optional[str],
        containers_path: Optional[str] = None,
        count_templates_path: Optional[str] = None,
    ) -> None:
        # --- Stream / History ---
        self.latest: Optional[Reading] = None
        self.last_seen: Optional[datetime] = None
        self.history: deque[Reading] = deque(maxlen=history_size)
        self.subscribers: set[asyncio.Queue[Reading]] = set()
        self.reader_alive: bool = False
        self.started_at: datetime = datetime.now()
        self.current_reader: Optional[Waage] = None
        # Wenn länger als `scale_stale_after_s` keine Frames mehr kamen,
        # gilt die Hardware als „weg" (z.B. USB-Adapter abgezogen). Wirkt
        # auf `scale_alive` und steuert den Reconnect-Trigger im Reader-
        # Loop. Default 5s — bei 0,5–1 Hz Polling-Rate viel Zeit für
        # gelegentliche Lücken, schnell genug um einen Disconnect noch
        # in derselben Sekunde sichtbar zu machen.
        self.scale_stale_after_s: float = float(
            os.getenv("WAAGE_SCALE_STALE_AFTER_S", "5")
        )

        # --- Hardware-Konfig ---
        self.port: str = port
        self.resolved_port: str = resolved_port
        self.baudrate: int = baudrate
        self.active_model_id: str = DEFAULT_MODEL_ID
        # Polling-Intervall in Sekunden für Live-Hardware. 0,2 s = 5 Hz
        # ist ein guter Kompromiss aus Reaktivität und Hardware-
        # Schonung; per env `WAAGE_POLL_INTERVAL_S` überschreibbar
        # (siehe Waage-Konstruktor in api._make_reader_factory).
        self.poll_interval_s: float = float(
            os.getenv("WAAGE_POLL_INTERVAL_S", "0.2")
        )
        # Quelle: 'live' liest von der Hardware, 'simulate' nutzt SimulatedWaage
        self.source_mode: str = "live"

        # --- Tool-Module ---
        # Toleranz
        self.target_g: Optional[float] = None
        self.tolerance_minus_g: Optional[float] = None
        self.tolerance_plus_g: Optional[float] = None
        # Netto / Software-Tara
        self.tare_g: Optional[float] = None
        self.tare_set_at: Optional[datetime] = None
        # Count
        self.piece_weight_g: Optional[float] = None
        self.piece_calibrated_at: Optional[datetime] = None
        self.piece_reference_count: Optional[int] = None

        # --- Speicher ---
        self.samples = SampleStore(samples_path or ":memory:")
        self.messlog = MesslogStore(messlog_path or ":memory:")
        self.containers = ContainerStore(containers_path or ":memory:")
        self.count_templates = CountTemplateStore(count_templates_path or ":memory:")
        self.differenz = DifferenzStore()

        # --- Persistenz für Config ---
        self._config_dir: Optional[Path] = (
            Path(config_dir) if config_dir else None
        )
        self._load_config()

        # --- Reader-Loop-Interna ---
        self.tare_pending: bool = False  # nach Tara-Befehl: nächster Stable -> Messlog-Marker

        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    #  Hardware-Lebenszeichen
    # ------------------------------------------------------------------
    @property
    def stale_for_s(self) -> Optional[float]:
        """Sekunden seit dem letzten erfolgreichen Frame, oder None
        wenn noch nie ein Frame angekommen ist."""
        if self.last_seen is None:
            return None
        return (datetime.now() - self.last_seen).total_seconds()

    @property
    def scale_alive(self) -> bool:
        """True wenn der Reader-Task läuft UND die Hardware kürzlich
        ein Frame geliefert hat.

        Anders als `reader_alive` (das nur sagt: der Python-Task läuft)
        ist `scale_alive` False, wenn der USB-Adapter abgezogen wurde,
        die Waage abgeschaltet ist oder das Kabel defekt ist — auch
        dann, wenn der Reader-Loop selbst noch fröhlich pollt.
        """
        if not self.reader_alive:
            return False
        s = self.stale_for_s
        if s is None:
            # Frisch nach Start: noch keine Frames bekommen — ist OK
            # für die ersten paar Sekunden, danach gilt das als „aus".
            uptime = (datetime.now() - self.started_at).total_seconds()
            return uptime < self.scale_stale_after_s
        return s < self.scale_stale_after_s

    # ------------------------------------------------------------------
    #  Stream-Verteilung
    # ------------------------------------------------------------------
    async def publish(self, reading: Reading) -> None:
        self.latest = reading
        self.last_seen = reading.timestamp
        self.history.append(reading)

        # Messlog: Tara-Marker bei tare_pending oder normaler Diff-Eintrag
        try:
            if self.tare_pending and reading.stable:
                self.messlog.mark_tare(reading)
                self.tare_pending = False
            else:
                self.messlog.feed(reading)
        except Exception:  # noqa: BLE001
            log.exception("Messlog-Feed Fehler")

        for q in list(self.subscribers):
            with suppress(asyncio.QueueFull):
                q.put_nowait(reading)

    # ------------------------------------------------------------------
    #  Config-Persistenz (JSON-Datei in data/config.json)
    # ------------------------------------------------------------------
    def _config_path(self) -> Optional[Path]:
        if self._config_dir is None:
            return None
        return self._config_dir / CONFIG_FILE_NAME

    def _load_config(self) -> None:
        path = self._config_path()
        if path is None or not path.is_file():
            return
        try:
            data = json.loads(path.read_text("utf-8"))
            if isinstance(data, dict):
                if "active_model_id" in data:
                    self.active_model_id = str(data["active_model_id"])
                if "poll_interval_s" in data:
                    self.poll_interval_s = float(data["poll_interval_s"])
                if "baudrate" in data:
                    self.baudrate = int(data["baudrate"])
                if "source_mode" in data:
                    mode = str(data["source_mode"])
                    if mode in ("live", "simulate"):
                        self.source_mode = mode
                log.info("Config geladen: %s", path)
        except Exception:  # noqa: BLE001
            log.exception("Config konnte nicht geladen werden: %s", path)

    def persist_config(self) -> None:
        path = self._config_path()
        if path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "active_model_id": self.active_model_id,
                        "poll_interval_s": self.poll_interval_s,
                        "baudrate": self.baudrate,
                        "source_mode": self.source_mode,
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except Exception:  # noqa: BLE001
            log.exception("Config konnte nicht geschrieben werden: %s", path)

    def close(self) -> None:
        for store_name in ("samples", "messlog", "containers", "count_templates"):
            try:
                getattr(self, store_name).close()
            except Exception:
                pass
