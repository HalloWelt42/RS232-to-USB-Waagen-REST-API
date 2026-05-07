"""Differenz-Wiegen mit Mehrfach-Tara-Stapel.

Klassisches Anwendungsszenario: ein Behälter wird auf die Waage gestellt
und als Tara eingefroren, ein Trägermedium darauf, ebenfalls als Tara
eingefroren, danach kommt der eigentliche Inhalt rein. Das Netto-
Gewicht ist Brutto minus Summe aller Tarae.

Server-seitiger Speicher, persistiert nicht — überlebt nur den
Backend-Lauf. Mehrere Clients sehen denselben Stack.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TareLayer:
    """Eine einzelne Tara-Stufe im Stapel."""

    id: int
    label: str
    weight_g: float
    set_at: datetime


class DifferenzStore:
    """Verwaltet einen Stapel von Tara-Werten."""

    def __init__(self) -> None:
        self._layers: list[TareLayer] = []
        self._next_id = 1
        self._lock = threading.Lock()

    def push(self, weight_g: float, label: str = "") -> TareLayer:
        with self._lock:
            layer = TareLayer(
                id=self._next_id,
                label=label,
                weight_g=weight_g,
                set_at=datetime.now(),
            )
            self._next_id += 1
            self._layers.append(layer)
            return layer

    def remove(self, layer_id: int) -> bool:
        with self._lock:
            before = len(self._layers)
            self._layers = [l for l in self._layers if l.id != layer_id]
            return len(self._layers) != before

    def clear(self) -> int:
        with self._lock:
            n = len(self._layers)
            self._layers = []
            return n

    def list(self) -> list[TareLayer]:
        with self._lock:
            return list(self._layers)

    def total_g(self) -> float:
        with self._lock:
            return sum(l.weight_g for l in self._layers)

    def netto(self, brutto_g: Optional[float]) -> Optional[float]:
        if brutto_g is None:
            return None
        return brutto_g - self.total_g()
