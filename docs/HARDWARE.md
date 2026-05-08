# Waage — Hardware- und Protokoll-Referenz

Stand: Mai 2026 · Quellen: offizielle G&G-Manuale (gandg.de), eigener
Reverse-Engineering-Stand des Reader-Codes, Live-Verifikation mit dem
laufenden Backend gegen eine angeschlossene PLC-6000.

Dieses Dokument fasst zusammen, **was die G&G-Präzisionswaagen über
ihre RS232-Schnittstelle leisten**, was die App davon nutzt und wo
die Grenzen der Hardware liegen. Alle Aussagen sind entweder aus den
G&G-Bedienungsanleitungen belegt oder durch Live-Test verifiziert;
spekulative Punkte sind explizit als solche markiert.

---

## 1. Direktantwort: lassen sich Geräte-Zustände auslesen?

**Nein, mit Ausnahme dessen, was im Wäge-Frame mitkommt.** Das G&G-
Protokoll ist eine reine Print-Schnittstelle: der PC fragt einen Wert
an, die Waage antwortet mit dem aktuellen Anzeigewert. Es gibt
**keine Read-Back-Befehle** für interne Zustände.

| Zustand | Per RS232 abfragbar? | Anmerkung |
|---|:---:|---|
| Aktueller Wägewert | ✅ | im Frame (`Sign + Data + Unit`) |
| Aktive Einheit (g, kg, oz, lb, ct, pcs) | ✅ | im Frame, Feld `Unit` |
| Vorzeichen ± | ✅ | im Frame, Feld `Sign` |
| Stabil/instabil | ⚠️ | **nicht direkt** — G&G sendet keinen ST/US-Header. Heuristik: bei schwankender Anzeige antwortet die Waage erst, wenn sie sich beruhigt hat (effektiv „immer stabil") |
| Beleuchtungs-Status (an/aus) | ❌ | nur Toggle (`ESC u`), keine Read-Antwort |
| Aktiver Modus (Wiegen vs. Stückzählen) | ⚠️ | nur indirekt: im Pcs-Modus erscheint `pcs` als Einheit im Frame |
| Hardware-Tara-Wert | ❌ | nur Set (`ESC t`), kein Read; der angezeigte Wert ist relativ |
| Kalibrier-Datum / Service-Daten | ❌ | nicht vorgesehen |
| Filter-Stärke / C1–C7-Setup | ❌ | nur am Gerät über das Setup-Menü konfigurierbar |
| COMM-ID (erstes Steuer-Byte) | ❌ | nur am Gerät über C4 änderbar |
| Maximalkapazität / Modellname | ❌ | hartcodiert in der App-Modell-Liste |

Die App muss daher den **Software-State** (Toleranz, Software-Tara,
Differenz-Stapel, Stückzähl-Kalibrierung) selbst halten. Genau dafür
gibt es die `/app/*`-Endpunkte (siehe Abschnitt 8).

---

## 2. Vollständiger Befehlssatz

Steuerbyte ist `ESC` (`0x1B`) ab Werk; via Setup-Code C4 änderbar
(z.B. um mehrere Waagen am gleichen Bus mit unterschiedlichen
Präfixen zu adressieren). Buchstabe danach bleibt jeweils gleich.

| Befehl | Bytes | Wirkung | Risiko | App-Endpunkt |
|---|---|---|---|---|
| `ESC p` | `1B 70` | **Print** — Waage sendet einmalig den Wäge-Frame | – | implizit über `/scale/weight`, Polling-Loop |
| `ESC q` | `1B 71` | **Calibrate** — startet die interne Kalibrierroutine (entspricht der `CAL`-Taste) | ⚠️ **Hoch** — verändert Kalibrierung | absichtlich nicht im Frontend exponiert |
| `ESC r` | `1B 72` | **Count** — schaltet den Stückzählmodus an/aus | mittel | nicht exponiert (App nutzt eigene Software-Stückzählung) |
| `ESC s` | `1B 73` | **Unit** — schaltet die Anzeige-Einheit weiter (g → kg → oz → …) | gering | `POST /scale/command/unit` |
| `ESC t` | `1B 74` | **Tare** — setzt die Anzeige auf Null (entspricht der `TARE`-Taste) | gering | `POST /scale/command/tare` |
| `ESC u` | `1B 75` | **Light** — schaltet die Hintergrund-Beleuchtung um | gering | `POST /scale/command/light` |

**Weitere Befehle existieren laut G&G-Manualen nicht.** Recherche
in den Quellen JJ-BC, EY2015, PLC2018, Schnittstelle-E ergab
übereinstimmend, dass dies der vollständige offizielle Befehlssatz
ist. Wer Filter-Stärke, Auto-Off-Zeit oder Print-Tasten-Belegung
ändern will, muss das **am Gerät** über das C-Menü tun (Abschnitt 5).

---

## 3. Frame-Format (16 Bytes)

```
[Sign 2B] [Data 7B] [Unit 3B] [CR] [LF]
   ↑          ↑         ↑       ↑    ↑
 0x20×2    "  12.345"  " g "  0x0d 0x0a
 oder
 "- "
```

**Live-Beispiel** vom angeschlossenen PLC-6000 bei Auflage 0 g:

```
Hex   :  20 20 20 20 20 20 30 2e 30 20 67 20 0d 0a
ASCII : '      0.0 g \r\n'
Länge :  14 Bytes (PLC-6000 lässt das Sign-Feld bei 0 g weg)
```

Bei Last würde die Anzeige z.B.

```
ASCII : ' +123.45 g \r\n'    (positiv)
ASCII : ' -  12.3 kg\r\n'    (negativ, kg)
```

senden. Das Backend parst beides toleriert über die Regex in
`backend/src/waage/parser.py`.

**Was das Frame nicht enthält:**

- **Kein Stabilitäts-Indikator.** Anders als A&D, Mettler, OHAUS oder
  Kern (die mit `ST,+ 123.4 g\r\n` bzw. `US,…` arbeiten) gibt G&G
  keinen ST/US-Header aus. Der Parser erkennt das Alternativ-Format
  trotzdem für Kompatibilität mit anderen Hersteller-Frames.
- **Keine Modus-Information.** Ob die Waage gerade im Wiege- oder
  Stückzählmodus ist, lässt sich nur an der Einheit `pcs` erahnen.
- **Keine Geräte-ID, kein Zeitstempel, keine Sequenznummer.** Die
  Zuordnung geschieht ausschließlich anhand der Reihenfolge.

---

## 4. Serielle Parameter

| Parameter | Wert |
|---|---|
| Baud | 600 / 1200 / 2400 / 4800 / 9600 (siehe Setup C3) — **Default 600 für JJ-BC/EY**, **9600 für PLC-Stream-Modi** |
| Datenbits | 8 |
| Stopbits | 1 |
| Parity | none |
| Flow control | none (3 Drähte: TxD, RxD, GND) |
| Steckverbinder | DE-9 weiblich an der Waage (DCE) |
| Pinout | Pin 2 = TxD (Waage→PC), Pin 3 = RxD (PC→Waage), Pin 5 = GND |
| Kabel | **Nullmodem zwingend** — Pins 2/3 gekreuzt |

Im hier vorliegenden Setup wird ein FTDI-USB-Serial-Adapter zwischen
Pi und Waage benutzt (`/dev/ttyUSB0`), Nullmodem-Adapter-Stecker am
Waagen-Ende.

---

## 5. Konfiguration über das C-Menü (am Gerät)

Aufruf: bei **ausgeschaltetem** Gerät die `[CAL]`-Taste halten und
zusätzlich `[ON/OFF]` drücken. Mit `[CAL]` durch die Codes blättern,
mit `[TARE]` den Wert ändern, am Ende `[CAL]` zum Speichern.

| Code | Bedeutung | Werte | Default |
|---|---|---|---|
| C1 | Empfindlichkeit / Filter A | 0–4 (JJ/EY), 0–6 (PLC) | 2 (JJ/EY), 1 (PLC) |
| C2 | Filter-Stärke / Schwingungsfilter | 0–3 bzw. 0–4 | 2 bzw. 1 |
| **C3** | **Sende-Modus + Baudrate** | siehe Tabelle unten | 6 (= 9600 Polling) bzw. 2 (= 600 Polling) |
| C4 | COMM-ID (erstes Steuerbyte) | 0–255 | 27 = `0x1B` (ESC) |
| C5 | Auto-Power-Off / Backlight-Modus | 0–4 (Akku) | modellabhängig |
| C6 | Print-Tasten-Belegung | 0 / 1 / 2 | 0 |
| C7 | Rück-Display | 0 / 1 | 1 |

### C3 — Sende-Modus

| C3-Wert | Modus | Baud |
|---|---|---|
| **0** | **Stream** — Waage sendet kontinuierlich 1 × pro Sekunde | 9600 fix |
| **1** | **Auto-on-stable** — sendet automatisch, sobald der Wert stabil ist; muss erst auf 0 zurück, bevor neu getriggert wird | 9600 fix |
| 2 | Manuell, Polling | 600 |
| 3 | Manuell, Polling | 1200 |
| 4 | Manuell, Polling | 2400 |
| 5 | Manuell, Polling | 4800 |
| 6 | Manuell, Polling | 9600 |

**Stream-Mode (C3 = 0/1) gibt es nur auf den ausdrücklich
bezeichneten PLC-`-C`/`-B`-Modellen** (z.B. PLC-300-C, 600-C, 1200-C,
100B-C, 200B-C, 300B-C, 2000B, 3000B). Auf JJ-/EY-/TJ-Y-Modellen
funktioniert ausschließlich Polling vom PC aus.

**Sendefrequenzen >1 Hz** sind hardwareseitig nicht konfigurierbar.
Höhere Raten erreicht man nur durch aktives Polling (PC schickt z.B.
alle 100 ms ein `ESC p`), limitiert durch die interne Filterzeit der
Waage und die Baudrate. Bei 9600 8N1 und 16-Byte-Frame ist das
theoretische Maximum etwa 50 Hz.

---

## 6. Modell-Matrix

| Familie | RS232 ab Werk | Stream-Modus (C3=0) | Auto-on-stable (C3=1) | `ESC u` (Light) |
|---|:---:|:---:|:---:|:---:|
| PLC-300-C / 600-C / 1200-C / 100B-C / 200B-C / 300B-C / 2000B / 3000B | ✅ | ✅ | ✅ | ✅ dokumentiert |
| PLC-300 / 600 / 1200 / 3000 / **6000** (ohne -C/-B) | ✅ | – | – | ✅ dokumentiert |
| PLC-15K / 30K | ✅ | – | – | ✅ dokumentiert |
| JJ / JJ-B / JJ-BC | ✅ | ❌ (nur Polling) | ❌ | – nicht dokumentiert |
| EY-Serie (EY2015 …) | ✅ | ❌ (nur Polling) | ❌ | ✅ (`ESC u`) |
| TJ-Y | ✅ | unklar | unklar | unklar — Manual ist Bild-PDF |

Die App liest die Modell-Eigenschaften aus
`backend/src/waage/models.py`, in der ScaleModel-Datenklasse mit
Maximalkapazität, Auflösung, Mindest-Auflage, Linearität, Wieder-
holbarkeit, Beruhigungs-/Aufwärmzeit und Betriebstemperatur.

---

## 7. Wie das Backend mit den Frames umgeht

### Reader-Loop (`backend/src/waage/reader.py`)

```
┌────────────────────────────┐
│  serial.Serial.read(...)   │  ← rohes Byte-Stream vom Port
└──────────┬─────────────────┘
           │ append into _buf (bytearray)
           ▼
┌────────────────────────────┐
│  _take_frame() — Split bei │  ← _buf.find(b'\n')
│  LF (Zeilenende)           │
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│  parser.parse(frame)       │  ← Regex auf Sign/Value/Unit
│  → Reading                 │
└──────────┬─────────────────┘
           │
           ▼
   state.publish(reading)
   ┌──────────────┬───────────┐
   ▼              ▼           ▼
state.latest  WS-Stream    Messlog (SQLite)
              /scale/stream  /app/messlog
```

### Polling-Modus (`Waage(poll_command=COMMAND_PRINT, poll_interval=2.0)`)

Schickt periodisch `ESC p`. Ist der Default für G&G-Geräte ohne
Stream-Mode-Support. Polling-Intervall in der laufenden Instanz
wird durch `WAAGE_POLL_HZ` (env) bzw. den Default 0.5 Hz bestimmt.

### Idempotente `close()`-Methoden

Sowohl die echte `Waage` als auch die `SimulatedWaage` haben eine
public `close()`-Methode (seit 0.4.6), damit der Reader-Loop beim
Wechsel zwischen Live und Simulator sauber abräumen kann.

---

## 8. Welche „Schaltstellungen" die App selbst kennt

Da die Hardware keine Status-Reads bietet, hält die App ihren
eigenen Software-State und stellt ihn als REST-Endpunkte bereit:

| Endpunkt | Inhalt | Bemerkung |
|---|---|---|
| `GET /scale/health` | Reader-Status, Port, Baudrate, Uptime, source_mode (live/simulate), simulated, version | Single-Source für Verbindungs- und Backend-Diagnose |
| `GET /scale/weight` | letztes Reading inklusive `raw`-Bytes | das echte Hardware-Frame |
| `GET /scale/weight/stable?timeout=N` | wartet auf den nächsten stabilen Frame | für Skript-Integration |
| `GET /scale/stream` (WS) | kontinuierlicher Push aller Frames | für Live-Anzeige |
| `GET /scale/history?limit=N` | Ringpuffer der letzten N Readings | |
| `GET /scale/models` / `GET /scale/config` / `PUT /scale/config` | Modell-Auswahl | reine App-Konfig, nicht hardware-relevant |
| `GET /app/netto` | Software-Tara aktiv? Wert? Live-Netto | App-State |
| `GET /app/differenz` | Tara-Stapel mit Schichten, Σ-Tara | App-State |
| `GET /app/tolerance` | Soll-Wert, ±, Status (ok/low/high/idle) | App-State |
| `GET /app/count` | Stückgewicht, Referenz-Anzahl, kalibriert? | App-State |
| `GET /app/messlog?limit=N` | Letzte N Wert-Änderungen mit Diff | persistent in `data/messlog.db` |

Eine aggregierte „Snapshot aller App-Zustände auf einen Schlag"-Route
existiert nicht; sie ließe sich aber leicht ergänzen, falls für
Drittsysteme ein einzelnes Polling sinnvoller wäre als 5 parallele.

---

## 9. Live-Befehle praktisch ausprobieren

### Aktuellen Wert holen

```bash
curl -s http://localhost:8200/scale/weight | python3 -m json.tool
```

### Rohbytes des letzten Frames als Text

```bash
curl -s http://localhost:8200/scale/weight \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(bytes.fromhex(d['raw']))"
```

### Hardware-Befehl absetzen

```bash
curl -s -X POST http://localhost:8200/scale/command/tare    # ESC t
curl -s -X POST http://localhost:8200/scale/command/unit    # ESC s
curl -s -X POST http://localhost:8200/scale/command/light   # ESC u
```

### Live-Stream über Websocket (Python)

```python
import asyncio, json, base64, websockets

async def stream():
    async with websockets.connect("ws://localhost:8200/scale/stream") as ws:
        async for msg in ws:
            d = json.loads(msg)
            raw = base64.b64decode(d["raw"])
            print(d["timestamp"], d["weight_g"], "g", "stable" if d["stable"] else "—",
                  "raw:", raw)

asyncio.run(stream())
```

---

## 10. Anschlussplan

### Verkabelung Waage ↔ Pi

```
┌──────────────────┐
│  G&G PLC-6000    │ DE-9 weiblich (DCE) an der Waage
│                  │
│  Pin 2 = TxD ────┼──┐    Nullmodem-Adapter
│  Pin 3 = RxD ────┼──┼──┐ (Pins 2 ↔ 3 gekreuzt,
│  Pin 5 = GND ────┼──┼──┼──┐ 5 ↔ 5 straight)
│  Pin 4 = DTR (─) │  │  │  │
│  Pin 7 = RTS (─) │  │  │  │
└──────────────────┘  │  │  │
                      │  │  │
                      ▼  ▼  ▼
                 ┌──────────────┐
                 │  USB-Serial  │  z.B. FTDI FT232RL
                 │  Adapter     │  USB-VID:PID 0403:6001
                 │              │
                 │  TxD ─── 3 ──┐
                 │  RxD ─── 2 ──┘  Crossover bereits im Adapter,
                 │  GND ─── 5      wenn das Kabel ein „Console"-
                 │  USB ──> A ──┐  oder „Nullmodem"-Kabel ist.
                 └──────────────┘
                                │
                                ▼
                 ┌───────────────────────────┐
                 │  Raspberry Pi 5/4/Zero 2W │
                 │  /dev/ttyUSB0             │
                 │                           │
                 │  Backend liest mit        │
                 │  pyserial 8N1, 9600 baud  │
                 │  poll: ESC p alle 2 s     │
                 └───────────────────────────┘
```

### Signal-Flussrichtung (entscheidend!)

Da die Waage ein **DCE** ist und der PC/Pi ein **DTE**, müssen TxD und
RxD **gekreuzt** werden. Das übernimmt der Nullmodem-Adapter zwischen
Waage und Adapter-Kabel. Wenn statt dem Adapter ein „echtes" RS232-
Kabel benutzt wird, muss es ein **Crossover-Kabel** sein.

**Kontrolle**:

```bash
# Waage müsste auf ESC p antworten
.venv/bin/python -c "
import serial, time
s = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
s.write(b'\x1bp')
time.sleep(0.2)
print(repr(s.read(64)))
"
```

Erwartete Ausgabe:
```
b'      0.0 g \r\n'   bei Auflage 0
b' +123.4 g \r\n'    bei 123,4 g positiv
b''                    falls Verkabelung falsch (Tx/Rx vertauscht)
```

---

## 11. Hardware-Stückliste

Was man tatsächlich braucht, um eine G&G-Waage an einen Raspberry Pi zu
hängen — getestet mit der hier vorliegenden Kombination:

| # | Komponente | Empfehlung | Bezug | Preis ~ |
|---|---|---|---|---|
| 1 | **Pi-Host** | Raspberry Pi 5 (4 GB) oder Pi 4 (2 GB+) oder Pi Zero 2 W | Reichelt, BerryBase, BuyZero | 50–80 € |
| 2 | **MicroSD** | 32 GB Class 10 (Sandisk Industrial / Kingston Endurance) | dito | 8–12 € |
| 3 | **USB-Serial-Adapter** | FTDI FT232RL (z.B. FTDI Chipi-X) **oder** CP210x (CSL CP2102) **oder** PL2303 (gold) **oder** CH340 | Reichelt, AliExpress | 8–25 € |
| 4 | **Nullmodem-Adapter DE-9 W↔M** | beliebiger Markenhersteller mit gekreuzten Pins 2/3 | Conrad, Reichelt | 3–6 € |
| 5 | **Stromversorgung Pi** | offizielles Pi-5 / Pi-4 PSU (5 V / 5 A USB-C bzw. 5 V / 3 A USB-C) | Pi-Foundation-Reseller | 12–18 € |
| 6 | **Pi-Gehäuse** | Argon NEO oder Flirc Case (passive Kühlung, gut für 24/7) | dito | 15–30 € |
| 7 | **Ethernet-Kabel oder WLAN** | Cat-5e ≥ 1 m, oder Pi-internes WLAN | – | 0–5 € |
| 8 | **G&G-Waage** | PLC-6000 (oder JJ-B/JJ-BC/EY) — siehe Modell-Matrix oben | gandg.de oder ggscales.com | je nach Modell 250–800 € |

**Optional, für Werkstatt-Setup:**

| # | Komponente | Zweck |
|---|---|---|
| 9 | Industrie-USB-Verlängerung 2–5 m | Pi an Schaltschrank, Waage an Werkbank |
| 10 | DIN-Hutschienen-Pi-Halter | Aufbau im Schaltschrank |
| 11 | Touch-Display 7" für Pi | Standalone-Wäge-Terminal |
| 12 | Ferrit-Kerne | falls EMV-Probleme bei langem RS232-Kabel |

**Erfahrungswerte:**

- **FTDI-Adapter** sind am zuverlässigsten und werden vom Backend ohne
  Konfiguration auto-erkannt (USB-VID `0403`).
- **CH340-Adapter** funktionieren auch, brauchen unter macOS ggf.
  Treiber-Installation.
- **PL2303 schwarz/silber** sind oft Klone und unter Linux/Windows
  manchmal instabil — die goldene FTDI-Variante ist bei Pi-Setups
  zuverlässiger.
- **Kabel-Längen über 5 m** rufen vereinzelt Frame-Korruptionen hervor;
  bei industriellem Einsatz lieber eine USB-Verlängerung (statt langes
  RS232) plus Adapter direkt an der Waage.

---

## 12. Erweiterte Protokoll-Interpretation und Lösungsansätze

Für jeden „Hardware-Mangel" aus Abschnitt 1 hier ein Workaround,
soweit vom Reader-Code oder von der App-Logik realisierbar.

### 12.0 USB-Adapter abgezogen / Hardware tot

**Problem**: bei pyserial blockiert `read()` nach einem Adapter-Abriss
nicht zwingend mit einer Exception — `read_one()` gibt dann nur leere
Frames (`None`) zurück, der Reader-Loop drehte vorher endlos im 10 ms-
Takt, `last_seen` blieb auf dem letzten erfolgreichen Frame stehen,
und `reader_alive` war stoisch `True`.

**Lösung im Reader-Loop seit 0.5.12**:

- `AppState.scale_alive` als zweite Wahrheit neben `reader_alive`:
  `True` nur, wenn die Hardware in den letzten
  `WAAGE_SCALE_STALE_AFTER_S` Sekunden (Default 5 s) ein Frame
  geliefert hat. Default-Schwelle ist großzügig genug für
  0,5–1 Hz Polling, eng genug, dass ein Disconnect binnen Sekunden
  sichtbar wird.
- `AppState.stale_for_s` für Diagnose: Sekunden seit dem letzten
  erfolgreichen Frame.
- Periodischer Stale-Check im Reader-Loop (alle 2 s): liegt
  `stale_for_s` über dem doppelten Schwellwert (Default 10 s) ODER
  hat der gerade frisch geöffnete Reader nach 10 s noch keinen
  einzigen Frame bekommen, wirft der Loop selbst einen
  `RuntimeError`. Das löst den schon vorhandenen Reconnect-Pfad
  mit exponentiellem Backoff aus — wenn der Adapter zurückkommt,
  wird er beim nächsten `reader_factory()`-Aufruf wieder gefunden.
- HTTP-Health (`GET /scale/health`) liefert beide Felder
  (`scale_alive`, `stale_for_s`) zusätzlich zum bisherigen
  `reader_alive`. `ok` bleibt für Backward-Kompatibilität an
  `reader_alive AND latest is not None` gebunden — die UI nutzt
  primär `scale_alive` für die WAAGE-LED.

**Konfigurations-Stellschraube**:

```bash
# Stale-Schwelle in Sekunden anpassen — Default 5 s
WAAGE_SCALE_STALE_AFTER_S=10 .venv/bin/python -m waage.api
```

### 12.1 Stable/Unstable trotz fehlendem Header

**Problem**: G&G sendet keine `ST,`/`US,`-Markierung. Reader weiß nicht
direkt, ob der Wert gerade schwankt.

**Lösung im Code (`messlog.py`)**:
- Nach jedem `ESC p` antwortet die Waage erst, wenn der interne Filter
  einen stabilen Mittelwert ermittelt hat (Beruhigungs-Zeit, modell-
  abhängig 2–5 s).
- Der Reader interpretiert „Frame kommt zurück" implizit als „stabil".
  Bei kontinuierlichem Polling fällt eine schwankende Phase als Lücke
  zwischen Frames auf.
- Heuristik in `messlog.py`: ein neuer Eintrag wird nur dann gespeichert,
  wenn `|new − last| ≥ ε` (Default `ε = 0,05 g`). Damit fallen Mikro-
  Schwankungen ohne Bedeutung raus.

### 12.2 Beleuchtungs-Status

**Problem**: `ESC u` ist Toggle, kein Read.

**Lösungsansatz**: App speichert den Toggle-Zustand selbst nach jedem
gesendeten Befehl. Vor dem ersten Toggle ist der Status unbekannt — die
App zeigt das in der UI als „—" und schaltet beim ersten Klick auf
„an" (Annahme: Standard nach Boot ist „aus" bei vielen Modellen).
Aktuell **nicht implementiert** — zu wenig Mehrwert für die typischen
Werkstatt-Szenarien.

