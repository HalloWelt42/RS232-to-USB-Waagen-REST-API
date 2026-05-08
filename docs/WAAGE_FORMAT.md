# `.waage` — eigenes App-Datei-Format

Stand: Mai 2026 · Version `waage-protocol-v1`

Beim Speichern eines Messprotokolls über den Protokoll-Dialog
(Disketten-Symbol im Messprotokoll-Header) bietet die App neben den
gängigen Formaten (CSV/TSV/JSON/Markdown) auch ein **eigenes
App-Format** mit Endung `.waage` an.

Sinn: vollständige, selbsterklärende Datei, die das Backend später
auch wieder einlesen kann — ohne sich an Industrie-Standards binden
zu müssen, die für den Werkstatt-Einsatz Overkill wären.

## Schema (v1)

`.waage`-Dateien sind valides JSON mit fester Schlüssel-Struktur:

```json
{
  "format":      "waage-protocol-v1",
  "created_at":  "2026-05-08T03:42:11.123Z",
  "app_version": "0.5.17",
  "scale": {
    "manufacturer":  "G&G",
    "series":        "PLC",
    "name":          "PLC-6000",
    "max_g":         6000,
    "resolution_g":  0.1
  },
  "stats": {
    "count": 12,
    "min":   0.1,
    "max":   1234.5,
    "mean":  410.3,
    "stdev": 87.4,
    "sum":   4923.6
  },
  "entries": [
    { "id": 1, "ts": "2026-05-08T03:30:00.000", "kind": "start",  "value_g":   0.0, "diff_g": null },
    { "id": 2, "ts": "2026-05-08T03:30:42.000", "kind": "change", "value_g": 123.4, "diff_g": 123.4 }
  ]
}
```

## Felder

| Feld | Typ | Pflicht | Bedeutung |
|---|---|:---:|---|
| `format`      | string | ja | Format-Marker. Aktuell `"waage-protocol-v1"`. |
| `created_at`  | ISO-8601 string | ja | Wann die Datei erzeugt wurde. |
| `app_version` | string | ja | Version der App, die das File geschrieben hat. |
| `scale`       | object | ja | Aktive Waage zum Zeitpunkt des Exports. |
| `scale.manufacturer` | string | ja | z.B. `"G&G"` |
| `scale.series`       | string | ja | z.B. `"PLC"` |
| `scale.name`         | string | ja | z.B. `"PLC-6000"` |
| `scale.max_g`        | number | ja | Maximalkapazität in Gramm. |
| `scale.resolution_g` | number | ja | Ablesbarkeit in Gramm. |
| `stats`       | object \| null | ja | Statistik aller `change`-Einträge. `null`, wenn keine vorhanden. |
| `stats.count` | number | ja | Anzahl Einträge. |
| `stats.min` / `max` / `mean` / `stdev` / `sum` | number | ja | jeweils in Gramm. |
| `entries`     | array  | ja | Vollständige Liste aller Messprotokoll-Einträge. |
| `entries[].id`     | number | ja | Backend-ID, monoton steigend. |
| `entries[].ts`     | ISO-8601 string | ja | Zeitstempel. |
| `entries[].kind`   | `"start"` \| `"change"` \| `"tare"` | ja | Eintrags-Typ. |
| `entries[].value_g`| number | ja | Wert in Gramm. |
| `entries[].diff_g` | number \| null | ja | Differenz zum vorigen Eintrag, `null` bei `start`/`tare`. |

## Versionierung

`format: "waage-protocol-v1"` ist die erste Version. Wenn sich das
Schema ändert (neue Pflichtfelder, abweichende Typen), wird die
Endziffer erhöht (`-v2`). Die App lehnt unbekannte
`format`-Strings beim Re-Import ab statt zu raten.

## Was bewusst NICHT drin ist

- Kein Operator/Firma/Standort — die App ist ein Werkstatt-Werkzeug,
  kein Audit-System.
- Kein eingebauter Audit-Trail-Hash — wer Tamper-Evidence will, kann
  die Datei extern hashen (`sha256sum messprotokoll.waage`).
- Keine Unterschrift-Slots, keine 4-Augen-Markierung — siehe
  DISCLAIMER, das ist keine GxP-Software.

## Ausblick

- **Re-Import** über `POST /app/messlog/import` — geplant, sobald
  ein konkreter Anwendungsfall (Tausch zwischen zwei Pi-Setups,
  Backup-Wiederherstellung) auftaucht.
- Format `-v2` würde z.B. ein optionales `notes`-Feld pro Eintrag
  einführen — bei Bedarf, ohne dass `-v1` invalide wird.
