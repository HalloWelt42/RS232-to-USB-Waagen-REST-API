#!/usr/bin/env bash
#
# Plattformunabhängiges Setup-Skript für das Waagen-Projekt.
# Funktioniert auf macOS, Linux und Raspberry Pi OS.
#
# Aufruf:  ./scripts/setup.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OS="$(uname -s)"
echo "==> Plattform: $OS"

# ---------------- Python-Backend ---------------------------------------
echo "==> Backend-Setup"
cd "$ROOT/backend"

if [[ ! -d ".venv" ]]; then
  PY=python3
  command -v python3.13 >/dev/null 2>&1 && PY=python3.13
  command -v python3.12 >/dev/null 2>&1 && PY=python3.12
  command -v python3.11 >/dev/null 2>&1 && PY=python3.11
  echo "    venv wird mit $PY angelegt"
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade --quiet pip
pip install --quiet -e ".[dev]" "fastapi>=0.110" "uvicorn[standard]>=0.27"
deactivate

# ---------------- Frontend ---------------------------------------------
echo "==> Frontend-Setup"
cd "$ROOT/frontend"

if [[ ! -d "node_modules" ]]; then
  npm install --no-audit --no-fund
else
  echo "    node_modules vorhanden, Skipping npm install"
fi

# ---------------- Plattform-Hinweise -----------------------------------
echo
echo "==> Plattform-spezifische Hinweise:"
case "$OS" in
  Darwin)
    echo "    macOS erkannt"
    echo "    - FTDI-Treiber: meist im System enthalten (Apple-VCP). Falls"
    echo "      nicht: 'brew install --cask ftdi-vcp-driver' oder VCP-Driver"
    echo "      direkt von ftdichip.com."
    echo "    - Serieller Port liegt typischerweise unter:"
    echo "        /dev/cu.usbserial-FTxxxxxx"
    echo "    - Docker Desktop für Mac kann KEINE USB-Devices durchreichen."
    echo "      -> Backend bitte nativ starten (nicht via 'docker compose'),"
    echo "      Frontend kann beides."
    ;;
  Linux)
    if [[ -f "/etc/rpi-issue" ]] || grep -qi "raspberry" /proc/cpuinfo 2>/dev/null; then
      echo "    Raspberry Pi erkannt"
    else
      echo "    Linux erkannt"
    fi
    echo "    - Treiber: ftdi_sio + usbserial sind im Mainline-Kernel."
    echo "    - User in dialout-Gruppe? Prüfen mit 'groups'."
    echo "      Falls nicht: 'sudo usermod -aG dialout,plugdev \$USER && newgrp dialout'"
    echo "    - Serieller Port typischerweise: /dev/ttyUSB0"
    ;;
  *)
    echo "    Unbekannte Plattform: $OS"
    ;;
esac

# Auto-Detection live laufen lassen
echo
echo "==> Hardware-Erkennung:"
cd "$ROOT/backend"
.venv/bin/python -c "
from waage.tools import find_serial_port, list_serial_ports
found = find_serial_port()
print(f'    Erkannter Port: {found or \"(keiner)\"}')
all_ports = list_serial_ports()
if all_ports:
    print(f'    Alle Ports:')
    for p in all_ports:
        vid = f'{p[\"vid\"]:04X}' if p['vid'] else '----'
        pid = f'{p[\"pid\"]:04X}' if p['pid'] else '----'
        print(f'      {p[\"device\"]}  VID:{vid} PID:{pid}  {p[\"description\"]}')
else:
    print('    (keine seriellen Ports gefunden)')
"

cat <<EOF

==> Setup fertig.

Nächste Schritte:
  Backend starten:
    cd backend
    source .venv/bin/activate
    python -m waage.api

  Frontend starten:
    cd frontend
    npm run dev

  Backend ohne Hardware (Simulator):
    WAAGE_SIMULATE=1 python -m waage.api

  Mit Docker Compose (Linux/Pi):
    docker compose up -d --build

EOF
