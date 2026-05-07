/**
 * Deutsche Übersetzungen.
 *
 * Schlüssel-Konvention: ``bereich.key``. Werte sind menschenlesbar in
 * deutscher Sprache mit Umlauten, Hover-Tooltips enthalten zusätzlich
 * die englische Original-Bezeichnung und den RS232-Befehl.
 */

const de = {
  app: {
    title: 'Waage',
    subtitle: 'Präzisionswaagen über RS232',
    apiDocs: 'API-Doku',
  },
  topbar: {
    glossary: 'Glossar',
    info: 'Information und Hilfe',
    donate: 'Danke — Unterstütze die Entwicklung',
    themeAuto: 'Anzeigemodus: Automatisch',
    themeLight: 'Anzeigemodus: Hell',
    themeDark: 'Anzeigemodus: Dunkel',
  },
  tools: {
    wiegen: 'Wiegen',
    netto: 'Behälter wiegen',
    count: 'Stückzählung',
    tolerance: 'Qualitätskontrolle',
    samples: 'Messwerte erfassen',
    differenz: 'Differenz-Wiegen',
    help: 'Hilfe und Glossar',
    settings: 'Einstellungen',
    donate: 'Danke',
  },
  toolsShort: {
    wiegen: 'Wiegen',
    netto: 'Behälter',
    count: 'Zählen',
    tolerance: 'QC',
    samples: 'Erfassen',
    differenz: 'Differenz',
    help: 'Hilfe',
    settings: 'Settings',
    donate: 'Danke',
  },
  toolsDescription: {
    wiegen: 'Live-Wert ablesen, festhalten, kopieren.',
    netto: 'Tara einfrieren, Netto-Anzeige.',
    count: 'Anzahl aus Stückgewicht ermitteln.',
    tolerance: 'Soll mit Ampel grün/gelb/rot.',
    samples: 'Werte mit Label und CSV-Export.',
    differenz: 'Mehrere Tarae stapeln, Inhalt = Brutto − Σ.',
    help: 'Anleitung, Beispiele, Begriffe.',
    settings: 'Modell, Theme, Anschluss, Lizenz.',
    donate: 'Unterstütze die Entwicklung.',
  },
  toolsOriginal: {
    wiegen: 'WEIGHING',
    netto: 'TARA / NETTO',
    count: 'COUNTING',
    tolerance: 'QC / TOLERANCE',
    samples: 'SAMPLES',
    differenz: 'MULTI-TARE',
    help: 'HELP',
    settings: 'SETTINGS',
    donate: 'DONATE',
  },
  commands: {
    tare: 'Auf Null setzen',
    tareTooltip: 'Tara — Anzeige der Waage auf Null setzen (RS232: ESC t)',
    unit: 'Maßeinheit',
    unitTooltip: 'Einheit umschalten — g, kg, oz, lb, ct (RS232: ESC s)',
    light: 'Beleuchtung',
    lightTooltip: 'Display-Beleuchtung ein/aus (RS232: ESC u)',
  },
  status: {
    live: 'Live',
    connecting: 'Verbinde',
    closed: 'Getrennt',
    error: 'Fehler',
    stable: 'STABIL',
    unstable: 'INSTABIL',
    readerActive: 'Reader aktiv',
    readerInactive: 'Reader aus',
    port: 'Anschluss',
    baudrate: 'Baudrate',
    uptime: 'Uptime',
    version: 'Version',
  },
  donate: {
    title: 'Waage unterstützen',
    intro:
      'Quelloffen, aber ausschließlich für die private, nicht-kommerzielle ' +
      'Nutzung gedacht. Wenn dir die Anwendung gefällt, freue ich mich über ' +
      'eine kleine Unterstützung — per Ko-fi oder über eine der Krypto-Adressen.',
    kofi: 'Auf Ko-fi unterstützen',
    orCrypto: 'oder per Kryptowährung',
    addressCopy: 'Adresse kopieren',
    addressCopied: 'Kopiert',
    thanks: 'Vielen Dank für deine Unterstützung',
    addressCopyError: 'Kopieren fehlgeschlagen',
    qrLabel: 'QR-Code zur Adresse',
    selectCrypto: 'Eine Währung wählen — QR-Code und Adresse erscheinen dann darunter.',
  },
  contact: {
    label: 'Entwickler-Kontakt für Workflow-Integration',
    intro: 'Sie möchten die Software in Ihren Workflow integrieren? Schreiben Sie mir.',
    license: 'CC BY-NC-ND 4.0 + Zusatzbestimmungen — Private Nutzung. Copyright 2026 HalloWelt42',
    licenseShort: 'Quelloffen, nur Privat — CC BY-NC-ND 4.0',
  },
  toast: {
    valueCopied: 'Wert kopiert',
    valueCopiedG: (g: string) => `${g} kopiert`,
    jsonCopied: 'JSON kopiert',
    addressCopied: 'Adresse kopiert',
    copyError: 'Kopieren nicht möglich',
    settingSaved: 'Einstellung gespeichert',
    error: 'Fehler',
  },
  general: {
    back: 'Zurück',
    close: 'Schließen',
    save: 'Speichern',
    cancel: 'Abbrechen',
    delete: 'Löschen',
    activate: 'Aktivieren',
    deactivate: 'Deaktivieren',
    apply: 'Übernehmen',
    confirm: 'Bestätigen',
    yes: 'Ja',
    no: 'Nein',
    loading: 'Lädt …',
  },
  units: {
    pieces: 'Stück',
    grams: 'Gramm',
    kilograms: 'Kilogramm',
  },
} as const;

export default de;
export type Locale = typeof de;
