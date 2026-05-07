"""REST-Tests für /app/count/templates."""

from __future__ import annotations

from fastapi.testclient import TestClient

from waage.api import create_app


def _client() -> TestClient:
    app = create_app(simulate=True)
    return TestClient(app)


def test_list_seeded_defaults() -> None:
    """Beim ersten Aufruf liefert die Liste die vier Default-Vorlagen."""
    with _client() as client:
        r = client.get("/app/count/templates")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 4
        names = {it["name"] for it in data["items"]}
        assert names == {"Schrauben", "Tabletten", "Münzen", "Briefe"}


def test_create_custom_template() -> None:
    with _client() as client:
        r = client.post(
            "/app/count/templates",
            json={
                "name": "Knöpfe (Hosenknopf)",
                "piece_weight_g": 0.62,
                "icon_class": "fa-solid fa-circle",
                "description": "Standard-Hosenknopf, 0,62 g/Stück.",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Knöpfe (Hosenknopf)"
        assert body["piece_weight_g"] == 0.62

        r2 = client.get("/app/count/templates")
        assert r2.json()["count"] == 5


def test_create_validates() -> None:
    with _client() as client:
        # Stückgewicht 0 nicht erlaubt
        r = client.post(
            "/app/count/templates",
            json={"name": "X", "piece_weight_g": 0},
        )
        assert r.status_code == 422
        # leerer Name
        r = client.post(
            "/app/count/templates",
            json={"name": "", "piece_weight_g": 1},
        )
        assert r.status_code == 422


def test_partial_update() -> None:
    with _client() as client:
        # Erstelle eine eigene Vorlage
        cid = client.post(
            "/app/count/templates",
            json={"name": "Origi", "piece_weight_g": 1.0},
        ).json()["id"]

        # Nur Stückgewicht ändern
        r = client.put(
            f"/app/count/templates/{cid}",
            json={"piece_weight_g": 1.55},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Origi"
        assert body["piece_weight_g"] == 1.55


def test_update_missing_returns_404() -> None:
    with _client() as client:
        r = client.put(
            "/app/count/templates/9999",
            json={"name": "ghost"},
        )
        assert r.status_code == 404


def test_delete() -> None:
    with _client() as client:
        cid = client.post(
            "/app/count/templates",
            json={"name": "Tmp", "piece_weight_g": 1.0},
        ).json()["id"]
        r = client.delete(f"/app/count/templates/{cid}")
        assert r.status_code == 200
        assert r.json()["ok"] is True
        r = client.delete(f"/app/count/templates/{cid}")
        assert r.status_code == 404


def test_clear_all() -> None:
    with _client() as client:
        r = client.delete("/app/count/templates")
        assert r.status_code == 200
        # mindestens die vier Defaults waren da
        assert r.json()["deleted"] >= 4
        assert client.get("/app/count/templates").json()["count"] == 0
