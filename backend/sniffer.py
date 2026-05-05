#!/usr/bin/env python3
"""Roher RS232-Mitschnitt der G&G PLC Waage.

Hört auf dem angegebenen Port mit, gibt jede Zeile mit Zeitstempel und
repr() aus, sodass auch Steuerzeichen wie \\r\\n sichtbar werden.

Wenn auf der Default-Baudrate nichts ankommt, kann mit --autobaud eine
kurze Suche über typische Baudraten (2400, 4800, 9600, 19200) gestartet
werden.
"""

from __future__ import annotations

import argparse
import sys
import time
from contextlib import suppress

import serial

DEFAULT_PORT = "/dev/ttyUSB0"
COMMON_BAUDRATES = (9600, 2400, 4800, 19200, 1200, 38400)


def open_port(port: str, baud: int, timeout: float) -> serial.Serial:
    return serial.Serial(
        port=port,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=timeout,
    )


def listen(port: str, baud: int, timeout: float) -> None:
    with open_port(port, baud, timeout) as ser:
        print(f"Lausche auf {port} @ {baud} 8N1 ... (Ctrl+C zum Beenden)",
              file=sys.stderr)
        while True:
            data = ser.readline()
            if data:
                print(f"{time.strftime('%H:%M:%S')}  {data!r}", flush=True)


def autobaud_probe(port: str, seconds_per_baud: float = 3.0) -> None:
    """Probiert nacheinander die häufigsten Baudraten durch.

    Bei jeder Rate werden für ``seconds_per_baud`` Sekunden Daten
    mitgeschnitten. Bei der ersten Baudrate, die druckbare Bytes liefert,
    wird ein Hinweis ausgegeben — die Schleife läuft aber bewusst weiter,
    damit der Mensch entscheiden kann.
    """
    for baud in COMMON_BAUDRATES:
        print(f"\n=== Test @ {baud} Baud ===", file=sys.stderr)
        try:
            with open_port(port, baud, timeout=0.5) as ser:
                deadline = time.monotonic() + seconds_per_baud
                got_anything = False
                while time.monotonic() < deadline:
                    data = ser.readline()
                    if data:
                        got_anything = True
                        printable = sum(1 for b in data if 32 <= b < 127
                                        or b in (10, 13))
                        ratio = printable / len(data)
                        marker = " <- plausibel" if ratio > 0.7 else ""
                        print(f"{time.strftime('%H:%M:%S')}  {data!r}"
                              f"  [printable {ratio:.0%}]{marker}",
                              flush=True)
                if not got_anything:
                    print("(keine Daten)", file=sys.stderr)
        except serial.SerialException as exc:
            print(f"Fehler bei {baud}: {exc}", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", default=DEFAULT_PORT)
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("--timeout", type=float, default=2.0,
                   help="readline-Timeout in Sekunden")
    p.add_argument("--autobaud", action="store_true",
                   help="probiert typische Baudraten der Reihe nach durch")
    args = p.parse_args()

    with suppress(KeyboardInterrupt):
        if args.autobaud:
            autobaud_probe(args.port)
        else:
            listen(args.port, args.baud, args.timeout)


if __name__ == "__main__":
    main()
