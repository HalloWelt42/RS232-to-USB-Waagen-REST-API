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
| `WAAGE_SIMULATE` | aus | `1`/`true`/`yes` aktiviert den Software-Simulator anstelle der echten Waage |

## Simulationsmodus

Für UI-Demos, Frontend-Entwicklung und End-to-End-Tests ohne Hardware
gibt es einen Software-Simulator. Aktivierung über die Umgebungsvariable
`WAAGE_SIMULATE=1`:

```bash
WAAGE_SIMULATE=1 python -m waage.api
```

Der Simulator imitiert das Verhalten der echten Waage:

- Standard-Frame-Rate von 4 Hz
- Wechselnde Zielgewichte zwischen 0 g und 3000 g
- Realistische Übergänge mit instabilen Frames während des Wägens
- Mess-Jitter im Bereich der Geräteauflösung (0,1 g)
- Frames im G&G-typischen Format `ST,+ 1234.5 g\r\n`

Die im Simulationsmodus erzeugten Frames durchlaufen denselben Parser
und dieselben Sinks wie echte Daten — die API ist von außen nicht zu
unterscheiden.

## Treiber

Der FTDI-Adapter (Chip FT232R, USB-VID:PID `0403:6001`) wird unter
Linux durch das Kernel-Modul `ftdi_sio` bedient. Das Modul ist bei
Raspberry Pi OS, Debian und Ubuntu standardmäßig im Kernel enthalten —
**kein zusätzlicher Treiber notwendig**.

Statusprüfung:

```bash
lsmod | grep ftdi          # ftdi_sio + usbserial sollten gelistet sein
lsusb | grep -i ftdi       # Future Technology Devices ... FT232 Serial
ls -l /dev/ttyUSB0         # Device-Knoten muss da sein
dmesg | grep -i ttyusb     # Verbindungs-Log
```

Falls `/dev/ttyUSB0` nicht erscheint, hilft meist:

```bash
sudo modprobe ftdi_sio
sudo dmesg | tail
```

User in die Zugriffsgruppe aufnehmen (sonst Permission denied):

```bash
sudo usermod -aG dialout,plugdev $USER
newgrp dialout
```

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
