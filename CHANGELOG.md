# Changelog

Alle nennenswerten Änderungen in diesem Projekt.

Versionsschema: [Semantic Versioning](https://semver.org/lang/de/) — MAJOR.MINOR.PATCH.
Datumsformat: ISO 8601 (JJJJ-MM-TT). Quelle der Wahrheit für die aktuelle
Version ist die Datei `VERSION` im Repo-Wurzel — `pyproject.toml` und
`package.json` werden daraus synchronisiert.

## [0.4.1] — 2026-05-07

### Hinweise
- (bitte ergänzen)

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
