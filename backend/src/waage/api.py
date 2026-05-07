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
import sys
from collections import deque
from contextlib import asynccontextmanager, suppress
from dataclasses import asdict
from datetime import datetime
from typing import Any, AsyncIterator, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

from .logger import CsvSink, MultiSink, SqliteSink
from .parser import Reading
from .reader import (
    COMMAND_LIGHT,
    COMMAND_TARE,
    COMMAND_UNIT,
    DEFAULT_BAUD,
    DEFAULT_PORT,
    Waage,
)
from .samples import Sample, SampleStore, SampleStats
from .simulator import SimulatedWaage
from .tools import find_serial_port, list_serial_ports

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


class CountCalibrateIn(BaseModel):
    reference_count: int = Field(..., ge=1, le=100000,
                                 description="Anzahl der aktuell aufliegenden Teile")


class SampleIn(BaseModel):
    label: str = Field("", max_length=120, description="Kurze Beschriftung")
    note: str = Field("", max_length=1000, description="Längere Notiz")
    session: str = Field("default", max_length=80, description="Session-Name zum Gruppieren")


class SampleOut(BaseModel):
    id: int
    ts: str
    weight_g: float
    unit: str
    stable: bool
    label: str
    note: str
    session: str

    @classmethod
    def from_sample(cls, s: Sample) -> "SampleOut":
        return cls(
            id=s.id,
            ts=s.ts.isoformat(timespec="milliseconds"),
            weight_g=round(s.weight_g, 4),
            unit=s.unit,
            stable=s.stable,
            label=s.label,
            note=s.note,
            session=s.session,
        )


class SampleListOut(BaseModel):
    count: int
    items: list[SampleOut]


class ToleranceIn(BaseModel):
    target_g: float = Field(..., description="Sollwert in Gramm")
    tolerance_minus_g: float = Field(..., ge=0, description="Erlaubte Unterschreitung (positiv)")
    tolerance_plus_g: float = Field(..., ge=0, description="Erlaubte Überschreitung (positiv)")


class ToleranceOut(BaseModel):
    active: bool
    target_g: Optional[float] = None
    tolerance_minus_g: Optional[float] = None
    tolerance_plus_g: Optional[float] = None
    min_g: Optional[float] = None
    max_g: Optional[float] = None
    current_g: Optional[float] = None
    deviation_g: Optional[float] = Field(None, description="current - target")
    status: str = Field(..., description="ok, low, high oder idle")


class TareSetIn(BaseModel):
    tare_g: Optional[float] = Field(
        None,
        description="Wenn None oder weggelassen: aktuelles Gewicht als Tara setzen",
    )


class NettoOut(BaseModel):
    active: bool
    tare_g: Optional[float] = None
    gross_g: Optional[float] = None
    netto_g: Optional[float] = None
    tare_set_at: Optional[str] = None
    stable: Optional[bool] = None


class StatsOut(BaseModel):
    count: int
    min_g: Optional[float]
    max_g: Optional[float]
    mean_g: Optional[float]
    stdev_g: Optional[float]
    sum_g: Optional[float]
    session: Optional[str]

    @classmethod
    def from_stats(cls, s: SampleStats) -> "StatsOut":
        def r(x: Optional[float]) -> Optional[float]:
            return None if x is None else round(x, 4)
        return cls(
            count=s.count,
            min_g=r(s.min_g),
            max_g=r(s.max_g),
            mean_g=r(s.mean_g),
            stdev_g=r(s.stdev_g),
            sum_g=r(s.sum_g),
            session=s.session,
        )


