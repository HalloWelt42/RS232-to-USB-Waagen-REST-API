"""REST-Tests für /scale/source — Live/Simulator-Umschaltung."""

from __future__ import annotations

from fastapi.testclient import TestClient

from waage.api import create_app


def _client_simulating() -> TestClient:
    return TestClient(create_app(simulate=True))


def test_health_reports_simulated_when_started_in_simulate() -> None:
    with _client_simulating() as client:
        r = client.get("/scale/health")
        assert r.status_code == 200
        body = r.json()
        assert body["source_mode"] == "simulate"
        assert body["simulated"] is True
        assert body["port"] == "simulator"


def test_get_source() -> None:
    with _client_simulating() as client:
        r = client.get("/scale/source")
        assert r.status_code == 200
        body = r.json()
        assert body["mode"] == "simulate"
        assert body["simulated"] is True


def test_put_source_to_live_changes_mode() -> None:
    with _client_simulating() as client:
        r = client.put("/scale/source", json={"mode": "live"})
        assert r.status_code == 200
        body = r.json()
        assert body["mode"] == "live"
        assert body["simulated"] is False

        # Health spiegelt das wider
        h = client.get("/scale/health").json()
        assert h["source_mode"] == "live"
        assert h["simulated"] is False


def test_put_source_invalid_mode_rejected() -> None:
    with _client_simulating() as client:
        r = client.put("/scale/source", json={"mode": "wat"})
        assert r.status_code == 422
