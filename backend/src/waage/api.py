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


def _make_reader_factory(port: str, baudrate: int, simulate: bool):
    if simulate:
        log.info("Simulationsmodus aktiv — keine echte Waage am Port")
        return lambda: SimulatedWaage()
    return lambda: Waage(port, baudrate)


async def _reader_loop(reader_factory, state: AppState) -> None:
    backoff = 1.0
    while True:
        try:
            with reader_factory() as w:
                state.reader_alive = True
                state.current_reader = w
                backoff = 1.0
                log.info("Reader geöffnet: %s", type(w).__name__)
                while True:
                    reading = await asyncio.to_thread(w.read_one)
                    if reading is None:
                        await asyncio.sleep(0.01)
                        continue
                    await state.publish(reading)
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
    reader_factory = _make_reader_factory(port, baudrate, simulate)

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
