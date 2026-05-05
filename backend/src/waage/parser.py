"""Frame-Parser für G&G-Waagen-Frames.

Reine Funktion: rohe Bytes rein, ``Reading`` raus (oder ``None``, wenn das
Frame nicht passt). Hardware-frei und vollständig testbar mit Fixtures.

Primäres Format (offizielle G&G-Anleitung, Kapitel 5.1):

    [Sign 2B] [Data 7B] [Unit 3B] [CR] [LF]
    Beispiel:  b' -12.345 kg\\r\\n'

Bei G&G-Frames gibt es kein explizites Stable/Unstable-Flag im Frame —
die Übertragung erfolgt einmalig auf den Print-Befehl ``ESC p`` (oder
schlicht ``p``), das Ergebnis ist implizit der aktuelle Anzeigewert.
Wir setzen ``stable=True`` für G&G-Frames, da die Waage bei einer
schwankenden Anzeige typischerweise nicht antwortet.

Zusätzlich akzeptiert der Parser tolerant ein verbreitetes Alternativ-
Format mit ST/US-Status-Tag (z.B. bei A&D- oder Kern-Waagen):

    b'ST,+  123.4 g\\r\\n'   stable, positiv
    b'US,-   12.3 g\\r\\n'   unstable, negativ

Beide Terminatoren ``\\r\\n`` und einzelnes ``\\n`` werden akzeptiert,
führende und trailing Whitespaces toleriert.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Bekannte Einheiten in der Reihenfolge, wie sie geparst werden dürfen.
_UNIT_TO_GRAMS = {
    "g": 1.0,
    "kg": 1000.0,
    "ct": 0.2,        # Karat (manche G&G-Modelle), 1 ct = 0.2 g
    "oz": 28.3495,    # Unze
    "lb": 453.592,    # Pfund
}

# (?P<status>...)?  optional Status-Tag (ST/US/QT)
# (?P<sign>[+-])?   optional Vorzeichen
# (?P<value>...)    Zahl mit oder ohne Dezimalpunkt
# (?P<unit>...)     Einheit am Ende — Reihenfolge wichtig: kg vor g!
_FRAME_RE = re.compile(
    rb"^\s*"
    rb"(?:(?P<status>ST|US|QT)\s*,?\s*)?"
    rb"(?P<sign>[+-])?\s*"
    rb"(?P<value>\d+(?:\.\d+)?)\s*"
    rb"(?P<unit>kg|ct|oz|lb|g)"
    rb"\s*$"
)


@dataclass(frozen=True, slots=True)
class Reading:
    """Eine einzelne Wägung — Ergebnis von :func:`parse`.

    Attributes:
        weight: Gewicht in Gramm (immer; kg/oz/lb werden konvertiert).
        unit: Original-Einheit aus dem Frame (zur Anzeige).
        stable: True wenn Frame mit ``ST`` markiert war oder kein Status-Tag
            vorhanden war (dann wird per Konvention stable=True angenommen).
            False bei ``US``-Frames.
        raw: Original-Frame als Bytes — für Diagnose und Logging.
        timestamp: Zeitpunkt des Parsens.
    """

    weight: float
    unit: str
    stable: bool
    raw: bytes
    timestamp: datetime


def parse(frame: bytes, *, now: Optional[datetime] = None) -> Optional[Reading]:
    """Parst ein einzelnes Frame.

    Args:
        frame: Rohe Bytes inkl. oder ohne Terminator.
        now: Optionaler Zeitstempel (für deterministische Tests). Default
             ist :func:`datetime.now`.

    Returns:
        ``Reading`` bei erfolgreichem Parse, sonst ``None`` (z.B. bei
        Overload, leerem Frame oder unbekanntem Format).
    """
    if not frame:
        return None

    cleaned = frame.strip()
    if not cleaned:
        return None

    match = _FRAME_RE.match(cleaned)
    if not match:
        return None

    status = match.group("status")
    sign = match.group("sign") or b"+"
    value_bytes = match.group("value")
    unit_bytes = match.group("unit")

    try:
        value = float(value_bytes)
    except ValueError:
        return None

    if sign == b"-":
        value = -value

    unit = unit_bytes.decode("ascii")
    factor = _UNIT_TO_GRAMS.get(unit)
    if factor is None:
        return None
    weight_g = value * factor

    # Ohne Status-Tag wird stable=True angenommen (typisch für simple Frames).
    stable = status != b"US"

    return Reading(
        weight=weight_g,
        unit=unit,
        stable=stable,
        raw=bytes(frame),
        timestamp=now or datetime.now(),
    )
