"""Tests für ``waage.samples.SampleStore``."""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path

import pytest

from waage.parser import Reading
from waage.samples import Sample, SampleStore


def _r(weight: float, stable: bool = True) -> Reading:
    return Reading(
        weight=weight,
        unit="g",
        stable=stable,
        raw=b"",
        timestamp=datetime(2026, 5, 6, 12, 0, 0),
    )


def test_add_and_list(tmp_path: Path) -> None:
    with SampleStore(tmp_path / "s.db") as store:
        s1 = store.add(_r(100.0), label="A", note="erste")
        s2 = store.add(_r(200.0), label="B", note="zweite")
        rows = store.list()
        assert [r.weight_g for r in rows] == [200.0, 100.0]  # neueste zuerst
        assert s1.id < s2.id


def test_session_isolation(tmp_path: Path) -> None:
    with SampleStore(tmp_path / "s.db") as store:
        store.add(_r(50.0), session="alpha")
        store.add(_r(60.0), session="alpha")
        store.add(_r(99.0), session="beta")
        assert len(store.list(session="alpha")) == 2
        assert len(store.list(session="beta")) == 1


def test_delete(tmp_path: Path) -> None:
    with SampleStore(tmp_path / "s.db") as store:
        s = store.add(_r(10.0))
        assert store.delete(s.id) is True
        assert store.delete(s.id) is False  # zweimal löschen geht nicht
        assert store.list() == []


def test_clear_session(tmp_path: Path) -> None:
    with SampleStore(tmp_path / "s.db") as store:
        store.add(_r(1.0), session="alpha")
        store.add(_r(2.0), session="alpha")
        store.add(_r(3.0), session="beta")
        n = store.clear(session="alpha")
        assert n == 2
        assert len(store.list(session="alpha")) == 0
        assert len(store.list(session="beta")) == 1


def test_stats_empty() -> None:
    with SampleStore(":memory:") as store:
        st = store.stats()
        assert st.count == 0
        assert st.min_g is None
        assert st.mean_g is None


def test_stats_basic() -> None:
    with SampleStore(":memory:") as store:
        for w in (10.0, 20.0, 30.0):
            store.add(_r(w))
        st = store.stats()
        assert st.count == 3
        assert st.min_g == pytest.approx(10.0)
        assert st.max_g == pytest.approx(30.0)
        assert st.mean_g == pytest.approx(20.0)
        assert st.sum_g == pytest.approx(60.0)
        # population stdev: sqrt(((10-20)**2+(20-20)**2+(30-20)**2)/3) ~ 8.165
        assert st.stdev_g == pytest.approx(8.16497, rel=1e-3)


def test_csv_export() -> None:
    with SampleStore(":memory:") as store:
        store.add(_r(1.5), label="L1", note="hi")
        store.add(_r(-2.5), label="L2")
        csv_str = store.to_csv(store.list())
        lines = csv_str.strip().splitlines()
        assert lines[0] == "id,ts,weight_g,unit,stable,label,note,session"
        assert "1.5000" in csv_str
        assert "-2.5000" in csv_str


def test_concurrent_writes(tmp_path: Path) -> None:
    with SampleStore(tmp_path / "s.db") as store:
        def worker(n: int) -> None:
            for i in range(n):
                store.add(_r(float(i)))
        threads = [threading.Thread(target=worker, args=(15,)) for _ in range(4)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert store.stats().count == 60
