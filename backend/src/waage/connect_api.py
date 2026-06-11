"""Connect-Router: Konfiguration der Messwert-Weiterleitung unter
``/app/connect``.

- ``GET  /app/connect``       Konfig (Token maskiert) + Status
- ``PUT  /app/connect``       Konfig setzen (persistiert in config.json)
- ``POST /app/connect/test``  Einmal-Push sofort, Ergebnis zurueck

Siehe ``connect.py`` fuer den Forwarder selbst.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .connect import ConnectConfig
from .state import AppState

log = logging.getLogger(__name__)


class ConnectConfigIn(BaseModel):
    enabled: bool = False
    url: str = ""
    auth_header: str = Field(default="X-Device-Token", max_length=64)
    # Leer lassen = bestehendes Token behalten (Maskierung in GET).
    auth_token: Optional[str] = None
    interval_s: float = Field(default=1.0, ge=0.2, le=60)
    only_stable: bool = True
    send_netto: bool = False
    extra_fields: dict[str, Any] = Field(default_factory=dict)


class ConnectOut(BaseModel):
    enabled: bool
    url: str
    auth_header: str
    # Nie der Klartext -- nur ob eines gesetzt ist + die letzten 4 Zeichen.
    auth_token_set: bool
    auth_token_hint: str
    interval_s: float
    only_stable: bool
    send_netto: bool
    extra_fields: dict[str, Any]
    status: dict[str, Any]


class TestOut(BaseModel):
    ok: bool
    detail: str


def _mask(token: str) -> str:
    if not token:
        return ""
    return "****" + token[-4:] if len(token) > 4 else "****"


def build_connect_router(state: AppState) -> APIRouter:
    router = APIRouter(prefix="/app/connect", tags=["connect"])

    def _out() -> ConnectOut:
        cfg = state.connect.config
        return ConnectOut(
            enabled=cfg.enabled,
            url=cfg.url,
            auth_header=cfg.auth_header,
            auth_token_set=bool(cfg.auth_token),
            auth_token_hint=_mask(cfg.auth_token),
            interval_s=cfg.interval_s,
            only_stable=cfg.only_stable,
            send_netto=cfg.send_netto,
            extra_fields=dict(cfg.extra_fields),
            status=state.connect.status.to_dict(),
        )

    @router.get("", response_model=ConnectOut)
    def get_connect() -> ConnectOut:
        return _out()

    @router.put("", response_model=ConnectOut)
    def put_connect(payload: ConnectConfigIn) -> ConnectOut:
        old = state.connect.config
        cfg = ConnectConfig(
            enabled=payload.enabled,
            url=payload.url.strip(),
            auth_header=payload.auth_header.strip() or "X-Device-Token",
            # None = Token unangetastet lassen (UI schickt das Feld nur
            # wenn der User ein neues eingetragen hat).
            auth_token=(
                old.auth_token
                if payload.auth_token is None
                else payload.auth_token.strip()
            ),
            interval_s=payload.interval_s,
            only_stable=payload.only_stable,
            send_netto=payload.send_netto,
            extra_fields=dict(payload.extra_fields),
        )
        state.connect.config = cfg
        state.persist_config()
        log.info(
            "Connect-Konfig aktualisiert: enabled=%s url=%s",
            cfg.enabled,
            cfg.url or "(leer)",
        )
        return _out()

    @router.post("/test", response_model=TestOut)
    async def test_connect() -> TestOut:
        ok, detail = await state.connect.send_once()
        return TestOut(ok=ok, detail=detail)

    return router