### 12.3 Hardware-Tara erkennen

**Problem**: Wenn die Waage am Gerät tariert wurde (`TARE`-Taste), wertet
die App den anschließenden Wert als Netto, weiß aber nicht, was vorher
das Brutto war.

**Lösungsansatz**: Software-Tara als alternative Strategie — die App
hält ein eigenes Tara-Gewicht und zeigt Brutto = Live, Tara = Software-
Wert, Netto = Brutto − Tara. Vorteil: sichtbar und protokolliert.
Wird im **Behälter-wiegen-Tool** und im **Differenz-Wiegen-Tool** so
umgesetzt (siehe `FUNCTIONS.md`).

### 12.4 Stückzähl-Modus erkennen

**Problem**: Wenn die Waage am Gerät auf Stückzählen umgestellt wurde,
liefert sie statt `g` die Einheit `pcs`. Die App rechnet dann fälsch-
licherweise mit der Stück-Zahl als Gramm-Wert.

**Lösungsansatz**: Parser akzeptiert `pcs` als Einheit nicht — solche
Frames würden als Parse-Fehler verworfen. App-seitig sollte zusätzlich
ein Hinweis erscheinen, falls Frames lange ausbleiben — könnte
implementiert werden, ist aktuell **nicht** drin.

### 12.5 Überlast erkennen (`OL`)