class CountOut(BaseModel):
    pieces: Optional[int] = Field(None, description="Geschätzte Anzahl Teile auf der Waage")
    pieces_exact: Optional[float] = Field(None, description="Anzahl als Float, vor dem Runden")
    piece_weight_g: Optional[float] = Field(None, description="Gewicht eines Teils in Gramm")
    total_weight_g: Optional[float] = Field(None, description="Aktuelles Gesamtgewicht")
    reference_count: Optional[int] = Field(None, description="Beim Kalibrieren angegebene Stückzahl")
    calibrated_at: Optional[str] = Field(None, description="Zeitpunkt der Kalibrierung (ISO)")
    stable: Optional[bool] = Field(None, description="Ist der aktuelle Wägewert stabil?")
    calibrated: bool = Field(..., description="True sobald ein Stückgewicht eingelernt wurde")


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
        # Zählmodus: einmal kalibriertes Stückgewicht in Gramm. None = aus.
        self.piece_weight_g: Optional[float] = None
        self.piece_calibrated_at: Optional[datetime] = None
        self.piece_reference_count: Optional[int] = None
        # Aktiver Reader (oder None, wenn keine Verbindung steht).
        # Wird vom Reader-Loop gesetzt und genutzt, um aus HTTP-Handlern
        # heraus Kommandos an die Waage zu schicken.
        self.current_reader: Optional[Waage] = None
        # QC-Toleranzen: Sollwert mit absoluter Toleranz nach oben/unten,
        # oder klassisch Min/Max-Grenzen.
        self.target_g: Optional[float] = None
        self.tolerance_minus_g: Optional[float] = None
        self.tolerance_plus_g: Optional[float] = None
        # Differenz-Modus: gespeichertes Tara-Gewicht (z.B. leerer Behälter).
        # Netto = aktuelles Gewicht - tare_g.
        self.tare_g: Optional[float] = None
        self.tare_set_at: Optional[datetime] = None
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
                state.current_reader = w
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
            state.current_reader = None
            raise
        except Exception:  # noqa: BLE001
            state.reader_alive = False
            state.current_reader = None
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


def _resolve_port(name: str) -> str:
    """Auto-Detection des seriellen Ports.

    ``name='auto'`` (oder leer) sucht den ersten FTDI/USB-Serial-Adapter
    auf der jeweiligen Plattform. Bei expliziten Pfaden wird der Wert
    durchgereicht.
    """
    if not name or name == "auto":
        found = find_serial_port()
        if found:
            log.info("Serieller Port automatisch erkannt: %s", found)
            return found
        log.warning("WAAGE_PORT=auto, aber kein Adapter gefunden — "
                    "Reader wird in Reconnect-Schleife laufen")
        # Plattform-Default als Fallback, damit Logmeldungen Sinn ergeben
        if sys.platform == "darwin":
            return "/dev/cu.usbserial-AUTO"
        return "/dev/ttyUSB0"
    return name


def _make_reader_factory(port: str, baudrate: int, simulate: bool):
    """Liefert einen Callable, der den passenden Reader öffnet."""
    if simulate:
        log.info("Simulationsmodus aktiv — keine echte Waage am Port")
        return lambda: SimulatedWaage()
    resolved = _resolve_port(port)
    return lambda: Waage(resolved, baudrate)


