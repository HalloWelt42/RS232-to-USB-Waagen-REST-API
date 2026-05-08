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


def test_health_reports_scale_alive_and_stale_for_s(stubbed_app: TestClient) -> None:
    """`/scale/health` liefert die neuen Felder. Das tatsächliche
    Verhalten der Stale-Logik wird im Unit-Test
    `test_health_marks_stale_after_threshold` geprüft (mit kontrolliertem
    `last_seen`); hier nur Smoke-Test der Feld-Sichtbarkeit, weil die
    Fixture-Frames einen festen Timestamp aus 2026-05-07 nutzen."""
    h = stubbed_app.get("/scale/health").json()
    assert "scale_alive" in h, "Feld scale_alive fehlt im Health-Output"
    assert "stale_for_s" in h, "Feld stale_for_s fehlt im Health-Output"
    assert isinstance(h["scale_alive"], bool)
    assert h["stale_for_s"] is None or isinstance(h["stale_for_s"], (int, float))


def test_health_marks_stale_after_threshold() -> None:
    """Direkter Unit-Test gegen AppState — alte `last_seen`-Zeit
    macht `scale_alive` False, ohne dass wir das Backend warten lassen."""
    from datetime import datetime, timedelta
    from waage.state import AppState
    state = AppState(
        history_size=10, port="/dev/null", baudrate=9600,
        resolved_port="/dev/null", samples_path=None,
        messlog_path=None, config_dir=None,
    )
    state.reader_alive = True
    state.scale_stale_after_s = 5.0
    # 10 s alter Frame → stale
    state.last_seen = datetime.now() - timedelta(seconds=10)
    assert state.stale_for_s is not None
    assert state.stale_for_s >= 9.5
    assert state.scale_alive is False
    # 1 s alter Frame → alive
    state.last_seen = datetime.now() - timedelta(seconds=1)
    assert state.scale_alive is True
    # Reader-Task tot → scale_alive immer False
    state.reader_alive = False
    assert state.scale_alive is False


def test_messlog_http_preserves_store_ordering(stubbed_app: TestClient) -> None:
    """Der `/app/messlog`-Endpunkt reicht die Liste aus
    `state.messlog.list()` 1:1 weiter — keine zusätzliche Sortierung
    in der Route. Die kritische Reihenfolgen-Garantie (neuester oben)
    deckt `tests/test_messlog.py::test_list_returns_newest_first`
    auf Store-Ebene; hier verifizieren wir nur, dass die HTTP-Schale
    die Items unverändert durchgibt — die IDs müssen monoton sein."""
    items = stubbed_app.get("/app/messlog").json()["items"]
    if len(items) < 2:
        pytest.skip("Test-Pipe lieferte zu wenig Frames für Reihenfolge-Check")
    ids = [it["id"] for it in items]
    assert ids == sorted(ids, reverse=True), \
        f"Messlog-IDs müssen absteigend sortiert sein, sind: {ids}"


# ---------------- 404-Verhalten der Single-Delete-Routes ----------------
# Die Frontend-Bereiche (MessLog, SamplesPanel, DifferenzPanel) rufen die
# Single-Delete-Endpunkte direkt auf — ohne Bestätigungs-Popup.
# Ein versehentlicher 404 (z.B. weil das laufende Backend hinter dem
# Frontend zurückbleibt) muss als klarer Fehler kommen, damit die UI
# einen Toast zeigt statt stillschweigend zu schweigen.

def test_messlog_single_delete_existing(stubbed_app: TestClient) -> None:
    """Frontend ruft DELETE /app/messlog/{id} mit existierender ID."""
    items = stubbed_app.get("/app/messlog").json()["items"]
    assert items, "Test-Setup hat keinen Initial-Eintrag erzeugt"
    eid = items[0]["id"]
    r = stubbed_app.delete(f"/app/messlog/{eid}")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "id": eid}


def test_messlog_single_delete_404(stubbed_app: TestClient) -> None:
    """Existiert die Messlog-ID nicht, kommt sauberer 404 statt 500."""
    r = stubbed_app.delete("/app/messlog/999999")
    assert r.status_code == 404


def test_sample_delete_404(stubbed_app: TestClient) -> None:
    r = stubbed_app.delete("/app/samples/999999")
    assert r.status_code == 404


def test_differenz_remove_404(stubbed_app: TestClient) -> None:
    r = stubbed_app.delete("/app/differenz/999999")
    assert r.status_code == 404


