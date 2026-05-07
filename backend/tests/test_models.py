"""Tests für ``waage.models``."""

from __future__ import annotations

from waage import models


def test_known_models_not_empty() -> None:
    assert len(models.KNOWN_MODELS) > 5


def test_default_model_id_is_known() -> None:
    assert models.find_model(models.DEFAULT_MODEL_ID) is not None


def test_find_model_unknown() -> None:
    assert models.find_model("doesnt-exist") is None


def test_each_model_has_id_and_resolution() -> None:
    for m in models.KNOWN_MODELS:
        assert m.id
        assert m.max_g > 0
        assert m.resolution_g > 0
        assert m.manufacturer
        assert m.category in {
            "precision", "analytical", "bench", "counting",
            "kitchen", "fine", "platform", "custom",
        }


def test_plc_6000_present() -> None:
    m = models.find_model("gg.plc.6000")
    assert m is not None
    assert m.max_g == 6000.0
    assert m.resolution_g == 0.1
