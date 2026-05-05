"""Kommandozeilen-Interface zur Live-Anzeige der Waage."""

from __future__ import annotations

import argparse
import logging
import sys

from .reader import DEFAULT_BAUD, DEFAULT_PORT, Waage


def _format_reading(r) -> str:
    flag = "STABLE" if r.stable else "......"
    return (f"{r.timestamp:%H:%M:%S}  "
            f"{r.weight:>10.2f} g  "
            f"{flag}  "
            f"raw={r.raw!r}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="waage",
        description="G&G PLC Waage live auslesen",
    )
    p.add_argument("--port", default=DEFAULT_PORT,
                   help=f"serieller Port (default: {DEFAULT_PORT})")
    p.add_argument("--baud", type=int, default=DEFAULT_BAUD,
                   help=f"Baudrate (default: {DEFAULT_BAUD})")
    p.add_argument("--once", action="store_true",
                   help="nur einen Stable-Wert ausgeben, dann beenden")
    p.add_argument("--quiet", action="store_true",
                   help="nur das Gewicht in g, ohne Zusatz-Output (für Skripte)")
    p.add_argument("-v", "--verbose", action="count", default=0,
                   help="-v für INFO, -vv für DEBUG")
    args = p.parse_args(argv)

    level = logging.WARNING - 10 * args.verbose
    logging.basicConfig(level=max(logging.DEBUG, level),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    try:
        with Waage(args.port, args.baud) as w:
            for reading in w.stream():
                if args.quiet:
                    if reading.stable or not args.once:
                        print(f"{reading.weight:.2f}", flush=True)
                else:
                    print(_format_reading(reading), flush=True)
                if args.once and reading.stable:
                    return 0
    except KeyboardInterrupt:
        return 130
    except Exception as exc:  # noqa: BLE001 — CLI Top-Level
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
