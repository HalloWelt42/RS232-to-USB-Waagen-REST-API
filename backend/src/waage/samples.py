"""Mess-Snapshot-Speicher mit Label, Notiz und Statistik.

Während des Live-Betriebs kann der Anwender den aktuellen Wert per Klick
"festhalten" — der Wert landet mit Zeitstempel, Label und Notiz in einer
SQLite-Datenbank und wird im UI angezeigt. Aus den gesammelten Werten
einer Session lassen sich Min/Max/Mittelwert/Stdabw berechnen und als
CSV exportieren.
"""

from __future__ import annotations

import csv
import io
import logging
import sqlite3
import statistics
import threading
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from .parser import Reading

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Sample:
    """Eine festgehaltene Wägung mit Metadaten."""

    id: int
    ts: datetime
    weight_g: float
    unit: str
    stable: bool
    label: str
    note: str
    session: str


@dataclass(frozen=True)
class SampleStats:
    """Aggregierte Auswertung über mehrere Samples."""

    count: int
    min_g: Optional[float]
    max_g: Optional[float]
    mean_g: Optional[float]
    stdev_g: Optional[float]
    sum_g: Optional[float]
    session: Optional[str]


class SampleStore(AbstractContextManager["SampleStore"]):
    """SQLite-basierter Speicher mit thread-sicherem Zugriff."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = path if path == ":memory:" else str(Path(path))
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            self.path,
            check_same_thread=False,
            isolation_level=None,
        )
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                weight_g REAL NOT NULL,
                unit TEXT NOT NULL,
                stable INTEGER NOT NULL,
                label TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                session TEXT NOT NULL DEFAULT 'default'
            );
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_samples_session ON samples(session, ts);"
        )

    def __enter__(self) -> "SampleStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def add(
        self,
        reading: Reading,
        *,
        label: str = "",
        note: str = "",
        session: str = "default",
    ) -> Sample:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO samples (ts, weight_g, unit, stable, label, note, session) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    reading.timestamp.isoformat(timespec="milliseconds"),
                    reading.weight,
                    reading.unit,
                    int(reading.stable),
                    label,
                    note,
                    session,
                ),
            )
            row_id = cur.lastrowid
        return Sample(
            id=row_id,
            ts=reading.timestamp,
            weight_g=reading.weight,
            unit=reading.unit,
            stable=reading.stable,
            label=label,
            note=note,
            session=session,
        )

    def list(
        self,
        session: Optional[str] = None,
        limit: int = 1000,
    ) -> list[Sample]:
        with self._lock:
            if session is None:
                cur = self._conn.execute(
                    "SELECT id, ts, weight_g, unit, stable, label, note, session "
                    "FROM samples ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
            else:
                cur = self._conn.execute(
                    "SELECT id, ts, weight_g, unit, stable, label, note, session "
                    "FROM samples WHERE session = ? ORDER BY id DESC LIMIT ?",
                    (session, limit),
                )
            rows = cur.fetchall()
        return [_row_to_sample(r) for r in rows]

    def delete(self, sample_id: int) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM samples WHERE id = ?", (sample_id,)
            )
            return cur.rowcount > 0

    def clear(self, session: Optional[str] = None) -> int:
        with self._lock:
            if session is None:
                cur = self._conn.execute("DELETE FROM samples")
            else:
                cur = self._conn.execute(
                    "DELETE FROM samples WHERE session = ?", (session,)
                )
            return cur.rowcount

    def stats(self, session: Optional[str] = None) -> SampleStats:
        weights = [s.weight_g for s in self.list(session=session, limit=1_000_000)]
        n = len(weights)
        if n == 0:
            return SampleStats(0, None, None, None, None, None, session)
        mean = statistics.fmean(weights)
        sd = statistics.pstdev(weights) if n > 1 else 0.0
        return SampleStats(
            count=n,
            min_g=min(weights),
            max_g=max(weights),
            mean_g=mean,
            stdev_g=sd,
            sum_g=sum(weights),
            session=session,
        )

    def to_csv(self, samples: Iterable[Sample]) -> str:
        """CSV-Export im UTF-8-Format mit Byte-Order-Mark (BOM).

        Das BOM (\\ufeff) ist für Excel notwendig, damit Umlaute in
        Labels und Notizen nicht als „ä" / „ö" / „ü" auftauchen.
        Andere Tools (LibreOffice, pandas, Python-csv) ignorieren das
        BOM korrekt.
        """
        buf = io.StringIO()
        # UTF-8-BOM voranstellen — ohne, würde Excel die Umlaute als
        # Latin-1 fehlinterpretieren („Münzen" → „Münzen").
        buf.write("\ufeff")
        writer = csv.writer(buf)
        writer.writerow(("id", "ts", "weight_g", "unit", "stable", "label", "note", "session"))
        for s in samples:
            writer.writerow((
                s.id,
                s.ts.isoformat(timespec="milliseconds"),
                f"{s.weight_g:.4f}",
                s.unit,
                int(s.stable),
                s.label,
                s.note,
                s.session,
            ))
        return buf.getvalue()


def _row_to_sample(row: tuple) -> Sample:
    return Sample(
        id=row[0],
        ts=datetime.fromisoformat(row[1]),
        weight_g=row[2],
        unit=row[3],
        stable=bool(row[4]),
        label=row[5] or "",
        note=row[6] or "",
        session=row[7] or "default",
    )
