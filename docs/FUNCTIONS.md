# Waage — Funktionsumfang der App

Stand: Mai 2026 · Version 0.5.x · ergänzend zu
[`HARDWARE.md`](HARDWARE.md) (Hardware/Protokoll) und der
README (Setup). Hier sind alle in der App enthaltenen Funktionen
aufgeführt — wozu sie da sind, wie sie funktionieren, welche
Endpunkte sie nutzen und wo Daten persistiert werden.

---

## Übersicht

```
┌────────────────────────────────────────────────────────────────┐
│  Waage-App                                                     │
├──────────────┬─────────────────────────────────────────────────┤
│              │                                                  │
│  Sidebar     │  Werkzeug-Bereich (eines aus 9 Tools)           │
│              │                                                  │
│  ┌────────┐  │  ┌──────────────────────────────────────────┐  │
│  │ Live-  │  │  │  1. Wiegen          6. Differenz-Wiegen  │  │
│  │ Display│  │  │  2. Behälter wiegen 7. Hilfe & Glossar   │  │
│  │        │  │  │  3. Stückzählung    8. Einstellungen     │  │
│  │ Mess-  │  │  │  4. Toleranz        9. Spende            │  │
│  │ Proto- │  │  │  5. Werte erfassen                       │  │
│  │ koll   │  │  │                                            │  │
│  └────────┘  │  └──────────────────────────────────────────┘  │
│              │                                                  │
└──────────────┴─────────────────────────────────────────────────┘
```

---

## 1. Live-Display (Sidebar)

**Zweck**: aktueller Wägewert immer sichtbar, unabhängig vom gewählten
Werkzeug.

**Anzeige**:
- 7-Segment-artiger Display-Look (JetBrains Mono, Display-Grün)
- Ghost-Ziffern für führende Nullen (volle Stellenzahl gemäß Modell-
  Auflösung)
- Stable/Unstable-Indikator unter dem Wert
- Status-LEDs „BACKEND" und „WAAGE" — orange = Simulator, rot = aus
- Zeitstempel des letzten Frames

**Aktionen**:
- **Klick auf Wert** → in die Zwischenablage kopieren (mit Toast)
- **Auf Null setzen** → `POST /scale/command/tare` (sendet `ESC t`)
- **Maßeinheit** → `POST /scale/command/unit` (sendet `ESC s`)
- **Beleuchtung** → `POST /scale/command/light` (sendet `ESC u`)

**Mobile-Verhalten**: bleibt im Dashboard-Modus sticky am oberen Rand,
während die Karten und das Messprotokoll darunter durchscrollen.
Im Tool-Modus ausgeblendet — die Werkzeug-Panels zeigen den Live-
Wert eh prominent.

**Datenfluss**: WebSocket `/scale/stream` → `liveStore` → reactive
Bindung. Polling-Fallback alle 2 s über `/scale/weight`.

---

## 2. Messprotokoll (Sidebar)

**Zweck**: kompakte Liste aller Wert-Änderungen seit Backend-Start.
Dient als Verlauf, ohne dass der Anwender jeden Wert manuell erfassen
muss.

**Eintragsarten** (`messlog.kind`):
- `start` — erster stabiler Wert nach Backend-Start
- `change` — neuer stabiler Wert ≥ ε vom letzten gestoßen (Default
  `ε = 0,05 g`)
- `tare` — manueller Tara-Marker

**Anzeige (rechtsbündig, monospaced):**
```
22:42:30   Start    → +61,9 g
22:42:41  -61,9 g   → 0,0 g
22:42:56  +2,883 kg → 2,883 kg
```

**Aktionen**:
- **Hover über Zeile** → ×-Symbol einblenden, Klick = nur diesen Eintrag
  löschen (`DELETE /app/messlog/{id}`). Backend-Anker `_last_stored`
  wird beim Löschen sauber zurückgesetzt, damit der nächste Diff
  korrekt bezogen ist.
