# Locales — Sprachen erweitern

Dieses Verzeichnis enthält die Übersetzungs-Bäume. Jede Sprache liegt in
einer eigenen Datei (z.B. `de.ts`, `en.ts`); zur Laufzeit reagiert die
gesamte App reaktiv auf einen Sprachwechsel.

## Eine neue Sprache hinzufügen

1. **Datei kopieren:** `de.ts` als `<lang>.ts` ablegen — Deutsch ist der
   Master-Baum mit allen Schlüsseln. Wenn ein Schlüssel in einer anderen
   Sprache fehlt, fällt `t()` automatisch auf Deutsch zurück.

2. **Übersetzen:** Werte ersetzen, Schlüssel-Struktur unverändert lassen.

3. **In `lib/i18n.svelte.ts` registrieren:**
   - Den `Lang`-Typ erweitern: `'de' | 'en' | '<lang>'`
   - Import + `LOCALES`-Map ergänzen
   - `LOCALE_FORMAT` für Tausender-/Dezimaltrenner ergänzen

4. **Browser-Auto-Erkennung anpassen:** in `i18n.svelte.ts` der
   `detect()`-Funktion einen weiteren Branch hinzufügen.

5. **Sprachflagge:** `LanguageToggle.svelte` zeigt das Kürzel der aktuellen
   Sprache; `toggle()` durchläuft die Sprachen zyklisch — beim Hinzufügen
   weiterer Sprachen wird der Toggle automatisch um sie erweitert.

## Format-Konventionen

| Sprache | Tausender | Dezimal | Beispiel  |
|---------|-----------|---------|-----------|
| Deutsch | `.`       | `,`     | `1.234,5` |
| English | `,`       | `.`     | `1,234.5` |
| Français| ` `       | `,`     | `1 234,5` |

Diese Werte werden in `LOCALE_FORMAT` (siehe `i18n.svelte.ts`) hinterlegt
und von `format.ts` zur Laufzeit gelesen.

## Funktions-Werte

Schlüssel können auch Funktionen sein, die zur Laufzeit Argumente
einsetzen — z.B. `toast.valueCopiedG: (g: string) => \`${g} kopiert\``.
Aufruf: `t('toast.valueCopiedG', '12,3 g')`.

## Schlüssel-Konvention

`bereich.key` mit Punkt-Notation. Bestehende Bereiche:

- `app.*`, `topbar.*`, `tools.*`, `toolsShort.*`, `toolsDescription.*`,
  `toolsOriginal.*`, `commands.*`, `status.*`, `donate.*`, `contact.*`,
  `disclaimer.*`, `toast.*`, `general.*`, `units.*`, `containers.*`,
  `countTemplates.*`, `count.*`, `search.*`

Neue Schlüssel **immer zuerst in `de.ts`** hinzufügen — der Fallback
funktioniert nur in diese Richtung.
