"""waage — G&G und kompatible Präzisionswaagen über RS232."""

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path

from .parser import Reading, parse
from .reader import (
    COMMAND_CALIBRATE,
    COMMAND_COUNT,
    COMMAND_LIGHT,
    COMMAND_PRINT,
    COMMAND_TARE,
    COMMAND_UNIT,
    Waage,
)

__all__ = [
    "Reading",
    "Waage",
    "parse",
    "COMMAND_PRINT",
    "COMMAND_TARE",
    "COMMAND_UNIT",
    "COMMAND_LIGHT",
    "COMMAND_COUNT",
    "COMMAND_CALIBRATE",
]


def _load_version() -> str:
    """Liest die Version aus VERSION — Single Source of Truth.

    Priorität: VERSION-Datei zuerst, dann erst Paket-Metadaten.
    Hintergrund: bei `pip install -e .` schreibt setuptools die Version
    einmalig in die egg-info (`PKG-INFO`). Spätere Bumps via bump.sh
    aktualisieren VERSION + backend/VERSION + package.json synchron,
    aber NICHT die egg-info — `importlib.metadata.version("waage")`
    blieb dadurch auf der alten Build-Zeit-Version stehen, und die
    Backend-Health-Antwort (sowie alle Anzeigen, die diese Version
    spiegeln) waren falsch.

    Wir lesen jetzt zuerst die echte Datei aus dem Repo-Tree (egal ob
    `backend/VERSION` oder `VERSION` im Wurzelverzeichnis); erst wenn
    es im aktuellen Pfad keine solche Datei gibt — z.B. in einer
    fertig gepackten Wheel ohne Repo —, fällt der Loader auf die
    importlib-Metadata zurück.
    """
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "VERSION"
        if candidate.is_file():
            return candidate.read_text().strip()
    try:
        return _pkg_version("waage")
    except PackageNotFoundError:
        return "0.0.0+unknown"


__version__ = _load_version()
