"""Messprotokoll: Server-seitiges Logging der Werte-Änderungen.

Reagiert ausschließlich auf Änderungen — gleichbleibende Frames werden
nicht aufgenommen. Jeder Eintrag hält die Differenz zum vorherigen
gespeicherten Wert, den resultierenden Absolutwert, den Zeitstempel
und einen Eintragstyp (``change``, ``tare`` oder ``start``).

Der Speicher ist eine SQLite-Datenbank, sodass die Liste auch nach
Backend-Neustart noch da ist. Frontend-Clients können beim Mount die
Liste laden und parallel über den WebSocket-Stream eigene Live-Diffs
seit Mount selbst rechnen.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from .parser import Reading

log = logging.getLogger(__name__)

EntryKind = Literal["change", "tare", "start"]


@dataclass(frozen=True)
class MesslogEntry:
    """Ein Messprotokoll-Eintrag."""

    id: int
    ts: datetime
    kind: EntryKind
    diff_g: Optional[float]    # None bei "tare" und "start"
    value_g: float
    unit: str
    stable: bool


class MesslogStore(AbstractContextManager["MesslogStore"]):
    """SQLite-basierter Diff-Logger, threadsicher.

    ``feed(reading)`` muss bei jedem neuen Reading aufgerufen werden;
    intern entscheidet die Klasse, ob daraus ein Diff-Eintrag wird.
    Die Schwelle ``epsilon_g`` definiert, ab welcher Abweichung ein
    Frame als „echte Änderung" gilt — Standard 0,05 g entspricht der
    Zwischenfläche unter der Waage-Auflösung.
    """

    def __init__(
        self,
        path: str | Path = ":memory:",
        epsilon_g: float = 0.05,
        max_entries: int = 5000,
    ) -> None:
        self.path = path if path == ":memory:" else str(Path(path))
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._epsilon = epsilon_g
        self._max = max_entries
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            self.path, check_same_thread=False, isolation_level=None,
        )
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS messlog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                kind TEXT NOT NULL,
                diff_g REAL,
                value_g REAL NOT NULL,
                unit TEXT NOT NULL,
                stable INTEGER NOT NULL
            );
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messlog_ts ON messlog(ts);"
        )
        # Letzten gespeicherten Wert beim Boot laden, damit nach Neustart
        # der nächste Diff korrekt berechnet wird.
        self._last_stored: Optional[float] = self._load_last_value()

    @classmethod
    def from_env(cls, path: Optional[str]) -> "MesslogStore":
        return cls(path or ":memory:")

    def __enter__(self) -> "MesslogStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------------
    #  Schreiben
    # ------------------------------------------------------------------
    def feed(self, reading: Reading) -> Optional[MesslogEntry]:
        """Verarbeitet ein neues Reading und liefert ggf. einen Eintrag.

        Returns:
            ``MesslogEntry``, wenn der Frame als echte Änderung galt;
            sonst ``None`` (z.B. Wert hat sich nicht oder unter Epsilon
            geändert).
        """
        if not reading.stable:
            # Instabile Frames ignorieren — wir loggen erst bei stable
            return None

        last = self._last_stored
        if last is None:
            entry = self._insert("start", None, reading)
            self._last_stored = reading.weight
            return entry

        diff = reading.weight - last
        if abs(diff) <= self._epsilon:
            return None

        entry = self._insert("change", diff, reading)
        self._last_stored = reading.weight
        return entry

    def mark_tare(self, reading: Reading) -> MesslogEntry:
        """Explizit einen Tara-Eintrag setzen (nach Tara-Befehl)."""
        entry = self._insert("tare", None, reading)
        # Nach Tara setzen wir den Referenzwert auf den neuen Stand
        # (üblicherweise 0), sodass der nächste Diff darauf aufbaut.
        self._last_stored = reading.weight
        return entry

    def clear(self) -> int:
        with self._lock:
            cur = self._conn.execute("DELETE FROM messlog")
            self._last_stored = None
            return cur.rowcount

    # ------------------------------------------------------------------
    #  Lesen
    # ------------------------------------------------------------------
    def list(self, limit: int = 200) -> list[MesslogEntry]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, ts, kind, diff_g, value_g, unit, stable "
                "FROM messlog ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        return [self._row_to_entry(r) for r in rows]

    # ------------------------------------------------------------------
    #  Intern
    # ------------------------------------------------------------------
    def _insert(
        self, kind: EntryKind, diff_g: Optional[float], reading: Reading,
    ) -> MesslogEntry:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO messlog (ts, kind, diff_g, value_g, unit, stable) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    reading.timestamp.isoformat(timespec="milliseconds"),
                    kind,
                    diff_g,
                    reading.weight,
                    reading.unit,
                    int(reading.stable),
                ),
            )
            row_id = cur.lastrowid
            # Alte Einträge abschneiden
            self._conn.execute(
                "DELETE FROM messlog WHERE id <= ("
                "  SELECT MAX(id) - ? FROM messlog"
                ")",
                (self._max,),
            )
        return MesslogEntry(
            id=row_id,
            ts=reading.timestamp,
            kind=kind,
            diff_g=diff_g,
            value_g=reading.weight,
            unit=reading.unit,
            stable=reading.stable,
        )

    def _load_last_value(self) -> Optional[float]:
        cur = self._conn.execute(
            "SELECT value_g FROM messlog ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        return row[0] if row else None

    @staticmethod
    def _row_to_entry(row: tuple) -> MesslogEntry:
        return MesslogEntry(
            id=row[0],
            ts=datetime.fromisoformat(row[1]),
            kind=row[2],
            diff_g=row[3],
            value_g=row[4],
            unit=row[5],
            stable=bool(row[6]),
        )
