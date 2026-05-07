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

    # ------------------------------------------------------------------
    #  Export — mehrere Formate, frei konfigurierbar
    # ------------------------------------------------------------------
    EXPORT_COLUMNS: tuple[str, ...] = (
        "id", "ts", "weight_g", "unit", "stable", "label", "note", "session",
    )

    @staticmethod
    def _row_dict(s: Sample) -> dict[str, object]:
        return {
            "id":       s.id,
            "ts":       s.ts.isoformat(timespec="milliseconds"),
            "weight_g": round(s.weight_g, 4),
            "unit":     s.unit,
            "stable":   int(s.stable),
            "label":    s.label,
            "note":     s.note,
            "session":  s.session,
        }

    def export(
        self,
        samples: Iterable[Sample],
        *,
        fmt: str = "csv",
        delimiter: str = ",",
        columns: Optional[Iterable[str]] = None,
        labels: Optional[dict[str, str]] = None,
    ) -> str:
        """Export-Generator fuer mehrere Formate.

        Args:
            fmt:        ``csv``, ``tsv``, ``json`` oder ``md`` (Markdown).
            delimiter:  Trennzeichen fuer ``csv`` — ``,`` (US/UK) oder
                        ``;`` (DE-Excel-Default). Bei ``tsv`` wird immer
                        Tab verwendet.
            columns:    Reihenfolge und Auswahl der Spalten. Unbekannte
                        Spalten werden ignoriert; Default sind alle.
            labels:     Dict zum Umbenennen der Spalten-Header.

        Returns:
            Vollstaendiger Export-String. CSV bekommt UTF-8-BOM fuer
            Excel-Kompatibilitaet.
        """
        cols = tuple(c for c in (columns or self.EXPORT_COLUMNS) if c in self.EXPORT_COLUMNS)
        if not cols:
            cols = self.EXPORT_COLUMNS
        rows = [self._row_dict(s) for s in samples]
        header_for = lambda c: (labels or {}).get(c, c)
        fmt = fmt.lower()
        if fmt == "csv":
            return self._to_delim(rows, cols, header_for, delimiter, with_bom=True)
        if fmt == "tsv":
            return self._to_delim(rows, cols, header_for, "\t", with_bom=False)
        if fmt == "json":
            import json as _json
            payload = [{header_for(c): r[c] for c in cols} for r in rows]
            return _json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if fmt == "md":
            return self._to_markdown(rows, cols, header_for)
        raise ValueError(f"Unbekanntes Export-Format: {fmt}")

    @staticmethod
    def _to_delim(
        rows: list[dict[str, object]],
        cols: tuple[str, ...],
        header_for,
        delim: str,
        *,
        with_bom: bool,
    ) -> str:
        buf = io.StringIO()
        if with_bom:
            buf.write("\ufeff")
        writer = csv.writer(buf, delimiter=delim, lineterminator="\r\n")
        writer.writerow([header_for(c) for c in cols])
        for r in rows:
            writer.writerow([r[c] for c in cols])
        return buf.getvalue()

    @staticmethod
    def _to_markdown(
        rows: list[dict[str, object]],
        cols: tuple[str, ...],
        header_for,
    ) -> str:
        def esc(v: object) -> str:
            return str(v).replace("|", r"\|")
        lines = [
            "| " + " | ".join(header_for(c) for c in cols) + " |",
            "| " + " | ".join("---" for _ in cols) + " |",
        ]
        for r in rows:
            lines.append("| " + " | ".join(esc(r[c]) for c in cols) + " |")
        return "\n".join(lines) + "\n"

    def to_csv(self, samples: Iterable[Sample]) -> str:
        """Backward-kompatibler CSV-Wrapper."""
        return self.export(samples, fmt="csv")


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
