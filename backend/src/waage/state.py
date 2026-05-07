"""Gemeinsamer App-State zwischen Reader-Loop und HTTP-Handlern.

Hält den letzten ``Reading``, den Ringpuffer der History, die
WS-Subscriber, alle Toolmodi-Stati (Toleranz, Netto, Count) und die
Backend-Konfiguration (aktives Modell, Polling-Intervall, Sample-Pfad).
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

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
    ) -> None:
        # --- Stream / History ---
        self.latest: Optional[Reading] = None
        self.last_seen: Optional[datetime] = None
        self.history: deque[Reading] = deque(maxlen=history_size)
        self.subscribers: set[asyncio.Queue[Reading]] = set()
        self.reader_alive: bool = False
        self.started_at: datetime = datetime.now()
        self.current_reader: Optional[Waage] = None

        # --- Hardware-Konfig ---
        self.port: str = port
        self.resolved_port: str = resolved_port
        self.baudrate: int = baudrate
        self.active_model_id: str = DEFAULT_MODEL_ID
        self.poll_interval_s: float = 0.5

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
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except Exception:  # noqa: BLE001
            log.exception("Config konnte nicht geschrieben werden: %s", path)

    def close(self) -> None:
        try:
            self.samples.close()
        except Exception:
            pass
        try:
            self.messlog.close()
        except Exception:
            pass