**Problem**: Bei Last > Maximum sendet die Waage statt eines Werts den
String `OL` (oder eine Reihe Striche `------`).

**Lösungsansatz im Parser**: das Standard-Regex matcht nur Zahlen mit
optionalem Vorzeichen — `OL` wird als `Reading=None` zurückgegeben und
verworfen. Frontend sieht dadurch „letzter gültiger Wert", nicht das
`OL`.

**Verbesserung wäre**: explizite Überlast-Erkennung im Parser, die ein
spezielles `Reading.overload=True` setzt. Frontend könnte dann eine rote
„OVERLOAD"-Banner anzeigen. **Nicht** im aktuellen Code — wäre 30 Zeilen.

### 12.6 Kalibrierung skripten

**Problem**: `ESC q` startet die internen Kalibrier-Routine; sie erwartet
dann am Gerät die Kalibrier-Gewicht-Auflage und Bestätigung. Das ist
**nicht** rein per RS232 abwickelbar — am Gerät muss eine Hand sein.

**Lösungsansatz**: Befehl wird im Frontend bewusst **nicht exponiert**
(Risiko, Kalibrierung versehentlich zu starten). Wer das tun will,
benutzt direkt:

```bash
.venv/bin/python -c "
import serial, time
s = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
s.write(b'\x1bq')
print('Kalibrier-Routine angestoßen — Gewichte am Gerät auflegen.')
"
```

