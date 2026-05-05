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

```bash
git clone git@github.com:HalloWelt42/RS232-to-USB-Waagen-REST-API.git
cd RS232-to-USB-Waagen-REST-API

# Adapter prüfen
ls /dev/ttyUSB0

# alles bauen und starten
docker compose up -d --build

# fertig:
#   Frontend  http://<pi-ip>:8201
#   Backend   http://<pi-ip>:8200
#   API-Docs  http://<pi-ip>:8200/docs
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

## Hardware

- **Waage:** G&G PLC 6000g/0,1g (DB9 RS232)
- **Adapter:** FTDI FT232RL USB-RS232 (USB-VID:PID `0403:6001`)
- **Host:** Raspberry Pi 5 / Pi Zero 2 W (Linux)
- User muss in der `dialout`-Gruppe sein:
  `sudo usermod -aG dialout $USER && newgrp dialout`

## Lizenz

Self-hosted, no cloud, no tracking.
