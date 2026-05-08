# Changelog

Alle nennenswerten Änderungen in diesem Projekt.

Versionsschema: [Semantic Versioning](https://semver.org/lang/de/) — MAJOR.MINOR.PATCH.
Datumsformat: ISO 8601 (JJJJ-MM-TT). Quelle der Wahrheit für die aktuelle
Version ist die Datei `VERSION` im Repo-Wurzel — `pyproject.toml` und
`package.json` werden daraus synchronisiert.

## [0.5.16] — 2026-05-08

### Hinweise
- (bitte ergänzen)

## [0.5.15] — 2026-05-08

### Neu (UX)
- **IconPicker statt FontAwesome-Texteingabe** — beim Anlegen einer
  Stückzähl-Vorlage musste der Anwender die FA-Klasse als String
  tippen (z.B. `fa-solid fa-cube`). Wer FontAwesome nicht kennt,
  kam nicht weiter; selbst Kenner wissen die Glyph-Namen nicht
  auswendig. Jetzt:
  - Visueller Picker mit Suchfeld (substring-Match auf Klasse,
    Label und Keywords) und Klick-Auswahl in einem Icon-Grid.
  - Aktuell gewähltes Icon als visuelles Echo neben dem Suchfeld.
  - „Erweitert"-Bereich (eingeklappt) mit Texteingabe-Fallback —
    nur falls das gewünschte Icon nicht in der kuratierten Liste
    ist.
- Kuratierte Icon-Liste in `frontend/src/lib/icons.ts` mit ~80
  passenden FA-Free-Solid-Icons aus den Bereichen Werkstatt,
  Apotheke, Münzen, Versand, Lebensmittel, Schmuck, Garten,
  Industrie, Office, Standard-Formen — jedes mit DE/EN-Keywords
  für die Suche.
- Neue Komponente `IconPicker.svelte` ist allgemein einsetzbar
  und kann später auch im ContainerPicker verwendet werden.

### i18n
- Neuer `iconPicker.*`-Block (DE + EN): searchPlaceholder,
  noResults, advanced, advancedHint, apply.

## [0.5.14] — 2026-05-08

### Geändert (Status-Indikatoren konsolidiert)
- **Footer zeigt BACKEND- und WAAGE-LEDs zentral** — vorher saß
  unten links nur ein einsamer „Live"-Dot mit dem reinen WS-Status,
  der nichts über die Hardware aussagte; gleichzeitig hatte die
  LiveWaage-Karte eine Topline mit denselben zwei LEDs. Jetzt:
  - Footer zeigt links zwei LEDs (BACKEND = WS-Verbindung,
    WAAGE = Hardware live/SIMULATION/AUS) plus rechts die
    Live-Backend-Version.
  - Reader/Port/Baud/Uptime werden auf Mobile ausgeblendet
    (`only-desktop`-Klasse), der Footer ist auf Mobile dadurch
    SICHTBAR (war bisher komplett `display:none`) — Anwender hat
    den Hardware-Status auch im Hochformat im Blick.
- **LiveWaage zeigt nur noch den Wert** — die Topline mit
  BACKEND/WAAGE/Timestamp ist raus. Card beginnt direkt mit dem
  Display, darunter die drei Hardware-Aktions-Knöpfe. Saubere,
  fokussierte Anzeige.
- Damit: ein einziger Ort für den Verbindungsstatus, kein
  doppelter Aufwand mehr beim Hinschauen.

### Entfernt
- **`mockups/`-Verzeichnis komplett gelöscht.** Wurde wiederholt
  als „uralter Versionfehler v0.3.0" gemeldet, der Banner-Workaround
  hatte die Verwirrung nicht beendet. Datei war nicht Teil des
  aktiven App-Builds; der archivierte Stand bleibt über die Git-
  History abrufbar (`git show 9bf8983:mockups/index.html`).
  Frontend-Source enthält damit kein hardcoded „v0.3.0" mehr.

## [0.5.13] — 2026-05-08

### Behoben (Reaktivität nach Disconnect)
- **Display reagiert sofort auf USB-Disconnect** — bisher klebte
  die LiveWaage am letzten WebSocket-Frame, der Anwender sah weiter
  „61,9 g STABIL" obwohl die Hardware schon abgezogen war; erst
  ein Page-Reload räumte das auf. Jetzt:
  - LiveWaage zeigt bei `scaleState='offline'` explizit „WAAGE AUS"
    im Status-Slot, der Wert wird auf null gesetzt, der Display-
    Klick (Wert kopieren) ist deaktiviert.
  - App.svelte hat einen `$effect`, der `live.set(null)` aufruft,
    sobald `healthStore.scaleOk` auf false fällt. Damit ziehen
    alle Werkzeug-Panels (Wiegen/Netto/Toleranz/Differenz/Count)
    zentral auf den neutralen Zustand — kein stale „61,9 g" mehr,
    nirgends.

### Behoben (Versions-Anzeige)
- **Footer-Version dynamisch aus Backend** — vorher zeigte der
  Footer `v{__APP_VERSION__}`, eine Vite-Build-Zeit-Konstante.
  Nach jedem `bump.sh` blieb die UI auf der alten Version, bis
  jemand das Frontend neu baute — effektiv war das ein hardcoded
  Wert aus dem letzten Build. Jetzt:
  `v{health?.version ?? __APP_VERSION__}` — primär die Live-
  Version aus `/scale/health` (= zentrale VERSION-Datei via
  Backend-Loader), Fallback auf den Build-Wert nur, falls das
  Backend gerade nicht erreichbar ist.

### Geändert (Reaktivität der Live-Anzeige)
- **Polling-Intervall von 2 Hz auf 5 Hz reduziert** — Werte
  zeigten sich „träge", weil der Reader nur alle 0,5 s ein
  `ESC p` an die Waage schickte. Außerdem wurde das in
  `state.poll_interval_s` konfigurierte Intervall **nie an
  `Waage()` durchgereicht** — das Feld war ein totes Konstrukt.
  Beides gefixt:
  - `DEFAULT_POLL_INTERVAL` von `0.5` auf `0.2` (5 Hz).
  - `state.poll_interval_s` aus Env `WAAGE_POLL_INTERVAL_S`
    (Default `0.2`).
  - `_make_reader_factory` reicht das Intervall jetzt explizit
    an den `Waage`-Konstruktor durch.
- 5 Hz ist deutlich agiler bei der Wert-Verfolgung; G&G-Manuale
  geben theoretisch ~50 Hz (9600 8N1) an, praktisch limitiert die
  interne Filterzeit auf 5–10 Hz — wir bleiben bequem im sicheren
  Bereich. Per `WAAGE_POLL_INTERVAL_S` lässt sich das jederzeit
  anpassen.

## [0.5.12] — 2026-05-08

### Behoben (schwerwiegend, Hardware-Diagnose)
- **Backend erkennt USB-Disconnect der Waage** — bei einem
  abgezogenen USB-Serial-Adapter blieb `reader_alive=true` stoisch
  haften, weil pyserials `read()` nicht mit Exception fehlschlug,
  sondern still leere Frames lieferte. `last_seen` blieb auf dem
  letzten echten Frame stehen, das Frontend zeigte die WAAGE-LED
  weiter grün. Live-Test mit abgezogenem Adapter bestätigte das
  Problem (Backend zeigte „alive" trotz fehlender Hardware).

### Neu
- `AppState.scale_alive` und `AppState.stale_for_s` als Properties.
  `scale_alive` ist nur True, wenn der Reader-Task läuft UND in den
  letzten `WAAGE_SCALE_STALE_AFTER_S` Sekunden (Default 5 s) ein
  Frame angekommen ist.
- `GET /scale/health` liefert beide Felder zusätzlich aus —
  `scale_alive: bool`, `stale_for_s: float | null`. Das ältere `ok`-
  Feld bleibt backward-kompatibel (Reader-Task läuft + min. ein Frame).
- Frontend `healthStore.scaleOk` zieht jetzt `scale_alive` an erster
  Stelle (mit Fallback auf `reader_alive` für ältere Backends). Die
  WAAGE-LED in der LiveWaage zeigt damit zuverlässig rot, wenn die
  Hardware weg ist.
- Reader-Loop-Stale-Trigger: prüft alle 2 s, ob `stale_for_s` über
  dem doppelten Schwellwert liegt ODER ein frisch geöffneter Reader
  nach 10 s noch keinen Frame bekommen hat. In beiden Fällen wirft
  der Loop selbst einen `RuntimeError`, was den existierenden
  Reconnect-Pfad mit exponentiellem Backoff anstößt — bei Wieder-
  einstecken des Adapters greift `reader_factory()` automatisch.

### Konfiguration
- Neue Env-Variable `WAAGE_SCALE_STALE_AFTER_S` (Default `5`).

### Tests
- `test_health_reports_scale_alive_and_stale_for_s` — Smoke-Test
  der HTTP-Schale, Felder vorhanden + korrekte Typen.
- `test_health_marks_stale_after_threshold` — Unit-Test gegen
  AppState mit kontrolliertem `last_seen`. 188 Tests grün.

### Doku
- `docs/HARDWARE.md` Abschnitt 12.0 neu — beschreibt Problem,
  Lösung und Konfigurations-Stellschraube.

### Live-Verifikation
- Mit abgezogenem USB-Adapter: `scale_alive: false`,
  `stale_for_s: null`, Backend-Log zeigt
  `RuntimeError: Hardware liefert seit dem Öffnen keine Frames (10s)
  — Reconnect-Versuch.` ✓

## [0.5.11] — 2026-05-08

### Doku
- **`docs/HARDWARE.md`** auf ~640 Zeilen erweitert — Anschlussplan
  (ASCII-Schema Waage→Nullmodem→FTDI→Pi), Hardware-Stückliste mit
  Empfehlungen und Erfahrungswerten, Protokoll-Interpretation für
  jeden Hardware-Mangel mit konkretem Lösungsansatz (Stable-Heuristik,
  Tara-Workaround, OL-Erkennung, ESC q skripten, Mehrgerät-Bus),
  Foren-Recherche-Resultat (keine Hobbyist-Lore zu G&G-Internas;
  OEM-Identität: Bonvoisin/U.S. Solid/Steinberg/HoChoice
  baugleich, Kern/Sartorius/A&D nicht).
- **`docs/FUNCTIONS.md`** neu — vollständige Funktions-Referenz
  aller App-Tools: Live-Display, Messprotokoll, 9 Tools (Wiegen,
  Behälter wiegen, Stückzählung, Toleranz, Werte erfassen,
  Differenz-Wiegen, Hilfe & Glossar, Einstellungen, Spende),
  Behälter-Bibliothek, Querfunktionen (Sprache, Suche, Hilfe-Knopf,
  Zahlen-Format, Toasts), Routing-Schema, Datenpersistenz-Übersicht,
  bewusste Auslassungen mit Begründung. ~480 Zeilen.

### Behoben
- **Mockup-Datei klar als Archiv markiert** — `mockups/index.html`
  zeigt v0.3.0-Footer aus dem v0.3-Iteration-Snapshot, was
  als „uralter Versionfehler" gemeldet wurde. Datei ist nicht
  Teil des aktiven App-Builds; jetzt prominenter roter Banner
  oben mit Hinweis „HISTORISCHER SNAPSHOT" und neue
  `mockups/README.md` erklärt den dokumentarischen Zweck.

## [0.5.10] — 2026-05-08

### Behoben
- **Messprotokoll-Reihenfolge: neuester Eintrag wieder oben** —
  Backend liefert die Liste seit jeher mit `ORDER BY id DESC`
  (neueste zuerst); `MessLog.svelte` hat sie danach mit
  `[...entries].reverse()` doppelt gedreht und damit den ältesten
  Eintrag nach oben gesetzt. Im laufenden Betrieb sah man die
  Werte rückwärts — die jüngste Änderung verschwand am unteren
  Listenrand statt oben aufzutauchen.
- Fix: das `.reverse()` ist weg, `let recent = $derived(entries)`
  reicht die Backend-Liste 1:1 an die Tabelle weiter. Der
  irreführende Kommentar daneben („Server liefert auch so") ist
  ersetzt durch eine klare Begründung.

### Tests
- Zwei neue Regressions-Tests, damit die Reihenfolge nicht wieder
  stillschweigend kippt:
  - `tests/test_messlog.py::test_list_returns_newest_first` —
    prüft auf Store-Ebene streng monoton fallende IDs und Werte.
  - `tests/test_app_api.py::test_messlog_http_preserves_store_ordering` —
    verifiziert, dass die HTTP-Schale `/app/messlog` die Reihenfolge
    unverändert weiterreicht.

## [0.5.9] — 2026-05-08

### Tests (Lücken aus 0.5.0–0.5.7 geschlossen)
- **11 neue Backend-Cases** in `tests/test_app_api.py`:
  - `DELETE /app/messlog/{id}` mit existierender ID + 404-Fall.
  - `DELETE /app/samples/{id}` 404-Fall.
  - `DELETE /app/differenz/{id}` 404-Fall.
  - `GET /app/samples/export?fmt={csv,tsv,json,md}` jeweils einzeln.
  - `GET /app/samples/export?fmt=xml` → 422 (Validation).
- **Konsistenz-Test Frontend ↔ Backend**: parst
  `frontend/src/lib/api.ts` und prüft, dass jeder dort genutzte
  DELETE-Pfad eine passende Route in der Backend-OpenAPI hat.
  Fängt genau das Symptom „Löschen führt zu 404" ab, das auftritt,
  wenn das laufende Backend hinter der Frontend-Version zurückbleibt
  und neuere Endpunkte (z.B. Single-Delete im Messprotokoll, Multi-
  Format-Export) noch nicht kennt.

### Hintergrund
Im Live-Betrieb wurde 404 beim Löschen einzelner Messprotokoll-
Einträge beobachtet. Ursache: das laufende Backend steckte auf
v0.4.5 fest (Symptom des in 0.5.6 gefixten egg-info-Bugs), während
das Frontend seit 0.5.0 die neuen Routen aufrief. Die Test-Suite
konnte das nicht fangen, weil es weder Cases für die Single-Delete-
Routes noch einen Konsistenz-Check gegen die Frontend-API gab.
Backend-Tests insgesamt: 175 → 186, alle grün.

### Hinweis für Anwender
Damit der Fix im Live-Betrieb ankommt, muss der laufende Backend-
Prozess einmal neu gestartet werden — der seit 0.5.6 korrigierte
Versions-Loader liest die zentrale VERSION-Datei sonst nicht neu
aus dem Repo-Tree.

## [0.5.8] — 2026-05-08

### Revertiert
- **Die HTML-Struktur-„Fixes" aus 0.5.7 sind zurückgenommen.** Die
  zugrundeliegenden IDE-Meldungen („Element div is not allowed here")
  stammten aus einem veralteten/defekten Svelte-4-Plugin und sind
  in der offiziellen Svelte-5-Doku (`svelte.dev/llms.txt` und
  Folgedokumente) nicht als Fehler markiert; `svelte-check 4.x`
  meldet das Projekt mit 0/0 ohnehin sauber. Der laufende Betrieb
  war zu jeder Zeit fehlerfrei.
- Konkret zurückgenommen:
  - `<h3>`/`<p>` in `<button>` (ActionCard, HelpPanel) — wieder
    Original-Markup mit semantischer Heading-/Paragraph-Auszeichnung.
  - `<div class="row-flex">`/`<div class="row">` in `<label>` in
    NettoPanel, TolerancePanel, CountPanel, DifferenzPanel,
    WiegenPanel und ContainerPicker — wieder als `<div>`-Wrapper.
- Die übrigen Fixes seit 0.5.6 (Backend-Version-Loader, i18n-Lücken,
  Modell-Anzeigename) bleiben unverändert in Kraft.

## [0.5.7] — 2026-05-08

### Behoben (HTML-Spec-Konformität)
- **Kein Flow-Content mehr in `<button>` und `<label>`** — IDE-LSP
  meldete „Element div is not allowed here", `npm run check`
  (svelte-check 4.x) lief sauber durch, fing diese Verstöße aber
  nicht. Per Skript-Audit über alle 211 Svelte-Files **11 echte
  Stellen** gefunden und gefixt:
  - `<h3>`/`<p>` direkt in `<button>` in `ActionCard.svelte` und
    `panels/HelpPanel.svelte` — durch `<span class="title|desc|preview">`
    mit `display: block` ersetzt.
  - `<div class="row-flex">`/`<div class="row">` als Layout-Wrapper
    direkt in `<label>` in ContainerPicker, NettoPanel,
    TolerancePanel, CountPanel (zwei Stellen), DifferenzPanel und
    WiegenPanel — durch `<span>` ersetzt; CSS hat schon `display: flex`
    auf den Klassen.
- Subtile Browser-Bugs damit weg: bei Flow-Content im `<button>`
  schließt der Parser den Button vorzeitig (kaputte Tab-Navigation,
  Hit-Testing-Probleme); bei `<div>` im `<label>` ging die
  Klick-auf-Label-fokussiert-Input-Funktion verloren.
- Audit-Skript läuft jetzt auf 0 Verstöße über alle Svelte-Files.

### Klargestellt (kein Code-Bug)
Folgende IDE-LSP-Meldungen sind keine echten Fehler — `npm run check`
stützt das mit 0 Errors / 0 Warnings:
- „Unrecognized option 'runes'" — in Svelte 5 Sprachstandard, die
  `compilerOptions.runes: true` ist optional gültig.
- „Cannot find name '$state' / '$derived'" — Runes sind ambient
  globals (Quelle: `node_modules/svelte/types/index.d.ts`); LSP-
  Cache-Problem, Reload des Sprachservers genügt.
- „onclick does not exist" — Svelte 5 schreibt `onclick={...}`
  offiziell als Property statt `on:click`.
- Spell-/Grammatik-Hinweise (typo, Anführungszeichen-Paare,
  Komma-Empfehlungen) — Tooling-spezifisch.

## [0.5.6] — 2026-05-07

### Behoben (schwerwiegend)
- **Backend-Version stimmt jetzt zentral** — die Anzeige in
  `/scale/health` und damit in der Settings-Karte „Anschluss"
  zeigte dauerhaft eine alte Version (z.B. 0.4.5), während die
  zentrale `VERSION`-Datei längst auf 0.5.x gebumpt war.
- Ursache: `_load_version()` befragte zuerst
  `importlib.metadata.version("waage")`. setuptools schreibt diese
  bei `pip install -e .` einmalig in die egg-info; spätere
  `bump.sh`-Aufrufe aktualisieren `VERSION` synchron mit
  `backend/VERSION` und `package.json`, lassen die egg-info aber
  unangetastet — das Backend lebte mit der Build-Zeit-Version weiter.
- Reihenfolge in `_load_version()` umgedreht: VERSION-Datei (Repo-
  Tree, walk-up vom Modul-Pfad aus gesucht) hat jetzt Vorrang;
  `importlib.metadata` greift nur noch in fertig gepackten Wheels
  ohne Repo-Kontext.
- Zwei neue Backend-Tests (`tests/test_version_loader.py`):
  geladene `__version__` muss mit der VERSION-Datei übereinstimmen,
  und das Format muss SemVer-artig sein.
- 175 Backend-Tests grün.

## [0.5.5] — 2026-05-07

### Behoben (i18n)
- **Letzte hardcoded Strings übersetzt** — drei Toast-Texte in der
  LiveWaage („Tara gesetzt" / „Einheit gewechselt" / „Beleuchtung
  umgeschaltet") waren noch fix in Deutsch hinterlegt; ebenso der
  Display-Tooltip „Wert in die Zwischenablage kopieren", der
  Schließen-Knopf am Hilfe-Fenster und der Email-Knopf im
  ContactStrip. Alle laufen jetzt über neue `commands.*`-Keys
  (tareDone / unitDone / lightDone / copyValueTitle / copyValueAria
  / closeWindow / closeHelpWindow / contactMailTitle /
  contactMailAria), DE und EN parallel gepflegt.

### Behoben
- **Modell-Anzeigename ohne Doppel-Prefix** — bei Modellen, deren
  Name selbst schon den Serien-Prefix trägt (z.B. series=„PLC",
  name=„PLC-6000"), erschien das aktive Modell als „G&G PLC-PLC-6000".
  `displayName` in modelStore prüft jetzt `name.split(' ')[0]` auf
  den Serien-Prefix und setzt ihn nicht erneut voran.

## [0.5.4] — 2026-05-07

### Geändert
- **Native Bestätigungs-Popups durchgängig entfernt** — Anwender-
  Vorgabe „Löschen ist Löschen, niemals native Popups". Sieben
  Stellen waren betroffen: Messprotokoll-Komplett-Leeren, Tara-
  Stapel leeren, Session leeren, „Alles zurücksetzen" (war doppelt
  bestätigt), Stückzähl-Vorlage löschen, Behälter aus Bibliothek
  löschen, Differenz-Stapel leeren. Alle Aktionen sind jetzt direkt
  und mit Toast-Bestätigung; rückbaufähige Daten lassen sich
  zügig wieder erfassen, das spart Klicks im Werkstatt-Workflow.

### Behoben (i18n)
- **Durchgängige Übersetzungen in allen Tool-Panels** — über die
  Zeit waren in NettoPanel, DifferenzPanel, WiegenPanel,
  TolerancePanel, SamplesPanel, SettingsPanel und ContainerPicker
  zahlreiche Beschriftungen, Platzhalter, Toasts und Status-Strings
  hardcoded auf Deutsch durchgerutscht. Englische UI sah dann den
  englischen Tool-Header („Differential weighing", „Capture
  values") über deutschen Tabellen-Inhalten („BRUTTO/Σ TARA/NETTO").
- Neue Schlüssel-Blöcke `panels.*` (geteilte Tool-Strings:
  Brutto/Tara/Netto, Modi, Toleranz-Status, Sample-Statistik,
  Buttons/Toasts) und `settingsPanel.*` (Anzeigemodus, Aktives
  Modell, Quelle, Anschluss, Lizenz-Stichpunkte) — DE und EN
  parallel gepflegt.

### Behoben (Mobile-UI)
- **Hilfe-Vollbild schließt sich beim Tool-Sprung** — beim Klick
  auf einen `[[tool:...]]`-Cross-Link in der Hilfe blieb das
  Vollbild-Modal sonst über dem Werkzeug liegen. HelpLayer prüft
  jetzt `matchMedia('(max-width: 900px)')` und ruft auf Mobile
  `route.setHelp([])` auf, bevor zum Tool gesprungen wird. Auf
  Desktop bleibt das schwebende Hilfe-Fenster wie gehabt parallel
  offen.
- **LiveWaage-Action-Buttons schrumpfen sauber** — der dritte
  Knopf („Beleuchtung") wurde auf schmalen Bildschirmen über den
  Karten-Rand gedrückt. Mit `flex: 1 1 0`, `min-width: 0` und
  `overflow-wrap: anywhere` schrumpfen die drei Buttons jetzt
  gleichmäßig und brechen lange Wörter auf zwei Zeilen, statt
  zu überlaufen.

## [0.5.3] — 2026-05-07

### Behoben (Mobile-UI)
- **LiveWaage klebt sticky auf Mobile, nur Liste scrollt intern** —
  im 0.5.2-Stand war die Sidebar auf Mobile komplett ausgeblendet,
  der Wägewert war nur indirekt über die Tools sichtbar. Jetzt ist
  sie im Dashboard-Modus wieder da, aber mit klarem Scroll-Kontrakt:
  - `<aside class="sidebar">` löst sich auf Mobile zu `display: contents`
    auf, LiveWaage und MessLog werden direkte Flex-Kinder von `.body`.
  - LiveWaage bekommt `position: sticky; top: 0; z-index: 5` — der
    Wägewert bleibt beim Scrollen jederzeit am oberen Rand sichtbar.
  - MessLog bekommt `flex: 0 0 auto; max-height: 35vh`. Damit greift
    `overflow-y: auto` auf `.list`: nur die Liste rollt durch ihre
    Einträge, das Live-Display und die Karten scrollen nicht mit.
  - Im Tool-Modus bleibt die Sidebar weiterhin ausgeblendet.

## [0.5.2] — 2026-05-07

### Behoben (Mobile-UI)
- **Karten-Menü auf Mobile sofort sichtbar** — die Sidebar mit
  LiveWaage und Messprotokoll wurde im Dashboard-Modus auf Mobile
  bisher oben ausgespielt und drückte die Werkzeug-Karten unter die
  Bildschirmkante. Da die Karten das Hauptmenü sind und die Live-
  Werte über jedes Tool und Cmd+K erreichbar bleiben, wird die
  Sidebar jetzt auf Mobile generell ausgeblendet (Dashboard und Tool).
- **Modell-Label in der Topbar nicht mehr abgeschnitten** —
  „G&G PLC-6000 · 6 kg / 0,1 g" wurde auf schmalen Bildschirmen zu
  „…6000 · 6000 g / 0…" gekürzt. Label ist jetzt zweigeteilt:
  Modell-Name bleibt, Eckdaten-Anhang („· 6 kg / 0,1 g") wird unter
  900 px ausgeblendet. Neuer Getter `modelStore.specLabel`.
- **Footer-Statusleiste auf Mobile aus** — die ausführliche Zeile
  „Live · Reader aktiv · Anschluss /dev/ttyUSB0 · 9600 Baud · Uptime
  24m · v0.5.1" war zwischen den Zellen abgeschnitten. Information
  ist über die LiveWaage-LEDs („BACKEND" / „WAAGE") und Settings
  ohnehin verfügbar; der Footer wird unter 900 px komplett versteckt.
- **ContactStrip auf Email-Knopf reduziert** — Intro-Text, Label und
  Lizenz-Hinweis auf Mobile ausgeblendet (Settings + Disclaimer-Hilfe
  haben das doppelt).
- **Hilfe-Fenster auf Mobile als Vollbild-Modal** — das schwebende,
  per Drag verschiebbare Fenster ist auf 380-px-Smartphone-Bildschirmen
  unbrauchbar. Unter 900 px wird die gespeicherte Geometrie ignoriert
  und das Fenster auf 100 vw / 100 vh aufgezogen, ohne Border-Radius.
  Resize ist auf Mobile abgeschaltet.

## [0.5.1] — 2026-05-07

### Geändert
- **Topbar auf Mobile aufgeräumt** — Brand-Schriftzug „WAAGE",
  Such-Knopf mit ⌘K-Hint, API-Doku-Link und Glossar-Buch-Icon werden
  unter 900 px ausgeblendet. Diese Funktionen sind über Cmd+K-Shortcut,
  Hilfe-Karten und Settings sekundär erreichbar; auf schmalen Geräten
  zählt der Platz für Sprachflagge, Theme-Toggle, Hilfe und Spende.
  Umsetzung als wiederverwendbare CSS-Klasse `only-desktop`.
- **Mobile-Breakpoint von 800 px auf 900 px** — in der 800–900-px-
  Übergangsphase wurde die Sidebar zu schmal, um Live-Display und
  Messprotokoll lesbar zu halten, und gleichzeitig blieb für die
  Tool-Karten zu wenig Platz (Karten-Titel wie „Behälter wiegen"
  wurden zu „Be…" abgeschnitten). Der Wechsel ins Single-Column-Layout
  setzt jetzt früher ein.
- **Sidebar-Mindestbreite** von 280 px auf 320 px angehoben
  (clamp 30 vw, max 400 px). Im Desktop-Modus bleibt das Wäge-Display
  damit auch bei knapp über 900 px noch knackig lesbar.

## [0.5.0] — 2026-05-07

### Neu
- **Multi-Format-Export für Mess-Snapshots** — CSV (mit BOM, frei
  wählbarem Trenner), TSV (Tab-getrennt), JSON (Array von Objekten),
  Markdown (Tabelle für Doku/Issues). Neuer REST-Endpoint
  `/app/samples/export` mit Format-, Spalten- und Label-Parametern.
  ExportDialog im Frontend als Modal mit Format-Auswahl,
  Trenner-Wahl, Spalten-Toggle und freien Bezeichnern.
- **Single-Delete im Messprotokoll** — Hover über eine Zeile
  blendet ein ×-Symbol ein; Klick entfernt den einzelnen Eintrag.
  Header bekommt einen Mülleimer-Knopf zum Komplettleeren.
  Backend-Anker (`_last_stored`) wird beim Löschen sauber
  zurückgesetzt, damit der nächste Diff korrekt bezogen ist.
- **„Alles zurücksetzen"** im Settings-Tab — rote Karte mit
  doppelter Bestätigung leert Snapshots, Messprotokoll, Behälter,
  Stückzähl-Vorlagen, Differenz-Schichten und alle Werkzeug-
  Zustände parallel. Modell-Wahl und Theme bleiben erhalten.

### Tests
- 8 neue Backend-Cases (Multi-Format-Export, Messlog-Single-
  Delete + Anker-Reset) — 173 Tests gesamt grün.

## [0.4.6] — 2026-05-07

### Behoben
- **Source-Switch Live ↔ Simulator funktioniert jetzt zuverlässig** —
  `state.current_reader.close()` schlug still fehl, weil weder
  `Waage` noch `SimulatedWaage` eine public `close()`-Methode hatten.
  Reader-Loop hing am alten Reader fest. Beide Klassen haben jetzt
  ein idempotentes `close()`, der Simulator wirft danach `RuntimeError`
  aus `read_one()` — der Reader-Loop reconnectet sauber.
- **UTF-8-BOM im CSV-Export** — Excel interpretierte UTF-8-CSV als
  Latin-1 („Münzen" → „Münzen"). `to_csv()` schreibt jetzt das
  Byte-Order-Mark (`﻿`) voran; LibreOffice, pandas und Python-csv
  ignorieren das korrekt.
- **Symlink `backend/VERSION` entfernt** — User-Vorgabe „niemals
  Symlinks". Datei wird jetzt von `bump.sh` synchron mit der
  Repo-Wurzel-`VERSION` gepflegt.

### Tests
- 8 neue Backend-Cases (Reader-close, Simulator-Lifecycle, Source-
  Round-Trip, CSV-BOM mit Umlauten) — 165 Tests gesamt grün.
- Frontend weiterhin 56 Tests grün, 0 Errors / 0 Warnings.

## [0.4.5] — 2026-05-07

### Neu
- **Sprachumschalter mit Flaggen** — `LANG_META` bündelt Flag-Emoji,
  nativen Namen und Kürzel pro Sprache. Bei zwei Sprachen direkter
  Klick-Wechsel, ab drei Sprachen ein kleines Dropdown unter dem
  Header-Knopf mit 🇩🇪 Deutsch / 🇬🇧 English. Erweiterung um neue
  Sprachen vollständig in `locales/README.md` dokumentiert.

### Behoben
- **docker-compose.yml und Backend-Dockerfile** auf die aktuellen
  env-Variablen umgestellt. Die alten `WAAGE_CSV` und `WAAGE_SQLITE`
  existierten im Backend nicht mehr; jetzt werden alle SQLite-DBs
  (`samples`, `messlog`, `containers`, `count_templates`) ins
  `/data`-Volume persistiert, plus `WAAGE_DATA_DIR` für `config.json`.
  Healthcheck-Pfad korrigiert auf `/scale/health`.
- Compose: env-Variablen `${X:-default}`-überschreibbar, `WAAGE_SIMULATE`
  durchgereicht, Frontend wartet auf `service_healthy` statt nur
  `depends_on`.

### Geändert
- **README.md komplett überarbeitet** für den 0.4er-Stand —
  vollständige Endpoint-Tabelle (scale + app), aktuelle env-Variablen,
  Liste der unterstützten Modell-Familien, Hinweis auf Genauigkeits-
  Toleranzen, Lizenz- und Disclaimer-Verweise, Versionierungs-Anleitung,
  Datenpersistenz-Sektion mit konkreten Pfaden.

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
