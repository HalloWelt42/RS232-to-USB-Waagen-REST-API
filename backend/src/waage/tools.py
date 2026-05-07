"""Hilfsfunktionen rund um die Hardware-Erkennung.

``find_serial_port`` durchsucht die im Betriebssystem registrierten
seriellen Schnittstellen nach einem passenden FTDI- oder USB-Serial-
Adapter. Funktioniert plattformübergreifend (Linux, macOS, Raspberry Pi):

- Linux/Pi:  ``/dev/ttyUSB0``, ``/dev/ttyACM0``, ``/dev/ttyAMA0``, ...
- macOS:     ``/dev/cu.usbserial-FTEQZ0TS``, ``/dev/cu.usbmodem...``
- (Windows: ``COM3``, COM4 — falls jemand das mal braucht)

Erkannt wird primär über VID/PID des FTDI-Chips. Fällt das aus, sucht
die Funktion nach typischen Pfad-Bestandteilen (``usbserial``,
``ttyUSB``, ``ttyACM``).
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

import serial.tools.list_ports

log = logging.getLogger(__name__)

# Bekannte VID/PID-Kombinationen für USB-Serial-Adapter mit Waagen-Eignung
_KNOWN_DEVICES: list[tuple[int, int, str]] = [
    (0x0403, 0x6001, "FTDI FT232R"),
    (0x0403, 0x6011, "FTDI FT4232H"),
    (0x0403, 0x6014, "FTDI FT232H"),
    (0x0403, 0x6015, "FTDI FT-X"),
    (0x10C4, 0xEA60, "Silicon Labs CP210x"),
    (0x067B, 0x2303, "Prolific PL2303"),
    (0x1A86, 0x7523, "QinHeng CH340"),
]

# Pfad-Heuristiken für den Fall, dass VID/PID nicht zugeordnet werden konnten
_PATH_HINTS = ("usbserial", "ttyUSB", "ttyACM", "usbmodem", "wchusbserial")


def find_serial_port(preferred: Optional[str] = None) -> Optional[str]:
    """Findet den ersten passenden seriellen Port.

    Args:
        preferred: Falls gesetzt und der Pfad existiert/auflistbar ist,
            wird er bevorzugt zurückgegeben.

    Returns:
        Geräte-Pfad (z.B. ``/dev/ttyUSB0`` oder
        ``/dev/cu.usbserial-FTEQZ0TS``) oder ``None``.
    """
    ports = list(serial.tools.list_ports.comports())

    if preferred:
        for p in ports:
            if p.device == preferred:
                return preferred

    # 1) Erst nach bekannten VID/PID-Kombinationen suchen
    for p in ports:
        for vid, pid, label in _KNOWN_DEVICES:
            if p.vid == vid and p.pid == pid:
                log.info("Erkannt: %s an %s (Seriennr. %s)",
                         label, p.device, p.serial_number or "—")
                # macOS: bevorzugt cu.* statt tty.* (cu blockiert nicht
                # auf DCD wie tty es tut). pyserial liefert beides; wenn
                # wir tty.* finden, suchen wir das passende cu.* dazu.
                if sys.platform == "darwin" and p.device.startswith("/dev/tty."):
                    cu_path = p.device.replace("/dev/tty.", "/dev/cu.")
                    for q in ports:
                        if q.device == cu_path:
                            return cu_path
                return p.device

    # 2) Fallback über Pfad-Heuristik (VID/PID kann fehlen, z.B. virtuelle
    #    Ports oder ältere Kernel)
    for p in ports:
        if any(hint in (p.device or "") for hint in _PATH_HINTS):
            log.info("Fallback-Match: %s", p.device)
            return p.device

    log.warning("Kein passender serieller Port gefunden (geprüft: %s)",
                [p.device for p in ports])
    return None


def list_serial_ports() -> list[dict]:
    """Listet alle bekannten seriellen Ports mit Metadaten — zum Debuggen."""
    return [
        {
            "device": p.device,
            "name": p.name,
            "description": p.description,
            "vid": p.vid,
            "pid": p.pid,
            "serial_number": p.serial_number,
            "manufacturer": p.manufacturer,
        }
        for p in serial.tools.list_ports.comports()
    ]
