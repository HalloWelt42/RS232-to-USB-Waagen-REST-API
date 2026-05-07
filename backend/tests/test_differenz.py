"""Tests für ``waage.differenz``."""

from __future__ import annotations

import pytest

from waage.differenz import DifferenzStore


def test_push_and_total() -> None:
    s = DifferenzStore()
    s.push(50.0, "Behaelter")
    s.push(20.0, "Traeger")
    assert s.total_g() == pytest.approx(70.0)


def test_remove() -> None:
    s = DifferenzStore()
    a = s.push(10.0)
    b = s.push(20.0)
    assert s.remove(a.id) is True
    assert s.remove(a.id) is False
    layers = s.list()
    assert len(layers) == 1
    assert layers[0].id == b.id


def test_clear() -> None:
    s = DifferenzStore()
    s.push(10.0); s.push(20.0); s.push(30.0)
    assert s.clear() == 3
    assert s.list() == []


def test_netto() -> None:
    s = DifferenzStore()
    s.push(50.0)
    s.push(20.0)
    assert s.netto(200.0) == pytest.approx(130.0)
    assert s.netto(None) is None


def test_layer_ids_unique() -> None:
    s = DifferenzStore()
    a = s.push(10.0)
    b = s.push(10.0)
    c = s.push(10.0)
    assert {a.id, b.id, c.id} == {1, 2, 3}
