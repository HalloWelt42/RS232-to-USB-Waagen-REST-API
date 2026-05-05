"""Persistente Sinks für Readings: CSV und SQLite.

Jeder Sink ist append-only, threadsicher (per ``threading.Lock``) und
implementiert ``Sink``-Protokoll. Mehrere Sinks können parallel betrieben
werden — z.B. CSV für Excel-Import + SQLite für Queries.
"""

from __future__ import annotations

import csv
import logging
import sqlite3
import threading
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Protocol

from .parser import Reading

log = logging.getLogger(__name__)


class Sink(Protocol):
    """Minimaler Sink-Vertrag."""

    def write(self, reading: Reading) -> None: ...
    def close(self) -> None: ...


class CsvSink(AbstractContextManager["CsvSink"]):
    """Append-only CSV-Logger.

    Spalten: ``iso_timestamp,weight_g,unit,stable,raw_hex``.
    Header wird genau einmal geschrieben — bei neuer Datei oder leerer
    bestehender Datei.
    """

    FIELDS = ("iso_timestamp", "weight_g", "unit", "stable", "raw_hex")

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        is_new = not self.path.exists() or self.path.stat().st_size == 0
        self._fh = self.path.open("a", encoding="utf-8", newline="")
        self._writer = csv.writer(self._fh)
        self._lock = threading.Lock()
        if is_new:
            self._writer.writerow(self.FIELDS)
            self._fh.flush()

    def __enter__(self) -> "CsvSink":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def write(self, reading: Reading) -> None:
        with self._lock:
            self._writer.writerow([
                reading.timestamp.isoformat(timespec="milliseconds"),
                f"{reading.weight:.4f}",
                reading.unit,
                int(reading.stable),
                reading.raw.hex(),
            ])
            self._fh.flush()

    def close(self) -> None:
        with self._lock:
            if not self._fh.closed:
                self._fh.close()


class SqliteSink(AbstractContextManager["SqliteSink"]):
    """SQLite-Logger mit einfachem Schema und ts-Index.

    Schema::

        CREATE TABLE readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,         -- ISO-8601 mit Millisekunden
            weight_g REAL NOT NULL,
            unit TEXT NOT NULL,
            stable INTEGER NOT NULL,  -- 0/1
            raw BLOB NOT NULL
        );
        CREATE INDEX idx_readings_ts ON readings(ts);

    Bei Initialisierung wird das Schema idempotent angelegt.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            str(self.path),
            check_same_thread=False,
            isolation_level=None,  # Autocommit
        )
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                weight_g REAL NOT NULL,
                unit TEXT NOT NULL,
                stable INTEGER NOT NULL,
                raw BLOB NOT NULL
            );
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_readings_ts ON readings(ts);"
        )

    def __enter__(self) -> "SqliteSink":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def write(self, reading: Reading) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO readings (ts, weight_g, unit, stable, raw) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    reading.timestamp.isoformat(timespec="milliseconds"),
                    reading.weight,
                    reading.unit,
                    int(reading.stable),
                    reading.raw,
                ),
            )

    def close(self) -> None:
        with self._lock:
            self._conn.close()


class MultiSink:
    """Schreibt in mehrere Sinks gleichzeitig — Fehler eines Sinks
    bremsen die anderen nicht aus."""

    def __init__(self, *sinks: Sink) -> None:
        self.sinks = list(sinks)

    def write(self, reading: Reading) -> None:
        for sink in self.sinks:
            try:
                sink.write(reading)
            except Exception:  # noqa: BLE001 — Sink darf Reader nicht killen
                log.exception("Sink %r failed for %r", sink, reading)

    def close(self) -> None:
        for sink in self.sinks:
            try:
                sink.close()
            except Exception:
                log.exception("Sink %r close failed", sink)
