"""Software-Simulation der G&G-Waage.

Liefert realistische Frames mit Gewichtsänderungen, Stable/Unstable-
Übergängen und Mess-Jitter, ohne dass eine echte Waage am seriellen Port
hängen muss. Praktisch für UI-Demos, Frontend-Entwicklung und
End-to-End-Tests gegen das Backend.

Frame-Format wie in der offiziellen G&G-Anleitung (Kapitel 5.1)
beschrieben:

    [Sign 2B] [Data 7B] [Unit 3B] [CR] [LF]
    Beispiel:  b' -12.345 kg\\r\\n'

Das Verhalten orientiert sich an einer realistisch bedienten Waage:

- Anfangs leer (0 g), stabil
- Alle paar Sekunden ändert sich das Zielgewicht (jemand legt etwas auf,
  korrigiert oder leert)
- Beim Übergang zum neuen Wert läuft die Anzeige unstabil mit Jitter
- Bei Annäherung ans Ziel wird der Frame als stabil markiert
- Auflösung 0,1 g wie bei der echten Waage
"""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Iterator, Optional

from .parser import Reading


class SimulatedWaage:
    """Drop-in-Ersatz für ``Waage`` ohne Hardware.

    Implementiert das gleiche Kontextmanager- und ``read_one()``-Protokoll,
    sodass der Reader-Loop in ``waage.api`` ohne Codeänderung beide
    Quellen verwenden kann.

    Args:
        port:           Wird ignoriert, nur zur API-Symmetrie vorhanden.
        baudrate:       dito.
        frame_rate_hz:  Frames pro Sekunde, Default 4 wie bei vielen
                        echten Waagen.
        seed:           Optionaler Seed für reproduzierbare Sequenzen
                        (vor allem für Tests).
    """

    # Zustandsmarker
    PHASE_IDLE = "idle"          # bei 0 g, lange Wartezeit
    PHASE_RAMP = "ramp"          # läuft auf neues Ziel zu
    PHASE_STABLE = "stable"      # am Ziel, kleines Jitter

    def __init__(
        self,
        port: str = "sim://",
        baudrate: int = 9600,
        frame_rate_hz: float = 4.0,
        seed: Optional[int] = None,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self._frame_period = 1.0 / max(frame_rate_hz, 0.1)
        self._rng = random.Random(seed)

        self._target = 0.0
        self._current = 0.0
        self._phase = self.PHASE_IDLE
        self._next_change_at = self._now() + self._rng.uniform(6.0, 12.0)
        self._next_frame_at = self._now()
        self._stable_count = 0  # wie viele Frames in Folge nahe am Ziel

    # In Tests überschreibbar, damit die Simulation deterministisch und
    # ohne echten Sleep abläuft.
    def _now(self) -> float:
        return time.monotonic()

    def _sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    def send_command(self, command: bytes) -> None:
        """Reagiert auf Fernsteuerkommandos im Simulator.

        Tara setzt das Zielgewicht auf 0 zurück. Andere Kommandos werden
        ohne sichtbare Auswirkung akzeptiert (das UI bekommt aber den
        OK-Status), damit das Frontend gegen den Simulator entwickelt
        werden kann.
        """
        if not command:
            return
        # ESC t = Tara
        if command in (b"\x1bt", b"t"):
            self._target = 0.0
            self._next_change_at = self._now() + self._rng.uniform(8.0, 16.0)
            self._phase = self.PHASE_RAMP
            self._stable_count = 0

    def __enter__(self) -> "SimulatedWaage":
        return self

    def __exit__(self, *exc) -> None:
        return None

    # ------------------------------------------------------------------
    #  Zustands-Transitionen
    # ------------------------------------------------------------------
    def _maybe_pick_new_target(self, now: float) -> None:
        if now < self._next_change_at:
            return
        roll = self._rng.random()
        if self._phase == self.PHASE_IDLE:
            # Aus der Ruhe: 70 % auflegen, 30 % bleiben
            if roll < 0.7:
                self._target = round(self._rng.uniform(50.0, 3000.0), 1)
            else:
                self._target = 0.0
            self._next_change_at = now + self._rng.uniform(8.0, 16.0)
        else:
            # Im aktiven Betrieb: 30 % entfernen, 30 % korrigieren,
            # 40 % neuer Wert
            if roll < 0.3:
                self._target = 0.0
            elif roll < 0.6 and self._target > 100.0:
                delta = self._rng.uniform(-150.0, 150.0)
                self._target = max(0.0, round(self._target + delta, 1))
            else:
                self._target = round(self._rng.uniform(50.0, 3000.0), 1)
            self._next_change_at = now + self._rng.uniform(6.0, 20.0)
        self._phase = self.PHASE_RAMP
        self._stable_count = 0

    def _step_current(self) -> bool:
        """Bewegt ``_current`` Richtung ``_target`` und liefert ``stable``."""
        diff = self._target - self._current

        # In Ruhephasen (IDLE, STABLE) bleibt das Frame stabil mit kleinem
        # Jitter — wie bei einer echten Waage, die ihr Gewicht hält.
        if self._phase in (self.PHASE_IDLE, self.PHASE_STABLE):
            self._current = self._target + self._rng.uniform(-0.05, 0.05)
            return True

        # Phase RAMP: Anzeige läuft auf das neue Ziel zu.
        if abs(diff) < 0.15:
            self._stable_count += 1
            self._current = self._target + self._rng.uniform(-0.08, 0.08)
            # Drei Settling-Frames mit leichter Bewegung melden noch instabil
            if self._stable_count >= 3:
                self._phase = (
                    self.PHASE_IDLE if self._target == 0.0
                    else self.PHASE_STABLE
                )
                return True
            return False

        # Auf dem Weg zum Ziel: 50 % der Differenz pro Frame plus Jitter
        step = diff * 0.5
        jitter = self._rng.uniform(-2.5, 2.5)
        self._current = round(self._current + step + jitter, 1)
        self._stable_count = 0
        return False

    # ------------------------------------------------------------------
    #  Frame-Erzeugung
    # ------------------------------------------------------------------
    @staticmethod
    def _build_frame(weight_g: float, stable: bool) -> bytes:
        """Erzeugt rohe Bytes im G&G-Format (Kapitel 5.1 der Anleitung).

        Format:  [Sign 2B] [Data 7B] [Unit 3B] [CR] [LF]
        Beispiel positiv:   b'    12.3 g  \\r\\n'  (zwei Leerzeichen vor Wert,
                            Padding-Spaces am Ende der Einheit)
        Beispiel negativ:   b'   -12.3 g  \\r\\n'

        Bei einer echten G&G-Waage gibt es keinen Stable/Unstable-Tag im
        Frame — die Print-Antwort kommt nur, wenn der Wert sinnvoll ist.
        Damit der Simulator dem Frontend trotzdem realistische Übergänge
        zeigen kann, wird der Stable-Status über das Status-Byte ausserhalb
        des Frames mitgeführt; im Frame selbst landet ausschliesslich das
        G&G-Format.
        """
        sign = "-" if weight_g < 0 else " "
        magnitude = abs(weight_g)
        # 7 Byte Datenfeld, rechtsbündig, eine Nachkommastelle
        data = f"{magnitude:6.1f}"           # z.B. "  12.3"
        # Einheit auf 3 Byte padden
        unit = f"{'g':<3}"                   # "g  "
        return f"{sign}{data} {unit}\r\n".encode("ascii")

    # ------------------------------------------------------------------
    #  Öffentliche API (deckungsgleich zu ``waage.reader.Waage``)
    # ------------------------------------------------------------------
    def read_one(self) -> Optional[Reading]:
        # Frame-Rate respektieren, damit der Stream nicht im Stakkato läuft
        now = self._now()
        wait = self._next_frame_at - now
        if wait > 0:
            self._sleep(wait)
            now = self._now()
        self._next_frame_at = now + self._frame_period

        self._maybe_pick_new_target(now)
        stable = self._step_current()
        weight_display = round(self._current, 1)
        frame = self._build_frame(weight_display, stable)

        return Reading(
            weight=weight_display,
            unit="g",
            stable=stable,
            raw=frame,
            timestamp=datetime.now(),
        )

    def stream(self) -> Iterator[Reading]:
        while True:
            r = self.read_one()
            if r is not None:
                yield r
