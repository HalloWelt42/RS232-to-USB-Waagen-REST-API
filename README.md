# RS232-to-USB-Waagen-REST-API

REST- und WebSocket-Schnittstelle zu einer **G&G PLC 6000g/0,1g**
Präzisionswaage, die per **RS232** über einen **FTDI USB-Adapter** an einen
Raspberry Pi angeschlossen ist. Das Backend ist eine FastAPI-Anwendung, das
Frontend eine eigenständige Svelte-5-SPA, die das Backend ausschließlich
über die REST-API anspricht.

**Stack:** FastAPI, pyserial, Svelte 5, Vite, nginx, Docker Compose.

## Architektur

```
+--------------+   RS232   +------+   USB    +-----------------------+
|  G&G PLC     |  ------>  | FTDI |  ----->  |  waage-backend        |
|  6000g/0,1g  |           |      |          |  FastAPI :8200        |
+--------------+           +------+          +-----------+-----------+
                                                         |
                                                         | REST + WS
                                                         v
                                             +-----------------------+
                                             |  waage-frontend       |
                                             |  Svelte 5 + nginx :80 |
                                             +-----------+-----------+
                                                         |
                                                  Browser :8201
```

## Schnellstart

Plattform-unabhängiges Setup-Skript erledigt venv, npm install und
zeigt erkannte Hardware:

```bash
git clone git@github.com:HalloWelt42/RS232-to-USB-Waagen-REST-API.git
cd RS232-to-USB-Waagen-REST-API
./scripts/setup.sh
```

Funktioniert auf **macOS, Linux, Raspberry Pi OS** — die richtigen
Treiber-Hinweise und Port-Erkennung kommen automatisch.

### Variante 1: Docker Compose (Linux / Raspberry Pi)

```bash
docker compose up -d --build
# Frontend  http://<host>:8201
# Backend   http://<host>:8200
# API-Docs  http://<host>:8200/docs
```

### Variante 2: Native (macOS, Linux, Pi)

Auf macOS ist das die empfohlene Variante, da Docker Desktop für Mac
keine USB-Devices durchreichen kann.

```bash
# Backend
cd backend
source .venv/bin/activate
python -m waage.api          # liest WAAGE_PORT=auto, findet Adapter selbst

# Frontend (zweites Terminal)
cd frontend
npm run dev                  # http://localhost:5184
```

## Endpoints

| Methode | Pfad | Zweck |
|---------|------|-------|
| GET | `/` | API-Info + Endpoint-Map |
| GET | `/health` | Reader-Status, Uptime, letzter Frame |
| GET | `/weight` | Letzter Wert (sofort, JSON) |
| GET | `/weight/stable?timeout=5` | Wartet auf nächsten Stable-Wert |
| GET | `/history?limit=100` | Letzte N Werte aus dem Ringpuffer |
| WS  | `/stream` | Live-Stream aller Readings als JSON |
| GET | `/docs` | Swagger UI (interaktiv) |
| GET | `/openapi.json` | OpenAPI 3.1 Schema |

Beispiel-Antwort `/weight`:
```json
{
  "weight_g": 1234.5,
  "unit": "g",
  "stable": true,
  "timestamp": "2026-05-05T18:42:11.234",
  "raw": "53542c2b313233342e3520670d0a"
}
```

## Repo-Struktur

```
RS232-to-USB-Waagen-REST-API/
├── docker-compose.yml          Top-Level Service-Komposition
├── README.md
├── data/                       Volume fuer CSV- und SQLite-Logs
├── backend/                    FastAPI + pyserial
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── sniffer.py              Standalone-Frame-Mitschnitt
│   ├── src/waage/              parser, reader, logger, api, cli
│   └── tests/                  pytest-Tests
└── frontend/                   Svelte 5 + Vite + nginx
    ├── package.json
    ├── Dockerfile              Multi-Stage: Build, dann nginx
    ├── nginx.conf              /api/* und /stream-WS, SPA-Fallback
    ├── vite.config.js          Dev-Proxy auf Backend :8200
    └── src/                    App.svelte, Komponenten, lib/
```

