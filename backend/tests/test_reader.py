"""Tests für ``waage.reader.Waage``.

Hardware-frei — `pyserial` wird durch `serial.serial_for_url('loop://')`
oder einen einfachen Stub ersetzt.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from waage.reader import Waage


class _FakeSerial:
    """Minimaler pyserial-Ersatz mit korrektem Partial-Read-Verhalten."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._buf = bytearray(b"".join(chunks))
        self.is_open = True
        self.in_waiting = 0
        self.writes: list[bytes] = []

    def read(self, size: int = 1) -> bytes:
        if not self._buf:
            return b""
        n = min(size, len(self._buf))
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def write(self, data: bytes) -> int:
        self.writes.append(bytes(data))
        return len(data)

    def close(self) -> None:
        self.is_open = False


def _patch_serial(chunks: list[bytes]):
    fake = _FakeSerial(chunks)
    return patch("waage.reader.serial.Serial", return_value=fake), fake


def test_read_one_extracts_complete_frame() -> None:
    patcher, _ = _patch_serial([b"ST,+  100.0 g\r\n"])
    with patcher, Waage("/dev/ttyUSB0") as w:
        r = w.read_one()
    assert r is not None
    assert r.weight == pytest.approx(100.0)
    assert r.stable is True


def test_read_one_handles_split_frames() -> None:
    """Frame über mehrere ``read()``-Aufrufe verteilt -> korrekt zusammengesetzt."""
    patcher, _ = _patch_serial([b"ST,+  ", b"50.0 g", b"\r\n"])
    with patcher, Waage("/dev/ttyUSB0") as w:
        r = None
        for _ in range(5):
            r = w.read_one()
            if r is not None:
                break
    assert r is not None
    assert r.weight == pytest.approx(50.0)


def test_read_one_returns_none_on_timeout() -> None:
    patcher, _ = _patch_serial([])
    with patcher, Waage("/dev/ttyUSB0") as w:
        assert w.read_one() is None


def test_stream_skips_garbage_yields_valid() -> None:
    patcher, _ = _patch_serial([
        b"junk-without-newline-in-middle\r\n",
        b"ST,+  1.0 g\r\n",
    ])
    with patcher, Waage("/dev/ttyUSB0") as w:
        gen = w.stream()
        first = next(gen)
    assert first.weight == pytest.approx(1.0)


def test_buffer_overflow_clears_safely() -> None:
    """Wenn nie ein Newline kommt, soll der Puffer geflusht werden."""
    from waage.reader import MAX_BUFFER_BYTES
    huge = b"X" * (MAX_BUFFER_BYTES + 500)
    patcher, _ = _patch_serial([huge])
    with patcher, Waage("/dev/ttyUSB0") as w:
        # Mehrfach lesen, bis der Puffer überläuft und geflusht wird
        for _ in range(50):
            w.read_one()
        assert len(w._buf) <= MAX_BUFFER_BYTES


def test_context_manager_closes_serial() -> None:
    patcher, fake = _patch_serial([b"ST,+ 10.0 g\r\n"])
    with patcher:
        with Waage("/dev/ttyUSB0") as w:
            w.read_one()
    assert fake.is_open is False


def test_explicit_close_makes_read_raise() -> None:
    """`Waage.close()` ist die public API für den Live↔Simulator-Switch.

    Nach close() darf read_one() nicht mehr lesen, sondern muss eine
    Exception werfen, damit der Reader-Loop reconnected.
    """
    patcher, fake = _patch_serial([b"ST,+ 10.0 g\r\n"])
    with patcher:
        w = Waage("/dev/ttyUSB0")
        with w:
            assert w.read_one() is not None
            w.close()
            assert fake.is_open is False
            with pytest.raises(RuntimeError):
                w.read_one()


def test_close_is_idempotent() -> None:
    """Doppelter close()-Aufruf darf nicht crashen."""
    patcher, fake = _patch_serial([b"ST,+ 10.0 g\r\n"])
    with patcher:
        with Waage("/dev/ttyUSB0") as w:
            w.close()
            w.close()  # zweiter Aufruf soll still bleiben


def test_read_one_without_open_raises() -> None:
    w = Waage("/dev/ttyUSB0")
    with pytest.raises(RuntimeError):
        w.read_one()


def test_polling_sends_print_command() -> None:
    """Default-Konfig pollt mit ESC p; Befehl muss bei jedem Read-Zyklus
    rausgehen, sofern das Polling-Intervall abgelaufen ist."""
    patcher, fake = _patch_serial([b"      0.0 g \r\n"])
    with patcher, Waage("/dev/ttyUSB0", poll_interval=0.0) as w:
        w.read_one()
    assert b"\x1bp" in fake.writes


def test_polling_disabled_when_command_is_none() -> None:
    """Mit poll_command=None darf der Reader nichts senden."""
    patcher, fake = _patch_serial([b"      0.0 g \r\n"])
    with patcher, Waage("/dev/ttyUSB0", poll_command=None) as w:
        w.read_one()
    assert fake.writes == []


def test_polling_respects_interval() -> None:
    """Bei poll_interval > 0 wird zwischen den Read-Aufrufen nicht gepollt."""
    patcher, fake = _patch_serial([
        b"      0.0 g \r\n", b"      0.0 g \r\n", b"      0.0 g \r\n",
    ])
    # Sehr langes Intervall, damit nur der erste read_one() pollt
    with patcher, Waage("/dev/ttyUSB0", poll_interval=60.0) as w:
        w.read_one()
        w.read_one()
        w.read_one()
    assert fake.writes.count(b"\x1bp") == 1


def test_send_command_writes_bytes() -> None:
    patcher, fake = _patch_serial([])
    with patcher, Waage("/dev/ttyUSB0", poll_command=None) as w:
        w.send_command(b"\x1bt")
        w.send_command(b"\x1bs")
        w.send_command(b"\x1bu")
    assert fake.writes == [b"\x1bt", b"\x1bs", b"\x1bu"]


def test_send_command_without_open_raises() -> None:
    w = Waage("/dev/ttyUSB0")
    with pytest.raises(RuntimeError):
        w.send_command(b"\x1bt")


def test_send_empty_command_is_noop() -> None:
    patcher, fake = _patch_serial([])
    with patcher, Waage("/dev/ttyUSB0", poll_command=None) as w:
        w.send_command(b"")
    assert fake.writes == []
