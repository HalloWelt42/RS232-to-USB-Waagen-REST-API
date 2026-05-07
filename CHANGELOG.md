# Changelog

Alle nennenswerten Änderungen in diesem Projekt.

Versionsschema: [Semantic Versioning](https://semver.org/lang/de/) — MAJOR.MINOR.PATCH.
Datumsformat: ISO 8601 (JJJJ-MM-TT). Quelle der Wahrheit für die aktuelle
Version ist die Datei `VERSION` im Repo-Wurzel — `pyproject.toml` und
`package.json` werden daraus synchronisiert.

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
