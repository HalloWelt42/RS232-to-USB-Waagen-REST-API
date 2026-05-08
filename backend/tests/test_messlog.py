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


def test_delete_single_entry() -> None:
    with MesslogStore(":memory:") as store:
        store.feed(_r(0.0))
        e = store.feed(_r(100.0))
        assert e is not None
        ids = [it.id for it in store.list()]
        # Lösche den jüngsten Eintrag
        assert store.delete(ids[0]) is True
        assert len(store.list()) == 1
        # Erneutes Löschen schlägt fehl
        assert store.delete(ids[0]) is False


def test_delete_resets_diff_anchor() -> None:
    """Nach dem Löschen des letzten Eintrags muss der nächste Diff
    auf den verbleibenden Eintrag und nicht auf den entfernten
    Wert bezogen werden."""
    with MesslogStore(":memory:") as store:
        store.feed(_r(0.0))
        store.feed(_r(100.0))
        e_drop = store.feed(_r(250.0))
        assert e_drop is not None
        # Lösche den letzten (250 g) — Anker wird wieder 100 g
        assert store.delete(e_drop.id) is True
        e_next = store.feed(_r(150.0))
        assert e_next is not None
        # 150 - 100 = 50 (nicht 150 - 250 = -100, was wäre wenn Anker nicht reset)
        assert e_next.diff_g == pytest.approx(50.0)


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


def test_list_returns_newest_first() -> None:
    """`list()` liefert in absteigender Insert-Reihenfolge — neuester
    Eintrag steht oben. Das Frontend rendert die Liste 1:1 ohne
    zusätzliches reverse(); ein Bruch dieser Garantie würde im UI
    die Reihenfolge umkehren (älteste oben statt unten)."""
    with MesslogStore(":memory:") as store:
        store.feed(_r(0.0))      # start
        store.feed(_r(10.0))     # change +10
        store.feed(_r(50.0))     # change +40
        store.feed(_r(100.0))    # change +50
        rows = store.list(limit=100)
        # Neuester Eintrag (100.0) muss an Index 0 stehen, ältester am Ende
        values = [r.value_g for r in rows]
        assert values[0] == pytest.approx(100.0), \
            f"Reihenfolge falsch — neuester Wert nicht oben. Got: {values}"
        assert values[-1] == pytest.approx(0.0), \
            f"Reihenfolge falsch — ältester Wert nicht unten. Got: {values}"
        # IDs streng monoton fallend
        ids = [r.id for r in rows]
        assert ids == sorted(ids, reverse=True), \
            f"IDs nicht absteigend sortiert: {ids}"
