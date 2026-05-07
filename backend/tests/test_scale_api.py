"""Tests für ``/scale/*`` (reine Hardware-Funktion).

Reader-Loop wird durch einen Stub ersetzt, der vorgegebene Readings
in den State pumpt.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from waage import api as api_module
from waage.parser import Reading


def _r(weight: float, stable: bool = True) -> Reading:
    return Reading(
        weight=weight, unit="g", stable=stable,
        raw=f"ST,+ {weight} g\r\n".encode(),
        timestamp=datetime(2026, 5, 7, 12, 0, 0),
    )


@pytest.fixture
def stubbed_app():
    pumped = [_r(100.0, True), _r(150.0, False), _r(200.0, True)]

    async def fake_loop(reader_factory, state):
        state.reader_alive = True
        for r in pumped:
            await state.publish(r)
            await asyncio.sleep(0.01)
        await asyncio.sleep(3600)

    with patch.object(api_module, "_reader_loop", fake_loop):
        app = api_module.create_app(port="/dev/null", baudrate=9600)
        with TestClient(app) as client:
            time.sleep(0.1)
            yield client


# ---------------- Meta ----------------
def test_root_endpoint_map(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "waage-api"
    assert "scale_weight" in body["endpoints"]
    assert "app_tolerance" in body["endpoints"]


# ---------------- Scale-Weight ----------------
def test_scale_weight_returns_latest(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/scale/weight")
    assert r.status_code == 200
    body = r.json()
    assert body["weight_g"] == 200.0
    assert body["stable"] is True


def test_scale_history(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/scale/history?limit=10")
    body = r.json()
    weights = [item["weight_g"] for item in body["items"]]
    assert 100.0 in weights and 200.0 in weights


def test_scale_history_limit_validates(stubbed_app: TestClient) -> None:
    assert stubbed_app.get("/scale/history?limit=0").status_code == 422
    assert stubbed_app.get("/scale/history?limit=99999").status_code == 422


# ---------------- Scale-Health ----------------
def test_scale_health(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/scale/health")
    body = r.json()
    assert body["ok"] is True
    assert body["reader_alive"] is True
    assert body["version"]


# ---------------- Scale-Stream ----------------
def test_scale_stream_pushes_latest(stubbed_app: TestClient) -> None:
    with stubbed_app.websocket_connect("/scale/stream") as ws:
        msg = ws.receive_json()
        assert "weight_g" in msg


# ---------------- Scale-Commands ----------------
def test_scale_commands_send_bytes() -> None:
    sent: list[bytes] = []

    class _Recorder:
        def send_command(self, c: bytes) -> None:
            sent.append(c)

    async def fake_loop(reader_factory, state):
        state.reader_alive = True
        state.current_reader = _Recorder()
        await asyncio.sleep(3600)

    with patch.object(api_module, "_reader_loop", fake_loop):
        app = api_module.create_app(port="/dev/null", baudrate=9600)
        with TestClient(app) as client:
            assert client.post("/scale/command/tare").status_code == 200
            assert client.post("/scale/command/unit").status_code == 200
            assert client.post("/scale/command/light").status_code == 200

    assert sent == [b"\x1bt", b"\x1bs", b"\x1bu"]


def test_scale_commands_503_without_reader() -> None:
    async def silent(reader_factory, state):
        await asyncio.sleep(3600)

    with patch.object(api_module, "_reader_loop", silent):
        app = api_module.create_app(port="/dev/null", baudrate=9600)
        with TestClient(app) as client:
            assert client.post("/scale/command/tare").status_code == 503


# ---------------- Scale-Models ----------------
def test_scale_models_listed(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/scale/models")
    body = r.json()
    assert isinstance(body, list)
    assert len(body) > 5
    # PLC-6000 ist als Standard dabei
    ids = [m["id"] for m in body]
    assert "gg.plc.6000" in ids


# ---------------- Scale-Config ----------------
def test_scale_config_default(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/scale/config")
    body = r.json()
    assert body["active_model_id"] == "gg.plc.6000"


def test_scale_config_change(stubbed_app: TestClient) -> None:
    r = stubbed_app.put("/scale/config", json={"model_id": "gg.plc.300"})
    assert r.status_code == 200
    body = r.json()
    assert body["active_model_id"] == "gg.plc.300"
    # Anschließend liefert GET den neuen Wert
    r = stubbed_app.get("/scale/config")
    assert r.json()["active_model_id"] == "gg.plc.300"


def test_scale_config_unknown_model_404(stubbed_app: TestClient) -> None:
    r = stubbed_app.put("/scale/config", json={"model_id": "doesnt-exist"})
    assert r.status_code == 404


# ---------------- Stable-Wait Timeout ----------------
def test_scale_stable_timeout() -> None:
    async def silent(reader_factory, state):
        await asyncio.sleep(3600)

    with patch.object(api_module, "_reader_loop", silent):
        app = api_module.create_app(port="/dev/null", baudrate=9600)
        with TestClient(app) as client:
            r = client.get("/scale/weight/stable?timeout=0.2")
            assert r.status_code == 504


# ---------------- 503 ohne Daten ----------------
def test_scale_weight_503_without_data() -> None:
    async def silent(reader_factory, state):
        await asyncio.sleep(3600)

    with patch.object(api_module, "_reader_loop", silent):
        app = api_module.create_app(port="/dev/null", baudrate=9600)
        with TestClient(app) as client:
            assert client.get("/scale/weight").status_code == 503