- **Mülleimer im Header** → Komplett-Leeren (`DELETE /app/messlog`).
  Direkt, ohne Bestätigungsdialog (User-Vorgabe „Löschen ist Löschen").

**Persistenz**: `data/messlog.db` (SQLite). Neueste zuerst sortiert
(`ORDER BY id DESC`).

**Mobile**: `max-height: 35vh`, internes Scrollen — der Live-Display
oben bleibt fix.

---

## 3. Wiegen (Tool 1)

**Zweck**: pures Ablesen.

**Untermodi**:
- **Frei** — Live-Wert sehen, Klick kopiert in die Zwischenablage
- **Sollwert** — man trägt einen Soll-Wert ein und sieht
  - Differenz absolut (z.B. `−12,3 g` rot wenn unter Soll, grün wenn
    über Soll)
  - Anteil in Prozent

**Mindest-Auflage-Warnung**: orange Banner, wenn die aktuelle Auflage
unter der Mindest-Last des Modells liegt (Hersteller-Spezifikation).

**Endpunkte**: keine eigenen — verwendet `/scale/weight` und
`/scale/stream`.

---

## 4. Behälter wiegen (Tool 2)

**Zweck**: Tara-Wiegen. Brutto/Tara/Netto-Anzeige in einer Karte.

**Möglichkeiten**:
- **Aktuelles Gewicht als Tara** → friert das aktuelle Gewicht als
  Tara-Wert ein (`POST /app/netto/tare`).
- **Manuell eintragen** — Tara als Zahl eingeben (`POST` mit
  `weight_g`).
- **Aus Behälter-Bibliothek** wählen — vorgespeicherter Behälter
  setzt das Tara automatisch.
- **Tara entfernen** → `DELETE /app/netto/tare`.

**Endpunkt-State**: `GET /app/netto` liefert
`{ active, tare_g, tare_set_at, container_id }`.

**Persistenz**: nicht persistent — Tara verfällt bei Backend-Neustart.

---

## 5. Stückzählung (Tool 3)

**Zweck**: aus dem aktuellen Gewicht und einem bekannten Stückgewicht
die Anzahl ermitteln.

**Workflow A (kalibrieren)**:
1. Bekannte Anzahl Referenz-Teile auflegen (z.B. 10 Schrauben)
2. „Anzahl Referenz-Teile" eintragen
3. **Kalibrieren** → App berechnet Stückgewicht und zeigt fortan die
   Live-Stückzahl

**Workflow B (Vorlage anwenden)**:
- Karussell zeigt gespeicherte Vorlagen (Schrauben, Tabletten, Münzen,
  Briefe — beim ersten Start geseedet)
- Klick auf Vorlage → Stückgewicht direkt aktiv
- Hover → Edit-/Delete-Symbole einblenden
- Plus-Karte → neue Vorlage anlegen (Name, FA-Icon, Stückgewicht,
  Beschreibung)

**Aktive Kalibrierung speichern als Vorlage**: nach erfolgreicher
Kalibrierung erscheint „Als Vorlage speichern" — Stückgewicht wird
mit Zeitstempel-Hinweis als neue Vorlage gespeichert.

**Endpunkte**:
- `GET /app/count` — aktueller Stückzähl-Status
- `POST /app/count/calibrate` — neue Kalibrierung
- `POST /app/count/reset` — Kalibrierung zurücksetzen
- `GET /app/count/templates` — Vorlagen-Liste
- `POST /app/count/templates` — neue Vorlage
- `PUT /app/count/templates/{id}` — Vorlage bearbeiten
- `DELETE /app/count/templates/{id}` — Vorlage löschen (direkt, kein
  Popup)
- `DELETE /app/count/templates` — alle Vorlagen leeren

**Persistenz**: `data/count_templates.db`.

---

## 6. Toleranz / Qualitätskontrolle (Tool 4)

**Zweck**: Ampel-Anzeige (grün/orange/rot), ob ein Wert innerhalb eines
Soll±Toleranz-Bereichs liegt.

**Eingabe**:
- Sollwert (g)
- Toleranz minus (g)
- Toleranz plus (g)

**Anzeige**:
- Große Ampel-Lampe mit Live-Wert in groß
- Abweichung absolut (`+1,2 g`)
- Status-Text: „INNERHALB TOLERANZ" / „UNTER MINIMUM" / „ÜBER MAXIMUM"
  / „TOLERANZ NICHT AKTIV"
- Farbe der Lampe und Border passt zum Status

**Aktionen**: Aktivieren / Aktualisieren / Deaktivieren.

**Endpunkte**:
- `GET /app/tolerance` — aktueller Status
- `POST /app/tolerance` — setzen
- `DELETE /app/tolerance` — deaktivieren

**Persistenz**: nicht persistent — verfällt bei Backend-Neustart.

---

## 7. Werte erfassen (Tool 5)

**Zweck**: Einzelwerte mit Label, Notiz und Session-Tag in einer
SQLite-Liste sammeln, statistisch auswerten und exportieren.

**Aufzeichnungs-Modi**:
- **Manuell** — Klick auf „Erfassen" speichert den aktuellen Live-Wert
- **Halb-Auto** — Klick wartet auf den nächsten stabilen Wert und
  erfasst dann
- **Voll-Auto** — jeder neue stabile Wert nach einer Unstable-Phase
  landet automatisch in der Liste, ohne Klick

**Statistik (live aktualisiert)**: Anzahl, Min, Max, Mittel, σ, Summe.

**Single-Delete**: jede Zeile mit ×-Symbol, Klick entfernt nur diesen
Eintrag.

**Session leeren**: Mülleimer-Knopf entfernt alle Werte der aktuellen
Session direkt (kein Popup).

**Multi-Format-Export** (Tool-Knopf „Exportieren"):
- **CSV** mit BOM (Excel-kompatibel), Trenner Komma oder Semikolon
- **TSV** Tab-getrennt
- **JSON** Array von Objekten
- **Markdown** Tabelle (für Doku/Issues)

Exporting-Dialog erlaubt Spalten-Auswahl und benutzerdefinierte Header
(z.B. `weight_g=Gewicht (g)`).

**Endpunkte**:
- `GET /app/samples?session=X&limit=N` — Liste
- `POST /app/samples` — neuen Snapshot
- `DELETE /app/samples/{id}` — Single-Delete
- `DELETE /app/samples?session=X` — Session leeren
- `GET /app/samples/stats?session=X` — Statistik
- `GET /app/samples/export?session=X&fmt=csv|tsv|json|md&delim=comma|semicolon&cols=...&labels=...`
- `GET /app/samples/export.csv` — alter Direkt-Download (Backward-
  Kompatibilität)

**Persistenz**: `data/samples.db`.

---

## 8. Differenz-Wiegen (Tool 6)

**Zweck**: mehrere Tara-Schichten stapeln. Brutto bleibt der Live-
Wert, Σ-Tara summiert alle Schichten, Netto = Brutto − Σ.

**Anwendungsfall**: man wiegt einen Beutel mit mehreren Komponenten
nacheinander (z.B. Mehl, Zucker, Salz). Jede Tara-Aktion „friert" die
aktuelle Komponente ein, und das angezeigte Netto entspricht der
nächsten gerade hinzugegebenen Menge.

**Aktionen**:
- **Aktuelles Gewicht als Tara** → fügt Live-Wert als neue Schicht hinzu
- **Manuell eintragen** — Wert direkt als Schicht
- **Aus Behälter-Bibliothek** — vorgespeicherter Behälter wird gestapelt
- **Schicht entfernen** — × neben jeder Zeile
- **Stapel leeren** — direkt, kein Popup

**Endpunkte**:
- `GET /app/differenz`
- `POST /app/differenz/push` — Schicht hinzufügen
- `DELETE /app/differenz/{layer_id}` — einzelne Schicht
- `DELETE /app/differenz` — komplett leeren

**Persistenz**: nicht persistent — verfällt bei Neustart.

---

## 9. Behälter-Bibliothek (in Tools 4 + 8 eingebettet)

**Zweck**: häufig benutzte Tara-Werte einmal anlegen und in NettoPanel
und DifferenzPanel direkt auswählen.

**Felder pro Behälter**: Name, Gewicht (g), Notiz.

**Aktionen**: Anlegen / Bearbeiten / Löschen (direkt, kein Popup) /
Aktuelles Gewicht übernehmen / Komplett leeren.

**Endpunkte**:
- `GET /app/containers` — Liste
- `POST /app/containers`
- `PUT /app/containers/{id}`
- `DELETE /app/containers/{id}`
- `DELETE /app/containers` — komplett leeren

**Persistenz**: `data/containers.db`.

---

## 10. Hilfe & Glossar (Tool 7)

**Zweck**: kontext-sensitive Hilfe zu allen Werkzeugen plus Glossar
und Branchen-Beispielen.

**Hilfe-Inhalt** (in `frontend/src/lib/help.ts`):
- 19 Hilfe-IDs: `overview`, `glossary`, je ein Eintrag pro Tool plus
  `containers`, `history`, `tolerances`, `tare`, `unit`, `light`,
  `copy`, `architecture`, `disclaimer`
- Cross-Links zwischen Hilfen via `[[help:KEY|Label]]` und
  `[[tool:KEY|Label]]`
- Modell-aware Platzhalter (`{{modelName}}`, `{{maxG}}`, …)
- Zwei Sprachen (DE/EN)

**Anzeige**:
- **Desktop**: schwebendes, frei verschiebbares + größenveränderbares
  Fenster pro Hilfe-ID
- **Mobile**: Vollbild-Modal; bei Klick auf Tool-Cross-Link schließt
  sich die Hilfe automatisch und springt ins Werkzeug

**URL-Synchronisierung**: offene Hilfen stehen im Querystring
(`?help=count,glossary`), so sind Deeplinks wie
`/count?help=count` direkt teilbar.

---

## 11. Einstellungen (Tool 8)

**Bereiche**:

### 11.1 Anzeigemodus
Theme-Wahl: Automatisch / Hell / Dunkel. Persistent in
`localStorage` (Schlüssel `waage.theme`).

### 11.2 Aktives Modell
Dropdown mit allen bekannten G&G-Modellen, gruppiert nach Hersteller
und Serie. Modell-Wahl beeinflusst:
- Anzeige-Präzision (0/1/3/4 Nachkommastellen je `resolution_g`)
- Mindest-Auflage-Warnung im Wiege-Tool
- Genauigkeits-Toleranzen-Tabelle (eigene Karte)

**Endpunkte**:
- `GET /scale/models` — Modell-Liste
- `GET /scale/config` — aktives Modell
- `PUT /scale/config` — Modell wechseln (`{ model_id }`)

**Persistenz**: `data/config.json`.

### 11.3 Quelle (Live ↔ Simulator)
Knopf-Paar zwischen echter Hardware (`/dev/ttyUSB0`) und Simulator-
Modus. Simulator-Banner unter der Topbar warnt orange.

**Endpunkt**: `POST /scale/source` mit `{ "mode": "live"|"simulate" }`.

### 11.4 Anschluss (read-only)
Port, Baudrate, Reader-Status, Backend-Version. Werte aus
`/scale/health`.

### 11.5 Alles zurücksetzen
Roter Karten-Block. Klick leert alle persistenten Listen parallel
(samples, messlog, containers, count_templates, differenz, tolerance,
netto, count). **Direkt, ohne Bestätigungsdialog**.

### 11.6 Disclaimer / Lizenz
Kurzfassung mit Link auf `DISCLAIMER.md` und `LICENSE`.

---

## 12. Spende (Tool 9)

**Zweck**: Ko-fi-Knopf plus Krypto-Adressen (BTC, DOGE, ETH) mit QR-
Codes. Inhalts-Stand identisch zu RadioHub.

**Aktionen**:
- Krypto-Karte anklicken → QR-Code und Adresse erscheinen
- Adresse kopieren → Clipboard

**Keine Endpunkte** — reines Frontend-Panel mit hartkodierten Adressen.

---

## 13. Globale Querfunktionen

### 13.1 Sprachumschalter
DE/EN, persistent in `localStorage` (Schlüssel `waage.lang`). Browser-
Sprache wird beim ersten Start auto-erkannt.

### 13.2 Volltextsuche
Lupe in Topbar oder `Cmd/Ctrl+K`. Sucht über Hilfe-Inhalte, Werkzeug-
Namen und Glossar. Tastatur-Navigation ↑/↓/Enter/Esc.

### 13.3 Hilfe-Knopf in jedem Panel
Klick öffnet die kontext-passende Hilfe. URL bleibt im Querystring
synchron, mehrere Hilfen gleichzeitig deeplink-fähig.

### 13.4 Zahlen-Format locale-aware
DE: „1.234,5 g" — EN: „1,234.5 g". Wirkt sowohl auf `formatGrams` als
auch auf das Display.

### 13.5 Toast-Benachrichtigungen
Jede asynchrone Aktion liefert ein kurzes Toast oben (grün = ok,
orange = error). Auto-Dismiss nach 2,5 s.

---

## 14. Routing-Schema

```
/                  Dashboard (Live + Karten)
/<tool>            Tool-Modus
?help=<id1>,<id2>  Hilfe-Stack offen (orthogonal zur Tool-Auswahl)

Beispiele:
/                              Übersicht
/count                         Stückzählung aktiv
/count?help=count,glossary     Stückzählung + zwei Hilfen offen
/?help=disclaimer              Dashboard mit Disclaimer-Hilfe
```

**History-API**, kein Hash. SPA-Fallback in `nginx.conf` und Vite-Dev-
Server konfiguriert — alle nicht-statischen Pfade liefern
`index.html`.

---

## 15. Datenpersistenz im Überblick

| Datei / Ort | Inhalt | Backup-Empfehlung |
|---|---|---|
| `data/samples.db` | Erfassen-Snapshots aller Sessions | **ja** — Mess-Daten |
| `data/messlog.db` | Wert-Änderungs-Verlauf | nein, aufbauend |
| `data/containers.db` | Behälter-Bibliothek | optional |
| `data/count_templates.db` | Stückzähl-Vorlagen | optional |
| `data/config.json` | Aktives Modell | klein, optional |
| `localStorage` (Browser) | Theme, Sprache, Hilfe-Position, gewählter Tool | – |

`data/`-Verzeichnis ist im Container persistent unter `/data` gemountet
(siehe `docker-compose.yml`); im Native-Setup landet es in
`backend/data/`.

---

## 16. Tests

| Bereich | Tests | Tool |
|---|:---:|---|
| Backend (FastAPI + SQLite + Reader) | 188 | pytest |
| Frontend (Format, i18n, StableValue, Search) | 56 | vitest |
| Konsistenz Frontend↔Backend (DELETE-Routen) | 1 | pytest (im backend) |

`npm run check` (svelte-check) sauber mit 0 Errors / 0 Warnings über
211 Files.

---

## 17. Was die App **nicht** kann

Bewusste Auslassungen, weil entweder Hardware-limitiert oder zu
selten:

- **Mehrere Waagen parallel** — Backend erwartet ein Gerät
- **Hardware-Kalibrierung skripten** — `ESC q` ist exponiert nicht
  über Frontend, nur via direktem Python-Skript
- **Auto-Print >1 Hz** — Hardware-Limit, nicht steuerbar
- **Beleuchtungs-Status auslesen** — Hardware kennt keinen Read
- **Filter-Stärke setzen** — nur am Gerät über Setup C-Menü
- **Bluetooth-Adapter** — nur RS232 + USB-Serial
- **Webhook-Notification** bei Schwellwert-Überschreitung — nicht
  geplant
- **Audit-Log mit User-Identität** — Single-User-Setup, keine Auth
