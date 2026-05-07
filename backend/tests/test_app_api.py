"""Tests für ``/app/*`` (UI-Komfort-Features)."""

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
        raw=b"", timestamp=datetime(2026, 5, 7, 12, 0, 0),
    )


@pytest.fixture
def stubbed_app():
    pumped = [_r(200.0, True)]

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


# ---------------- Toleranz ----------------
def test_tolerance_idle(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/app/tolerance")
    body = r.json()
    assert body["active"] is False
    assert body["status"] == "idle"


def test_tolerance_ok_low_high(stubbed_app: TestClient) -> None:
    r = stubbed_app.post("/app/tolerance",
        json={"target_g": 200.0, "tolerance_minus_g": 5.0, "tolerance_plus_g": 5.0})
    assert r.json()["status"] == "ok"

    r = stubbed_app.post("/app/tolerance",
        json={"target_g": 100.0, "tolerance_minus_g": 1.0, "tolerance_plus_g": 1.0})
    assert r.json()["status"] == "high"

    r = stubbed_app.post("/app/tolerance",
        json={"target_g": 1000.0, "tolerance_minus_g": 1.0, "tolerance_plus_g": 1.0})
    assert r.json()["status"] == "low"


def test_tolerance_clear(stubbed_app: TestClient) -> None:
    stubbed_app.post("/app/tolerance",
        json={"target_g": 200.0, "tolerance_minus_g": 1.0, "tolerance_plus_g": 1.0})
    r = stubbed_app.delete("/app/tolerance")
    assert r.json()["active"] is False


# ---------------- Netto ----------------
def test_netto_idle(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/app/netto")
    body = r.json()
    assert body["active"] is False


def test_netto_tare_current(stubbed_app: TestClient) -> None:
    r = stubbed_app.post("/app/netto/tare", json={})
    body = r.json()
    assert body["tare_g"] == pytest.approx(200.0)
    assert body["netto_g"] == pytest.approx(0.0)


def test_netto_tare_explicit(stubbed_app: TestClient) -> None:
    r = stubbed_app.post("/app/netto/tare", json={"tare_g": 50.0})
    body = r.json()
    assert body["tare_g"] == pytest.approx(50.0)
    assert body["netto_g"] == pytest.approx(150.0)


def test_netto_clear(stubbed_app: TestClient) -> None:
    stubbed_app.post("/app/netto/tare", json={"tare_g": 10.0})
    r = stubbed_app.delete("/app/netto/tare")
    assert r.json()["active"] is False


# ---------------- Count ----------------
def test_count_calibrate(stubbed_app: TestClient) -> None:
    r = stubbed_app.post("/app/count/calibrate", json={"reference_count": 10})
    body = r.json()
    assert body["calibrated"] is True
    assert body["piece_weight_g"] == pytest.approx(20.0)
    assert body["pieces"] == 10


def test_count_reset(stubbed_app: TestClient) -> None:
    stubbed_app.post("/app/count/calibrate", json={"reference_count": 4})
    r = stubbed_app.post("/app/count/reset")
    assert r.json()["calibrated"] is False


def test_count_validates_reference(stubbed_app: TestClient) -> None:
    assert stubbed_app.post("/app/count/calibrate", json={"reference_count": 0}).status_code == 422


# ---------------- Samples ----------------
def test_sample_post_get_delete(stubbed_app: TestClient) -> None:
    r = stubbed_app.post("/app/samples", json={"label": "L", "note": "N"})
    sid = r.json()["id"]

    r = stubbed_app.get("/app/samples")
    assert r.json()["count"] == 1

    r = stubbed_app.delete(f"/app/samples/{sid}")
    assert r.status_code == 200

    r = stubbed_app.get("/app/samples")
    assert r.json()["count"] == 0


def test_sample_csv_export(stubbed_app: TestClient) -> None:
    stubbed_app.post("/app/samples", json={"label": "X"})
    r = stubbed_app.get("/app/samples/export.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "X" in r.text


def test_sample_stats(stubbed_app: TestClient) -> None:
    stubbed_app.post("/app/samples", json={})
    r = stubbed_app.get("/app/samples/stats")
    body = r.json()
    assert body["count"] == 1


def test_sample_clear_session(stubbed_app: TestClient) -> None:
    stubbed_app.post("/app/samples", json={"session": "alpha"})
    stubbed_app.post("/app/samples", json={"session": "beta"})
    r = stubbed_app.delete("/app/samples?session=alpha")
    assert r.json()["deleted"] == 1
    r = stubbed_app.get("/app/samples?session=beta")
    assert r.json()["count"] == 1


# ---------------- Differenz ----------------
def test_differenz_push_remove(stubbed_app: TestClient) -> None:
    # Push aktuelles Gewicht (200 g) als Tara
    r = stubbed_app.post("/app/differenz/push", json={})
    body = r.json()
    assert len(body["layers"]) == 1
    assert body["total_tare_g"] == pytest.approx(200.0)
    assert body["netto_g"] == pytest.approx(0.0)

    # Push expliziten Wert (50 g) als zweite Tara
    r = stubbed_app.post("/app/differenz/push", json={"weight_g": 50.0, "label": "Träger"})
    body = r.json()
    assert len(body["layers"]) == 2
    assert body["total_tare_g"] == pytest.approx(250.0)
    assert body["netto_g"] == pytest.approx(-50.0)  # 200 - 250

    # Erste Schicht entfernen
    first_id = body["layers"][0]["id"]
    r = stubbed_app.delete(f"/app/differenz/{first_id}")
    body = r.json()
    assert len(body["layers"]) == 1


def test_differenz_clear(stubbed_app: TestClient) -> None:
    stubbed_app.post("/app/differenz/push", json={})
    r = stubbed_app.delete("/app/differenz")
    assert r.json()["layers"] == []


# ---------------- Messlog ----------------
def test_messlog_initial_entry(stubbed_app: TestClient) -> None:
    """Beim ersten stable Reading sollte ein 'start'-Eintrag entstanden sein."""
    r = stubbed_app.get("/app/messlog")
    body = r.json()
    assert body["count"] >= 1
    # Neuester zuerst, also der älteste 'start' ist hinten
    kinds = [it["kind"] for it in body["items"]]
    assert "start" in kinds


def test_messlog_clear(stubbed_app: TestClient) -> None:
    r = stubbed_app.delete("/app/messlog")
    assert r.json()["ok"] is True
    r = stubbed_app.get("/app/messlog")
    assert r.json()["count"] == 0
