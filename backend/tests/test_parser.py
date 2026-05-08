"""Tests für ``waage.parser.parse``."""

from __future__ import annotations

import codecs
from datetime import datetime
from pathlib import Path

import pytest

from waage.parser import Reading, parse

FIXED_TS = datetime(2026, 1, 1, 12, 0, 0)


def _decode(literal: str) -> bytes:
    """``'ST,+  123.4 g\\r\\n'`` -> tatsächliche Bytes mit CR/LF."""
    return codecs.decode(literal, "unicode_escape").encode("ascii")


@pytest.mark.parametrize(
    ("frame_literal", "expected_weight", "expected_stable", "expected_unit"),
    [
        # Offizielles G&G-Format laut Anleitung Kap. 5.1:
        # [Sign 2B][Data 7B][Unit 3B][CR][LF]
        (r"    12.3 g  \r\n",           12.3,  True,  "g"),
        (r"   123.4 g  \r\n",          123.4,  True,  "g"),
        (r"  1234.5 g  \r\n",         1234.5,  True,  "g"),
        (r"     0.0 g  \r\n",            0.0,  True,  "g"),
        (r"   -50.0 g  \r\n",          -50.0,  True,  "g"),
        (r" -12.345 kg \r\n",       -12345.0,  True,  "kg"),
        # Variations ohne Padding (z.B. von Bluetooth-Bridge)
        (r"-1234.5 g\r\n",           -1234.5,  True,  "g"),
        (r"5999.9 g\n",               5999.9,  True,  "g"),
        # Alternativ-Format mit ST/US-Tag (toleriert, z.B. A&D, Kern)
        (r"ST,+  123.4 g\r\n",         123.4,  True,  "g"),
        (r"ST,+ 1234.5 g\r\n",        1234.5,  True,  "g"),
        (r"US,+   12.3 g\r\n",          12.3, False,  "g"),
        (r"ST,-    5.0 g\r\n",          -5.0,  True,  "g"),
        (r"ST,+   0.0 g\r\n",            0.0,  True,  "g"),
        (r"US,+ 5999.9 g\r\n",        5999.9, False,  "g"),
        (r"ST,+    1.234 kg\r\n",     1234.0,  True,  "kg"),
        (r"ST,-1234.5g\r\n",         -1234.5,  True,  "g"),
    ],
)
def test_parse_valid_frames(
    frame_literal: str,
    expected_weight: float,
    expected_stable: bool,
    expected_unit: str,
) -> None:
    frame = _decode(frame_literal)
    result = parse(frame, now=FIXED_TS)
    assert result is not None, f"parse({frame!r}) returned None"
    assert result.weight == pytest.approx(expected_weight)
    assert result.stable is expected_stable
    assert result.unit == expected_unit
    assert result.raw == frame
    assert result.timestamp == FIXED_TS


@pytest.mark.parametrize(
    "frame",
    [
        b"",
        b"\r\n",
        b"   \r\n",
        b"abc\r\n",
        b"ST,+ XYZ g\r\n",
        b"\x00\x01\x02",      # Nur Müll-Bytes
        # OL und ------ wandern in test_overload_frames_set_overload_flag
        # (sie sind seit 0.5.16 KEINE invaliden Frames mehr, sondern
        # Overload-Marker mit eigenem Flag).
    ],
)
def test_parse_invalid_frames_return_none(frame: bytes) -> None:
    assert parse(frame, now=FIXED_TS) is None


def test_kg_is_converted_to_grams() -> None:
    result = parse(b"ST,+  2.500 kg\r\n", now=FIXED_TS)
    assert result is not None
    assert result.weight == pytest.approx(2500.0)
    assert result.unit == "kg"  # Original-Einheit zur Anzeige bleibt erhalten


def test_reading_is_frozen() -> None:
    result = parse(b"ST,+  100.0 g\r\n", now=FIXED_TS)
    assert result is not None
    with pytest.raises(Exception):  # FrozenInstanceError ist eine AttributeError-Subklasse
        result.weight = 999.0  # type: ignore[misc]


def test_fixture_file_loads_and_parses() -> None:
    """Smoke-Test: alle Zeilen in sample_frames.txt parsen ohne Crash."""
    fixtures = Path(__file__).parent / "fixtures" / "sample_frames.txt"
    parsed = 0
    total = 0
    for line in fixtures.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        total += 1
        frame = _decode(line)
        if parse(frame, now=FIXED_TS) is not None:
            parsed += 1
    assert total > 0, "Fixture-Datei hat keine Test-Frames"
    assert parsed == total, f"{total - parsed}/{total} Frames nicht geparst"


def test_negative_weight_with_kg() -> None:
    result = parse(b"ST,-  1.500 kg\r\n", now=FIXED_TS)
    assert result is not None
    assert result.weight == pytest.approx(-1500.0)


def test_no_status_tag_assumes_stable() -> None:
    result = parse(b"  +50.0 g\r\n", now=FIXED_TS)
    assert result is not None
    assert result.stable is True


# ---------------- Overload-Frames ----------------
@pytest.mark.parametrize("frame", [
    b"OL\r\n",
    b" OL g\r\n",
    b"  OL kg\r\n",
    b"+OL\r\n",
    b"------\r\n",
    b"++++++\r\n",
    b"  ----- \r\n",
    b"ovr\r\n",
    b"unr\r\n",
])
def test_overload_frames_set_overload_flag(frame: bytes) -> None:
    """Overload-/Underload-Frames werden als gültiges Reading erkannt,
    aber mit `overload=True` markiert. So zeigt die UI ein klares
    Warn-Banner statt den letzten echten Wert eingefroren weiter
    anzuzeigen."""
    r = parse(frame, now=FIXED_TS)
    assert r is not None, f"Frame {frame!r} sollte als Overload erkannt werden"
    assert r.overload is True
    assert r.stable is False
    # Ungültiger Wert wird auf 0.0 gesetzt — UI muss `overload` prüfen.
    assert r.weight == 0.0


def test_normal_frame_is_not_overload() -> None:
    """Reguläre Wäge-Frames haben overload=False."""
    r = parse(b"  +123.4 g\r\n", now=FIXED_TS)
    assert r is not None
    assert r.overload is False
    assert r.weight == pytest.approx(123.4)