### 12.7 Mehrere Waagen am gleichen Bus

**Problem**: zwei Waagen am gleichen RS232-Strang würden sich auf
`ESC p` gleichzeitig melden und Frames ineinander mischen.

**Lösungsansatz** laut G&G-Manual: Setup-Code C4 ändert das Steuer-Byte
pro Gerät (z.B. `!` statt `ESC` bei Waage 2). Der PC schickt dann
`!p` für Waage 2 und `\x1bp` für Waage 1. **Im Code nicht implementiert**;
die App erwartet aktuell genau ein angeschlossenes Gerät.

---

## 13. Foren-Recherche und OEM-Identität

Status nach Durchstöbern von mikrocontroller.net, eevblog,
electronics.stackexchange, Reddit, GitHub und Hackaday: **es gibt
praktisch keine Hobbyist-Lore zu undokumentierten G&G-Befehlen oder
Service-Modi.** Das offizielle Manual ist die einzige Quelle.

### Baugleiche OEM-Marken

G&G ist eine deutsche Vertriebsmarke (G&G GmbH, Kaarst), die Geräte
werden in China gefertigt. Anhand identischer Spezifikationen,
Tasten-Layouts und 9600-8N1-Konfiguration verhalten sich folgende
Marken **wahrscheinlich kompatibel** zum gleichen RS232-Protokoll
(nicht alle bestätigt — vor produktivem Einsatz testen):

