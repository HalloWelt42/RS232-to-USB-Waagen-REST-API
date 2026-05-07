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
    """Liest die Version aus VERSION oder Paket-Metadaten — Single Source ist
    die Datei VERSION im Repo-Wurzel."""
    try:
        return _pkg_version("waage")
    except PackageNotFoundError:
        pass
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "VERSION"
        if candidate.is_file():
            return candidate.read_text().strip()
    return "0.0.0+unknown"


__version__ = _load_version()
