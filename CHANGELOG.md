# Changelog

Alle nennenswerten Änderungen in diesem Projekt.

Versionsschema: [Semantic Versioning](https://semver.org/lang/de/) — MAJOR.MINOR.PATCH.
Datumsformat: ISO 8601 (JJJJ-MM-TT). Quelle der Wahrheit für die aktuelle
Version ist die Datei `VERSION` im Repo-Wurzel — `pyproject.toml` und
`package.json` werden daraus synchronisiert.

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
