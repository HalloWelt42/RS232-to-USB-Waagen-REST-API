/**
 * Hilfe-Inhalte zu jeder Funktion der App.
 *
 * Strukturiert in kurze Erklär-Blöcke: Was, So benutzen, Beispiel,
 * Tipps. Anzeige im DraggableHelpWindow. Texte sind durchgängig
 * deutsch mit ordentlichen Umlauten.
 */

export type HelpId =
  | 'overview'
  | 'tare'
  | 'unit'
  | 'light'
  | 'tolerance'
  | 'netto'
  | 'count'
  | 'samples'
  | 'sparkline'
  | 'history';

export interface HelpBlock {
  heading: string;
  body: string;
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
          'Eine Live-Anzeige für Ihre G&G-Präzisionswaage mit Zusatz-' +
          'funktionen für Qualitätskontrolle, Stückzählung und Mess-' +
          'protokollierung. Die Waage liefert Werte über die serielle ' +
          'Schnittstelle, die Anwendung zeigt sie sofort an und schreibt ' +
          'sie auf Wunsch in eine Datenbank.',
      },
      {
        heading: 'Wie ist die Anwendung aufgebaut?',
        body:
          'Links sehen Sie den großen Wägewert mit Verlauf der letzten ' +
          'Minute. Rechts gibt es vier Werkzeuge — Toleranz, Netto, ' +
          'Zählen und Erfassen — die Sie über die Tabs umschalten. Oben ' +
          'in der Leiste finden Sie die Schnellaktionen Tara, Einheit ' +
          'und Licht. Unten zeigt eine kleine Statuszeile, ob alles ' +
          'läuft.',
      },
      {
        heading: 'Hilfe immer dabei',
        body:
          'In jedem Bereich gibt es einen Fragezeichen-Knopf. Wenn Sie ' +
          'Hilfe brauchen, klicken Sie ihn an. Das Hilfe-Fenster lässt ' +
          'sich frei verschieben, damit es nichts verdeckt.',
      },
    ],
  },

  tare: {
    id: 'tare',
    title: 'Tara',
    blocks: [
      {
        heading: 'Was macht der Knopf?',
        body:
          'Setzt den aktuellen Anzeigewert der Waage auf Null. Genau ' +
          'das, was die Tara-Taste an der Waage selbst auch tut.',
      },
      {
        heading: 'Wozu nutzen?',
        body:
          'Wenn Sie ein Gefäß auf die Waage stellen und nur den Inhalt ' +
          'wiegen möchten: leeres Gefäß auflegen, Tara drücken — ' +
          'danach füllen, die Waage zeigt direkt das Netto-Gewicht.',
      },
      {
        heading: 'Tipp',
        body:
          'Wenn Sie das Tara-Gewicht später noch wissen möchten oder ' +
          'mehrere unterschiedliche Behälter haben, ist der Reiter ' +
          'Netto die bessere Wahl: dort bleibt das Tara-Gewicht ' +
          'gespeichert.',
      },
    ],
  },

  unit: {
    id: 'unit',
    title: 'Einheit umschalten',
    blocks: [
      {
        heading: 'Was passiert?',
        body:
          'Die Waage wechselt zwischen den verfügbaren Einheiten — je ' +
          'nach Modell sind das Gramm, Kilogramm, Karat, Unzen und ' +
          'Pfund.',
      },
      {
        heading: 'Tipp',
        body:
          'Die Anzeige in dieser Anwendung rechnet intern immer in ' +
          'Gramm. Selbst wenn die Waage in Kilogramm sendet, sehen Sie ' +
          'hier die Werte einheitlich in Gramm bzw. ab 1000 g ' +
          'automatisch in Kilogramm.',
      },
    ],
  },

  light: {
    id: 'light',
    title: 'Beleuchtung',
    blocks: [
      {
        heading: 'Was macht der Knopf?',
        body:
          'Schaltet die Hintergrundbeleuchtung am Display der Waage ' +
          'ein oder aus.',
      },
      {
        heading: 'Praktisch dafür',
        body:
          'Bei Dauereinsatz Strom sparen, oder kurz prüfen, ob die ' +
          'Verbindung wirklich steht: wenn das Display reagiert, kommen ' +
          'Ihre Befehle bei der Waage an.',
      },
    ],
  },

  tolerance: {
    id: 'tolerance',
    title: 'Qualitätskontrolle',
    blocks: [
      {
        heading: 'Was ist das?',
        body:
          'Sie geben einen Sollwert vor, dazu eine erlaubte Über- und ' +
          'Unterschreitung. Die Anwendung zeigt dann live in einer ' +
          'großen Ampel, ob das aktuelle Gewicht im Bereich liegt ' +
          '(grün), zu leicht (gelb) oder zu schwer (rot) ist.',
      },
      {
        heading: 'So benutzen Sie es',
        body:
          'Sollwert in Gramm eintragen, untere und obere Toleranz ' +
          'eingeben, Aktivieren drücken. Danach legen Sie Ihre Teile ' +
          'auf — die Ampel reagiert sofort. Mit Deaktivieren schalten ' +
          'Sie den Modus wieder ab.',
      },
      {
        heading: 'Beispiel',
        body:
          'Sie packen Tütchen mit 50 g Gewürz, erlaubte Abweichung ist ' +
          '±2 g. Soll = 50, Tol- = 2, Tol+ = 2. Alles zwischen 48 g und ' +
          '52 g zeigt grün, darunter gelb, darüber rot.',
      },
      {
        heading: 'Tipp',
        body:
          'Asymmetrische Toleranzen sind erlaubt. Wenn Sie nur Mindest-' +
          'Mengen prüfen, setzen Sie Tol+ auf einen großen Wert ' +
          '(etwa 9999) und nur Tol- restriktiv.',
      },
    ],
  },

  netto: {
    id: 'netto',
    title: 'Netto / Tara',
    blocks: [
      {
        heading: 'Was kann das?',
        body:
          'Speichert ein bekanntes Behältergewicht (Tara) in der ' +
          'Software und zeigt fortan das Netto-Gewicht — also Brutto ' +
          'minus Tara — in großer Schrift an.',
      },
      {
        heading: 'Variante 1: Behälter aufstellen',
        body:
          'Leeres Gefäß auf die Waage stellen, Aktuelles Gewicht als ' +
          'Tara einfrieren drücken. Ab jetzt zeigt das Panel das ' +
          'Netto-Gewicht des Inhalts.',
      },
      {
        heading: 'Variante 2: Tara als Zahl eingeben',
        body:
          'Wenn Sie das Behältergewicht schon kennen (z.B. 23,4 g), ' +
          'tragen Sie es ins Feld neben Setzen ein und klicken Setzen.',
      },
      {
        heading: 'Unterschied zur Tara-Taste',
        body:
          'Die Tara-Taste oben in der Leiste setzt den Nullpunkt direkt ' +
          'an der Waage. Das Netto-Panel hier macht es nur in der ' +
          'Software — die Waage selbst zeigt weiter den Brutto-Wert.',
      },
    ],
  },

  count: {
    id: 'count',
    title: 'Stückzählung',
    blocks: [
      {
        heading: 'Funktionsweise',
        body:
          'Sie kalibrieren die Anwendung mit einer bekannten Anzahl ' +
          'gleicher Teile — die Software berechnet daraus das Stück-' +
          'gewicht. Danach zeigt sie für jedes neue Gewicht die ' +
          'aktuelle Stückzahl an.',
      },
      {
        heading: 'Anwendungsbeispiel',
        body:
          '10 identische Schrauben auf die Waage legen, Eingabefeld auf ' +
          '10 stellen, Kalibrieren klicken. Wenn jetzt mehr Schrauben ' +
          'aufgelegt werden, zeigt die Anzeige live deren Anzahl.',
      },
      {
        heading: 'Genauigkeit',
        body:
          'Je mehr Referenzteile Sie zum Kalibrieren nehmen, desto ' +
          'genauer wird das Stückgewicht. Bei kleinen Teilen unter 1 g ' +
          'sollten es mindestens 20 Stück sein, sonst kippt die Anzeige ' +
          'wegen der Auflösungsgrenze von 0,1 g.',
      },
      {
        heading: 'Neu kalibrieren',
        body:
          'Wenn Sie auf andere Teile wechseln, nutzen Sie Neu ' +
          'kalibrieren — das überschreibt das gespeicherte Stück-' +
          'gewicht. Zurücksetzen schaltet den Zählmodus ganz aus.',
      },
    ],
  },

  samples: {
    id: 'samples',
    title: 'Werte erfassen',
    blocks: [
      {
        heading: 'Was wird gespeichert?',
        body:
          'Sie halten den aktuellen Wägewert mit einem optionalen Label ' +
          'und einer Notiz fest. Der Eintrag wandert in eine SQLite-' +
          'Datenbank auf dem Server und überlebt Backend-Neustarts.',
      },
      {
        heading: 'Sessions',
        body:
          'Mehrere Wägungen lassen sich unter einem Session-Namen ' +
          'gruppieren — etwa Charge-2026-05-07 oder Probe-Mehl. Im ' +
          'Feld oben rechts geben Sie den Session-Namen ein.',
      },
      {
        heading: 'Statistik',
        body:
          'Sobald mehrere Werte erfasst sind, sehen Sie automatisch ' +
          'Anzahl, Minimum, Maximum, Mittelwert, Standardabweichung ' +
          'und Summe für die aktuelle Session.',
      },
      {
        heading: 'CSV-Export',
        body:
          'Klick auf CSV-Export liefert die Werte als Datei zum ' +
          'Download — geeignet für Import in Excel, Numbers oder ' +
          'eine Auswertungssoftware.',
      },
    ],
  },

  sparkline: {
    id: 'sparkline',
    title: 'Mini-Verlauf',
    blocks: [
      {
        heading: 'Was zeigt die Linie?',
        body:
          'Den Verlauf des Wägewerts der letzten 60 Sekunden. Der ' +
          'Bereich zwischen Minimum und Maximum füllt sich automatisch.',
      },
      {
        heading: 'Tipp',
        body:
          'Ideal um zu sehen, ob ein Wert wirklich zur Ruhe kommt oder ' +
          'noch driftet — gerade bei feineren Wägungen sehr nützlich.',
      },
    ],
  },

  history: {
    id: 'history',
    title: 'Verlauf',
    blocks: [
      {
        heading: 'Was steht da?',
        body:
          'Eine Liste mit den letzten Werten — aber nur die Frames, ' +
          'bei denen sich der Wert wirklich geändert hat. Werte unter ' +
          'der Auflösungs-Schwelle (0,05 g) gelten als gleich und ' +
          'tauchen nicht erneut auf.',
      },
      {
        heading: 'Warum nicht alle Frames?',
        body:
          'Eine ruhige Waage liefert mehrere Frames pro Sekunde mit ' +
          'demselben Wert — das wäre nicht hilfreich. Stattdessen ' +
          'sehen Sie die echte Bewegung: jede neue Auflage, jede ' +
          'Entnahme, jedes Tara.',
      },
    ],
  },
};
