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
│  LF (Zeilenende)            │
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

## 10. Quellen

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
