/**
 * Hilfe-Inhalte. Texte mind. 18 px lesbar (siehe Styles), Zahlen
 * werden im Markup mit <strong> hervorgehoben.
 */

export type HelpId =
  | 'overview' | 'glossary' | 'wiegen' | 'netto' | 'count' | 'tolerance'
  | 'samples' | 'differenz' | 'sparkline' | 'history'
  | 'tare' | 'unit' | 'light' | 'copy' | 'settings' | 'donate'
  | 'architecture' | 'disclaimer';

export interface HelpBlock {
  heading: string;
  body: string;       // einfaches HTML zulässig (für <strong>)
}

export interface HelpEntry {
  id: HelpId;
  title: string;
  blocks: HelpBlock[];
}

export const helpEntries: Record<HelpId, HelpEntry> = {
  overview: {
    id: 'overview',
    title: 'Willkommen',
    blocks: [
      {
        heading: 'Was ist das hier?',
        body:
          'Eine Live-Anzeige für Ihre Präzisionswaage mit Werkzeugen für ' +
          'Qualitätskontrolle, Stückzählung, Behälterwägung und Mess-Protokoll. ' +
          'Die Waage wird über RS232 ausgelesen und ihre Werte erscheinen sofort ' +
          'in der Anzeige.',
      },
      {
        heading: 'Aufbau',
        body:
          'Beim Start sehen Sie ein Dashboard mit Karten — links die Live-Anzeige ' +
          'der Waage, rechts die verfügbaren Werkzeuge. Klick auf eine Karte ' +
          'öffnet das Werkzeug; oben erscheint dann eine Tab-Leiste, mit der Sie ' +
          'zwischen den Werkzeugen wechseln können.',
      },
      {
        heading: 'Hilfe immer dabei',
        body:
          'In jedem Bereich gibt es einen <strong>blauen Info-Knopf</strong>. ' +
          'Das Hilfe-Fenster lässt sich frei verschieben und in der Größe ändern. ' +
          'Mehrere Fenster können parallel offen sein.',
      },
    ],
  },

  glossary: {
    id: 'glossary',
    title: 'Glossar',
    blocks: [
      { heading: 'Brutto', body: 'Gesamtgewicht — Behälter plus Inhalt zusammen.' },
      { heading: 'Tara', body: 'Gewicht des leeren Behälters. Wer Tara speichert, sieht nur noch das Netto.' },
      { heading: 'Netto', body: 'Brutto minus Tara — nur der Inhalt.' },
      { heading: 'Stückgewicht', body: 'Gewicht eines einzelnen Teils. Beispiel: <strong>100</strong> Schrauben wiegen <strong>250 g</strong> -> <strong>2,5 g</strong> pro Stück.' },
      { heading: 'Stable / Stabil', body: 'Wert hat sich beruhigt und schwankt nicht mehr.' },
      { heading: 'Toleranz', body: 'Erlaubte Abweichung vom Sollwert. Bei <strong>50 g ± 2 g</strong> ist alles zwischen <strong>48 g</strong> und <strong>52 g</strong> in Ordnung.' },
      { heading: 'Auflösung', body: 'Kleinste Anzeigeschritt der Waage. Bei der PLC-6000: <strong>0,1 g</strong>.' },
      { heading: 'Maximalkapazität', body: 'Höchste Last, die die Waage messen kann. Bei der PLC-6000: <strong>6000 g</strong>.' },
      { heading: 'Session', body: 'Name für eine Mess-Reihe — gruppiert mehrere Wägungen unter einem Etikett.' },
      { heading: 'Mittelwert / Standardabweichung', body: 'Durchschnitt mehrerer Wägungen und ihre Streuung darum herum.' },
    ],
  },

  wiegen: {
    id: 'wiegen', title: 'Wiegen',
    blocks: [
      { heading: 'Funktion', body: 'Reines Ablesen des Live-Werts. Klick auf den großen Wert kopiert ihn in die Zwischenablage.' },
      { heading: 'Untermodi', body: 'Frei (nur ablesen) oder mit Sollwert-Hinweis: gewünschtes Gewicht eintragen, beim Auflegen sieht man wie nahe man dran ist.' },
    ],
  },

  netto: {
    id: 'netto', title: 'Netto und Tara',
    blocks: [
      { heading: 'Was kann das?', body: 'Speichert ein Behältergewicht (Tara) in der Software und zeigt fortan nur den Inhalt — Netto = Brutto − Tara.' },
      { heading: 'Variante 1: Behälter aufstellen', body: 'Leeres Gefäß auf die Waage, „Tara einfrieren". Ab jetzt Netto-Anzeige.' },
      { heading: 'Variante 2: Tara als Zahl', body: 'Behältergewicht direkt eintragen, z.B. <strong>23,4 g</strong>. „Setzen" speichert es.' },
      { heading: 'Beispiel Bäckerei', body: 'Schüssel auflegen, Tara — Mehl bis <strong>500 g</strong>, Wasser bis <strong>250 g</strong>. Alles im selben Gefäß abgewogen, ohne zu rechnen.' },
    ],
  },

  count: {
    id: 'count', title: 'Stückzählung',
    blocks: [
      { heading: 'Funktionsweise', body: 'Mit bekannter Anzahl gleicher Teile kalibrieren. Die App rechnet das Stückgewicht aus und zeigt für jedes neue Gewicht die Anzahl.' },
      { heading: 'Vorlagen', body: 'Schrauben, Tabletten, Münzen, Briefe — Vorlagen mit typischen Stückgewichten als Schnell-Start.' },
      { heading: 'Beispiel Werkstatt', body: '<strong>10</strong> Schrauben auflegen, <strong>10</strong> eingeben, kalibrieren. Beim weiteren Auflegen sieht man live die Stückzahl.' },
      { heading: 'Beispiel Apotheke', body: '<strong>50</strong> Tabletten als Referenz. Beim Befüllen einer Bestellung zeigt die App die aktuelle Anzahl.' },
      { heading: 'Genauigkeit', body: 'Mehr Referenzteile = genauer. Bei Teilen unter <strong>1 g</strong> mindestens <strong>20</strong> Stück, sonst kippt die Anzeige wegen der Auflösung von <strong>0,1 g</strong>.' },
    ],
  },

  tolerance: {
    id: 'tolerance', title: 'Qualitätskontrolle',
    blocks: [
      { heading: 'Was ist das?', body: 'Sie geben einen Sollwert mit Toleranzgrenzen vor. Eine große Ampel zeigt grün, gelb oder rot — je nach Abweichung.' },
      { heading: 'Beispiel Apotheke', body: 'Rezeptur verlangt <strong>2,000 g</strong> ± <strong>0,05 g</strong>. Beim Einwiegen reagiert die Ampel sofort — kein Rechnen, kein zweiter Blick.' },
      { heading: 'Beispiel Verpackung', body: 'Tütchen mit <strong>50 g</strong> ± <strong>2 g</strong>. Alles zwischen <strong>48 g</strong> und <strong>52 g</strong> ist grün.' },
      { heading: 'Tipp Mindestmenge', body: 'Wenn Sie nur Untergewicht prüfen wollen, setzen Sie Tol+ auf einen sehr großen Wert.' },
    ],
  },

  samples: {
    id: 'samples', title: 'Werte erfassen',
    blocks: [
      { heading: 'Was wird gespeichert?', body: 'Aktueller Wägewert mit Label und Notiz, in einer Datenbank — überlebt Backend-Neustarts.' },
      { heading: 'Sessions', body: 'Mehrere Wägungen unter einem Session-Namen gruppieren, z.B. „Charge-2026-05-07".' },
      { heading: 'Statistik', body: 'Anzahl, Min, Max, Mittelwert, Standardabweichung und Summe automatisch berechnet.' },
      { heading: 'Beispiel Labor', body: 'Versuchsreihe mit Probe-A1, A2, A3 ... CSV-Export liefert die Reihe als Datei für die Auswertung.' },
    ],
  },

  differenz: {
    id: 'differenz', title: 'Differenz-Wiegen',
    blocks: [
      { heading: 'Mehrfach-Tara', body: 'Mehrere Tara-Stufen stapelbar. Inhalt = Brutto minus Summe aller Tarae.' },
      { heading: 'Beispiel', body: 'Behälter auflegen, „als Tara" — <strong>53 g</strong>. Trägermedium auflegen, „als Tara" — weitere <strong>20 g</strong>. Der eigentliche Inhalt erscheint als Netto, ohne dass die Behälter mitgewogen werden.' },
      { heading: 'Schichten verwalten', body: 'Jede Schicht in einer Liste — einzelne Tarae lassen sich entfernen, ohne den Rest zu verlieren.' },
    ],
  },

  history: {
    id: 'history', title: 'Messprotokoll',
    blocks: [
      { heading: 'Was steht da?', body: 'Eine Liste der Werte-<strong>Änderungen</strong>: jede neue Auflage, jede Entnahme, jeder Tara-Vorgang ein Eintrag mit Differenz und resultierendem Wert.' },
      { heading: 'Warum nicht alle Frames?', body: 'Eine ruhige Waage liefert dieselben Werte mehrfach pro Sekunde — das wäre nicht hilfreich. Die Liste reagiert nur auf echte Änderungen.' },
    ],
  },

  sparkline: {
    id: 'sparkline', title: 'Mini-Verlauf',
    blocks: [{ heading: 'Hinweis', body: 'In dieser Version ist der Mini-Verlauf durch das Messprotokoll ersetzt — siehe Hilfe „Messprotokoll".' }],
  },

  tare: {
    id: 'tare', title: 'Auf Null setzen (Tara)',
    blocks: [
      { heading: 'Funktion', body: 'Setzt den aktuellen Anzeigewert der Waage auf Null. Entspricht der Tara-Taste an der Waage.' },
      { heading: 'Wozu?', body: 'Behälter aufstellen, Tara, Inhalt füllen — die Anzeige zeigt direkt das Netto.' },
    ],
  },

  unit: {
    id: 'unit', title: 'Maßeinheit umschalten',
    blocks: [
      { heading: 'Funktion', body: 'Die Waage wechselt zwischen Gramm, Kilogramm, Karat, Unzen und Pfund — je nach Modell.' },
      { heading: 'Tipp', body: 'Die Anzeige in der App rechnet intern immer in Gramm.' },
    ],
  },

  light: {
    id: 'light', title: 'Beleuchtung',
    blocks: [
      { heading: 'Funktion', body: 'Schaltet die Hintergrundbeleuchtung am Display der Waage ein oder aus.' },
      { heading: 'Diagnose', body: 'Wenn die Beleuchtung umschaltet, kommen Ihre Befehle bei der Waage an — guter Funktionstest.' },
    ],
  },

  copy: {
    id: 'copy', title: 'Werte kopieren',
    blocks: [
      { heading: 'Klick kopiert', body: 'Tippen oder klicken Sie auf den großen Wägewert. Der Wert wandert in die Zwischenablage; ein kurzer Hinweis bestätigt.' },
      { heading: 'Übernehmen', body: 'In Toleranz, Netto und Zählung gibt es Knöpfe „aktuellen Wert übernehmen". Spart Tippen, vermeidet Tippfehler.' },
    ],
  },

  settings: {
    id: 'settings', title: 'Einstellungen',
    blocks: [
      { heading: 'Modell', body: 'Wählen Sie Ihre Waage aus der Liste. Das Modell beeinflusst Anzeige-Einheiten und Maximal-/Auflösungswerte.' },
      { heading: 'Theme', body: 'Hell, Dunkel oder Automatisch (folgt der Systemeinstellung).' },
      { heading: 'Anschluss', body: 'Serieller Port und Baudrate. Beim Default „auto" findet die App den FTDI-Adapter selbst.' },
      { heading: 'Polling', body: 'Wie oft die App den Print-Befehl an die Waage schickt — Standard <strong>0,5 s</strong>.' },
    ],
  },

  donate: {
    id: 'donate', title: 'Danke',
    blocks: [
      { heading: 'Worum geht es?', body: 'Quelloffen, aber ausschließlich für die <strong>private, nicht-kommerzielle</strong> Nutzung gedacht. Wer Lust hat, kann mich per Ko-fi oder Krypto unterstützen.' },
      { heading: 'Lizenz', body: 'CC BY-NC-ND 4.0 mit Zusatzbestimmungen — private Modifikation und private Forks erlaubt, kommerzielle Nutzung und Veröffentlichung modifizierter Versionen nicht. Volltext liegt im Repository unter <code>LICENSE</code>.' },
      { heading: 'Krypto', body: 'Drei Karten — BTC, DOGE, ETH. Klick zeigt QR-Code und Adresse. Ein-Klick-Kopieren-Knopf.' },
    ],
  },

  architecture: {
    id: 'architecture', title: 'Architektur Scale ↔ App',
    blocks: [
      { heading: 'Was ist getrennt?', body: 'Das <strong>Scale-Modul</strong> (Endpoint /scale/*) macht nur das Auslesen und Steuern der Waage. Es kann eigenständig laufen — Drittsysteme können das einbinden, ohne den App-Layer mitzunehmen.' },
      { heading: 'Was ist optional?', body: 'Das <strong>App-Modul</strong> (/app/*) bietet Toleranz, Netto, Zählen, Erfassen, Differenz und Messprotokoll — UI-Komfort. Setzt das Scale-Modul voraus.' },
      { heading: 'Konsequenz', body: 'Wer nur das Gewicht in seinen Workflow integriert, braucht nur /scale/*. UI-Updates an /app/* berühren das Scale-Modul nicht.' },
    ],
  },

  disclaimer: {
    id: 'disclaimer', title: 'Haftungsausschluss',
    blocks: [
      { heading: 'Keine Gewähr', body: 'Diese Software wird kostenlos bereitgestellt — <strong>ohne Gewähr</strong> für Richtigkeit, Vollständigkeit oder Aktualität der Werte. Keine Eignung für einen bestimmten Zweck zugesichert.' },
      { heading: 'Nicht eichfähig', body: 'Die Software ist <strong>kein eichfähiges Mess-System</strong>. Für Verkauf nach Gewicht, amtliche Mengenangaben, medizinische Dosierungen mit gesetzlichen Toleranzen, Zoll- oder Steuer­relevanz ist sie <strong>nicht zulässig</strong>.' },
      { heading: 'Keine Haftung', body: 'Soweit gesetzlich zulässig, ist jede Haftung für mittelbare Schäden, entgangenen Gewinn, Datenverlust oder Folgeschäden ausgeschlossen. Haftung bei Verletzung von Leben/Körper/Gesundheit oder bei Vorsatz/grober Fahrlässigkeit bleibt unberührt.' },
      { heading: 'Verantwortung beim Anwender', body: 'Die Verantwortung für richtige Anwendung, regelmäßige Kontrolle mit geeichten Prüfgewichten und Plausibilität der Werte liegt allein beim Anwender. Volltext: <code>DISCLAIMER.md</code> im Repo.' },
    ],
  },
};