# ---------------- Multi-Format-Export (0.5.0+) ----------------
def test_samples_export_csv(stubbed_app: TestClient) -> None:
    stubbed_app.post("/app/samples", json={"label": "csv-test"})
    r = stubbed_app.get("/app/samples/export?fmt=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "csv-test" in r.text


def test_samples_export_tsv(stubbed_app: TestClient) -> None:
    stubbed_app.post("/app/samples", json={"label": "tsv-test"})
    r = stubbed_app.get("/app/samples/export?fmt=tsv")
    assert r.status_code == 200
    assert "tab-separated" in r.headers["content-type"]
    assert "tsv-test" in r.text


def test_samples_export_json(stubbed_app: TestClient) -> None:
    stubbed_app.post("/app/samples", json={"label": "json-test"})
    r = stubbed_app.get("/app/samples/export?fmt=json")
    assert r.status_code == 200
    assert "application/json" in r.headers["content-type"]
    assert "json-test" in r.text


def test_samples_export_markdown(stubbed_app: TestClient) -> None:
    stubbed_app.post("/app/samples", json={"label": "md-test"})
    r = stubbed_app.get("/app/samples/export?fmt=md")
    assert r.status_code == 200
    assert "markdown" in r.headers["content-type"]
    assert "md-test" in r.text


def test_samples_export_invalid_format(stubbed_app: TestClient) -> None:
    r = stubbed_app.get("/app/samples/export?fmt=xml")
    # FastAPI lehnt das Pattern direkt ab → 422 (Validation)
    assert r.status_code == 422


# ---------------- Konsistenz Frontend ↔ Backend ----------------
# Letztes Loch im Audit von 0.5.x: keine Garantie, dass jeder vom
# Frontend-Client genutzte DELETE-Pfad im OpenAPI-Schema des Backends
# tatsächlich existiert. Ein vergessener Bump des laufenden Backends
# fällt sonst erst dem Anwender beim Klick auf 404 auf.

def _frontend_delete_paths() -> list[str]:
    """Holt alle aufgerufenen DELETE-Pfade aus `frontend/src/lib/api.ts`.

    Wir suchen nach `this.del('...')` und `this.del(`...`)`-Aufrufen
    in der Datei und normalisieren `${id}`-Template-Literale auf den
    OpenAPI-Style `{name}`. Nicht-`/app/`-Pfade ignorieren wir, sie
    treffen Scale-Endpoints und werden nicht über DELETE genutzt.
    """
    import re
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent
    api_ts = repo_root / "frontend" / "src" / "lib" / "api.ts"
    if not api_ts.is_file():
        return []
    src = api_ts.read_text(encoding="utf-8")
    paths: list[str] = []
    # this.del('/literal') und this.del("/literal")
    for m in re.finditer(r"this\.del\(\s*['\"]([^'\"`]+?)(\?[^'\"`]*)?['\"]\s*\)", src):
        paths.append(m.group(1))
    # this.del(`/template/${var}`) — Variablen zu {name} normalisieren.
    # Wichtig: nur ${...}, dem ein '/' vorangeht, ist ein Path-Param;
    # ${...} ohne führendes '/' (z.B. `/app/samples${q}` mit q='?...')
    # baut nur einen Querystring an und gehört nicht in den Pfad.
    for m in re.finditer(r"this\.del\(\s*`([^`]+)`\s*\)", src):
        path = m.group(1)
        path = re.sub(r"/\$\{[^}]+\}", "/{id}", path)   # Path-Param
        path = re.sub(r"(?<!/)\$\{[^}]+\}", "", path)   # Querystring-Reste
        paths.append(path)
    return paths


def test_all_frontend_delete_routes_exist_in_backend(stubbed_app: TestClient) -> None:
    """Jeder DELETE-Pfad in api.ts muss im OpenAPI-Schema des Backends
    als DELETE-Route registriert sein. Schützt vor stale Backends, die
    hinter dem Frontend zurückbleiben (Symptom: 404 beim Löschen)."""
    schema = stubbed_app.get("/openapi.json").json()
    backend_delete_paths = {
        p for p, methods in schema["paths"].items()
        if "delete" in {m.lower() for m in methods}
    }
    # OpenAPI verwendet konkrete Param-Namen wie {sample_id}, {entry_id} …
    # Frontend-Audit normalisiert auf {id}; wir akzeptieren den Match,
    # wenn die Pfad-Struktur (Anzahl Segmente, statische Teile) gleich ist.
    def normalize(p: str) -> str:
        import re
        return re.sub(r"\{[^}]+\}", "{*}", p)

    backend_norm = {normalize(p) for p in backend_delete_paths}
    missing: list[str] = []
    for fe_path in _frontend_delete_paths():
        # API-Client hat Prefix /api → wegnehmen
        clean = fe_path.split("?", 1)[0]
        if normalize(clean) not in backend_norm:
            missing.append(clean)

    assert not missing, (
        "DELETE-Pfade im Frontend-Client ohne Backend-Pendant: "
        f"{missing}\nBackend kennt: {sorted(backend_delete_paths)}"
    )