## Lokale Entwicklung (ohne Docker)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest                              # 47 Tests grün
python -m waage.api                 # läuft auf :8200
```

### Frontend

```bash
cd frontend
npm install
npm run dev                         # läuft auf :5184, Proxy auf Backend
npm run test                        # vitest
npm run build                       # statisches Bundle in dist/
```

Im Dev-Modus proxyt Vite `/api/*` und `/stream` auf `http://localhost:8200`,
sodass das Frontend in beiden Modi (Dev und Production-nginx) ohne Code-
Änderung läuft.

## Sniffer (Frame-Format ermitteln)

Wenn die Waage angeschlossen ist, das Frame-Format aber noch unbekannt:

```bash
cd backend
python sniffer.py --port /dev/ttyUSB0          # 9600 Baud
python sniffer.py --autobaud                   # Baudraten durchprobieren
```

Das Output (mit sichtbaren `\r\n` etc.) hilft, den Parser-Regex in
`backend/src/waage/parser.py` an das echte Format anzupassen, falls nötig.

## Konfiguration (Backend Environment)

| Variable | Default | Bedeutung |
|----------|---------|-----------|
| `WAAGE_PORT` | `/dev/ttyUSB0` | Serieller Port |
| `WAAGE_BAUD` | `9600` | Baudrate |
| `WAAGE_API_PORT` | `8200` | HTTP Port |
| `WAAGE_CSV` | — | Optional: CSV-Logdatei |
| `WAAGE_SQLITE` | — | Optional: SQLite-DB |
| `WAAGE_HISTORY` | `1000` | Größe des In-Memory-Ringpuffers |
| `WAAGE_CORS` | `*` | Allowed-Origins |

## Hardware und Plattform-Hinweise

- **Waage:** G&G PLC 6000g/0,1g (DB9 RS232, 9600 Baud, 8N1)
- **Adapter:** FTDI FT232RL USB-RS232 (USB-VID:PID `0403:6001`),
  zwingend mit **Nullmodem-Adapter / Crossover-Kabel** dazwischen
- **Host:** Raspberry Pi 5 / Pi Zero 2 W, beliebiges Linux-System,
  oder macOS

### Linux / Raspberry Pi

```bash
lsmod | grep ftdi          # ftdi_sio und usbserial sollten geladen sein
lsusb | grep -i ftdi       # FTDI-Adapter sichtbar?
ls -l /dev/ttyUSB0         # Device-Knoten muss da sein
```

User-Zugriffsrechte einrichten (einmalig):

```bash
sudo usermod -aG dialout,plugdev $USER
newgrp dialout
```

### macOS

Treiber für FTDI sind ab macOS 10.15 im System enthalten (Apple-VCP).
Falls nicht: VCP-Treiber von ftdichip.com oder
`brew install --cask ftdi-vcp-driver`. Der Port erscheint unter

```
/dev/cu.usbserial-FTxxxxxx
```

Die Auto-Erkennung im Backend (`WAAGE_PORT=auto`, Default) findet
diesen Pfad selbst — kein manuelles Setzen nötig. **Achtung:** Docker
Desktop für Mac reicht USB-Geräte nicht durch — auf macOS bitte das
Backend nativ starten (siehe Schnellstart Variante 2).

### Auto-Port-Erkennung

Das Backend startet im Default mit `WAAGE_PORT=auto` und sucht selbst
nach FTDI-, CP210x-, PL2303- oder CH340-Adaptern. Manueller Override
über die Umgebungsvariable:

```bash
WAAGE_PORT=/dev/ttyUSB1 python -m waage.api
WAAGE_PORT=/dev/cu.usbserial-FTEQZ0TS python -m waage.api
```

## Simulationsmodus (ohne Hardware)

Für Frontend-Entwicklung oder Demos ohne angeschlossene Waage gibt es
einen Software-Simulator, der über `WAAGE_SIMULATE=1` aktiviert wird:

```bash
# Compose mit Simulator
WAAGE_SIMULATE=1 docker compose up -d --build

# Bare metal
cd backend && WAAGE_SIMULATE=1 .venv/bin/python -m waage.api
```

Der Simulator generiert realistische Frames mit Gewichtsänderungen,
Stable/Unstable-Übergängen und Mess-Jitter. Frames durchlaufen denselben
Parser wie echte Daten — die API ist von außen nicht zu unterscheiden.

## Lizenz

Self-hosted, no cloud, no tracking.
