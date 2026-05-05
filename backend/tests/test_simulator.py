"""Tests für ``waage.simulator.SimulatedWaage``.

Die Simulation wird mit hoher Frame-Rate und festem Seed gefahren, damit
die Tests in Bruchteilen einer Sekunde durchlaufen und reproduzierbar sind.
"""

from __future__ import annotations

import re

import pytest

from waage.parser import Reading, parse
from waage.simulator import SimulatedWaage


@pytest.fixture
def fast_sim() -> SimulatedWaage:
    """Simulator mit deaktiviertem Sleep für schnelle Tests."""
    sim = SimulatedWaage(frame_rate_hz=1000.0, seed=42)
    sim._sleep = lambda s: None
    return sim


def test_read_one_returns_reading(fast_sim: SimulatedWaage) -> None:
    with fast_sim as w:
        r = w.read_one()
    assert isinstance(r, Reading)
    assert r.unit == "g"
    assert isinstance(r.weight, float)


def test_first_frame_is_at_zero_and_stable(fast_sim: SimulatedWaage) -> None:
    """Direkt nach Start: Waage ist leer und stable."""
    with fast_sim as w:
        # Die ersten paar Frames müssen stabil bei ~0 sein
        for _ in range(3):
            r = w.read_one()
            assert abs(r.weight) < 0.5
            assert r.stable is True


def test_raw_frame_is_parsable(fast_sim: SimulatedWaage) -> None:
    """Die erzeugten Frames müssen mit dem echten Parser kompatibel sein."""
    with fast_sim as w:
        for _ in range(20):
            r = w.read_one()
            roundtrip = parse(r.raw)
            assert roundtrip is not None, f"unparsable frame: {r.raw!r}"
            assert roundtrip.unit == r.unit
            assert roundtrip.stable == r.stable
            # Gewicht stimmt bis auf Rundung
            assert abs(roundtrip.weight - r.weight) < 0.01


def test_raw_frame_format(fast_sim: SimulatedWaage) -> None:
    """Frames passen zum offiziellen G&G-Format aus Kapitel 5.1 der Anleitung.

    Aufbau: [Sign 2B][Data 7B][Unit 3B][CR][LF]
    Beispiele: b'    12.3 g  \\r\\n', b'   -50.0 g  \\r\\n'
    """
    pattern = re.compile(rb"^[ -]\s*\d+\.\d g\s*\r\n$")
    with fast_sim as w:
        for _ in range(5):
            r = w.read_one()
            assert pattern.match(r.raw), f"unexpected format: {r.raw!r}"
            # Niemals ein ST/US-Tag im G&G-Frame
            assert not r.raw.startswith((b"ST", b"US"))


def test_simulator_eventually_changes_weight(fast_sim: SimulatedWaage) -> None:
    """Innerhalb von ein paar hundert Frames muss sich was tun."""
    with fast_sim as w:
        # Zustands-Wechsel-Zeit künstlich verkürzen, damit es schneller geht
        w._next_change_at = 0.0
        weights = [w.read_one().weight for _ in range(100)]
    distinct = set(round(x, 1) for x in weights)
    assert len(distinct) > 5, f"zu wenig Variation: {distinct}"


def test_simulator_produces_both_stable_and_unstable(
    fast_sim: SimulatedWaage,
) -> None:
    """Über eine längere Sequenz müssen beide Status vorkommen."""
    with fast_sim as w:
        w._next_change_at = 0.0
        flags = set()
        for _ in range(200):
            r = w.read_one()
            flags.add(r.stable)
            if len(flags) == 2:
                break
    assert flags == {True, False}, f"nur {flags} gesehen"


def test_seed_makes_sequence_deterministic() -> None:
    """Gleicher Seed -> gleiche Frame-Sequenz."""
    a = SimulatedWaage(frame_rate_hz=1000.0, seed=123)
    b = SimulatedWaage(frame_rate_hz=1000.0, seed=123)
    a._sleep = lambda s: None
    b._sleep = lambda s: None
    a._next_change_at = 0.0
    b._next_change_at = 0.0
    seq_a = [a.read_one().weight for _ in range(50)]
    seq_b = [b.read_one().weight for _ in range(50)]
    assert seq_a == seq_b


def test_stream_yields_indefinitely(fast_sim: SimulatedWaage) -> None:
    with fast_sim as w:
        gen = w.stream()
        first = next(gen)
        second = next(gen)
    assert isinstance(first, Reading)
    assert isinstance(second, Reading)
