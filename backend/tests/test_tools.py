"""Tests für ``waage.tools.find_serial_port``."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from waage import tools


def _port(device, vid=None, pid=None, serial_number=None):
    return SimpleNamespace(
        device=device, name=device.rsplit("/", 1)[-1],
        description="", vid=vid, pid=pid,
        serial_number=serial_number, manufacturer=None,
    )


def test_find_returns_none_without_ports():
    with patch("waage.tools.serial.tools.list_ports.comports", return_value=[]):
        assert tools.find_serial_port() is None


def test_find_returns_ftdi_match():
    ports = [
        _port("/dev/ttyAMA0"),
        _port("/dev/ttyUSB0", vid=0x0403, pid=0x6001, serial_number="FTEQZ0TS"),
    ]
    with patch("waage.tools.serial.tools.list_ports.comports", return_value=ports):
        assert tools.find_serial_port() == "/dev/ttyUSB0"


def test_find_returns_cp210x_match():
    ports = [_port("/dev/ttyUSB1", vid=0x10C4, pid=0xEA60)]
    with patch("waage.tools.serial.tools.list_ports.comports", return_value=ports):
        assert tools.find_serial_port() == "/dev/ttyUSB1"


def test_find_falls_back_to_path_hint():
    """Ohne VID/PID nimmt die Funktion den ersten Pfad mit ttyUSB/usbserial."""
    ports = [
        _port("/dev/ttyAMA0"),
        _port("/dev/ttyUSB0"),  # kein VID/PID, aber Pfad passt
    ]
    with patch("waage.tools.serial.tools.list_ports.comports", return_value=ports):
        assert tools.find_serial_port() == "/dev/ttyUSB0"


def test_find_macos_prefers_cu_over_tty():
    """Auf macOS soll cu.* statt tty.* zurückgegeben werden."""
    ports = [
        _port("/dev/tty.usbserial-FTEQZ0TS",
              vid=0x0403, pid=0x6001, serial_number="FTEQZ0TS"),
        _port("/dev/cu.usbserial-FTEQZ0TS",
              vid=0x0403, pid=0x6001, serial_number="FTEQZ0TS"),
    ]
    with patch("waage.tools.sys.platform", "darwin"):
        with patch("waage.tools.serial.tools.list_ports.comports", return_value=ports):
            assert tools.find_serial_port() == "/dev/cu.usbserial-FTEQZ0TS"


def test_find_with_preferred():
    ports = [_port("/dev/ttyUSB0", vid=0x0403, pid=0x6001)]
    with patch("waage.tools.serial.tools.list_ports.comports", return_value=ports):
        assert tools.find_serial_port(preferred="/dev/ttyUSB0") == "/dev/ttyUSB0"


def test_list_serial_ports_returns_dicts():
    ports = [_port("/dev/ttyUSB0", vid=0x0403, pid=0x6001, serial_number="X")]
    with patch("waage.tools.serial.tools.list_ports.comports", return_value=ports):
        result = tools.list_serial_ports()
    assert len(result) == 1
    assert result[0]["device"] == "/dev/ttyUSB0"
    assert result[0]["vid"] == 0x0403
    assert result[0]["serial_number"] == "X"
