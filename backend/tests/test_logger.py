"""Tests für ``waage.logger``."""

from __future__ import annotations

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from waage.logger import CsvSink, MultiSink, SqliteSink
from waage.parser import Reading


def _make_reading(weight: float = 100.0, stable: bool = True) -> Reading:
    return Reading(
        weight=weight,
        unit="g",
        stable=stable,
        raw=b"ST,+ 100.0 g\r\n",
        timestamp=datetime(2026, 1, 2, 3, 4, 5, 678000),
    )


def test_csv_sink_writes_header_and_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "log.csv"
    with CsvSink(csv_path) as sink:
        sink.write(_make_reading(100.0, True))
        sink.write(_make_reading(200.0, False))
        sink.write(_make_reading(-1.5, True))

    rows = list(csv.reader(csv_path.read_text().splitlines()))
    assert rows[0] == list(CsvSink.FIELDS)
    assert len(rows) == 4  # header + 3 readings
    assert rows[1][1] == "100.0000"
    assert rows[2][3] == "0"  # stable=False
    assert rows[3][1] == "-1.5000"


def test_csv_sink_appends_without_duplicate_header(tmp_path: Path) -> None:
    csv_path = tmp_path / "log.csv"
    with CsvSink(csv_path) as sink:
        sink.write(_make_reading())
    with CsvSink(csv_path) as sink:
        sink.write(_make_reading(50.0))

    rows = list(csv.reader(csv_path.read_text().splitlines()))
    assert rows[0] == list(CsvSink.FIELDS)
    assert len(rows) == 3  # header + 2 readings, KEIN zweiter Header


def test_sqlite_sink_persists_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "log.db"
    with SqliteSink(db_path) as sink:
        sink.write(_make_reading(100.0, True))
        sink.write(_make_reading(50.0, False))

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT weight_g, stable, unit FROM readings ORDER BY id"
    ).fetchall()
    conn.close()
    assert rows == [(100.0, 1, "g"), (50.0, 0, "g")]


def test_sqlite_sink_index_exists(tmp_path: Path) -> None:
    db_path = tmp_path / "log.db"
    with SqliteSink(db_path):
        pass
    conn = sqlite3.connect(db_path)
    indexes = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()]
    conn.close()
    assert "idx_readings_ts" in indexes


def test_multisink_continues_on_single_failure(tmp_path: Path) -> None:
    """Ein kaputter Sink soll die anderen nicht killen."""

    class _BrokenSink:
        def write(self, reading: Reading) -> None:
            raise RuntimeError("boom")
        def close(self) -> None:
            pass

    csv_path = tmp_path / "log.csv"
    csv_sink = CsvSink(csv_path)
    multi = MultiSink(_BrokenSink(), csv_sink)
    multi.write(_make_reading())
    multi.close()

    rows = list(csv.reader(csv_path.read_text().splitlines()))
    assert len(rows) == 2  # header + 1 reading


def test_csv_creates_parent_dir(tmp_path: Path) -> None:
    nested = tmp_path / "sub" / "dir" / "log.csv"
    with CsvSink(nested) as sink:
        sink.write(_make_reading())
    assert nested.exists()


def test_sqlite_concurrent_writes(tmp_path: Path) -> None:
    """Mehrere Threads schreiben gleichzeitig — kein Crash, alle landen drin."""
    import threading
    db_path = tmp_path / "log.db"
    sink = SqliteSink(db_path)

    def worker(n: int) -> None:
        for i in range(n):
            sink.write(_make_reading(float(i)))

    threads = [threading.Thread(target=worker, args=(20,)) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    sink.close()

    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
    conn.close()
    assert count == 100  # 5 threads x 20 writes
