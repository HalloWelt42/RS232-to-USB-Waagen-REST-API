"""Stückzählungs-Vorlagen mit eigenen Werten und freiem Verwalten.

Wer regelmäßig dieselben Teile zählt — bestimmte Schrauben-Sorten,
Tabletten-Sorten, gemünztes Sortiment einer Wechselstube — legt sich
einmal Vorlagen an und ruft sie beim nächsten Mal als Schnell-Start
ab. Vorlage liefert ein Stückgewicht, das die App direkt als
Kalibrierung übernimmt.

Persistenz analog zu containers.py / samples.py — SQLite mit
Thread-Lock, mit `:memory:` für Tests.

Beim ersten Start (leere Tabelle) wird ein Default-Set geseedet
mit den vier ursprünglichen Vorlagen Schrauben/Tabletten/Münzen/
Briefe — der Anwender hat damit gleich etwas zum Anfassen, kann
aber alles bearbeiten oder ersetzen.
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
class CountTemplate:
    """Eine wiederverwendbare Stückzähl-Vorlage."""

    id: int
    name: str
    icon_class: str
    piece_weight_g: float
    description: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
#  Default-Set für den ersten Start
# ---------------------------------------------------------------------------

DEFAULT_TEMPLATES: tuple[tuple[str, str, float, str], ...] = (
    ("Schrauben", "fa-solid fa-screwdriver-wrench", 2.8,
     "M5×20-Standardgewinde, ca. 2,8 g/Stück."),
    ("Tabletten", "fa-solid fa-pills", 0.5,
     "Standardtablette ca. 0,5 g/Stück (bitte selbst kalibrieren)."),
    ("Münzen", "fa-solid fa-coins", 8.5,
     "2-Euro-Münze 8,5 g/Stück. Andere Münzen abweichend."),
    ("Briefe", "fa-solid fa-envelope", 12.0,
     "Standardbrief ca. 12 g/Stück mit Inhalt."),
)


class CountTemplateStore(AbstractContextManager["CountTemplateStore"]):
    """SQLite-basierter Speicher für Stückzähl-Vorlagen."""

    def __init__(self, path: str | Path = ":memory:", *, seed_defaults: bool = True) -> None:
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
            CREATE TABLE IF NOT EXISTS count_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                icon_class TEXT NOT NULL DEFAULT '',
                piece_weight_g REAL NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        if seed_defaults:
            self._seed_if_empty()

    # ------------------------------------------------------------------
    #  CRUD
    # ------------------------------------------------------------------

    def add(
        self,
        name: str,
        piece_weight_g: float,
        *,
        icon_class: str = "",
        description: str = "",
    ) -> CountTemplate:
        name = name.strip()
        if not name:
            raise ValueError("Vorlagen-Name darf nicht leer sein")
        if piece_weight_g <= 0:
            raise ValueError("Stückgewicht muss größer als 0 sein")
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO count_templates"
                " (name, icon_class, piece_weight_g, description, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (name, icon_class, float(piece_weight_g), description, now, now),
            )
            row_id = cur.lastrowid
        return self._fetch(row_id)

    def update(
        self,
        template_id: int,
        *,
        name: str | None = None,
        icon_class: str | None = None,
        piece_weight_g: float | None = None,
        description: str | None = None,
    ) -> CountTemplate:
        existing = self._fetch(template_id)
        new_name = existing.name if name is None else name.strip()
        if not new_name:
            raise ValueError("Vorlagen-Name darf nicht leer sein")
        new_pw = existing.piece_weight_g if piece_weight_g is None else float(piece_weight_g)
        if new_pw <= 0:
            raise ValueError("Stückgewicht muss größer als 0 sein")
        new_icon = existing.icon_class if icon_class is None else icon_class
        new_desc = existing.description if description is None else description
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                "UPDATE count_templates"
                " SET name = ?, icon_class = ?, piece_weight_g = ?, description = ?, updated_at = ?"
                " WHERE id = ?",
                (new_name, new_icon, new_pw, new_desc, now, template_id),
            )
        return self._fetch(template_id)

    def delete(self, template_id: int) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM count_templates WHERE id = ?", (template_id,)
            )
        return cur.rowcount > 0

    def get(self, template_id: int) -> CountTemplate | None:
        try:
            return self._fetch(template_id)
        except KeyError:
            return None

    def list(self) -> list[CountTemplate]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, name, icon_class, piece_weight_g, description, created_at, updated_at"
                " FROM count_templates ORDER BY name COLLATE NOCASE ASC"
            ).fetchall()
        return [self._row_to_template(r) for r in rows]

    def clear(self) -> int:
        with self._lock:
            cur = self._conn.execute("DELETE FROM count_templates")
        return cur.rowcount

    # ------------------------------------------------------------------
    #  Internals
    # ------------------------------------------------------------------

    def _seed_if_empty(self) -> None:
        with self._lock:
            count = self._conn.execute(
                "SELECT COUNT(*) FROM count_templates"
            ).fetchone()[0]
        if count > 0:
            return
        for name, icon, pw, desc in DEFAULT_TEMPLATES:
            try:
                self.add(name, pw, icon_class=icon, description=desc)
            except Exception:  # noqa: BLE001
                log.exception("Default-Vorlage konnte nicht angelegt werden: %s", name)

    def _fetch(self, template_id: int) -> CountTemplate:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, name, icon_class, piece_weight_g, description, created_at, updated_at"
                " FROM count_templates WHERE id = ?",
                (template_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Vorlage {template_id} nicht gefunden")
        return self._row_to_template(row)

    @staticmethod
    def _row_to_template(row: tuple) -> CountTemplate:
        return CountTemplate(
            id=row[0],
            name=row[1],
            icon_class=row[2] or "",
            piece_weight_g=float(row[3]),
            description=row[4] or "",
            created_at=datetime.fromisoformat(row[5]),
            updated_at=datetime.fromisoformat(row[6]),
        )

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __exit__(self, *exc_info) -> None:  # pragma: no cover - trivial
        self.close()
