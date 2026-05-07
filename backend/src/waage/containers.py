"""Behälter-Bibliothek: gespeicherte Tara-Werte zum Wiederverwenden.

Anwendungsfall:
  Ein Labor oder eine Apotheke hat fünf Standardgefäße — Erlenmeyer-Kolben,
  Kunststoffbecher S/M/L, Glasschale. Statt jedes Mal die Tara neu zu
  setzen, legt der Anwender die Behälter einmal an (Name + Gewicht) und
  wählt sie beim nächsten Wiegen aus einer Liste aus.

Persistenz:
  SQLite analog zu samples.py / messlog.py. Der Store ist thread-sicher
  und kann als Kontextmanager genutzt werden.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Container:
    """Ein vorgespeicherter Behälter mit bekanntem Tara-Gewicht."""

    id: int
    name: str
    weight_g: float
    note: str
    created_at: datetime
    updated_at: datetime


class ContainerStore(AbstractContextManager["ContainerStore"]):
    """SQLite-basierter Behälter-Speicher."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = path if path == ":memory:" else str(Path(path))
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            self.path,
            check_same_thread=False,
            isolation_level=None,
        )
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS containers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                weight_g REAL NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

    # ------------------------------------------------------------------
    #  CRUD
    # ------------------------------------------------------------------

    def add(self, name: str, weight_g: float, note: str = "") -> Container:
        name = name.strip()
        if not name:
            raise ValueError("Behälter-Name darf nicht leer sein")
        if weight_g < 0:
            raise ValueError("Gewicht darf nicht negativ sein")
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO containers (name, weight_g, note, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (name, float(weight_g), note, now, now),
            )
            row_id = cur.lastrowid
        return self._fetch(row_id)

    def update(
        self,
        container_id: int,
        *,
        name: str | None = None,
        weight_g: float | None = None,
        note: str | None = None,
    ) -> Container:
        existing = self._fetch(container_id)
        new_name = existing.name if name is None else name.strip()
        if not new_name:
            raise ValueError("Behälter-Name darf nicht leer sein")
        new_weight = existing.weight_g if weight_g is None else float(weight_g)
        if new_weight < 0:
            raise ValueError("Gewicht darf nicht negativ sein")
        new_note = existing.note if note is None else note
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                "UPDATE containers SET name = ?, weight_g = ?, note = ?, updated_at = ?"
                " WHERE id = ?",
                (new_name, new_weight, new_note, now, container_id),
            )
        return self._fetch(container_id)

    def delete(self, container_id: int) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM containers WHERE id = ?", (container_id,)
            )
        return cur.rowcount > 0

    def get(self, container_id: int) -> Container | None:
        try:
            return self._fetch(container_id)
        except KeyError:
            return None

    def list(self) -> list[Container]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, name, weight_g, note, created_at, updated_at"
                " FROM containers ORDER BY name COLLATE NOCASE ASC"
            ).fetchall()
        return [self._row_to_container(r) for r in rows]

    def clear(self) -> int:
        with self._lock:
            cur = self._conn.execute("DELETE FROM containers")
        return cur.rowcount

    # ------------------------------------------------------------------
    #  Internals
    # ------------------------------------------------------------------

    def _fetch(self, container_id: int) -> Container:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, name, weight_g, note, created_at, updated_at"
                " FROM containers WHERE id = ?",
                (container_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Behälter {container_id} nicht gefunden")
        return self._row_to_container(row)

    @staticmethod
    def _row_to_container(row: tuple) -> Container:
        return Container(
            id=row[0],
            name=row[1],
            weight_g=float(row[2]),
            note=row[3] or "",
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
        )

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __exit__(self, *exc_info) -> None:  # pragma: no cover - trivial
        self.close()
