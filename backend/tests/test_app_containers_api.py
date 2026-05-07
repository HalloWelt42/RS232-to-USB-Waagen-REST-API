"""REST-Tests für /app/containers."""

from __future__ import annotations

from fastapi.testclient import TestClient

from waage.api import create_app


def _client() -> TestClient:
    app = create_app(simulate=True)
    return TestClient(app)


def test_list_empty() -> None:
    with _client() as client:
        r = client.get("/app/containers")
        assert r.status_code == 200
        assert r.json() == {"count": 0, "items": []}


def test_create_and_list() -> None:
    with _client() as client:
        r = client.post("/app/containers", json={"name": "Becher", "weight_g": 12.3})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Becher"
        assert data["weight_g"] == 12.3
        assert "id" in data

        r2 = client.get("/app/containers")
        assert r2.json()["count"] == 1


def test_create_validates() -> None:
    with _client() as client:
        # negatives Gewicht
        r = client.post("/app/containers", json={"name": "X", "weight_g": -1})
        assert r.status_code == 422
        # leerer Name
        r = client.post("/app/containers", json={"name": "", "weight_g": 1})
        assert r.status_code == 422


def test_update_and_partial_update() -> None:
    with _client() as client:
        cid = client.post(
            "/app/containers", json={"name": "Alt", "weight_g": 5.0, "note": "n"}
        ).json()["id"]

        # Nur Gewicht ändern
        r = client.put(f"/app/containers/{cid}", json={"weight_g": 7.5})
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Alt"
        assert body["weight_g"] == 7.5
        assert body["note"] == "n"

        # Name + Note
        r = client.put(
            f"/app/containers/{cid}",
            json={"name": "Neu", "note": "anders"},
        )
        assert r.json()["name"] == "Neu"
        assert r.json()["note"] == "anders"


def test_update_missing_returns_404() -> None:
    with _client() as client:
        r = client.put("/app/containers/9999", json={"name": "ghost"})
        assert r.status_code == 404


def test_delete() -> None:
    with _client() as client:
        cid = client.post(
            "/app/containers", json={"name": "Tmp", "weight_g": 2.0}
        ).json()["id"]
        r = client.delete(f"/app/containers/{cid}")
        assert r.status_code == 200
        assert r.json()["ok"] is True

        r = client.delete(f"/app/containers/{cid}")
        assert r.status_code == 404


def test_clear_all() -> None:
    with _client() as client:
        client.post("/app/containers", json={"name": "A", "weight_g": 1.0})
        client.post("/app/containers", json={"name": "B", "weight_g": 2.0})
        r = client.delete("/app/containers")
        assert r.status_code == 200
        assert r.json()["deleted"] == 2
        assert client.get("/app/containers").json()["count"] == 0