| Marke | Vermutlich kompatibel | Quelle |
|---|:---:|---|
| **Bonvoisin** Analytical Balances | ja | Datenblatt: `9600 bps, 8 data, 1 stop, no parity; modes continuous/press/timing` |
| **U.S. Solid** Lab Scales | wahrscheinlich | identisches Tasten-Layout, dokumentierter RS232 |
| **Steinberg Systems SBS-LW** | wahrscheinlich | dito, deutscher Wiederverkäufer |
| **HoChoice / TFCFL** | wahrscheinlich | Direkt-Importe aus China, gleiches Gehäuse |
| ggscales.com (Direktvertrieb G&G) | ja | gleicher Hersteller |
| **Kern, Sartorius, A&D, OHAUS** | **nein** | eigene Protokolle (KCP, xBPI/SBI, AD-4212) |

### Was das bedeutet

Die App und der Reader-Code sollten an Bonvoisin-/Steinberg-Geräten ohne
Änderung funktionieren. Bei den ausdrücklich ausgeschlossenen Marken
(Kern, Sartorius etc.) braucht es einen anderen Parser — die Frame-
Formate dort sind grundlegend anders aufgebaut.

### Praktischer Plan-B für Geräte ohne Befehl

Der einzige in Foren bestätigte Workaround für blinde Hardware-
Steuerung ist das **Relais am `PRINT`-Taster**: ein Mikrocontroller
schließt physikalisch den Tastkontakt, dadurch sendet die Waage einen
Frame ohne RS232-Befehl. Anwendung typischerweise bei billigen
Waagen, die nur ein einseitig-aktives RS232-Output ohne Print-Anfrage
unterstützen. Bei den hier gelisteten G&G-/Bonvoisin-Geräten **nicht
nötig** — `ESC p` funktioniert.

