# waage-backend

FastAPI-Service für die G&G PLC 6000g/0,1g Präzisionswaage über RS232/FTDI.

## Endpoints

| Methode | Pfad | Zweck |
|---------|------|-------|
| GET | `/` | API-Info + Endpoint-Map |
| GET | `/health` | Reader-Status, Uptime, letzter Frame |
| GET | `/weight` | Letzter bekannter Wert (JSON) |
| GET | `/weight/stable?timeout=5` | Wartet bis zum nächsten Stable-Wert |
| GET | `/history?limit=100` | Letzte N Readings aus dem Ringpuffer |
| WS  | `/stream` | Live-Stream aller neuen Readings |
| GET | `/docs` | Swagger UI |
| GET | `/openapi.json` | OpenAPI Schema |

## Setup ohne Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest                                    # 47 Tests
python -m waage.api                       # läuft auf :8200
```

## Setup mit Docker

```bash
docker build -t waage-backend .
docker run --rm -p 8200:8200 \
    --device=/dev/ttyUSB0 \
    -v ./data:/data \
    waage-backend
```

## Konfiguration (Environment)

| Variable | Default | Bedeutung |
|----------|---------|-----------|
| `WAAGE_PORT` | `/dev/ttyUSB0` | Serieller Port |
| `WAAGE_BAUD` | `9600` | Baudrate |
| `WAAGE_HOST` | `0.0.0.0` | HTTP Bind-Host |
| `WAAGE_API_PORT` | `8200` | HTTP Port |
| `WAAGE_HISTORY` | `1000` | Größe des In-Memory-Ringpuffers |
| `WAAGE_CSV` | — | Optional: CSV-Logdatei |
| `WAAGE_SQLITE` | — | Optional: SQLite-DB |
| `WAAGE_CORS` | `*` | Allowed-Origins, kommagetrennt |
| `WAAGE_LOGLEVEL` | `info` | uvicorn log level |

## Sniffer

Wenn das Frame-Format der Waage noch nicht bekannt ist:

```bash
python sniffer.py --port /dev/ttyUSB0          # 9600 Baud
python sniffer.py --autobaud                   # alle gängigen Baudraten testen
```

## Architektur

```
+----------+  RS232   +------+  USB   +------------------+
| G&G PLC  | ------>  | FTDI | -----> |  waage.reader    |
+----------+          +------+        |  (pyserial)      |
                                      +--------+---------+
                                               |
                                               v
                                      +------------------+
                                      |  waage.parser    |
                                      +--------+---------+
                                               |  (Reading)
                                               v
                +------------------------------+------------------------------+
                |                              |                              |
                v                              v                              v
       +-----------------+          +--------------------+        +---------------------+
       | MultiSink       |          | In-Memory          |        | WebSocket           |
       | CSV + SQLite    |          | State + History    |        | Subscriber-Queues   |
       +-----------------+          +----------+---------+        +-----------+---------+
                                               |                              |
                                               v                              v
                                     +-----------------------------------------------+
                                     |        FastAPI (REST + WebSocket)             |
                                     +-----------------------------------------------+
```

## Tests

```bash
pytest                  # alle Tests
pytest tests/test_api.py # nur API-Tests (mit gestubbtem Reader)
```

47 Tests verteilt auf:
- `test_parser.py` — 23 Tests, reine Frame-Parsing-Logik
- `test_reader.py` — 7 Tests, Serial-Wrapper mit Fake-Serial
- `test_logger.py` — 7 Tests, CSV/SQLite/MultiSink + Concurrency
- `test_api.py` — 10 Tests, REST + WebSocket via TestClient