def create_app(
    port: str = DEFAULT_PORT,
    baudrate: int = DEFAULT_BAUD,
    history_size: int = 1000,
    simulate: bool = False,
    samples_path: Optional[str] = None,
) -> FastAPI:

    state = _State(history=history_size)
    # Resolved Port für Diagnose-Anzeige (Health, root)
    resolved_port = "simulator" if simulate else _resolve_port(port)
    reader_factory = _make_reader_factory(port, baudrate, simulate)
    samples_db = SampleStore(samples_path or ":memory:")

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
            samples_db.close()

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
            "count":         "/count",
            "count_calibrate": "POST /count/calibrate",
            "count_reset":   "POST /count/reset",
            "command_tare":  "POST /command/tare",
            "command_unit":  "POST /command/unit",
            "command_light": "POST /command/light",
            "samples":       "/samples",
            "samples_stats": "/samples/stats",
            "samples_csv":   "/samples/export.csv",
            "tolerance":     "/tolerance",
            "netto":         "/netto",
            "netto_tare":    "POST /netto/tare",
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
            port=resolved_port,
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

    # ----------------------- Zählmodus -------------------------------
    def _count_response() -> CountOut:
        latest = state.latest
        if state.piece_weight_g is None or state.piece_weight_g <= 0:
            return CountOut(
                calibrated=False,
                total_weight_g=round(latest.weight, 4) if latest else None,
                stable=latest.stable if latest else None,
            )
        if latest is None:
            return CountOut(
                calibrated=True,
                piece_weight_g=round(state.piece_weight_g, 6),
                reference_count=state.piece_reference_count,
                calibrated_at=state.piece_calibrated_at.isoformat(timespec="seconds")
                              if state.piece_calibrated_at else None,
            )
        pieces_exact = latest.weight / state.piece_weight_g
        return CountOut(
            calibrated=True,
            pieces=int(round(pieces_exact)),
            pieces_exact=round(pieces_exact, 4),
            piece_weight_g=round(state.piece_weight_g, 6),
            total_weight_g=round(latest.weight, 4),
            reference_count=state.piece_reference_count,
            calibrated_at=state.piece_calibrated_at.isoformat(timespec="seconds")
                          if state.piece_calibrated_at else None,
            stable=latest.stable,
        )

    @app.get("/count", response_model=CountOut, tags=["count"])
    def get_count() -> CountOut:
        """Aktueller Zählmodus-Status mit Live-Stückzahl, sofern kalibriert."""
        return _count_response()

    @app.post(
        "/count/calibrate",
        response_model=CountOut,
        tags=["count"],
        responses={
            400: {"description": "Aktuelles Gewicht ist nicht positiv oder Waage instabil"},
            503: {"description": "Noch kein Reading verfügbar"},
        },
    )
    def post_count_calibrate(payload: CountCalibrateIn) -> CountOut:
        """Lernt das Stückgewicht ein.

        Vorgehen: lege ``reference_count`` Teile auf die Waage, warte bis
        der Wert stabil ist, dann diesen Endpoint mit der Anzahl aufrufen.
        Das Backend merkt sich anschließend das Stückgewicht und liefert
        in ``GET /count`` und im WebSocket-Stream die Anzahl der Teile,
        die aktuell auf der Waage liegen.
        """
        latest = state.latest
        if latest is None:
            raise HTTPException(503, detail="Waage hat noch nichts gesendet")
        if latest.weight <= 0:
            raise HTTPException(
                400,
                detail=(f"Aktuelles Gewicht muss positiv sein "
                        f"(ist {latest.weight:.2f} g)"),
            )
        state.piece_weight_g = latest.weight / payload.reference_count
        state.piece_reference_count = payload.reference_count
        state.piece_calibrated_at = datetime.now()
        log.info("Zählmodus kalibriert: %d Teile = %.3f g (%.6f g/Stück)",
                 payload.reference_count, latest.weight, state.piece_weight_g)
        return _count_response()

    @app.post("/count/reset", response_model=CountOut, tags=["count"])
    def post_count_reset() -> CountOut:
        """Verwirft die aktuelle Stückgewicht-Kalibrierung."""
        state.piece_weight_g = None
        state.piece_reference_count = None
        state.piece_calibrated_at = None
        log.info("Zählmodus zurückgesetzt")
        return _count_response()

    # --------------------- Direkte Steuerung -------------------------
    async def _send_to_scale(command: bytes, label: str) -> dict:
        reader = state.current_reader
        if reader is None:
            raise HTTPException(503, detail="Reader nicht verbunden")
        try:
            await asyncio.to_thread(reader.send_command, command)
        except Exception as exc:  # noqa: BLE001
            log.exception("Befehl %s fehlgeschlagen", label)
            raise HTTPException(500, detail=f"Befehl fehlgeschlagen: {exc}")
        return {"ok": True, "command": label, "hex": command.hex()}

    @app.post("/command/tare", tags=["command"])
    async def post_tare() -> dict:
        """Sendet Tara-Befehl (ESC t / 1B 74) an die Waage."""
        return await _send_to_scale(COMMAND_TARE, "tare")

    @app.post("/command/unit", tags=["command"])
    async def post_unit() -> dict:
        """Schaltet die Einheit an der Waage um (ESC s / 1B 73)."""
        return await _send_to_scale(COMMAND_UNIT, "unit")

    @app.post("/command/light", tags=["command"])
    async def post_light() -> dict:
        """Schaltet die Display-Beleuchtung um (ESC u / 1B 75)."""
        return await _send_to_scale(COMMAND_LIGHT, "light")

    # --------------------- Samples / Mess-Sessions -------------------
    @app.post(
        "/samples",
        response_model=SampleOut,
        tags=["samples"],
        responses={503: {"description": "Noch kein Reading verfügbar"}},
    )
    def post_sample(payload: SampleIn) -> SampleOut:
        """Hält den aktuellen Wägewert mit Label/Notiz fest."""
        if state.latest is None:
            raise HTTPException(503, detail="Waage hat noch nichts gesendet")
        sample = samples_db.add(
            state.latest,
            label=payload.label,
            note=payload.note,
            session=payload.session,
        )
        return SampleOut.from_sample(sample)

    @app.get("/samples", response_model=SampleListOut, tags=["samples"])
    def get_samples(
        session: Optional[str] = Query(None, description="Session-Filter"),
        limit: int = Query(500, ge=1, le=10000),
    ) -> SampleListOut:
        items = samples_db.list(session=session, limit=limit)
        return SampleListOut(
            count=len(items),
            items=[SampleOut.from_sample(s) for s in items],
        )

    @app.delete(
        "/samples/{sample_id}",
        tags=["samples"],
        responses={404: {"description": "Sample nicht gefunden"}},
    )
    def delete_sample(sample_id: int) -> dict:
        if not samples_db.delete(sample_id):
            raise HTTPException(404, detail="Sample nicht gefunden")
        return {"ok": True, "id": sample_id}

    @app.delete("/samples", tags=["samples"])
    def clear_samples(
        session: Optional[str] = Query(None, description="nur diese Session löschen"),
    ) -> dict:
        n = samples_db.clear(session=session)
        return {"ok": True, "deleted": n, "session": session}

    @app.get("/samples/stats", response_model=StatsOut, tags=["samples"])
    def get_sample_stats(
        session: Optional[str] = Query(None),
    ) -> StatsOut:
        return StatsOut.from_stats(samples_db.stats(session=session))

    @app.get(
        "/samples/export.csv",
        tags=["samples"],
        responses={200: {"content": {"text/csv": {}}}},
    )
    def export_samples_csv(
        session: Optional[str] = Query(None),
    ) -> Response:
        items = samples_db.list(session=session, limit=1_000_000)
        # Reihenfolge umdrehen, damit der CSV-Export chronologisch ist
        items_chronological = list(reversed(items))
        csv_text = samples_db.to_csv(items_chronological)
        filename = f"waage-samples{'-' + session if session else ''}.csv"
        return Response(
            content=csv_text,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # --------------------- QC-Toleranz -------------------------------
    def _tolerance_response() -> ToleranceOut:
        target = state.target_g
        tm = state.tolerance_minus_g
        tp = state.tolerance_plus_g
        latest = state.latest
        if target is None or tm is None or tp is None:
            return ToleranceOut(
                active=False,
                current_g=round(latest.weight, 4) if latest else None,
                status="idle",
            )
        min_g = target - tm
        max_g = target + tp
        if latest is None:
            return ToleranceOut(
                active=True,
                target_g=round(target, 4),
                tolerance_minus_g=round(tm, 4),
                tolerance_plus_g=round(tp, 4),
                min_g=round(min_g, 4),
                max_g=round(max_g, 4),
                status="idle",
            )
        deviation = latest.weight - target
        if latest.weight < min_g:
            status = "low"
        elif latest.weight > max_g:
            status = "high"
        else:
            status = "ok"
        return ToleranceOut(
            active=True,
            target_g=round(target, 4),
            tolerance_minus_g=round(tm, 4),
            tolerance_plus_g=round(tp, 4),
            min_g=round(min_g, 4),
            max_g=round(max_g, 4),
            current_g=round(latest.weight, 4),
            deviation_g=round(deviation, 4),
            status=status,
        )

    @app.get("/tolerance", response_model=ToleranceOut, tags=["tolerance"])
    def get_tolerance() -> ToleranceOut:
        """Aktueller QC-Toleranz-Status (ok/low/high/idle)."""
        return _tolerance_response()

    @app.post("/tolerance", response_model=ToleranceOut, tags=["tolerance"])
    def post_tolerance(payload: ToleranceIn) -> ToleranceOut:
        """Setzt Sollwert und Toleranzgrenzen."""
        state.target_g = payload.target_g
        state.tolerance_minus_g = payload.tolerance_minus_g
        state.tolerance_plus_g = payload.tolerance_plus_g
        log.info("QC-Toleranz: %.3f g (-%.3f / +%.3f)",
                 payload.target_g, payload.tolerance_minus_g, payload.tolerance_plus_g)
        return _tolerance_response()

    @app.delete("/tolerance", response_model=ToleranceOut, tags=["tolerance"])
    def delete_tolerance() -> ToleranceOut:
        """Schaltet die QC-Toleranz aus."""
        state.target_g = None
        state.tolerance_minus_g = None
        state.tolerance_plus_g = None
        return _tolerance_response()

    # --------------------- Software-Tara / Netto ---------------------
    def _netto_response() -> NettoOut:
        latest = state.latest
        if state.tare_g is None:
            return NettoOut(
                active=False,
                gross_g=round(latest.weight, 4) if latest else None,
                stable=latest.stable if latest else None,
            )
        return NettoOut(
            active=True,
            tare_g=round(state.tare_g, 4),
            gross_g=round(latest.weight, 4) if latest else None,
            netto_g=round(latest.weight - state.tare_g, 4) if latest else None,
            tare_set_at=state.tare_set_at.isoformat(timespec="seconds")
                        if state.tare_set_at else None,
            stable=latest.stable if latest else None,
        )

    @app.get("/netto", response_model=NettoOut, tags=["netto"])
    def get_netto() -> NettoOut:
        """Aktuelles Brutto/Tara/Netto."""
        return _netto_response()

    @app.post(
        "/netto/tare",
        response_model=NettoOut,
        tags=["netto"],
        responses={503: {"description": "Noch kein Reading verfügbar"}},
    )
    def post_netto_tare(payload: Optional[TareSetIn] = None) -> NettoOut:
        """Setzt Tara — entweder auf einen festen Wert oder auf das
        aktuell aufliegende Brutto-Gewicht.

        Ohne Body oder mit ``tare_g=null`` wird der aktuelle Wert
        eingefroren. Mit ``tare_g=12.5`` wird der angegebene Wert
        gespeichert (z.B. bekanntes Behältergewicht).
        """
        if payload is None or payload.tare_g is None:
            if state.latest is None:
                raise HTTPException(503, detail="Waage hat noch nichts gesendet")
            state.tare_g = state.latest.weight
        else:
            state.tare_g = payload.tare_g
        state.tare_set_at = datetime.now()
        log.info("Software-Tara gesetzt: %.3f g", state.tare_g)
        return _netto_response()

    @app.delete("/netto/tare", response_model=NettoOut, tags=["netto"])
    def delete_netto_tare() -> NettoOut:
        """Verwirft die Software-Tara."""
        state.tare_g = None
        state.tare_set_at = None
        return _netto_response()

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
    port=os.getenv("WAAGE_PORT", "auto"),
    baudrate=int(os.getenv("WAAGE_BAUD", DEFAULT_BAUD)),
    history_size=int(os.getenv("WAAGE_HISTORY", 1000)),
    simulate=_env_flag("WAAGE_SIMULATE"),
    samples_path=os.getenv("WAAGE_SAMPLES_DB"),
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
