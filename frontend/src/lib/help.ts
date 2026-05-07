/**
 * Hilfe-Inhalte zu jeder Funktion der App.
 *
 * Strukturiert in kurze Erklär-Blöcke: Was, So benutzen, Beispiel,
 * Tipps. Anzeige im DraggableHelpWindow. Texte sind durchgängig
 * deutsch mit ordentlichen Umlauten.
 *
 * Die Hilfe ist branchen-übergreifend formuliert — zu jeder Funktion
 * gibt es Beispiele aus verschiedenen Anwendungsbereichen (Apotheke,
 * Bäckerei, Werkstatt, Versand, Schmuck, Labor), damit der Bezug zur
 * eigenen Tätigkeit leicht herzustellen ist.
 */

export type HelpId =
  | 'overview'
  | 'glossary'
  | 'tare'
  | 'unit'
  | 'light'
  | 'tolerance'
  | 'netto'
  | 'count'
  | 'samples'
  | 'sparkline'
  | 'history'
  | 'copy';

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
          'Eine Live-Anzeige für Ihre Präzisionswaage mit Zusatz-' +
          'funktionen für Qualitätskontrolle, Stückzählung, Behälter-' +
          'wägung (Tara/Netto) und Mess-Protokollierung. Die Waage ' +
          'liefert Werte über die serielle Schnittstelle, die Anwendung ' +
          'zeigt sie sofort an und schreibt sie auf Wunsch in eine ' +
          'Datenbank.',
      },
      {
        heading: 'Wie ist die Anwendung aufgebaut?',
        body:
          'Auf dem Computer: links der große Wägewert mit Mini-Verlauf ' +
          'der letzten Minute, rechts vier Werkzeuge in Tabs. Auf dem ' +
          'Smartphone: Werkzeuge unten als Tab-Leiste, Wert oben groß. ' +
          'Oben in der Leiste die Schnellaktionen Tara, Einheit, Licht. ' +
          'Unten eine schmale Statuszeile.',
      },
      {
        heading: 'Vier Werkzeuge im Überblick',
        body:
          'Toleranz: prüft, ob ein Wert in einem festgelegten Bereich ' +
          'liegt — Ampel grün/gelb/rot. ' +
          'Netto: zieht das Behältergewicht ab und zeigt nur den Inhalt. ' +
          'Zählen: ermittelt aus dem Stückgewicht die Anzahl. ' +
          'Erfassen: speichert Werte mit Beschriftung, exportierbar als ' +
          'CSV-Datei.',
      },
      {
        heading: 'Hilfe immer dabei',
        body:
          'In jedem Bereich gibt es einen Fragezeichen-Knopf. Wenn Sie ' +
          'Hilfe brauchen, klicken Sie ihn an. Das Hilfe-Fenster lässt ' +
          'sich frei verschieben, damit es nichts verdeckt. Mehrere ' +
          'Fenster können parallel offen sein.',
      },
      {
        heading: 'Begriffe schnell nachschlagen',
        body:
          'Im Glossar finden Sie kurze Erklärungen für Tara, Netto, ' +
          'Brutto, Stückgewicht, Standardabweichung und weitere ' +
          'Begriffe — geöffnet über den Übersichts-Knopf rechts oben.',
      },
    ],
  },

  glossary: {
    id: 'glossary',
    title: 'Glossar',
    blocks: [
      {
        heading: 'Brutto',
        body:
          'Das ist das gesamte Gewicht, das auf der Waage liegt — also ' +
          'Behälter plus Inhalt zusammen. Ohne Tara entspricht der ' +
          'angezeigte Wert immer dem Brutto.',
      },
      {
        heading: 'Tara',
        body:
          'Das Gewicht des leeren Behälters. Wer ein Tara-Gewicht ' +
          'speichert, sieht danach nur noch das Netto-Gewicht. Beispiel: ' +
          'Schale 53 g (Tara) + Mehl 247 g (Netto) = 300 g (Brutto).',
      },
      {
        heading: 'Netto',
        body:
          'Das reine Gewicht des Inhalts ohne Behälter. Wird berechnet ' +
          'als Brutto minus Tara. Auf der Verpackung im Supermarkt steht ' +
          'genau dieser Wert.',
      },
      {
        heading: 'Stückgewicht',
        body:
          'Das Gewicht eines einzelnen Teils. Wird in der App durch ' +
          'Auflegen einer bekannten Anzahl gleicher Teile ermittelt. ' +
          'Beispiel: 100 Schrauben wiegen 250 g, das Stückgewicht ist ' +
          '2,5 g pro Stück.',
      },
      {
        heading: 'Stable / Stabil',
        body:
          'Die Waage hat sich beruhigt und der Wert schwankt nicht ' +
          'mehr. Erst dann ist die Anzeige verlässlich. Wenn sich noch ' +
          'etwas bewegt — Luftzug, Vibration, Mensch tippt an die Waage ' +
          '— erscheint die Anzeige als instabil.',
      },
      {
        heading: 'Toleranz',
        body:
          'Die erlaubte Abweichung vom Sollwert. Wenn Sie 50 g abfüllen ' +
          'wollen und ±2 g toleriert sind, ist alles zwischen 48 g und ' +
          '52 g in Ordnung.',
      },
      {
        heading: 'Mittelwert / Standardabweichung',
        body:
          'Der Mittelwert ist der Durchschnitt mehrerer Wägungen. Die ' +
          'Standardabweichung sagt, wie stark die Werte um den Mittel-' +
          'wert streuen. Eine kleine Standardabweichung bedeutet: alle ' +
          'Wägungen waren ähnlich.',
      },
      {
        heading: 'Auflösung',
        body:
          'Die kleinste Änderung, die die Waage anzeigen kann. Bei ' +
          '0,1 g springt die Anzeige in 0,1-g-Schritten. Bei feineren ' +
          'Waagen sind es 0,01 g oder 0,001 g.',
      },
      {
        heading: 'Maximalkapazität',
        body:
          'Das höchste Gewicht, das die Waage messen kann. Steht meist ' +
          'auf dem Typenschild ("Max = 6000 g"). Mehr darf nicht ' +
          'aufgelegt werden, sonst zeigt die Waage Overload.',
      },
      {
        heading: 'Session',
        body:
          'Ein Name für eine zusammengehörige Mess-Reihe. So lassen ' +
          'sich z.B. die heutigen Wägungen einer bestimmten Charge von ' +
          'denen einer anderen Charge trennen — auch wenn sie alle in ' +
          'derselben Datenbank liegen.',
      },
      {
        heading: 'CSV',
        body:
          'Comma-Separated Values: ein einfaches Tabellenformat, das ' +
          'jede Tabellen-Software lesen kann (Excel, LibreOffice ' +
          'Calc, Google Sheets, Numbers).',
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
        heading: 'Beispiel Bäckerei',
        body:
          'Schüssel auf die Waage stellen, Tara — auf 0 zurück. Mehl ' +
          'einrieseln lassen, bis die Waage 500 g zeigt. Wasser dazu ' +
          'bis 250 g hinzukommen. Salz bis 10 g. Fertig — alles im ' +
          'gleichen Gefäß abgewogen, ohne Rechnen.',
      },
      {
        heading: 'Beispiel Versand',
        body:
          'Versandkarton auf die Waage, Tara. Inhalt einlegen — die ' +
          'Anzeige ist sofort das verkehrsgerechte Gewicht des Inhalts ' +
          'ohne Verpackung.',
      },
      {
        heading: 'Tipp',
        body:
          'Wenn Sie das Tara-Gewicht später noch wissen möchten oder ' +
          'mehrere unterschiedliche Behälter haben, ist der Tab Netto ' +
          'die bessere Wahl: dort bleibt das Tara-Gewicht gespeichert.',
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
        heading: 'Beispiel Schmuck',
        body:
          'Ein Schmuckhändler arbeitet meist in Karat (1 ct = 0,2 g). ' +
          'Statt umzurechnen einfach mit der Einheit-Taste auf ct ' +
          'umstellen — der Wert erscheint direkt in der gewünschten ' +
          'Einheit auf der Waage.',
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
        heading: 'Beispiel Apotheke',
        body:
          'Eine Rezeptur verlangt 2,000 g Wirkstoff, erlaubte Abweichung ' +
          '±0,05 g. Soll = 2, Tol- = 0,05, Tol+ = 0,05. Beim Einwiegen ' +
          'zeigt die Ampel sofort, ob die Menge im engen Bereich liegt — ' +
          'kein Rechnen, kein zweiter Blick auf Notizen.',
      },
      {
        heading: 'Beispiel Verpackung',
        body:
          'Sie packen Tütchen mit 50 g Gewürz, erlaubte Abweichung ist ' +
          '±2 g. Soll = 50, Tol- = 2, Tol+ = 2. Alles zwischen 48 g und ' +
          '52 g zeigt grün, darunter gelb, darüber rot.',
      },
      {
        heading: 'Beispiel Versand',
        body:
          'Pakete bis 500 g Briefporto, alles darüber kostet mehr. ' +
          'Soll = 250, Tol- = 250, Tol+ = 250. Solange die Ampel grün ' +
          'ist, passt das Paket noch in die günstige Klasse.',
      },
      {
        heading: 'Tipp: nur Mindestmenge',
        body:
          'Wenn Sie nur sicherstellen wollen, dass nicht zu wenig drin ' +
          'ist, setzen Sie Tol+ auf einen großen Wert (etwa 9999) und ' +
          'nur Tol- restriktiv. Dann wird ausschließlich Untergewicht ' +
          'rot angezeigt.',
      },
    ],
  },

  netto: {
    id: 'netto',
    title: 'Netto und Tara',
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
          'Wenn Sie das Behältergewicht schon kennen (z.B. 23,4 g für ' +
          'eine Standard-Schale), tragen Sie es ins Feld neben Setzen ' +
          'ein und klicken Setzen.',
      },
      {
        heading: 'Beispiel Labor',
        body:
          'Ein Reagenzglas wiegt 18,5 g. Tarawert eintragen: 18,5. Ab ' +
          'jetzt sehen Sie ausschließlich, wie viel an Probe drin ist — ' +
          'auch wenn Sie das Glas zwischendurch von der Waage nehmen.',
      },
      {
        heading: 'Beispiel Werkstatt',
        body:
          'Eine Schale für Kleinteile, Eigengewicht unbekannt. Schale ' +
          'auflegen, „Aktuelles Gewicht als Tara einfrieren". Beim ' +
          'Hinzufügen von Schrauben sehen Sie immer nur das reine ' +
          'Schraubengewicht.',
      },
      {
        heading: 'Unterschied zur Tara-Taste oben',
        body:
          'Die Tara-Taste oben in der Leiste setzt den Nullpunkt direkt ' +
          'an der Waage. Das Netto-Panel hier macht es nur in der ' +
          'Software — die Waage selbst zeigt weiter den Brutto-Wert. ' +
          'Vorteil: das Behältergewicht bleibt gespeichert und kann ' +
          'weiter verwendet werden, auch wenn die Waage zwischendurch ' +
          'genullt wird.',
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
        heading: 'Beispiel Werkstatt',
        body:
          '10 identische Schrauben auf die Waage legen, Eingabefeld auf ' +
          '10 stellen, Kalibrieren klicken. Wenn jetzt mehr Schrauben ' +
          'aufgelegt werden, zeigt die Anzeige live deren Anzahl. ' +
          'Schneller als jedes Zählen von Hand.',
      },
      {
        heading: 'Beispiel Apotheke',
        body:
          'Tabletten verteilen: 50 Tabletten als Referenz auflegen, ' +
          'kalibrieren. Beim Befüllen einer Bestellung zeigt die App ' +
          'sofort, wie viele Tabletten in der Schale liegen — ohne ' +
          'einzeln nachzählen.',
      },
      {
        heading: 'Beispiel Versand',
        body:
          'Briefe oder kleine Päckchen mit gleichem Inhalt: 20 Stück ' +
          'auflegen, kalibrieren. Danach sehen Sie auf einen Blick, ob ' +
          'in der nächsten Charge alle Stück mit drin sind.',
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
          'und einer Notiz fest. Der Eintrag wandert in eine Datenbank ' +
          'auf dem Server und überlebt Backend-Neustarts.',
      },
      {
        heading: 'Sessions',
        body:
          'Mehrere Wägungen lassen sich unter einem Session-Namen ' +
          'gruppieren — etwa Charge-2026-05-07 oder Probe-Mehl. Im ' +
          'Feld oben rechts geben Sie den Session-Namen ein.',
      },
      {
        heading: 'Beispiel Labor',
        body:
          'Mehrere Proben einer Versuchsreihe wiegen, jede mit eindeu-' +
          'tiger Bezeichnung. Session = Versuch-2026-05-07, Label = ' +
          'Probe-A1, A2, A3 ... Am Ende exportieren Sie die Reihe als ' +
          'CSV und importieren sie in die Auswertungs-Software.',
      },
      {
        heading: 'Beispiel Bäckerei',
        body:
          'Tagesproduktion: jedes Brot wiegen und mit Sortenname ' +
          'erfassen. Sessionname pro Tag, Label = Sorte. Am Monatsende ' +
          'lassen sich Mittelwerte und Streuung pro Sorte auswerten.',
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
          'Download — geeignet für Import in Excel, Numbers, ' +
          'LibreOffice oder eine Auswertungssoftware.',
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

  copy: {
    id: 'copy',
    title: 'Werte kopieren und übernehmen',
    blocks: [
      {
        heading: 'Klick kopiert',
        body:
          'Tippen oder klicken Sie auf den großen Wägewert oder eine ' +
          'beliebige Kennzahl in der App — der Wert wandert direkt in ' +
          'die Zwischenablage. Eine kurze Meldung bestätigt das.',
      },
      {
        heading: 'Aktuellen Wert übernehmen',
        body:
          'Im Toleranz-, Netto- oder Zähl-Panel gibt es den Knopf ' +
          '"Aktuellen Wert übernehmen". Er setzt den aktuell live ' +
          'angezeigten Wägewert in das passende Eingabefeld — z.B. als ' +
          'Sollwert für die Toleranz oder als Tara-Gewicht.',
      },
      {
        heading: 'Wofür praktisch?',
        body:
          'Statt Werte abzulesen und einzutippen, einfach übernehmen — ' +
          'kein Tippfehler, keine Verzögerung. Funktioniert auch auf ' +
          'dem Touchpanel oder Tablet.',
      },
    ],
  },
};
