"""Adapter-Erkennung: Start ohne Adapter, später eingesteckt.

Simuliert wird nur die Betriebssystem-Schicht (``comports``) und der
serielle Reader; Reader-Loop, Factory und Gesundheit laufen echt. So
ist geprüft, dass das Backend ohne Adapter startet, die Gesundheit den
fehlenden Adapter getrennt von ``scale_alive`` meldet und ein später
eingesteckter Adapter ohne Neustart in Betrieb geht.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from types import SimpleNamespace
from typing import Optional
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from waage import api as api_module
from waage.parser import Reading


class _Bus:
    """Was das Betriebssystem gerade an seriellen Ports listet."""

    def __init__(self) -> None:
        self.ports: list[SimpleNamespace] = []

    def plug(self, device: str = "/dev/ttyUSB0") -> None:
        self.ports = [SimpleNamespace(
            device=device, name=device.rsplit("/", 1)[-1], description="",
            vid=0x0403, pid=0x6001, serial_number="TEST", manufacturer=None,
        )]

    def unplug(self) -> None:
        self.ports = []

    def comports(self):
        return list(self.ports)


def _make_fake_waage(frames: bool):
    """Ersatz für ``reader.Waage``; ``frames=False`` heißt Waage aus."""

    class _FakeWaage:
        opened: list[str] = []

        def __init__(self, port: str, baudrate: int, poll_interval: float = 0.2):
            self.port = port

        def __enter__(self):
            _FakeWaage.opened.append(self.port)
            return self

        def __exit__(self, *exc) -> None:
            pass

        def close(self) -> None:
            pass

        def send_command(self, command: bytes) -> None:
            pass

        def read_one(self) -> Optional[Reading]:
            time.sleep(0.02)
            if not frames:
                return None
            return Reading(
                weight=12.5, unit="g", stable=True,
                raw=b"ST,+    12.5 g\r\n", timestamp=datetime.now(),
            )

    return _FakeWaage


def _wait_for(client: TestClient, predicate, timeout: float = 3.0) -> dict:
    deadline = time.monotonic() + timeout
    body: dict = {}
    while time.monotonic() < deadline:
        body = client.get("/scale/health").json()
        if predicate(body):
            return body
        time.sleep(0.05)
    raise AssertionError(f"Zustand nicht erreicht, zuletzt: {body}")


@pytest.fixture
def fast_polling(monkeypatch):
    monkeypatch.setenv("WAAGE_ADAPTER_POLL_S", "0.05")


def test_starts_without_adapter_and_reports_it(fast_polling) -> None:
    bus = _Bus()
    with patch("waage.tools.serial.tools.list_ports.comports", bus.comports), \
         patch.object(api_module, "Waage", _make_fake_waage(frames=True)):
        app = api_module.create_app(port="auto")
        with TestClient(app) as client:
            body = client.get("/scale/health").json()
            assert body["adapter_present"] is False
            assert body["scale_alive"] is False
            assert body["reader_alive"] is False
            assert body["port"] == "auto"


def test_adapter_plugged_later_is_used_without_restart(fast_polling) -> None:
    bus = _Bus()
    fake = _make_fake_waage(frames=True)
    with patch("waage.tools.serial.tools.list_ports.comports", bus.comports), \
         patch.object(api_module, "Waage", fake):
        app = api_module.create_app(port="auto")
        with TestClient(app) as client:
            assert client.get("/scale/health").json()["adapter_present"] is False

            # Adapter erscheint unter einem anderen Namen als dem alten
            # Standard: die automatische Suche muss ihn trotzdem finden.
            bus.plug("/dev/ttyACM0")
            body = _wait_for(client, lambda b: b["scale_alive"])
            assert body["adapter_present"] is True
            assert body["port"] == "/dev/ttyACM0"
            assert fake.opened == ["/dev/ttyACM0"]


def test_adapter_present_but_scale_silent(fast_polling, monkeypatch) -> None:
    """Adapter steckt, Waage antwortet nicht: adapter_present bleibt
    True, scale_alive wird False. Genau das trennt die Oberfläche in
    "Kein Adapter" und "Waage aus oder antwortet nicht"."""
    monkeypatch.setenv("WAAGE_SCALE_STALE_AFTER_S", "0")
    bus = _Bus()
    bus.plug()
    with patch("waage.tools.serial.tools.list_ports.comports", bus.comports), \
         patch.object(api_module, "Waage", _make_fake_waage(frames=False)):
        app = api_module.create_app(port="auto")
        with TestClient(app) as client:
            body = _wait_for(client, lambda b: b["reader_alive"])
            assert body["adapter_present"] is True
            assert body["scale_alive"] is False


def test_fixed_port_waits_for_device_node(fast_polling, tmp_path) -> None:
    """Fester WAAGE_PORT: vorhanden, sobald der Geräteknoten existiert."""
    node = tmp_path / "ttyUSB0"
    fake = _make_fake_waage(frames=True)
    with patch("waage.tools.serial.tools.list_ports.comports", return_value=[]), \
         patch.object(api_module, "Waage", fake):
        app = api_module.create_app(port=str(node))
        with TestClient(app) as client:
            assert client.get("/scale/health").json()["adapter_present"] is False
            node.touch()
            body = _wait_for(client, lambda b: b["scale_alive"])
            assert body["adapter_present"] is True
            assert fake.opened == [str(node)]


def test_simulator_reports_real_adapter_state(fast_polling) -> None:
    """Im Simulator bleibt adapter_present die echte Hardware-Aussage."""
    bus = _Bus()
    with patch("waage.tools.serial.tools.list_ports.comports", bus.comports):
        app = api_module.create_app(port="auto", simulate=True)
        with TestClient(app) as client:
            body = client.get("/scale/health").json()
            assert body["simulated"] is True
            assert body["adapter_present"] is False
            bus.plug()
            assert client.get("/scale/health").json()["adapter_present"] is True


def test_missing_adapter_does_not_escalate_backoff(fast_polling) -> None:
    """Ohne Adapter prüft der Loop im festen Takt statt mit wachsendem
    Backoff: nach kurzer Zeit muss die Factory mehrfach gefragt haben."""
    calls = 0
    state = SimpleNamespace(
        reader_alive=False, current_reader=None, adapter_poll_s=0.01,
    )

    def factory():
        nonlocal calls
        calls += 1
        raise api_module.AdapterMissingError("Kein Adapter angeschlossen")

    async def run() -> None:
        task = asyncio.create_task(api_module._reader_loop(factory, state))
        await asyncio.sleep(0.3)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())
    assert calls >= 5
    assert state.reader_alive is False
