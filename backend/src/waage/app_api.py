"""App-Router: UI-Komfort-Features unter ``/app/*``.

Setzt das Scale-Modul voraus — liest passiv vom Stream, baut den
UI-State auf. Endpoints:

- ``/app/tolerance``                Soll/Min/Max-Ampel
- ``/app/netto``                    Software-Tara
- ``/app/count``                    Stückzählung
- ``/app/samples``                  Mess-Snapshots mit Sessions
- ``/app/differenz``                Mehrfach-Tara-Stapel
- ``/app/messlog``                  Diff-Liste der Änderungen
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .differenz import TareLayer
from .messlog import EntryKind, MesslogEntry
from .samples import Sample, SampleStats
from .state import AppState

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Schemas
# ---------------------------------------------------------------------------

class ToleranceIn(BaseModel):
    target_g: float
    tolerance_minus_g: float = Field(..., ge=0)
    tolerance_plus_g: float = Field(..., ge=0)


class ToleranceOut(BaseModel):
    active: bool
    target_g: Optional[float] = None
    tolerance_minus_g: Optional[float] = None
    tolerance_plus_g: Optional[float] = None
    min_g: Optional[float] = None
    max_g: Optional[float] = None
    current_g: Optional[float] = None
    deviation_g: Optional[float] = None
    status: str


class TareIn(BaseModel):
    tare_g: Optional[float] = None


class NettoOut(BaseModel):
    active: bool
    tare_g: Optional[float] = None
    gross_g: Optional[float] = None
    netto_g: Optional[float] = None
    tare_set_at: Optional[str] = None
    stable: Optional[bool] = None


class CountCalibrateIn(BaseModel):
    reference_count: int = Field(..., ge=1, le=100000)


class CountOut(BaseModel):
    pieces: Optional[int] = None
    pieces_exact: Optional[float] = None
    piece_weight_g: Optional[float] = None
    total_weight_g: Optional[float] = None
    reference_count: Optional[int] = None
    calibrated_at: Optional[str] = None
    stable: Optional[bool] = None
    calibrated: bool


class SampleIn(BaseModel):
    label: str = Field("", max_length=120)
    note: str = Field("", max_length=1000)
    session: str = Field("default", max_length=80)


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
            unit=s.unit, stable=s.stable, label=s.label,
            note=s.note, session=s.session,
        )


class SampleListOut(BaseModel):
    count: int
    items: list[SampleOut]


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
            count=s.count, min_g=r(s.min_g), max_g=r(s.max_g),
            mean_g=r(s.mean_g), stdev_g=r(s.stdev_g),
            sum_g=r(s.sum_g), session=s.session,
        )


class TareLayerOut(BaseModel):
    id: int
    label: str
    weight_g: float
    set_at: str

    @classmethod
    def from_layer(cls, l: TareLayer) -> "TareLayerOut":
        return cls(
            id=l.id, label=l.label,
            weight_g=round(l.weight_g, 4),
            set_at=l.set_at.isoformat(timespec="seconds"),
        )


class DifferenzPushIn(BaseModel):
    weight_g: Optional[float] = None  # None = aktuelles Brutto übernehmen
    label: str = Field("", max_length=80)


class DifferenzOut(BaseModel):
    layers: list[TareLayerOut]
    total_tare_g: float
    gross_g: Optional[float]
    netto_g: Optional[float]


class MesslogOut(BaseModel):
    id: int
    ts: str
    kind: str   # 'change' | 'tare' | 'start'
    diff_g: Optional[float]
    value_g: float
    unit: str
    stable: bool

    @classmethod
    def from_entry(cls, e: MesslogEntry) -> "MesslogOut":
        return cls(
            id=e.id,
            ts=e.ts.isoformat(timespec="milliseconds"),
            kind=e.kind,
            diff_g=None if e.diff_g is None else round(e.diff_g, 4),
            value_g=round(e.value_g, 4),
            unit=e.unit, stable=e.stable,
        )


class MesslogListOut(BaseModel):
    count: int
    items: list[MesslogOut]


class ContainerOut(BaseModel):
    id: int
    name: str
    weight_g: float
    note: str
    created_at: datetime
    updated_at: datetime


class ContainerListOut(BaseModel):
    count: int
    items: list[ContainerOut]


class ContainerIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    weight_g: float = Field(..., ge=0)
    note: str = Field(default="", max_length=500)


class ContainerPatchIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    weight_g: Optional[float] = Field(default=None, ge=0)
    note: Optional[str] = Field(default=None, max_length=500)


class CountTemplateOut(BaseModel):
    id: int
    name: str
    icon_class: str
    piece_weight_g: float
    description: str
    created_at: datetime
    updated_at: datetime


class CountTemplateListOut(BaseModel):
    count: int
    items: list[CountTemplateOut]


class CountTemplateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    piece_weight_g: float = Field(..., gt=0)
    icon_class: str = Field(default="", max_length=120)
    description: str = Field(default="", max_length=500)


class CountTemplatePatchIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    piece_weight_g: Optional[float] = Field(default=None, gt=0)
    icon_class: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)


# ---------------------------------------------------------------------------
#  Router-Factory
# ---------------------------------------------------------------------------

def build_app_router(state: AppState) -> APIRouter:
    router = APIRouter(prefix="/app", tags=["app"])

    # =========================== Toleranz ============================
    def _tol_response() -> ToleranceOut:
        latest = state.latest
        target, tm, tp = state.target_g, state.tolerance_minus_g, state.tolerance_plus_g
        if target is None or tm is None or tp is None:
            return ToleranceOut(
                active=False,
                current_g=round(latest.weight, 4) if latest else None,
                status="idle",
            )
        min_g, max_g = target - tm, target + tp
        if latest is None:
            return ToleranceOut(
                active=True,
                target_g=round(target, 4),
                tolerance_minus_g=round(tm, 4),
                tolerance_plus_g=round(tp, 4),
                min_g=round(min_g, 4), max_g=round(max_g, 4),
                status="idle",
            )
        deviation = latest.weight - target
        if latest.weight < min_g: status = "low"
        elif latest.weight > max_g: status = "high"
        else: status = "ok"
        return ToleranceOut(
            active=True,
            target_g=round(target, 4),
            tolerance_minus_g=round(tm, 4),
            tolerance_plus_g=round(tp, 4),
            min_g=round(min_g, 4), max_g=round(max_g, 4),
            current_g=round(latest.weight, 4),
            deviation_g=round(deviation, 4),
            status=status,
        )

    @router.get("/tolerance", response_model=ToleranceOut)
    def get_tol() -> ToleranceOut:
        return _tol_response()

    @router.post("/tolerance", response_model=ToleranceOut)
    def set_tol(payload: ToleranceIn) -> ToleranceOut:
        state.target_g = payload.target_g
        state.tolerance_minus_g = payload.tolerance_minus_g
        state.tolerance_plus_g = payload.tolerance_plus_g
        return _tol_response()

    @router.delete("/tolerance", response_model=ToleranceOut)
    def del_tol() -> ToleranceOut:
        state.target_g = state.tolerance_minus_g = state.tolerance_plus_g = None
        return _tol_response()

    # =========================== Netto ============================
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

    @router.get("/netto", response_model=NettoOut)
    def get_netto() -> NettoOut:
        return _netto_response()

    @router.post("/netto/tare", response_model=NettoOut)
    def post_netto_tare(payload: Optional[TareIn] = None) -> NettoOut:
        if payload is None or payload.tare_g is None:
            if state.latest is None:
                raise HTTPException(503, detail="Waage hat noch nichts gesendet")
            state.tare_g = state.latest.weight
        else:
            state.tare_g = payload.tare_g
        state.tare_set_at = datetime.now()
        return _netto_response()

    @router.delete("/netto/tare", response_model=NettoOut)
    def del_netto_tare() -> NettoOut:
        state.tare_g = None
        state.tare_set_at = None
        return _netto_response()

    # =========================== Count ============================
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

    @router.get("/count", response_model=CountOut)
    def get_count() -> CountOut:
        return _count_response()

    @router.post("/count/calibrate", response_model=CountOut)
    def post_count_calibrate(payload: CountCalibrateIn) -> CountOut:
        latest = state.latest
        if latest is None:
            raise HTTPException(503, detail="Waage hat noch nichts gesendet")
        if latest.weight <= 0:
            raise HTTPException(400, detail=f"Aktuelles Gewicht muss positiv sein (ist {latest.weight:.2f} g)")
        state.piece_weight_g = latest.weight / payload.reference_count
        state.piece_reference_count = payload.reference_count
        state.piece_calibrated_at = datetime.now()
        return _count_response()

    @router.post("/count/reset", response_model=CountOut)
    def post_count_reset() -> CountOut:
        state.piece_weight_g = None
        state.piece_reference_count = None
        state.piece_calibrated_at = None
        return _count_response()

    # =========================== Samples ============================
    @router.post("/samples", response_model=SampleOut)
    def post_sample(payload: SampleIn) -> SampleOut:
        if state.latest is None:
            raise HTTPException(503, detail="Waage hat noch nichts gesendet")
        sample = state.samples.add(
            state.latest, label=payload.label, note=payload.note, session=payload.session,
        )
        return SampleOut.from_sample(sample)

    @router.get("/samples", response_model=SampleListOut)
    def get_samples(
        session: Optional[str] = Query(None),
        limit: int = Query(500, ge=1, le=10000),
    ) -> SampleListOut:
        items = state.samples.list(session=session, limit=limit)
        return SampleListOut(count=len(items), items=[SampleOut.from_sample(s) for s in items])

    @router.delete("/samples/{sample_id}")
    def del_sample(sample_id: int) -> dict:
        if not state.samples.delete(sample_id):
            raise HTTPException(404, detail="Sample nicht gefunden")
        return {"ok": True, "id": sample_id}

    @router.delete("/samples")
    def clear_samples(session: Optional[str] = Query(None)) -> dict:
        n = state.samples.clear(session=session)
        return {"ok": True, "deleted": n, "session": session}

    @router.get("/samples/stats", response_model=StatsOut)
    def get_stats(session: Optional[str] = Query(None)) -> StatsOut:
        return StatsOut.from_stats(state.samples.stats(session=session))

    @router.get("/samples/export.csv")
    def export_csv(session: Optional[str] = Query(None)) -> Response:
        items = state.samples.list(session=session, limit=1_000_000)
        chronological = list(reversed(items))
        csv_text = state.samples.to_csv(chronological)
        filename = f"waage-samples{'-' + session if session else ''}.csv"
        return Response(
            content=csv_text,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # =========================== Differenz ============================
    def _differenz_response() -> DifferenzOut:
        layers = [TareLayerOut.from_layer(l) for l in state.differenz.list()]
        total = state.differenz.total_g()
        gross = state.latest.weight if state.latest else None
        netto = (gross - total) if gross is not None else None
        return DifferenzOut(
            layers=layers,
            total_tare_g=round(total, 4),
            gross_g=round(gross, 4) if gross is not None else None,
            netto_g=round(netto, 4) if netto is not None else None,
        )

    @router.get("/differenz", response_model=DifferenzOut)
    def get_diff() -> DifferenzOut:
        return _differenz_response()

    @router.post("/differenz/push", response_model=DifferenzOut)
    def push_diff(payload: DifferenzPushIn) -> DifferenzOut:
        if payload.weight_g is None:
            if state.latest is None:
                raise HTTPException(503, detail="Waage hat noch nichts gesendet")
            weight = state.latest.weight
        else:
            weight = payload.weight_g
        state.differenz.push(weight, payload.label)
        return _differenz_response()

    @router.delete("/differenz/{layer_id}", response_model=DifferenzOut)
    def remove_diff(layer_id: int) -> DifferenzOut:
        if not state.differenz.remove(layer_id):
            raise HTTPException(404, detail="Tara-Schicht nicht gefunden")
        return _differenz_response()

    @router.delete("/differenz", response_model=DifferenzOut)
    def clear_diff() -> DifferenzOut:
        state.differenz.clear()
        return _differenz_response()

    # =========================== Messlog ============================
    @router.get("/messlog", response_model=MesslogListOut)
    def get_messlog(limit: int = Query(200, ge=1, le=5000)) -> MesslogListOut:
        items = state.messlog.list(limit=limit)
        return MesslogListOut(
            count=len(items),
            items=[MesslogOut.from_entry(e) for e in items],
        )

    @router.delete("/messlog")
    def clear_messlog() -> dict:
        n = state.messlog.clear()
        return {"ok": True, "deleted": n}

    # ============================ Container-Bibliothek ============================
    def _container_to_out(c) -> ContainerOut:
        return ContainerOut(
            id=c.id, name=c.name, weight_g=round(c.weight_g, 4),
            note=c.note, created_at=c.created_at, updated_at=c.updated_at,
        )

    @router.get("/containers", response_model=ContainerListOut)
    def list_containers() -> ContainerListOut:
        items = [_container_to_out(c) for c in state.containers.list()]
        return ContainerListOut(count=len(items), items=items)

    @router.post("/containers", response_model=ContainerOut)
    def add_container(payload: ContainerIn) -> ContainerOut:
        try:
            c = state.containers.add(payload.name, payload.weight_g, payload.note)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _container_to_out(c)

    @router.put("/containers/{container_id}", response_model=ContainerOut)
    def update_container(container_id: int, payload: ContainerPatchIn) -> ContainerOut:
        if state.containers.get(container_id) is None:
            raise HTTPException(status_code=404, detail="Behälter nicht gefunden")
        try:
            c = state.containers.update(
                container_id,
                name=payload.name,
                weight_g=payload.weight_g,
                note=payload.note,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _container_to_out(c)

    @router.delete("/containers/{container_id}")
    def delete_container(container_id: int) -> dict:
        ok = state.containers.delete(container_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Behälter nicht gefunden")
        return {"ok": True, "id": container_id}

    @router.delete("/containers")
    def clear_containers() -> dict:
        n = state.containers.clear()
        return {"ok": True, "deleted": n}

    # ============================ Stückzähl-Vorlagen ============================
    def _template_to_out(t) -> CountTemplateOut:
        return CountTemplateOut(
            id=t.id, name=t.name, icon_class=t.icon_class,
            piece_weight_g=round(t.piece_weight_g, 6),
            description=t.description,
            created_at=t.created_at, updated_at=t.updated_at,
        )

    @router.get("/count/templates", response_model=CountTemplateListOut)
    def list_count_templates() -> CountTemplateListOut:
        items = [_template_to_out(t) for t in state.count_templates.list()]
        return CountTemplateListOut(count=len(items), items=items)

    @router.post("/count/templates", response_model=CountTemplateOut)
    def add_count_template(payload: CountTemplateIn) -> CountTemplateOut:
        try:
            t = state.count_templates.add(
                payload.name, payload.piece_weight_g,
                icon_class=payload.icon_class, description=payload.description,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _template_to_out(t)

    @router.put("/count/templates/{template_id}", response_model=CountTemplateOut)
    def update_count_template(template_id: int, payload: CountTemplatePatchIn) -> CountTemplateOut:
        if state.count_templates.get(template_id) is None:
            raise HTTPException(status_code=404, detail="Vorlage nicht gefunden")
        try:
            t = state.count_templates.update(
                template_id,
                name=payload.name,
                piece_weight_g=payload.piece_weight_g,
                icon_class=payload.icon_class,
                description=payload.description,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _template_to_out(t)

    @router.delete("/count/templates/{template_id}")
    def delete_count_template(template_id: int) -> dict:
        if not state.count_templates.delete(template_id):
            raise HTTPException(status_code=404, detail="Vorlage nicht gefunden")
        return {"ok": True, "id": template_id}

    @router.delete("/count/templates")
    def clear_count_templates() -> dict:
        n = state.count_templates.clear()
        return {"ok": True, "deleted": n}

    return router