---

## 14. Quellen

- [G&G Schnittstelle (DE) — Anleitung-Schnittstelle.pdf](https://gandg.de/download/anleitungen/Anleitung-Schnittstelle.pdf)
- [G&G Schnittstelle (EN) — Anleitung-Schnittstelle-E.pdf](https://www.gandg.de/download/anleitungen/Anleitung-Schnittstelle-E.pdf)
- [G&G JJ-BC (EN) — JJ-BC_e.pdf](https://www.gandg.de/download/anleitungen/englisch/JJ-BC_e.pdf) — RS232-Sektion S. 14–15, C1–C6 S. 16
- [G&G EY2015 (EN) — EY2015_english.pdf](https://www.gandg.de/download/anleitungen/englisch/EY2015_english.pdf) — RS232-Sektion S. 17–18, C1–C7 S. 16–17
- [G&G PLC 2018 (DE) — PLC2018_Deutsch.pdf](https://www.gandg.de/download/anleitungen/praezisionswaagen/PLC2018_Deutsch.pdf) — RS232 Kap. 12, Stream-Mode-Definition Kap. 11
- [G&G TJ-Y (DE) — TJ-Y.pdf](https://www.gandg.de/download/anleitungen/zaehlwaage/TJ-Y.pdf) — Bild-PDF, nicht text-extrahierbar
- [G&G Downloads-Übersicht](https://gandg.de/index.php/downloads)
- Vergleichs-Spezifikationen anderer Hersteller (zur Abgrenzung
  vom G&G-Format): [A&D FX-i/FZ-i](https://www.digitalscalesblog.com/interface-description-rs-232-fx-i-fz-i-precision-balances/),
  [A&D GX-A/GF-A Communication Manual](https://weighing.andonline.com/wp-content/uploads/2024/01/Revised-Communication-Manual.pdf),
  [OHAUS RS232](https://www.techadv.com.au/literature/ohaus/userguides/83032107-ohaus-rs232-data-interface-user-guide.pdf)
  — bestätigen, dass `ST,+...` / `US,+...` ein A&D-/OHAUS-Format ist
  und **nicht** Teil der G&G-Spezifikation.
- Eigene Live-Verifikation: `curl http://localhost:8200/scale/weight`
  gegen eine angeschlossene PLC-6000 am `/dev/ttyUSB0` (FTDI-Adapter,
  Nullmodem-Stecker), Backend v0.5.10.
