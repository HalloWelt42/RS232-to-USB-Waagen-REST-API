"""Tests für die Behälter-Bibliothek."""

from __future__ import annotations

import pytest

from waage.containers import ContainerStore


def test_add_and_list() -> None:
    store = ContainerStore(":memory:")
    a = store.add("Becher klein", 12.3, "Kunststoff")
    b = store.add("Erlenmeyer 100 ml", 87.5)
    items = store.list()
    assert len(items) == 2
    # alphabetisch sortiert
    assert items[0].name == "Becher klein"
    assert items[1].name == "Erlenmeyer 100 ml"
    assert items[0].weight_g == pytest.approx(12.3)
    assert items[0].note == "Kunststoff"
    assert items[1].note == ""
    assert a.id != b.id


def test_add_validates_input() -> None:
    store = ContainerStore(":memory:")
    with pytest.raises(ValueError):
        store.add("", 10.0)
    with pytest.raises(ValueError):
        store.add("   ", 10.0)
    with pytest.raises(ValueError):
        store.add("Negativ", -1.0)


def test_get_returns_none_for_missing() -> None:
    store = ContainerStore(":memory:")
    assert store.get(999) is None


def test_update_partial() -> None:
    store = ContainerStore(":memory:")
    c = store.add("Original", 10.0, "n1")
    updated = store.update(c.id, weight_g=11.5)
    assert updated.name == "Original"          # unverändert
    assert updated.weight_g == pytest.approx(11.5)
    assert updated.note == "n1"

    updated2 = store.update(c.id, name="Neu", note="n2")
    assert updated2.name == "Neu"
    assert updated2.note == "n2"
    assert updated2.weight_g == pytest.approx(11.5)


def test_update_validates_input() -> None:
    store = ContainerStore(":memory:")
    c = store.add("X", 5.0)
    with pytest.raises(ValueError):
        store.update(c.id, name="")
    with pytest.raises(ValueError):
        store.update(c.id, weight_g=-0.1)


def test_update_missing_raises() -> None:
    store = ContainerStore(":memory:")
    with pytest.raises(KeyError):
        store.update(404, name="ghost")


def test_delete() -> None:
    store = ContainerStore(":memory:")
    c = store.add("Drop", 1.0)
    assert store.delete(c.id) is True
    assert store.delete(c.id) is False
    assert store.list() == []


def test_clear() -> None:
    store = ContainerStore(":memory:")
    store.add("A", 1.0)
    store.add("B", 2.0)
    n = store.clear()
    assert n == 2
    assert store.list() == []
