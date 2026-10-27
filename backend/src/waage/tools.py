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

``locate_adapter`` beantwortet die Frage "steckt der Adapter gerade?"
für den konfigurierten Port (``WAAGE_PORT``): bei ``auto`` über die
Suche oben, bei einem festen Pfad über den Geräteknoten. Reader-Loop
und Gesundheit fragen beide hier nach, jedes Mal neu beim
Betriebssystem; ein später eingesteckter Adapter wird so ohne
Neustart gefunden.
"""

from __future__ import annotations

import logging
import os
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
                # debug statt info: die Gesundheit fragt alle paar
                # Sekunden nach, Übergänge loggt der Reader-Loop.
                log.debug("Erkannt: %s an %s (Seriennr. %s)",
                          label, p.device, p.serial_number or "-")
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
            log.debug("Fallback-Match: %s", p.device)
            return p.device

    log.debug("Kein passender serieller Port gefunden (geprüft: %s)",
              [p.device for p in ports])
    return None


AUTO_PORT = "auto"


class AdapterMissingError(RuntimeError):
    """Am konfigurierten bzw. gesuchten Port steckt gerade kein Adapter."""


def is_auto_port(configured: Optional[str]) -> bool:
    """True, wenn der Port automatisch gesucht werden soll (``auto``/leer)."""
    return not configured or configured == AUTO_PORT


def locate_adapter(configured: Optional[str]) -> Optional[str]:
    """Gerätepfad des Adapters, wenn er gerade angeschlossen ist, sonst None.

    Args:
        configured: Wert von ``WAAGE_PORT``. ``auto`` (oder leer) sucht
            über ``find_serial_port``; ein fester Pfad (``/dev/ttyUSB0``,
            ``COM3``) gilt als vorhanden, wenn der Geräteknoten existiert
            oder das Betriebssystem den Port listet.
    """
    if is_auto_port(configured):
        return find_serial_port()
    if os.path.exists(configured):
        return configured
    if any(p.device == configured for p in serial.tools.list_ports.comports()):
        return configured
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
