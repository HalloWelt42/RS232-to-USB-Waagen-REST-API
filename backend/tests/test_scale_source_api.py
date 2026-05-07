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


def test_round_trip_simulate_to_live_to_simulate() -> None:
    """End-to-End-Lebenszyklus: Backend boots im Simulator, schaltet auf
    Live (was offline scheitern darf), und dann zurück auf Simulator —
    state.source_mode muss in jedem Schritt korrekt sein."""
    with _client_simulating() as client:
        assert client.get("/scale/health").json()["source_mode"] == "simulate"

        client.put("/scale/source", json={"mode": "live"})
        # Im Test gibt's keine Hardware — der Reader-Loop wird in einer
        # Reconnect-Schleife landen, aber state.source_mode steht auf "live"
        assert client.get("/scale/source").json()["mode"] == "live"

        client.put("/scale/source", json={"mode": "simulate"})
        assert client.get("/scale/source").json()["mode"] == "simulate"
        assert client.get("/scale/health").json()["simulated"] is True


def test_setting_same_source_is_no_op() -> None:
    """Wer den aktiven Modus nochmal setzt, soll keinen Reader-Wechsel
    triggern — nur idempotent zurückbestätigen."""
    with _client_simulating() as client:
        before = client.get("/scale/health").json()
        r = client.put("/scale/source", json={"mode": "simulate"})
        assert r.status_code == 200
        after = client.get("/scale/health").json()
        # Uptime läuft monoton; reader_alive bleibt
        assert after["reader_alive"] == before["reader_alive"]
        assert after["source_mode"] == "simulate"
