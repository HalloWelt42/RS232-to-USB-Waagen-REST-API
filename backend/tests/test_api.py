"""Tests für ``waage.api``.

Der Reader-Loop wird durch einen Stub ersetzt, der vorgegebene Readings
in den State pumpt — so kann die API ohne Hardware getestet werden.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from waage import api as api_module
from waage.parser import Reading


def _r(weight: float, stable: bool = True, ts: datetime | None = None) -> Reading:
    return Reading(
        weight=weight,
        unit="g",
        stable=stable,
        raw=f"ST,+ {weight} g\r\n".encode(),
        timestamp=ts or datetime(2026, 1, 2, 3, 4, 5, 678000),
    )


@pytest.fixture
def stubbed_app():
    """App mit gestubbtem Reader-Loop, der ein paar Readings pumpt."""
    pumped: list[Reading] = [
        _r(100.0, True),
        _r(150.0, False),
        _r(200.0, True),
    ]

    async def fake_reader_loop(reader_factory, state, sinks):
        state.reader_alive = True
        for reading in pumped:
            await state.publish(reading)
            await asyncio.sleep(0.01)
        # weiter idle, damit der Task nicht endet (CancelledError beim Shutdown)
        await asyncio.sleep(3600)

    with patch.object(api_module, "_reader_loop", fake_reader_loop):
        app = api_module.create_app(port="/dev/null", baudrate=9600)
        with TestClient(app) as client:
            # kurz warten, bis Reader-Stub Readings gepumpt hat
            import time
            time.sleep(0.1)
            yield client


def test_root_returns_endpoint_map(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "waage-api"
    assert "endpoints" in body
    assert "weight" in body["endpoints"]


def test_health_reports_ok_after_first_reading(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["reader_alive"] is True
    assert body["last_seen"] is not None
    assert body["uptime_seconds"] >= 0


def test_weight_returns_latest(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/weight")
    assert r.status_code == 200
    body = r.json()
    assert body["weight_g"] == 200.0
    assert body["stable"] is True
    assert body["unit"] == "g"
    assert "raw" in body
    assert "timestamp" in body


def test_history_returns_recent_readings(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/history?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 3
    weights = [item["weight_g"] for item in body["items"]]
    assert 100.0 in weights
    assert 200.0 in weights


def test_history_respects_limit(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/history?limit=1")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1


def test_history_rejects_invalid_limit(stubbed_app: TestClient) -> None:
    assert stubbed_app.get("/history?limit=0").status_code == 422
    assert stubbed_app.get("/history?limit=99999").status_code == 422


def test_websocket_streams_readings(stubbed_app: TestClient) -> None:
    """WebSocket sendet beim Connect den letzten Wert."""
    with stubbed_app.websocket_connect("/stream") as ws:
        msg = ws.receive_json()
        assert "weight_g" in msg
        assert "stable" in msg


def test_weight_503_when_no_data() -> None:
    """Ohne Reader-Stub und ohne Daten -> 503."""

    async def silent_reader(reader_factory, state, sinks):
        await asyncio.sleep(3600)  # nichts publishen

    with patch.object(api_module, "_reader_loop", silent_reader):
        app = api_module.create_app(port="/dev/null", baudrate=9600)
        with TestClient(app) as client:
            r = client.get("/weight")
            assert r.status_code == 503


def test_openapi_schema_available(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert "paths" in schema
    assert "/weight" in schema["paths"]
    assert "/health" in schema["paths"]
    assert "/history" in schema["paths"]


def test_simulate_flag_uses_simulator() -> None:
    """Mit simulate=True läuft die App vollständig ohne Hardware."""
    import time as _time
    app = api_module.create_app(simulate=True)
    with TestClient(app) as client:
        # Simulator liefert sofort Readings (Default 4 Hz, also alle 250 ms)
        for _ in range(20):
            r = client.get("/weight")
            if r.status_code == 200:
                break
            _time.sleep(0.1)
        assert r.status_code == 200
        body = r.json()
        assert "weight_g" in body
        assert "unit" in body
        assert body["unit"] == "g"


def test_docs_page_renders(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/docs")
    assert r.status_code == 200
    assert "swagger" in r.text.lower()
