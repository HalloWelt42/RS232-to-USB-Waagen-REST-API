"""Tests für ``waage.messlog``."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from waage.messlog import MesslogStore
from waage.parser import Reading


def _r(weight: float, stable: bool = True) -> Reading:
    return Reading(
        weight=weight, unit="g", stable=stable,
        raw=b"", timestamp=datetime(2026, 5, 7, 12, 0, 0),
    )


def test_first_stable_creates_start_entry() -> None:
    with MesslogStore(":memory:") as store:
        entry = store.feed(_r(0.0))
        assert entry is not None
        assert entry.kind == "start"
        assert entry.diff_g is None


def test_unstable_frames_ignored() -> None:
    with MesslogStore(":memory:") as store:
        assert store.feed(_r(50.0, stable=False)) is None
        assert len(store.list()) == 0


def test_diff_above_epsilon_creates_change() -> None:
    with MesslogStore(":memory:") as store:
        store.feed(_r(0.0))           # start
        e = store.feed(_r(100.0))     # +100 -> change
        assert e is not None
        assert e.kind == "change"
        assert e.diff_g == pytest.approx(100.0)


def test_diff_under_epsilon_skipped() -> None:
    with MesslogStore(":memory:", epsilon_g=0.05) as store:
        store.feed(_r(100.0))
        assert store.feed(_r(100.02)) is None
        assert store.feed(_r(99.96)) is None


def test_negative_diff() -> None:
    with MesslogStore(":memory:") as store:
        store.feed(_r(100.0))
        e = store.feed(_r(50.0))
        assert e.kind == "change"
        assert e.diff_g == pytest.approx(-50.0)


def test_mark_tare() -> None:
    with MesslogStore(":memory:") as store:
        store.feed(_r(100.0))
        e = store.mark_tare(_r(0.0))
        assert e.kind == "tare"
        # Nach Tara wird der Referenzwert auf 0 gesetzt
        n = store.feed(_r(40.0))
        assert n.diff_g == pytest.approx(40.0)


def test_clear() -> None:
    with MesslogStore(":memory:") as store:
        store.feed(_r(0.0))
        store.feed(_r(100.0))
        assert store.clear() == 2


def test_persistence(tmp_path: Path) -> None:
    db = tmp_path / "ml.db"
    with MesslogStore(db) as store:
        store.feed(_r(0.0))
        store.feed(_r(50.0))

    with MesslogStore(db) as store2:
        assert len(store2.list()) == 2
        # Nach Reload sollte der nächste Diff korrekt sein
        e = store2.feed(_r(75.0))
        assert e is not None
        assert e.diff_g == pytest.approx(25.0)


def test_max_entries_truncation() -> None:
    with MesslogStore(":memory:", max_entries=10) as store:
        for i in range(20):
            store.feed(_r(float(i * 10)))   # genug Diff für jeden Eintrag
        rows = store.list(limit=100)
        assert len(rows) <= 10
