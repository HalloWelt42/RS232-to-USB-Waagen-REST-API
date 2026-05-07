"""Scale-Router: REST + WebSocket für die reine Waagen-Funktion.

Eigenständig nutzbar — Drittsysteme, die nur den aktuellen Wägewert
oder die Steuerbefehle brauchen, sprechen nur diesen Router an. Keine
Abhängigkeit zum App-Modul.

Endpoints (alle unter Prefix ``/scale``):

- ``GET  /weight``               letzter Reading
- ``GET  /weight/stable``        wartet bis zum nächsten Stable-Wert
- ``GET  /history``              Ringpuffer
- ``WS   /stream``               Live-Push aller neuen Readings
- ``POST /command/tare``         ESC t
- ``POST /command/unit``         ESC s
- ``POST /command/light``        ESC u
- ``GET  /health``               Reader-Status, Uptime, Port
- ``GET  /models``               bekannte Waagen-Modelle
- ``GET/PUT /config``            aktives Modell
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from .models import KNOWN_MODELS, ScaleModel, find_model
from .parser import Reading
from .reader import COMMAND_LIGHT, COMMAND_TARE, COMMAND_UNIT
from .state import AppState
from .tools import find_serial_port

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Pydantic-Schemas
# ---------------------------------------------------------------------------

class ReadingOut(BaseModel):
    weight_g: float = Field(..., description="Gewicht in Gramm")
    unit: str
    stable: bool
    timestamp: str
    raw: str = Field(..., description="Original-Frame als Hex")

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
    version: str
    source_mode: str         # 'live' oder 'simulate'
    simulated: bool          # True wenn aktuell der SimulatedWaage-Reader läuft


class SourceIn(BaseModel):
    mode: str = Field(..., pattern="^(live|simulate)$")


class SourceOut(BaseModel):
    mode: str
    port: str
    simulated: bool


class HistoryOut(BaseModel):
    count: int
    items: list[ReadingOut]


class CommandResult(BaseModel):
    ok: bool
    command: str
    hex: str


class ScaleModelOut(BaseModel):
    id: str
    manufacturer: str
    series: str
    name: str
    category: str
    max_g: float
    resolution_g: float
    default_baudrate: int
    rs232: bool
    note: str
    # Genauigkeits-Toleranzen aus dem Datenblatt (0 / None = nicht angegeben)
    min_load_g: float = 0.0
    linearity_g: float = 0.0
    repeatability_g: float = 0.0
    stabilization_s: float = 0.0
    warmup_min: int = 0
    operating_temp_c: Optional[tuple[float, float]] = None

    @classmethod
    def from_model(cls, m: ScaleModel) -> "ScaleModelOut":
        return cls(**m.__dict__)


class ScaleConfigOut(BaseModel):
    active_model_id: str
    active_model: ScaleModelOut


class ScaleConfigIn(BaseModel):
    model_id: str = Field(..., min_length=1, max_length=100)


# ---------------------------------------------------------------------------
#  Router-Factory
# ---------------------------------------------------------------------------

def build_scale_router(state: AppState, app_version: str) -> APIRouter:
    """Erstellt den Scale-Router; ``state`` wird als Closure-Capture genutzt."""

    router = APIRouter(prefix="/scale", tags=["scale"])

    # ---------------------- Wägung ----------------------
    @router.get(
        "/weight",
        response_model=ReadingOut,
        responses={503: {"description": "Noch kein Reading verfügbar"}},
    )
    def get_weight() -> ReadingOut:
        if state.latest is None:
            raise HTTPException(503, detail="Waage hat noch nichts gesendet")
        return ReadingOut.from_reading(state.latest)

    @router.get(
        "/weight/stable",
        response_model=ReadingOut,
        responses={504: {"description": "Timeout: kein Stable-Wert"}},
    )
    async def get_stable_weight(
        timeout: float = Query(5.0, ge=0.1, le=60.0,
                               description="Max Wartezeit in Sekunden"),
    ) -> ReadingOut:
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

    @router.get("/history", response_model=HistoryOut)
    def get_history(limit: int = Query(100, ge=1, le=10000)) -> HistoryOut:
        items = list(state.history)[-limit:]
        return HistoryOut(
            count=len(items),
            items=[ReadingOut.from_reading(r) for r in items],
        )

    # ---------------------- WebSocket ----------------------
    @router.websocket("/stream")
    async def stream(ws: WebSocket) -> None:
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

    # ---------------------- Steuerbefehle ----------------------
    async def _send(command: bytes, label: str) -> CommandResult:
        reader = state.current_reader
        if reader is None:
            raise HTTPException(503, detail="Reader nicht verbunden")
        try:
            await asyncio.to_thread(reader.send_command, command)
        except Exception as exc:  # noqa: BLE001
            log.exception("Befehl %s fehlgeschlagen", label)
            raise HTTPException(500, detail=f"Befehl fehlgeschlagen: {exc}")
        return CommandResult(ok=True, command=label, hex=command.hex())

    @router.post("/command/tare", response_model=CommandResult)
    async def cmd_tare() -> CommandResult:
        result = await _send(COMMAND_TARE, "tare")
        # Nach Tara einen Messlog-Tara-Marker setzen, sobald der nächste
        # Stable-Frame kommt — der Reader-Loop kümmert sich darum
        # (siehe AppState.tare_pending).
        state.tare_pending = True
        return result

    @router.post("/command/unit", response_model=CommandResult)
    async def cmd_unit() -> CommandResult:
        return await _send(COMMAND_UNIT, "unit")

    @router.post("/command/light", response_model=CommandResult)
    async def cmd_light() -> CommandResult:
        return await _send(COMMAND_LIGHT, "light")

    # ---------------------- Health ----------------------
    @router.get("/health", response_model=HealthOut)
    def health() -> HealthOut:
        uptime = (datetime.now() - state.started_at).total_seconds()
        simulated = state.source_mode == "simulate"
        return HealthOut(
            ok=state.reader_alive and state.latest is not None,
            reader_alive=state.reader_alive,
            last_seen=state.last_seen.isoformat(timespec="milliseconds")
                      if state.last_seen else None,
            port="simulator" if simulated else state.resolved_port,
            baudrate=state.baudrate,
            uptime_seconds=round(uptime, 2),
            version=app_version,
            source_mode=state.source_mode,
            simulated=simulated,
        )

    # ---------------------- Source: Live / Simulate ----------------------
    @router.get("/source", response_model=SourceOut)
    def get_source() -> SourceOut:
        simulated = state.source_mode == "simulate"
        return SourceOut(
            mode=state.source_mode,
            port="simulator" if simulated else state.resolved_port,
            simulated=simulated,
        )

    @router.put("/source", response_model=SourceOut)
    def set_source(payload: SourceIn) -> SourceOut:
        if payload.mode not in ("live", "simulate"):
            raise HTTPException(400, detail="Modus muss 'live' oder 'simulate' sein")
        if payload.mode != state.source_mode:
            state.source_mode = payload.mode
            # Wechsel zu Live: physischen Port neu auflösen, falls
            # `state.resolved_port` aus einer Simulator-Boot-Phase noch
            # auf "simulator" steht (sonst versucht der Reader den
            # nicht existierenden Port "auto"/"simulator" zu öffnen).
            if payload.mode == "live" and state.resolved_port in ("simulator", "auto", ""):
                if state.port and state.port != "auto":
                    state.resolved_port = state.port
                else:
                    found = find_serial_port()
                    if found:
                        state.resolved_port = found
                        log.info("Live-Port automatisch aufgelöst: %s", found)
                    else:
                        log.warning("Live-Modus: kein serieller Adapter gefunden")
            state.persist_config()
            log.info("Quelle gewechselt: %s (Port=%s)", payload.mode, state.resolved_port)
            # Aktuellen Reader schließen — der Reader-Loop reconnectet
            # über die Factory, die das neue source_mode liest.
            try:
                if state.current_reader is not None:
                    state.current_reader.close()
            except Exception:  # noqa: BLE001
                log.exception("Reader konnte nicht gewechselt werden")
        simulated = state.source_mode == "simulate"
        return SourceOut(
            mode=state.source_mode,
            port="simulator" if simulated else state.resolved_port,
            simulated=simulated,
        )

    # ---------------------- Modelle / Konfig ----------------------
    @router.get("/models", response_model=list[ScaleModelOut])
    def list_models() -> list[ScaleModelOut]:
        return [ScaleModelOut.from_model(m) for m in KNOWN_MODELS]

    @router.get("/config", response_model=ScaleConfigOut)
    def get_config() -> ScaleConfigOut:
        m = find_model(state.active_model_id) or KNOWN_MODELS[0]
        return ScaleConfigOut(
            active_model_id=m.id,
            active_model=ScaleModelOut.from_model(m),
        )

    @router.put("/config", response_model=ScaleConfigOut)
    def set_config(payload: ScaleConfigIn) -> ScaleConfigOut:
        m = find_model(payload.model_id)
        if m is None:
            raise HTTPException(404, detail=f"Modell '{payload.model_id}' nicht bekannt")
        state.active_model_id = m.id
        state.persist_config()
        log.info("Aktives Modell gewechselt: %s", m.id)
        return ScaleConfigOut(
            active_model_id=m.id,
            active_model=ScaleModelOut.from_model(m),
        )

    return router
