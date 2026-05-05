"""FastAPI-Service für die G&G PLC Waage.

Stellt den aktuellen Wägewert als REST und WebSocket-Stream bereit.

Endpoints:

- ``GET  /``           -> API-Info + Links auf Docs/Endpoints
- ``GET  /health``     -> Healthcheck (Reader-Task lebt + offen?)
- ``GET  /weight``     -> letzter bekannter Wert (JSON)
- ``GET  /weight/stable`` -> wartet bis zum nächsten Stable-Wert (max ``timeout``s)
- ``GET  /history?limit=N`` -> letzte N Werte aus dem In-Memory-Ringpuffer
- ``WS   /stream``     -> Live-Stream aller neuen Readings als JSON

Konfiguration über Umgebungsvariablen:

- ``WAAGE_PORT``     (default: ``/dev/ttyUSB0``)
- ``WAAGE_BAUD``     (default: 9600)
- ``WAAGE_CSV``      (optional: Pfad zur CSV-Logdatei)
- ``WAAGE_SQLITE``   (optional: Pfad zur SQLite-DB)
- ``WAAGE_HISTORY``  (default: 1000 — Größe des Ringpuffers)
- ``WAAGE_CORS``     (default: ``*`` — Allowed-Origins, kommagetrennt)
- ``WAAGE_SIMULATE`` (default: aus; Werte ``1``/``true``/``yes`` aktivieren
                     den Software-Simulator anstelle der echten Waage —
                     praktisch für UI-Demos und Tests ohne Hardware)
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections import deque
from contextlib import asynccontextmanager, suppress
from dataclasses import asdict
from datetime import datetime
from typing import Any, AsyncIterator, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .logger import CsvSink, MultiSink, SqliteSink
from .parser import Reading
from .reader import DEFAULT_BAUD, DEFAULT_PORT, Waage
from .simulator import SimulatedWaage

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Pydantic Schemas (für OpenAPI-Doku)
# ---------------------------------------------------------------------------

class ReadingOut(BaseModel):
    weight_g: float = Field(..., description="Gewicht in Gramm")
    unit: str = Field(..., description="Original-Einheit aus dem Frame (g/kg/...)")
    stable: bool = Field(..., description="True wenn Frame stable war")
    timestamp: str = Field(..., description="ISO-8601 mit Millisekunden")
    raw: str = Field(..., description="Original-Frame als hex-String")

    @classmethod
    def from_reading(cls, r: Reading) -> "ReadingOut":
        return cls(
            weight_g=round(r.weight, 4),
            unit=r.unit,
            stable=r.stable,
            timestamp=r.timestamp.isoformat(timespec="milliseconds"),
            raw=r.raw.hex(),
        )


class HealthOut(BaseModel):
    ok: bool
    reader_alive: bool
    last_seen: Optional[str] = None
    port: str
    baudrate: int
    uptime_seconds: float


class HistoryOut(BaseModel):
    count: int
    items: list[ReadingOut]


class ApiInfo(BaseModel):
    name: str = "waage-api"
    version: str = "0.1.0"
    description: str = "G&G PLC 6000g/0,1g Waage als REST/WS-Service"
    endpoints: dict[str, str]


# ---------------------------------------------------------------------------
#  State + Background-Reader
# ---------------------------------------------------------------------------

class _State:
    """Gemeinsamer App-State für Hintergrund-Task und HTTP-Handler."""

    def __init__(self, history: int) -> None:
        self.latest: Optional[Reading] = None
        self.last_seen: Optional[datetime] = None
        self.history: deque[Reading] = deque(maxlen=history)
        self.subscribers: set[asyncio.Queue[Reading]] = set()
        self.reader_alive: bool = False
        self.started_at: datetime = datetime.now()
        self._lock = asyncio.Lock()

    async def publish(self, reading: Reading) -> None:
        self.latest = reading
        self.last_seen = reading.timestamp
        self.history.append(reading)
        # Snapshot der Subscriber-Liste für nicht-blockierendes Iter
        for q in list(self.subscribers):
            with suppress(asyncio.QueueFull):
                q.put_nowait(reading)


def _build_sinks() -> Optional[MultiSink]:
    """Baut Logger-Sinks aus Umgebungsvariablen — oder None."""
    sinks: list[Any] = []
    csv_path = os.getenv("WAAGE_CSV")
    sqlite_path = os.getenv("WAAGE_SQLITE")
    if csv_path:
        sinks.append(CsvSink(csv_path))
        log.info("CSV-Sink aktiv: %s", csv_path)
    if sqlite_path:
        sinks.append(SqliteSink(sqlite_path))
        log.info("SQLite-Sink aktiv: %s", sqlite_path)
    if not sinks:
        return None
    return MultiSink(*sinks)


async def _reader_loop(
    reader_factory,
    state: _State,
    sinks: Optional[MultiSink],
) -> None:
    """Liest die Waage in einem Hintergrund-Task und veröffentlicht Readings.

    ``reader_factory`` ist ein Callable ohne Argumente, das einen frisch
    geöffneten Reader-Kontextmanager liefert (echte Waage oder Simulator).
    Bei Verbindungsabbrüchen wird mit exponentiellem Backoff neu verbunden.
    """
    backoff = 1.0
    while True:
        try:
            with reader_factory() as w:
                state.reader_alive = True
                backoff = 1.0
                log.info("Reader geöffnet: %s", type(w).__name__)
                # Generator in Thread laufen lassen (pyserial ist blocking)
                while True:
                    reading = await asyncio.to_thread(w.read_one)
                    if reading is None:
                        await asyncio.sleep(0.01)
                        continue
                    if sinks is not None:
                        sinks.write(reading)
                    await state.publish(reading)
        except asyncio.CancelledError:
            log.info("Reader-Loop abgebrochen")
            state.reader_alive = False
            raise
        except Exception:  # noqa: BLE001
            state.reader_alive = False
            log.exception("Reader-Loop Fehler — Reconnect in %.1fs", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)


# ---------------------------------------------------------------------------
#  App-Factory + Lifespan
# ---------------------------------------------------------------------------

def _origins() -> list[str]:
    raw = os.getenv("WAAGE_CORS", "*").strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def _make_reader_factory(port: str, baudrate: int, simulate: bool):
    """Liefert einen Callable, der den passenden Reader öffnet."""
    if simulate:
        log.info("Simulationsmodus aktiv — keine echte Waage am Port")
        return lambda: SimulatedWaage()
    return lambda: Waage(port, baudrate)


def create_app(
    port: str = DEFAULT_PORT,
    baudrate: int = DEFAULT_BAUD,
    history_size: int = 1000,
    simulate: bool = False,
) -> FastAPI:

    state = _State(history=history_size)
    reader_factory = _make_reader_factory(port, baudrate, simulate)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        sinks = _build_sinks()
        task = asyncio.create_task(_reader_loop(reader_factory, state, sinks),
                                   name="waage-reader")
        log.info("API gestartet, Reader-Task läuft")
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            if sinks is not None:
                sinks.close()

    app = FastAPI(
        title="G&G PLC Waagen-API",
        summary="REST + WebSocket-Schnittstelle zur RS232-Waage",
        description=__doc__,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------- Routes -----------------------------------
    @app.get("/", response_model=ApiInfo, tags=["meta"])
    def root() -> ApiInfo:
        return ApiInfo(endpoints={
            "weight":        "/weight",
            "weight_stable": "/weight/stable",
            "history":       "/history?limit=100",
            "health":        "/health",
            "stream":        "ws://<host>:8200/stream",
            "docs":          "/docs",
            "openapi":       "/openapi.json",
        })

    @app.get("/health", response_model=HealthOut, tags=["meta"])
    def health() -> HealthOut:
        uptime = (datetime.now() - state.started_at).total_seconds()
        return HealthOut(
            ok=state.reader_alive and state.latest is not None,
            reader_alive=state.reader_alive,
            last_seen=state.last_seen.isoformat(timespec="milliseconds")
                      if state.last_seen else None,
            port=port,
            baudrate=baudrate,
            uptime_seconds=round(uptime, 2),
        )

    @app.get(
        "/weight",
        response_model=ReadingOut,
        tags=["weight"],
        responses={503: {"description": "Noch kein Reading verfügbar"}},
    )
    def get_weight() -> ReadingOut:
        if state.latest is None:
            raise HTTPException(503, detail="Waage hat noch nichts gesendet")
        return ReadingOut.from_reading(state.latest)

    @app.get(
        "/weight/stable",
        response_model=ReadingOut,
        tags=["weight"],
        responses={
            504: {"description": "Timeout: kein Stable-Wert in der Wartezeit"},
        },
    )
    async def get_stable_weight(
        timeout: float = Query(5.0, ge=0.1, le=60.0,
                               description="Max Wartezeit in Sekunden"),
    ) -> ReadingOut:
        """Wartet bis zum nächsten Stable-Reading.

        Wenn der aktuelle Wert bereits stable ist, wird er sofort zurückgegeben.
        Sonst wird auf den nächsten Stable-Wert gewartet (max ``timeout``s).
        """
        if state.latest is not None and state.latest.stable:
            return ReadingOut.from_reading(state.latest)

        q: asyncio.Queue[Reading] = asyncio.Queue(maxsize=64)
        state.subscribers.add(q)
        try:
            deadline = asyncio.get_event_loop().time() + timeout
            while True:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    raise HTTPException(504, detail="Timeout, kein Stable-Wert")
                try:
                    reading = await asyncio.wait_for(q.get(), timeout=remaining)
                except asyncio.TimeoutError:
                    raise HTTPException(504, detail="Timeout, kein Stable-Wert")
                if reading.stable:
                    return ReadingOut.from_reading(reading)
        finally:
            state.subscribers.discard(q)

    @app.get("/history", response_model=HistoryOut, tags=["weight"])
    def get_history(
        limit: int = Query(100, ge=1, le=10000),
    ) -> HistoryOut:
        items = list(state.history)[-limit:]
        return HistoryOut(
            count=len(items),
            items=[ReadingOut.from_reading(r) for r in items],
        )

    @app.websocket("/stream")
    async def stream(ws: WebSocket) -> None:
        """Live-Stream aller Readings als JSON-Messages.

        Sendet bei Connect zunächst den letzten bekannten Wert (falls
        vorhanden), danach jeden neuen Reading.
        """
        await ws.accept()
        q: asyncio.Queue[Reading] = asyncio.Queue(maxsize=128)
        state.subscribers.add(q)
        try:
            if state.latest is not None:
                await ws.send_json(ReadingOut.from_reading(state.latest).model_dump())
            while True:
                reading = await q.get()
                await ws.send_json(ReadingOut.from_reading(reading).model_dump())
        except WebSocketDisconnect:
            pass
        finally:
            state.subscribers.discard(q)

    return app


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


# Default-App-Instanz (für `uvicorn waage.api:app`)
app = create_app(
    port=os.getenv("WAAGE_PORT", DEFAULT_PORT),
    baudrate=int(os.getenv("WAAGE_BAUD", DEFAULT_BAUD)),
    history_size=int(os.getenv("WAAGE_HISTORY", 1000)),
    simulate=_env_flag("WAAGE_SIMULATE"),
)


def run() -> None:
    """Entry-Point für `waage-api` Console-Script."""
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
