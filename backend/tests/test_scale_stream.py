"""Tests für ``WS /scale/stream``: Trennungen ohne Datenfluss.

Der Client wird auf ASGI-Ebene nachgespielt, damit genau prüfbar ist,
dass der Handler eine Trennung von sich aus bemerkt, auch wenn die
Waage nichts sendet (Waage aus, kein Adapter). Sonst bliebe die Queue
in ``state.subscribers`` hängen und der Server beendete sich nach
SIGTERM nicht.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterator
from datetime import datetime

import pytest
from fastapi import FastAPI

from waage.parser import Reading
from waage.scale_api import build_scale_router
from waage.state import AppState

TIMEOUT_S = 1.0


class _Client:
    """Client-Seite eines WebSockets, wie der Server sie über ASGI sieht."""

    def __init__(self) -> None:
        self.to_app: asyncio.Queue[dict] = asyncio.Queue()
        self.from_app: asyncio.Queue[dict] = asyncio.Queue()

    async def receive(self) -> dict:
        return await self.to_app.get()

    async def send(self, message: dict) -> None:
        await self.from_app.put(message)

    async def next_message(self) -> dict:
        return await asyncio.wait_for(self.from_app.get(), TIMEOUT_S)


def _scope() -> dict:
    return {
        "type": "websocket",
        "asgi": {"version": "3.0"},
        "scheme": "ws",
        "path": "/scale/stream",
        "raw_path": b"/scale/stream",
        "root_path": "",
        "query_string": b"",
        "headers": [],
        "client": ("test", 50000),
        "server": ("test", 80),
        "subprotocols": [],
    }


@pytest.fixture
def state() -> Iterator[AppState]:
    s = AppState(
        history_size=10, port="auto", baudrate=9600, resolved_port="auto",
        samples_path=None, messlog_path=None, config_dir=None,
    )
    yield s
    s.close()


def _app(state: AppState) -> FastAPI:
    app = FastAPI()
    app.include_router(build_scale_router(state, app_version="test"))
    return app


async def _connect(app: FastAPI, client: _Client) -> asyncio.Task:
    await client.to_app.put({"type": "websocket.connect"})
    handler = asyncio.create_task(app(_scope(), client.receive, client.send))
    assert (await client.next_message())["type"] == "websocket.accept"
    return handler


def test_disconnect_without_readings_drops_subscriber(state: AppState) -> None:
    """Waage sendet nichts, Client trennt: Handler endet, Queue ist weg."""
    app = _app(state)

    async def run() -> None:
        client = _Client()
        handler = await _connect(app, client)
        assert len(state.subscribers) == 1
        await client.to_app.put({"type": "websocket.disconnect", "code": 1001})
        await asyncio.wait_for(handler, TIMEOUT_S)

    asyncio.run(run())
    assert state.subscribers == set()


def test_stream_pushes_readings_until_disconnect(state: AppState) -> None:
    """Neue Messwerte kommen an; nach der Trennung ist die Queue weg."""
    app = _app(state)
    reading = Reading(
        weight=42.0, unit="g", stable=True, raw=b"ST,+ 42.0 g\r\n",
        timestamp=datetime(2026, 10, 27, 12, 0, 0),
    )

    async def run() -> None:
        client = _Client()
        handler = await _connect(app, client)
        await state.publish(reading)
        message = await client.next_message()
        assert message["type"] == "websocket.send"
        assert json.loads(message["text"])["weight_g"] == 42.0
        await client.to_app.put({"type": "websocket.disconnect", "code": 1000})
        await asyncio.wait_for(handler, TIMEOUT_S)

    asyncio.run(run())
    assert state.subscribers == set()
