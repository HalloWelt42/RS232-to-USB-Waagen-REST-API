"""Serielles Lesen von der Waage.

Dünner Wrapper um pyserial mit Frame-basiertem Lesen. Akzeptiert sowohl
``\\r\\n`` als auch ``\\n`` als Terminator und behandelt unvollständige
Frames über einen internen Puffer.
"""

from __future__ import annotations

import logging
import threading
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

# G&G-Standard-Print-Befehl (Werkseinstellung Adresse 0x1B = ESC, plus 'p')
DEFAULT_POLL_COMMAND = b"\x1bp"
DEFAULT_POLL_INTERVAL = 0.5

# G&G-Fernsteuerkommandos laut Anleitung Kapitel 5.2
COMMAND_PRINT     = b"\x1bp"   # Datenanforderung (Print)
COMMAND_CALIBRATE = b"\x1bq"   # Kalibrierfunktion (gefährlich!)
COMMAND_COUNT     = b"\x1br"   # Stückzählung an der Waage aktivieren
COMMAND_UNIT      = b"\x1bs"   # Einheit umschalten
COMMAND_TARE      = b"\x1bt"   # Tara setzen
COMMAND_LIGHT     = b"\x1bu"   # Beleuchtung umschalten


class Waage(AbstractContextManager["Waage"]):
    """Kontextmanager für die serielle Verbindung zur Waage.

    Beispiel::

        with Waage("/dev/ttyUSB0", 9600) as w:
            for reading in w.stream():
                print(reading.weight, reading.stable)

    Der Reader puffert eingehende Bytes intern, sodass Frames auch dann
    korrekt erkannt werden, wenn sie über mehrere ``read()``-Aufrufe
    verteilt ankommen.

    G&G-Waagen senden im Standard nur auf einen Print-Befehl. Über die
    Parameter ``poll_command`` und ``poll_interval`` kann der Reader
    aktiv pollen — bei jedem Aufruf von ``read_one()`` wird, sofern seit
    dem letzten Polling mindestens ``poll_interval`` Sekunden vergangen
    sind, der Befehl gesendet, und auf die Antwort gewartet. Setze
    ``poll_command=None`` für rein passives Lesen (z.B. bei Waagen mit
    aktivem Stream-Mode oder Waagen mit Stable-Auto-Send).
    """

    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baudrate: int = DEFAULT_BAUD,
        timeout: float = DEFAULT_TIMEOUT,
        poll_command: Optional[bytes] = DEFAULT_POLL_COMMAND,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.poll_command = poll_command
        self.poll_interval = poll_interval
        self._ser: Optional[serial.Serial] = None
        self._buf = bytearray()
        self._last_poll: float = 0.0
        # Lock zum thread-sicheren Senden ad-hoc-Kommandos, falls der
        # Reader-Thread parallel pollt.
        self._write_lock = threading.Lock()

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

    def close(self) -> None:
        """Schließt den seriellen Port. Idempotent.

        Wird vom Live/Simulator-Source-Switch aufgerufen, damit der
        Reader-Loop einen Reconnect mit der neuen Factory ausführt.
        """
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:  # noqa: BLE001
                log.exception("Serieller Port konnte nicht sauber geschlossen werden")
            self._ser = None

    def __exit__(self, *exc) -> None:
        self.close()

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

    def _maybe_poll(self) -> None:
        """Sendet den Print-Befehl, wenn das Polling-Intervall abgelaufen ist."""
        if self.poll_command is None or self._ser is None:
            return
        now = time.monotonic()
        if now - self._last_poll < self.poll_interval:
            return
        try:
            with self._write_lock:
                self._ser.write(self.poll_command)
        except serial.SerialException:
            log.exception("Polling-Befehl konnte nicht gesendet werden")
            raise
        self._last_poll = now

    def send_command(self, command: bytes) -> None:
        """Sendet ein beliebiges Bytes-Kommando an die Waage.

        Thread-sicher gegenüber dem Polling im Reader-Loop. Wird typisch
        für die G&G-Fernsteuerkommandos (Tara, Unit, Light, ...) genutzt.
        """
        if self._ser is None:
            raise RuntimeError("Waage nicht geöffnet — als Kontextmanager benutzen")
        if not command:
            return
        with self._write_lock:
            self._ser.write(command)

    def read_one(self) -> Optional[Reading]:
        """Liest genau ein Frame und gibt das geparste ``Reading`` zurück.

        Wenn ``poll_command`` gesetzt ist, wird vor dem Lesen ggf. ein
        Print-Befehl an die Waage geschickt — typisch für G&G-Waagen, die
        nur auf Anforderung antworten.

        Returns:
            ``Reading`` bei erfolgreichem Lesen + Parsen, ``None`` bei
            Timeout oder nicht parsbarem Frame. Bei nicht-parsbaren
            Frames wird zur nächsten Frame-Grenze gesprungen — der Aufrufer
            kann erneut aufrufen.
        """
        if self._ser is None:
            raise RuntimeError("Waage nicht geöffnet — als Kontextmanager benutzen")

        self._maybe_poll()

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
