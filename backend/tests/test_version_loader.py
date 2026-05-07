"""Regressions-Tests für `_load_version()`.

Hintergrund: bei `pip install -e .` schreibt setuptools die Version
einmalig in die egg-info. Spätere Bumps via `bump.sh` aktualisieren
nur die Datei `VERSION`, nicht die egg-info — wenn der Loader die
Paket-Metadaten zuerst befragte, lieferte er stale Versions-Strings
und die `/scale/health`-Antwort lag falsch.

Verifiziert hier, dass die VERSION-Datei aus dem Repo-Tree
Vorrang vor `importlib.metadata.version("waage")` hat.
"""
from __future__ import annotations

from pathlib import Path

import waage


def test_version_matches_version_file() -> None:
    """Die geladene Version stimmt mit der zentralen VERSION-Datei überein."""
    here = Path(waage.__file__).resolve()
    file_version: str | None = None
    for parent in [here.parent, *here.parents]:
        candidate = parent / "VERSION"
        if candidate.is_file():
            file_version = candidate.read_text().strip()
            break

    assert file_version is not None, "VERSION-Datei nicht gefunden — Setup defekt"
    assert (
        waage.__version__ == file_version
    ), f"Loader liest {waage.__version__!r}, VERSION-Datei sagt {file_version!r}"


def test_version_is_semver_like() -> None:
    """Sanity-Check: Format X.Y.Z (oder X.Y.Z+suffix)."""
    parts = waage.__version__.split("+", 1)[0].split(".")
    assert len(parts) >= 3, f"Versions-String wirkt unvollständig: {waage.__version__!r}"
    assert all(p.isdigit() for p in parts[:3]), f"X.Y.Z muss numerisch sein: {waage.__version__!r}"
