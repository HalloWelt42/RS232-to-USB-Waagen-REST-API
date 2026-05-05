"""Serielles Lesen von der Waage.

Dünner Wrapper um pyserial mit Frame-basiertem Lesen. Akzeptiert sowohl
``\\r\\n`` als auch ``\\n`` als Terminator und behandelt unvollständige
Frames über einen internen Puffer.
"""

from __future__ import annotations

import logging
import time
from contextlib import AbstractContextManager
from typing import Iterator, Optional

import serial

from .parser import Reading, parse

log = logging.getLogger(__name__)

DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_BAUD = 9600
DEFAULT_TIMEOUT = 2.0
MAX_BUFFER_BYTES = 4096  # Schutz gegen unbegrenzten Pufferaufbau bei Müll


class Waage(AbstractContextManager["Waage"]):
    """Kontextmanager für die serielle Verbindung zur Waage.

    Beispiel::

        with Waage("/dev/ttyUSB0", 9600) as w:
            for reading in w.stream():
                print(reading.weight, reading.stable)

    Der Reader puffert eingehende Bytes intern, sodass Frames auch dann
    korrekt erkannt werden, wenn sie über mehrere ``read()``-Aufrufe
    verteilt ankommen.
    """

    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baudrate: int = DEFAULT_BAUD,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._ser: Optional[serial.Serial] = None
        self._buf = bytearray()

    def __enter__(self) -> "Waage":
        self._ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
        )
        return self

    def __exit__(self, *exc) -> None:
        if self._ser is not None:
            self._ser.close()
            self._ser = None

    def _take_frame(self) -> Optional[bytes]:
        """Versucht, ein vollständiges Frame aus dem Puffer zu extrahieren.

        Sucht den ersten Newline (``\\n``) im Puffer; alles davor (inkl.
        ``\\r``) wird als Frame zurückgegeben. ``None`` wenn der Puffer
        kein vollständiges Frame enthält.
        """
        idx = self._buf.find(b"\n")
        if idx == -1:
            return None
        frame = bytes(self._buf[: idx + 1])
        del self._buf[: idx + 1]
        return frame

    def read_one(self) -> Optional[Reading]:
        """Liest genau ein Frame und gibt das geparste ``Reading`` zurück.

        Returns:
            ``Reading`` bei erfolgreichem Lesen + Parsen, ``None`` bei
            Timeout oder nicht parsbarem Frame. Bei nicht-parsbaren
            Frames wird zur nächsten Frame-Grenze gesprungen — der Aufrufer
            kann erneut aufrufen.
        """
        if self._ser is None:
            raise RuntimeError("Waage nicht geöffnet — als Kontextmanager benutzen")

        frame = self._take_frame()
        if frame is None:
            chunk = self._ser.read(256) or b""
            if not chunk:
                return None
            self._buf.extend(chunk)
            if len(self._buf) > MAX_BUFFER_BYTES:
                # Notbremse: wenn nie ein Newline kommt, Puffer flushen
                log.warning("Puffer ohne Terminator gefüllt, flushe %d Bytes",
                            len(self._buf))
                self._buf.clear()
                return None
            frame = self._take_frame()
            if frame is None:
                return None

        return parse(frame)

    def stream(self) -> Iterator[Reading]:
        """Endloser Iterator über erfolgreich geparste Readings.

        Timeouts und kaputte Frames werden übersprungen. Bricht erst bei
        Exception ab (z.B. wenn der Port verschwindet).
        """
        while True:
            try:
                reading = self.read_one()
            except serial.SerialException:
                log.exception("Serial error — Verbindung abgebrochen")
                raise
            if reading is not None:
                yield reading
            elif self._ser is not None and not self._ser.in_waiting:
                # Kurze Pause bei leerem Bus, damit CPU nicht heißläuft
                time.sleep(0.01)
