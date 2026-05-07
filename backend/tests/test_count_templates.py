"""Tests für CountTemplateStore."""

from __future__ import annotations

import pytest

from waage.count_templates import CountTemplateStore, DEFAULT_TEMPLATES


def test_seeds_defaults_on_first_start() -> None:
    store = CountTemplateStore(":memory:")
    items = store.list()
    assert len(items) == len(DEFAULT_TEMPLATES)
    names = {it.name for it in items}
    assert names == {"Schrauben", "Tabletten", "Münzen", "Briefe"}


def test_does_not_seed_when_disabled() -> None:
    store = CountTemplateStore(":memory:", seed_defaults=False)
    assert store.list() == []


def test_add_and_validate() -> None:
    store = CountTemplateStore(":memory:", seed_defaults=False)
    t = store.add("Knöpfe", 0.6, icon_class="fa-solid fa-circle", description="Hosenknopf")
    assert t.name == "Knöpfe"
    assert t.piece_weight_g == pytest.approx(0.6)
    assert t.icon_class == "fa-solid fa-circle"
    assert t.description == "Hosenknopf"

    with pytest.raises(ValueError):
        store.add("", 1.0)
    with pytest.raises(ValueError):
        store.add("Null", 0.0)
    with pytest.raises(ValueError):
        store.add("Negativ", -0.1)


def test_update_partial() -> None:
    store = CountTemplateStore(":memory:", seed_defaults=False)
    t = store.add("Original", 1.0)
    upd = store.update(t.id, piece_weight_g=2.5)
    assert upd.name == "Original"
    assert upd.piece_weight_g == pytest.approx(2.5)

    upd2 = store.update(t.id, name="Neu", description="d")
    assert upd2.name == "Neu"
    assert upd2.description == "d"
    assert upd2.piece_weight_g == pytest.approx(2.5)


def test_update_validates() -> None:
    store = CountTemplateStore(":memory:", seed_defaults=False)
    t = store.add("X", 1.0)
    with pytest.raises(ValueError):
        store.update(t.id, name="")
    with pytest.raises(ValueError):
        store.update(t.id, piece_weight_g=0)


def test_delete_and_clear() -> None:
    store = CountTemplateStore(":memory:", seed_defaults=False)
    t = store.add("A", 1.0)
    store.add("B", 2.0)
    assert store.delete(t.id) is True
    assert store.delete(t.id) is False
    assert len(store.list()) == 1
    n = store.clear()
    assert n == 1
    assert store.list() == []


def test_list_alphabetical() -> None:
    store = CountTemplateStore(":memory:", seed_defaults=False)
    store.add("Charlie", 1.0)
    store.add("alpha", 1.0)
    store.add("Bravo", 1.0)
    names = [t.name for t in store.list()]
    assert names == ["alpha", "Bravo", "Charlie"]


def test_get_returns_none_for_missing() -> None:
    store = CountTemplateStore(":memory:", seed_defaults=False)
    assert store.get(404) is None
