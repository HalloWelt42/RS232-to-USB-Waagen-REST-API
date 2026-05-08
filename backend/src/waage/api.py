"""FastAPI-App: mountet Scale- und App-Router, sonst minimal.

Routen:

- ``GET /``                  Endpoint-Map
- ``/scale/...``             reine Hardware-Funktion (siehe scale_api.py)
- ``/app/...``               UI-Komfort-Features (siehe app_api.py)
- ``/docs``, ``/openapi.json``  FastAPI-Standard

Konfiguration über Umgebungsvariablen (siehe README):

- ``WAAGE_PORT``       (default ``auto``)
- ``WAAGE_BAUD``       (default 9600)
- ``WAAGE_HOST``       (default 0.0.0.0)
- ``WAAGE_API_PORT``   (default 8200)
- ``WAAGE_HISTORY``    (default 1000)
- ``WAAGE_SAMPLES_DB`` (optional)
- ``WAAGE_MESSLOG_DB`` (optional)
- ``WAAGE_DATA_DIR``   (optional, für config.json)
- ``WAAGE_CORS``       (default ``*``)
- ``WAAGE_SIMULATE``   (1 / true: Simulator statt Hardware)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager, suppress
from typing import AsyncIterator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import __version__
from .app_api import build_app_router
from .reader import DEFAULT_BAUD, DEFAULT_PORT, Waage
from .scale_api import build_scale_router
from .simulator import SimulatedWaage
from .state import AppState
from .tools import find_serial_port

log = logging.getLogger(__name__)


class ApiInfo(BaseModel):
    name: str = "waage-api"
    version: str = __version__
    description: str = (
        "G&G und kompatible Präzisionswaagen über RS232 — "
        "Scale-Modul (/scale) eigenständig, App-Modul (/app) als Erweiterung."
    )
    endpoints: dict[str, str]


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _resolve_port(name: str) -> str:
    if not name or name == "auto":
        found = find_serial_port()
        if found:
            log.info("Serieller Port automatisch erkannt: %s", found)
            return found
        log.warning("WAAGE_PORT=auto, kein Adapter gefunden")
        if sys.platform == "darwin":
            return "/dev/cu.usbserial-AUTO"
        return "/dev/ttyUSB0"
    return name


def _make_reader_factory(port: str, baudrate: int, state: AppState):
    """Erzeugt einen Reader passend zum aktuellen state.source_mode.

    Wird bei jedem Reconnect erneut ausgewertet — so kann der Anwender
    zwischen Live und Simulator umschalten, ohne das Backend neu zu
    starten.

    Beim Live-Modus wird der konkrete Port aus `state.resolved_port`
    gelesen (von ``set_source`` aktualisiert) — sonst würde der Reader
    auf einen veralteten Port-Wert aus der Boot-Phase zugreifen.
    """
    def factory():
        if state.source_mode == "simulate":
            log.info("Reader: Simulator")
            return SimulatedWaage()
        # Echte Hardware: nimm den aktuell aufgelösten Port, fall back
        # auf den Boot-Port nur wenn nötig.
        live_port = state.resolved_port
        if not live_port or live_port in ("simulator", "auto"):
            live_port = port
        log.info("Reader: Live (%s @ %d Baud)", live_port, state.baudrate)
        return Waage(live_port, state.baudrate)
    return factory


async def _reader_loop(reader_factory, state: AppState) -> None:
    """Liest in Schleife von der Hardware/Simulator und veröffentlicht
    Readings im AppState.

    Disconnect-Erkennung: bei pyserial schlägt der Lese-Aufruf nach
    einem USB-Adapter-Abriss nicht zwingend mit einer Exception fehl —
    `read_one()` gibt dann nur leere Frames (None) zurück, der Loop
    drehte vorher endlos im 10ms-Takt. Wir prüfen deshalb periodisch,
    ob seit dem letzten erfolgreichen Frame zu viel Zeit vergangen ist
    (Default 2× `state.scale_stale_after_s`), und werfen dann selbst
    eine Exception — das löst den existierenden Reconnect-Pfad mit
    Backoff aus, der das Device beim nächsten Stecken wieder findet.
    """
    import time as _time

    backoff = 1.0
    HEALTH_CHECK_INTERVAL_S = 2.0
    while True:
        try:
            with reader_factory() as w:
                state.reader_alive = True
                state.current_reader = w
                backoff = 1.0
                log.info("Reader geöffnet: %s", type(w).__name__)
                reader_opened_at = _time.monotonic()
                last_health_check = reader_opened_at
                while True:
                    reading = await asyncio.to_thread(w.read_one)
                    if reading is not None:
                        await state.publish(reading)
                        continue
                    await asyncio.sleep(0.01)
                    # Periodischer Stale-Check — bei abgezogenem
                    # USB-Adapter merkt der Lese-Pfad sonst nichts.
                    now = _time.monotonic()
                    if now - last_health_check < HEALTH_CHECK_INTERVAL_S:
                        continue
                    last_health_check = now
                    stale_threshold = state.scale_stale_after_s * 2
                    elapsed_since_open = now - reader_opened_at
                    stale_s = state.stale_for_s
                    if state.last_seen is None:
                        # Reader läuft, aber NIE einen Frame bekommen.
                        # Wahrscheinlich Hardware nicht da. Reconnect
                        # triggern, sobald die Geduld-Schwelle reißt.
                        if elapsed_since_open > stale_threshold:
                            raise RuntimeError(
                                "Hardware liefert seit dem Öffnen keine "
                                f"Frames ({elapsed_since_open:.0f}s) — "
                                "Reconnect-Versuch."
                            )
                        continue
                    if stale_s is not None and stale_s > stale_threshold:
                        raise RuntimeError(
                            f"Keine Frames seit {stale_s:.1f}s "
                            "(USB-Adapter wahrscheinlich getrennt) — "
                            "Reconnect-Versuch."
                        )
        except asyncio.CancelledError:
            state.reader_alive = False
            state.current_reader = None
            raise
        except Exception:  # noqa: BLE001
            state.reader_alive = False
            state.current_reader = None
            log.exception("Reader-Loop Fehler — Reconnect in %.1fs", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)


def _origins() -> list[str]:
    raw = os.getenv("WAAGE_CORS", "*").strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
#  App-Factory
# ---------------------------------------------------------------------------

def create_app(
    port: str = DEFAULT_PORT,
    baudrate: int = DEFAULT_BAUD,
    history_size: int = 1000,
    simulate: bool = False,
    samples_path: Optional[str] = None,
    messlog_path: Optional[str] = None,
    containers_path: Optional[str] = None,
    count_templates_path: Optional[str] = None,
    config_dir: Optional[str] = None,
) -> FastAPI:

    resolved = "simulator" if simulate else _resolve_port(port)

    state = AppState(
        history_size=history_size,
        port=port,
        baudrate=baudrate,
        resolved_port=resolved,
        samples_path=samples_path,
        messlog_path=messlog_path,
        containers_path=containers_path,
        count_templates_path=count_templates_path,
        config_dir=config_dir,
    )
    # Wenn beim Boot simulate=True übergeben wurde (env), den Mode setzen.
    if simulate:
        state.source_mode = "simulate"
    reader_factory = _make_reader_factory(port, baudrate, state)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        task = asyncio.create_task(
            _reader_loop(reader_factory, state),
            name="waage-reader",
        )
        log.info("API gestartet, Reader-Task läuft (Version %s)", __version__)
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            state.close()

    app = FastAPI(
        title="Waagen-API",
        summary="Scale (Hardware) und App (UI-Komfort) als getrennte Module",
        description=__doc__,
        version=__version__,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Router mounten
    app.include_router(build_scale_router(state, app_version=__version__))
    app.include_router(build_app_router(state))

    @app.get("/", response_model=ApiInfo, tags=["meta"])
    def root() -> ApiInfo:
        return ApiInfo(endpoints={
            "scale_weight":     "/scale/weight",
            "scale_stable":     "/scale/weight/stable",
            "scale_history":    "/scale/history",
            "scale_stream":     "ws://<host>/scale/stream",
            "scale_tare":       "POST /scale/command/tare",
            "scale_unit":       "POST /scale/command/unit",
            "scale_light":      "POST /scale/command/light",
            "scale_health":     "/scale/health",
            "scale_models":     "/scale/models",
            "scale_config":     "/scale/config",
            "scale_source":     "/scale/source",
            "app_tolerance":    "/app/tolerance",
            "app_netto":        "/app/netto",
            "app_count":        "/app/count",
            "app_samples":      "/app/samples",
            "app_samples_csv":  "/app/samples/export.csv",
            "app_differenz":    "/app/differenz",
            "app_messlog":      "/app/messlog",
            "app_containers":   "/app/containers",
            "app_count_templates": "/app/count/templates",
            "docs":             "/docs",
            "openapi":          "/openapi.json",
        })

    return app


# Default-Instanz für `uvicorn waage.api:app`
app = create_app(
    port=os.getenv("WAAGE_PORT", "auto"),
    baudrate=int(os.getenv("WAAGE_BAUD", DEFAULT_BAUD)),
    history_size=int(os.getenv("WAAGE_HISTORY", 1000)),
    simulate=_env_flag("WAAGE_SIMULATE"),
    samples_path=os.getenv("WAAGE_SAMPLES_DB"),
    messlog_path=os.getenv("WAAGE_MESSLOG_DB"),
    containers_path=os.getenv("WAAGE_CONTAINERS_DB"),
    count_templates_path=os.getenv("WAAGE_COUNT_TEMPLATES_DB"),
    config_dir=os.getenv("WAAGE_DATA_DIR"),
)


def run() -> None:
    """Entry-Point für `waage-api`."""
    import uvicorn
    uvicorn.run(
        "waage.api:app",
        host=os.getenv("WAAGE_HOST", "0.0.0.0"),
        port=int(os.getenv("WAAGE_API_PORT", 8200)),
        reload=False,
        log_level=os.getenv("WAAGE_LOGLEVEL", "info"),
    )


if __name__ == "__main__":
    run()
