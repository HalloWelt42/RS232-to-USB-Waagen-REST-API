# Changelog

Alle nennenswerten Änderungen in diesem Projekt.

Versionsschema: [Semantic Versioning](https://semver.org/lang/de/) — MAJOR.MINOR.PATCH.
Datumsformat: ISO 8601 (JJJJ-MM-TT). Quelle der Wahrheit für die aktuelle
Version ist die Datei `VERSION` im Repo-Wurzel — `pyproject.toml` und
`package.json` werden daraus synchronisiert.

## [0.4.5] — 2026-05-07

### Hinweise
- (bitte ergänzen)

## [0.4.4] — 2026-05-07

### Behoben
- **Live-Modus liest die echte Waage zuverlässig** auch dann, wenn
  das Backend mit `WAAGE_SIMULATE=1` gestartet wurde. Bisher blieb
  `state.resolved_port` permanent „simulator" — beim späteren Wechsel
  auf Live öffnete der Reader-Loop den nicht existierenden Port und
  Health zeigte inkonsistent `port:"simulator"` mit `simulated:false`.
- `set_source('live')` löst den Port jetzt neu auf
  (`find_serial_port()` aus `tools.py`) und schreibt ihn in
  `state.resolved_port`. Die Reader-Factory greift bei Live-Modus
  konsequent auf den aktuellen `state.resolved_port` zurück, nicht
  mehr auf den unveränderlichen Boot-Wert.

## [0.4.3] — 2026-05-07

### Geändert
- **Display-Grün auf reines #00ff00** (Hellmodus #008f1a) plus
  subtiler text-shadow für leichten Glow — die Wäge-Anzeige wirkt
  jetzt wie eine echte 7-Segment-LED-Anzeige.
- **Topline der LiveWaage in zwei getrennte Status-LEDs aufgeteilt:**
  „BACKEND" (REST/WS) und „WAAGE" (Hardware-Reader). Die WAAGE-LED
  ist im Simulator-Modus **niemals grün** — stattdessen orange mit
  Label „SIMULATION", auch wenn Werte fließen. So ist auf einen Blick
  klar, ob gerade echte Hardware gemessen wird oder nur simuliert.
- **Minus-Slot im Display ist immer reserviert** — bei positivem Wert
  ghost (10 % Opazität), bei negativem Wert opak. Beim Wechsel
  zwischen + und − springt die Stellen-Position nicht mehr.

### Neu
- `lib/healthStore.svelte.ts` — zentraler Reactive-Store für den
  Backend-Health-Status, mit getrennten Aussagen `backendOk` und
  `scaleOk` (letzteres immer false bei Simulator-Modus).
- i18n `live.*` Schlüssel in DE und EN (BACKEND, WAAGE, SIMULATION,
  WAAGE AUS) — kompakte Großbuchstaben für die Status-Zeile.

### Tests
- 54 Frontend-Tests (Minus-Slot-Logik) und 157 Backend-Tests grün.

## [0.4.2] — 2026-05-07

### Behoben
- **Hilfe-Fenster öffnen sich wieder zuverlässig** — der bisherige
  HelpLayer-Wrapper mit `display: contents` schluckte unter Svelte 5
  die Klick-Events; Hilfe blieb stumm, ohne Fehler. Wrapper entfernt,
  Cross-Link-Klicks per `<svelte:document onclick>` global abgefangen.
  Zusätzlich `{#if entry}`-Guard, falls eine HelpId in der URL
  landet, die in der aktuellen Sprache (noch) keinen Eintrag hat.

### Geändert
- **Messprotokoll rechtsbündig** — bei gemischten Werten
  (+1.969 kg / +38,8 g / −105,8 g) fluchten jetzt Einheiten und
  Dezimaltrenner untereinander, das Ablesen wird ruhiger.
  Tabular-Figures auf Row-Ebene.
- **Display-Anzeige adaptive** — `LiveWaage`, `WiegenPanel`,
  `TolerancePanel` mit `container-type: inline-size`. Schrift skaliert
  per `clamp(…, 13–14cqi, …)` mit der Container-Breite. Damit passt
  jetzt sicher auch ein langer Wert wie „-30.000,0 g" auf eine
  schmale Sidebar (280 px), ohne dass etwas abgeschnitten wird.
- **StableValue ohne min-width-Reservierung** auf den Ziffern —
  JetBrains Mono ist bereits monospaced, die zusätzlichen 0.65em
  pro Glyph fielen für den schmalen Fall ins Gewicht.
- **Simulator-Banner ist komplett klickbarer Knopf** mit Action-Chip
  „Auf Live umschalten" rechts. Direkter Sprung in die Quellen-Karte
  der Einstellungen, beim Hover invertierter Look.

## [0.4.1] — 2026-05-07

### Neu
- **Genauigkeits-Toleranzen pro Modell** — ScaleModel um sechs
  neue Felder erweitert: Mindest-Auflage, Linearität, Wieder-
  holbarkeit, Beruhigungs- und Aufwärmzeit, Betriebstemperatur.
  Werte gepflegt für PLC-6000, JJ-B 220, JJ-BC 224 (andere
  Modelle „nicht im Datenblatt").
- **ModelTolerances-Komponente** im Settings-Tab zeigt alle
  Toleranzen als kompakte Schlüssel/Wert-Tabelle.
- **Live-Mindestlast-Warnung** im WiegenPanel — orange Hinweis,
  wenn die Auflage unter der Mindest-Auflage des Modells liegt.
- **Mono-Schrift JetBrains Mono** ausschließlich für die
  StableValue-Display-Anzeige — pixelgenaue Stellen-Position,
  jede Ziffer gleich breit. Übrige App nutzt weiter Chakra Petch.
- Hilfe-Eintrag „Genauigkeits-Toleranzen" mit acht Blöcken
  (DE+EN) inkl. Cross-Links zu Erfassen und Qualitätskontrolle.

### Geändert
- FontAwesome-Icon `fa-arrow-down-to-bracket` (Pro-only, nicht
  in der Free-Auslieferung enthalten) durch `fa-circle-down`
  ersetzt — sieben Stellen quer durch die Werkzeug-Panels.

## [0.4.0] — 2026-05-07

### Neu
- **Stabile Display-Anzeige mit Ghost-Ziffern:** der Wägewert wird
  im Hauptdisplay (LiveWaage, Wiegen, Toleranz-Lampe) mit fester
  Stellen-Zahl angezeigt — abgeleitet aus dem aktiven Modell.
  Führende Nullen sind Ghost (10 % Opazität), echte Werte voll
  sichtbar. Bei einer 6000g/0,1g-Waage steht immer „0.000,0 g" im
  Display, bei value 12,3 → „0.012,3 g" mit „0.0" als Ghost. Das
  Auge muss zwischen Frames nicht neu fokussieren.
- **Live ↔ Simulator-Umschalter** im Settings-Tab. Backend wechselt
  ohne Neustart; ein orangefarbenes Warn-Banner unter der Topbar
  weist auf aktive Simulation hin.
- **Auto-Erfassen-Modi** im SamplesPanel — Manuell (Default),
  Halb-Auto (Klick wartet auf nächsten Stable und erfasst dann),
  Voll-Auto (jeder neue Stable-Wert nach einer Unstable-Phase
  landet automatisch in der Liste, ohne Klick).
- **Locale-Number-Format:** DE „1.234,5", EN „1,234.5" — wirkt
  sowohl auf `formatGrams` als auch auf die Display-Anzeige.
- **i18n-Erweiterung dokumentiert** in `locales/README.md` mit
  Schritt-für-Schritt-Anleitung für neue Sprachen.

### Geändert
- **Messprotokoll tabellarisch** mit drei festen Spalten und
  links-bündigen Werten. Mehr Abstand zwischen den Spalten und
  Padding zum Scrollbalken.
- **Scrollbar global überarbeitet** — Daumen/Track mit transparentem
  Border (8 px breit, sichtbarer 4 px), so klebt der Inhalt nicht
  am Rand.

### Tests
- Backend: 4 neue Cases für `/scale/source` — 157 Tests gesamt grün.
- Frontend: 14 neue Cases für `buildStableSegments` und
  Locale-aware `formatGrams` — 54 Tests gesamt grün.

## [0.3.4] — 2026-05-07

### Neu
- **Stückzähl-Vorlagen voll verwaltbar:** Anlegen, Bearbeiten,
  Löschen — wer regelmäßig dieselben Teile zählt (Schrauben-Sorten,
  Tabletten-Chargen, Münzsortimente), hält Name, Icon, Stückgewicht
  und Beschreibung als Vorlage fest.
- **„Als Vorlage speichern"** nach Kalibrierung — das exakte
  Stückgewicht aus der aktuellen Kalibrierung landet direkt mit
  Zeitstempel-Hinweis in der Vorlagen-Liste.
- REST-Endpoints unter `/app/count/templates` mit CRUD,
  SQLite-persistent, alphabetisch sortiert. Beim ersten Aufruf
  werden vier Default-Vorlagen geseedet (Schrauben, Tabletten,
  Münzen, Briefe) — sind aber sofort frei änder- oder löschbar.

### Geändert
- CountPanel komplett neu — Vorlagen-Karussell aus dem Server-Store
  statt hardcoded. Hover auf einer Vorlage blendet Edit/Delete
  ein, Plus-Karte am Ende öffnet das Anlege-Form mit FA-Icon-
  Auswahl.
- Hilfe-Eintrag „Stückzählung" um die Vorlagen-Verwaltung
  erweitert (DE+EN).

### Entfernt
- `lib/countTemplates.ts` (hardcoded Defaults) — Logik ist jetzt
  serverseitig im CountTemplateStore.

### Tests
- Backend: 15 neue Cases (8 Store + 7 REST) — 153 Tests gesamt grün.
- Frontend weiterhin 40 Tests grün.

## [0.3.3] — 2026-05-07

### Neu
- **Behälter-Bibliothek:** häufig benutzte Gefäße einmal anlegen
  und beim Wiegen aus einer Liste wählen — Default „Kein Behälter
  (0 g)". REST-Endpoints unter `/app/containers` mit CRUD,
  SQLite-persistent, alphabetisch sortiert. Eingebaut als
  ContainerPicker in NettoPanel (setzt Software-Tara) und
  DifferenzPanel (stapelt direkt als neue Schicht).
- Toast-Bestätigung beim „Aktuellen Wert übernehmen"-Klick in
  WiegenPanel und TolerancePanel.

### Geändert
- **Zahleneingabe-Felder rechtsbündig** in der gesamten App
  (`inputmode=decimal/numeric/number`) — passend zur üblichen
  Konvention für Mess- und Zahlenwerte.
- **Toleranz-Form** kompakter: drei-Spalten-Layout mit Sollwert
  breiter, Tol-/Tol+ schmaler; keine überquellenden Zahlenfelder.
- **Mobile + Tool-Modus:** Sidebar (LiveWaage + MessLog)
  ausgeblendet, weil die Werkzeug-Panels den Live-Wert eh
  prominent zeigen — keine doppelte Wert-Anzeige mehr.
- App-Body mit zusätzlichem padding-top für saubere Abgrenzung
  zur Topbar.

### Tests
- Backend: 15 neue Cases (8 ContainerStore + 7 REST-Endpoints) —
  138 Tests gesamt grün.
- Frontend weiterhin 40 Tests grün.

## [0.3.2] — 2026-05-07

### Geändert
- **Industrial-Look eckiger:** `--radius` von 10 px auf 0 px,
  Buttons leicht gerundet (`--radius-sm` 4 px), spezielle Anzeigen
  wie Live-Display und Toleranz-Lampe behalten 6 px (`--radius-soft`).
  Mehr Luft zwischen Topbar und Body — der Fokus-Ring der TabBar
  rutscht nicht mehr in den Header-Bereich.
- **Modell-bewusst:** alle Texte und Anzeige-Präzisionen folgen
  jetzt dem aktiven Waagen-Modell. `formatGrams` zeigt 0 / 1 / 3 / 4
  Nachkommastellen je nach `resolution_g`. Topbar zeigt das aktive
  Modell als Klick zu Einstellungen statt hardcoded „G&G PLC 6000g".
- **Hilfe-Texte modell-neutral** mit Platzhaltern `{{modelName}}`,
  `{{maxG}}`, `{{resolutionG}}`, `{{minPiecesUnder1g}}`. Englische
  und deutsche Variante komplett synchronisiert.

### Neu
- `lib/modelStore.svelte.ts` — reaktiver Speicher für das aktive
  Modell, lädt `/scale/config` beim Start, App-Root setzt darüber
  die Default-Auflösung der Format-Funktionen.
- **Hilfe-Cross-Links** als `[[tool:KEY|Label]]` und
  `[[help:KEY|Label]]`. HelpLayer rendert sie zu Buttons mit
  `data-route-*` Attributen und navigiert via `route.go()` /
  `route.openHelp()` — kein Page-Reload, sauberes PWA-Verhalten.
- TabBar mit Akzent-Strich am unteren Rand statt umlaufender Box;
  Fokus-Ring nun innerhalb der Klick-Fläche.

### Tests
- 18 neue Cases (decimalsForResolution, modell-aware formatGrams,
  buildHelpVars, renderHelpBody Platzhalter und Cross-Links) — 40
  Tests gesamt grün.

## [0.3.1] — 2026-05-07

### Geändert
- **Routing ohne Raute:** History-API statt `#/...`. Pfade jetzt
  `/`, `/<tool>` mit optionalem `?help=<id1>,<id2>`. Deeplinks aus
  Mails/Chats funktionieren — `/count?help=count` öffnet Stückzählung
  und das Hilfe-Fenster gleichzeitig.
- **Sidebar permanent links:** LiveWaage und Messprotokoll sind im
  Desktop dauerhaft sichtbar — auch während ein Werkzeug aktiv ist.
  Mobile zeigt sie weiter als kompakten Header oben.
- **Lizenz präzisiert:** Texte in App und Mockup auf
  `CC BY-NC-ND 4.0 + Zusatzbestimmungen (private Nutzung)` korrigiert
  (war fälschlich „MIT — Private Nutzung"); LICENSE-Datei ergänzt.

### Neu
- Sprachflagge im Header — DE/EN umschaltbar, persistent in
  localStorage; Browser-Sprache wird beim ersten Start auto-erkannt.
  Englische Locale komplett mit allen Schlüsseln.
- Globale Volltextsuche über Hilfe-Inhalte, Werkzeug-Namen und
  Glossar-Begriffe. Lupe in Topbar plus `Cmd/Ctrl+K`.
  Tastatur-Navigation ↑/↓/Enter/Esc.
- Hilfe-Fenster werden beim Öffnen, beim Speichern und bei
  Viewport-Änderungen automatisch in den sichtbaren Bereich
  geclamped — nichts verschwindet mehr hinter dem Rand.
- Hilfe-Stack als URL-Querystring `?help=...` mit Komma-Trennung —
  mehrere Hilfen gleichzeitig deeplink-fähig.
- `DISCLAIMER.md` im Repo-Wurzel mit rechtssicherem Standard-Text
  (deutsch + englisch): keine Gewähr, keine Haftung, nicht eichfähig.
- Disclaimer-Karte im Settings-Tab und eigener Hilfe-Eintrag.
- WebSocket über `/api/scale/stream` — nginx-Config mit
  `Connection`-Map für sauberen Upgrade-Header.

### Entfernt
- `Dashboard.svelte` ersetzt durch `Sidebar.svelte` + `CardGrid.svelte`.

## [0.3.0] — 2026-05-07

### Geändert (Breaking)
- API komplett neu organisiert: reine Waagen-Funktionen unter `/scale/*`,
  UI-Komfort-Features unter `/app/*`. Drittsysteme können das Scale-Modul
  jetzt eigenständig ansprechen, ohne UI-Erweiterungen mitzunehmen.
- Endpoint-Mapping: `/weight` -> `/scale/weight`, `/health` -> `/scale/health`,
  `/stream` -> `/scale/stream`, `/command/*` -> `/scale/command/*`,
  `/tolerance` -> `/app/tolerance`, `/netto` -> `/app/netto`,
  `/count` -> `/app/count`, `/samples` -> `/app/samples`.

### Neu
- Industrial-Design mit Petrol-Akzentfarbe und Anthrazit-Hintergrund
- Schriften lokal: Barlow für UI, Chakra Petch Bold für Zahlen (Tabular)
- FontAwesome Free Solid + Regular als einzige Icon-Quelle
- Dashboard mit Karten-Auswahl als Eingangsansicht
- Tool-Modus: Karten werden zu Tab-Bar, Werkzeug öffnet sich
- Messprotokoll mit Diff-Liste (Server speichert, Frontend live-eigenes)
- Differenz-Wiegen mit Mehrfach-Tara-Stack (server-seitig)
- Wiegen-Modus mit Untermodi (frei + Sollwert-Hinweis)
- Settings-Tab: Modell-Auswahl (PLC, JJ, EY, TJ-Y …), Theme, Anschluss,
  Polling-Intervall, Lizenz
- Spende-Karte mit Ko-fi-Link und Krypto-Adressen
- Hilfe-Texte mind. 18 px, Zahlen fett und in Akzentfarbe hervorgehoben
- Hilfe-Fenster im Desktop frei verschiebbar UND in der Größe änderbar
- Info-Knopf in industriellem Blau, gefülltes circle-info-Symbol
- Header-Knöpfe alle einheitlich 40 px hoch
- Tasten-Beschriftungen klar deutsch („Auf Null setzen", „Maßeinheit",
  „Beleuchtung"), Hover-Tooltip zeigt Original und RS232-Befehl
- i18n-Vorbereitung: zentrale lib/locales/de.ts, später erweiterbar
- Entwickler-Kontakt im Footer als SVG-Grafik (Spam-Schutz)

## [0.2.0] — 2026-05-07

### Neu
- Mobile-First-Layout mit Bottom-Tab-Bar auf kleinen Bildschirmen
- Touch-taugliche Buttons (mindestens 44 × 44 Pixel)
- Klick auf Wägewert kopiert in die Zwischenablage
- "Wert übernehmen"-Aktion: aktueller Wägewert in Eingabefelder von
  Toleranz-, Netto- und Zähl-Panel
- Erweitertes Hilfe-System mit Glossar und Anwendungsbeispielen aus
  Apotheke, Bäckerei, Werkstatt, Versand und Schmuckbranche
- Zentrale Versionierung über `VERSION`-Datei und Bump-Skript
- Helles und dunkles Theme mit Auto-Modus
- Goldener Schnitt im Layout, Tabular Figures auf allen Zahlen
- Frei verschiebbare Hilfe-Fenster pro Bereich

## [0.1.0] — 2026-05-05

### Neu
- Backend in FastAPI mit REST und WebSocket
- Frontend in Svelte 5 + Vite + nginx
- Reader, Parser, Logger, Simulator, Sample-Store
- QC-Toleranz mit Ampel-Anzeige
- Software-Tara mit Brutto/Netto-Anzeige
- Stückzählung mit Gewichts-Kalibrierung
- Werte-Erfassung mit Sessions und CSV-Export
- Auto-Erkennung des seriellen Ports (Linux, Pi, macOS)
- Polling-Modus für G&G-Waagen (ESC p, 0,5 Hz)
- Docker-Compose-Setup mit Backend und Frontend
