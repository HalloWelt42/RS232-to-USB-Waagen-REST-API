/**
 * Hilfe-Inhalte. Texte mind. 18 px lesbar (siehe Styles), Zahlen
 * werden im Markup mit <strong> hervorgehoben.
 *
 * Die Texte sind modell-neutral — modellspezifische Werte erscheinen
 * als Platzhalter und werden zur Laufzeit aus dem `modelStore`
 * ersetzt:
 *   {{maxG}}        Maximalkapazität in Gramm  (z.B. „6000 g")
 *   {{resolutionG}} Auflösung in Gramm        (z.B. „0,1 g")
 *   {{modelName}}   Anzeigename des Modells   (z.B. „G&G PLC-6000")
 *   {{minPiecesUnder1g}} empfohlene Mindest-Referenzmenge bei
 *                        Stückzählung kleiner Teile
 *
 * Cross-Links zu anderen Werkzeugen oder Hilfe-Eintragungen sind
 * mit doppelten eckigen Klammern markiert und werden vom HelpLayer
 * in PWA-konforme Buttons umgewandelt — kein Page-Reload:
 *   [[tool:count|Stückzählung]]   öffnet das Werkzeug
 *   [[help:wiegen|Wiegen]]        öffnet ein Hilfe-Fenster
 */

export type HelpId =
  | 'overview' | 'glossary' | 'wiegen' | 'netto' | 'count' | 'tolerance'
  | 'samples' | 'differenz' | 'sparkline' | 'history' | 'containers'
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

/**
 * Locale-spezifischer Hilfe-Baum. Sprache wird vom HelpLayer beim
 * Lesen anhand der aktuellen i18n-Locale ausgewählt.
 */
type HelpTree = Record<HelpId, HelpEntry>;

const helpDe: HelpTree = {
  overview: {
    id: 'overview',
    title: 'Willkommen',
    blocks: [
      {
        heading: 'Was ist das hier?',
        body:
          'Eine Live-Anzeige für Ihre Präzisionswaage mit Werkzeugen für ' +
          '[[tool:tolerance|Qualitätskontrolle]], [[tool:count|Stückzählung]], ' +
          '[[tool:netto|Behälterwägung]] und Mess-Protokoll. Die Waage wird über ' +
          'RS232 ausgelesen und ihre Werte erscheinen sofort in der Anzeige.',
      },
      {
        heading: 'Aktuelles Modell',
        body:
          'Es ist <strong>{{modelName}}</strong> mit max. <strong>{{maxG}}</strong> ' +
          'und einer Auflösung von <strong>{{resolutionG}}</strong> aktiv. ' +
          'Eine andere Waage wählen Sie unter [[tool:settings|Einstellungen]].',
      },
      {
        heading: 'Aufbau',
        body:
          'Links steht die Live-Anzeige der Waage, rechts die verfügbaren ' +
          'Werkzeuge als Karten. Klick auf eine Karte öffnet das Werkzeug; ' +
          'die Live-Anzeige bleibt sichtbar. Eine Tab-Leiste oben erlaubt ' +
          'das Wechseln zwischen Werkzeugen.',
      },
      {
        heading: 'Hilfe immer dabei',
        body:
          'In jedem Bereich gibt es einen <strong>blauen Info-Knopf</strong>. ' +
          'Das Hilfe-Fenster lässt sich frei verschieben und in der Größe ändern. ' +
          'Mehrere Fenster können parallel offen sein.',
      },
      {
        heading: 'Wichtig',
        body:
          'Die Software ist <strong>nicht eichfähig</strong> — siehe ' +
          '[[help:disclaimer|Haftungsausschluss]].',
      },
    ],
  },

  glossary: {
    id: 'glossary',
    title: 'Glossar',
    blocks: [
      { heading: 'Brutto', body: 'Gesamtgewicht — Behälter plus Inhalt zusammen.' },
      { heading: 'Tara', body: 'Gewicht des leeren Behälters. Wer Tara speichert, sieht nur noch das Netto. Werkzeug: [[tool:netto|Behälter wiegen]].' },
      { heading: 'Netto', body: 'Brutto minus Tara — nur der Inhalt.' },
      { heading: 'Stückgewicht', body: 'Gewicht eines einzelnen Teils. Beispiel: <strong>100</strong> Schrauben wiegen <strong>250 g</strong> → <strong>2,5 g</strong> pro Stück. Werkzeug: [[tool:count|Stückzählung]].' },
      { heading: 'Stable / Stabil', body: 'Wert hat sich beruhigt und schwankt nicht mehr.' },
      { heading: 'Toleranz', body: 'Erlaubte Abweichung vom Sollwert. Bei <strong>50 g ± 2 g</strong> ist alles zwischen <strong>48 g</strong> und <strong>52 g</strong> in Ordnung. Werkzeug: [[tool:tolerance|Qualitätskontrolle]].' },
      { heading: 'Auflösung', body: 'Kleinster Anzeigeschritt der Waage. Aktuelles Modell: <strong>{{resolutionG}}</strong>.' },
      { heading: 'Maximalkapazität', body: 'Höchste Last, die die Waage messen kann. Aktuelles Modell: <strong>{{maxG}}</strong>.' },
      { heading: 'Session', body: 'Name für eine Mess-Reihe — gruppiert mehrere Wägungen unter einem Etikett. Werkzeug: [[tool:samples|Werte erfassen]].' },
      { heading: 'Mittelwert / Standardabweichung', body: 'Durchschnitt mehrerer Wägungen und ihre Streuung darum herum.' },
    ],
  },

  wiegen: {
    id: 'wiegen', title: 'Wiegen',
    blocks: [
      { heading: 'Funktion', body: 'Reines Ablesen des Live-Werts. Klick auf den großen Wert kopiert ihn in die Zwischenablage.' },
      { heading: 'Untermodi', body: 'Frei (nur ablesen) oder mit Sollwert-Hinweis: gewünschtes Gewicht eintragen, beim Auflegen sieht man wie nahe man dran ist.' },
      { heading: 'Reichweite', body: 'Aktives Modell <strong>{{modelName}}</strong> — bis maximal <strong>{{maxG}}</strong> bei <strong>{{resolutionG}}</strong> Auflösung.' },
      { heading: 'Verwandt', body: 'Tara setzen siehe [[help:tare|Auf Null setzen]], Einheit wechseln siehe [[help:unit|Maßeinheit]].' },
    ],
  },

  netto: {
    id: 'netto', title: 'Netto und Tara',
    blocks: [
      { heading: 'Was kann das?', body: 'Speichert ein Behältergewicht (Tara) in der Software und zeigt fortan nur den Inhalt — Netto = Brutto − Tara.' },
      { heading: 'Variante 1: Behälter aufstellen', body: 'Leeres Gefäß auf die Waage, „Tara einfrieren". Ab jetzt Netto-Anzeige.' },
      { heading: 'Variante 2: Tara als Zahl', body: 'Behältergewicht direkt eintragen, z.B. <strong>23,4 g</strong>. „Setzen" speichert es.' },
      { heading: 'Beispiel Bäckerei', body: 'Schüssel auflegen, Tara — Mehl bis <strong>500 g</strong>, Wasser bis <strong>250 g</strong>. Alles im selben Gefäß abgewogen, ohne zu rechnen.' },
      { heading: 'Mehrfach-Tara?', body: 'Wenn Sie Schichten stapeln möchten (mehrere Behälter übereinander), nutzen Sie [[tool:differenz|Differenz-Wiegen]].' },
      { heading: 'Behälter-Bibliothek', body: 'Häufig verwendete Gefäße einmal anlegen und beim Wiegen aus einer Liste auswählen. Siehe [[help:containers|Behälter-Bibliothek]].' },
    ],
  },

  count: {
    id: 'count', title: 'Stückzählung',
    blocks: [
      { heading: 'Funktionsweise', body: 'Mit bekannter Anzahl gleicher Teile kalibrieren. Die App rechnet das Stückgewicht aus und zeigt für jedes neue Gewicht die Anzahl.' },
      { heading: 'Vorlagen verwalten', body: 'Vorlagen sind frei verwaltbar — anlegen, bearbeiten, löschen. Hover auf einer Vorlage blendet die kleinen Symbole zum Bearbeiten und Löschen ein. Eine Vorlage wendet ein gespeichertes Stückgewicht an, ohne dass man neu kalibrieren muss.' },
      { heading: 'Wiederkehrendes', body: 'Nach dem Kalibrieren erscheint <strong>„Als Vorlage speichern"</strong> — wer regelmäßig dieselbe Schrauben-Sorte oder Tabletten-Charge zählt, hält das Stückgewicht so dauerhaft fest. Beim nächsten Mal reicht ein Klick auf die Vorlage.' },
      { heading: 'Beispiel Werkstatt', body: '<strong>10</strong> Schrauben auflegen, <strong>10</strong> eingeben, kalibrieren. Beim weiteren Auflegen sieht man live die Stückzahl. Mit „Als Vorlage speichern" landet die Sorte in der Liste.' },
      { heading: 'Beispiel Apotheke', body: '<strong>50</strong> Tabletten als Referenz. Beim Befüllen einer Bestellung zeigt die App die aktuelle Anzahl.' },
      { heading: 'Genauigkeit', body: 'Mehr Referenzteile = genauer. Bei Teilen unter <strong>1 g</strong> mindestens <strong>{{minPiecesUnder1g}}</strong> Stück, sonst kippt die Anzeige wegen der Auflösung von <strong>{{resolutionG}}</strong>.' },
    ],
  },

  tolerance: {
    id: 'tolerance', title: 'Qualitätskontrolle',
    blocks: [
      { heading: 'Was ist das?', body: 'Sie geben einen Sollwert mit Toleranzgrenzen vor. Eine große Ampel zeigt grün, gelb oder rot — je nach Abweichung.' },
      { heading: 'Beispiel Apotheke', body: 'Rezeptur verlangt <strong>2,000 g</strong> ± <strong>0,05 g</strong>. Beim Einwiegen reagiert die Ampel sofort — kein Rechnen, kein zweiter Blick. (Voraussetzung: die Waage löst fein genug auf.)' },
      { heading: 'Beispiel Verpackung', body: 'Tütchen mit <strong>50 g</strong> ± <strong>2 g</strong>. Alles zwischen <strong>48 g</strong> und <strong>52 g</strong> ist grün.' },
      { heading: 'Tipp Mindestmenge', body: 'Wenn Sie nur Untergewicht prüfen wollen, setzen Sie Tol+ auf einen sehr großen Wert.' },
      { heading: 'Verwandt', body: 'Werte erfassen siehe [[tool:samples|Erfassen]].' },
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
      { heading: 'Einfache Tara?', body: 'Wenn Sie nur eine Schicht brauchen, ist [[tool:netto|Behälter wiegen]] schneller.' },
      { heading: 'Behälter-Bibliothek', body: 'Häufig benutzte Gefäße einmal anlegen — siehe [[help:containers|Behälter-Bibliothek]]. Auswahl stapelt das Gewicht direkt als neue Schicht.' },
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
    blocks: [{ heading: 'Hinweis', body: 'In dieser Version ist der Mini-Verlauf durch das [[help:history|Messprotokoll]] ersetzt.' }],
  },

  tare: {
    id: 'tare', title: 'Auf Null setzen (Tara)',
    blocks: [
      { heading: 'Funktion', body: 'Setzt den aktuellen Anzeigewert der Waage auf Null. Entspricht der Tara-Taste an der Waage.' },
      { heading: 'Wozu?', body: 'Behälter aufstellen, Tara, Inhalt füllen — die Anzeige zeigt direkt das Netto.' },
      { heading: 'Software-Tara', body: 'Wer die Tara nicht in der Hardware löschen will, nutzt [[tool:netto|Behälter wiegen]].' },
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
      { heading: 'Übernehmen', body: 'In [[tool:tolerance|Toleranz]], [[tool:netto|Behälter]] und [[tool:count|Zählung]] gibt es Knöpfe „aktuellen Wert übernehmen". Spart Tippen, vermeidet Tippfehler.' },
    ],
  },

  settings: {
    id: 'settings', title: 'Einstellungen',
    blocks: [
      { heading: 'Modell', body: 'Wählen Sie Ihre Waage aus der Liste. Das Modell beeinflusst Anzeige-Einheiten, Maximal- und Auflösungswerte. Aktiv: <strong>{{modelName}}</strong>.' },
      { heading: 'Theme', body: 'Hell, Dunkel oder Automatisch (folgt der Systemeinstellung).' },
      { heading: 'Sprache', body: 'DE oder EN — Auswahl bleibt zwischen Sitzungen erhalten.' },
      { heading: 'Anschluss', body: 'Serieller Port und Baudrate. Beim Default „auto" findet die App den USB-Serial-Adapter selbst.' },
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

  containers: {
    id: 'containers', title: 'Behälter-Bibliothek',
    blocks: [
      { heading: 'Wofür?', body: 'Häufig benutzte Gefäße einmal anlegen — Name plus Gewicht. Bei [[tool:netto|Behälter wiegen]] oder [[tool:differenz|Differenz-Wiegen]] wählt man sie aus einer Liste, statt jedes Mal den Tara-Wert neu einzutragen.' },
      { heading: 'Anlegen', body: 'Gefäß auf die Waage stellen, „Aktuelles Gewicht übernehmen" — der Wert landet im Eingabefeld. Name vergeben (z.B. „Erlenmeyer 100 ml"), optional eine Notiz, „Anlegen". Default-Gewicht ist <strong>0 g</strong>.' },
      { heading: 'Bearbeiten und Löschen', body: 'Klick auf das Stift-Symbol bei einem Eintrag öffnet das Formular mit den vorhandenen Werten. Das Mülleimer-Symbol löscht den Behälter nach einer Sicherheitsabfrage.' },
      { heading: 'Beispiel Labor', body: 'Fünf Standardgefäße — Becher S, M, L, Kolben 100 ml, Kolben 250 ml. Einmal angelegt, beim nächsten Wiegen aus dem Drop-down wählen. Die App zieht das Behältergewicht automatisch ab.' },
    ],
  },
};

const helpEn: HelpTree = {
  overview: {
    id: 'overview', title: 'Welcome',
    blocks: [
      { heading: 'What is this?', body: 'A live display for your precision scale with tools for [[tool:tolerance|quality control]], [[tool:count|piece counting]], [[tool:netto|tare-and-net weighing]] and a measurement log. The scale is read out via RS232 and its values appear instantly in the display.' },
      { heading: 'Active model', body: 'Currently <strong>{{modelName}}</strong> with a maximum of <strong>{{maxG}}</strong> and a resolution of <strong>{{resolutionG}}</strong>. To choose a different scale, see [[tool:settings|Settings]].' },
      { heading: 'Layout', body: 'The live display sits permanently on the left, the available tools as cards on the right. Click a card to open the tool — the live value stays visible. A tab bar at the top lets you switch between tools.' },
      { heading: 'Help is always there', body: 'Each section has a <strong>blue info button</strong>. Help windows can be moved freely and resized. Several windows can be open at the same time.' },
      { heading: 'Important', body: 'The software is <strong>not legal-for-trade</strong> — see [[help:disclaimer|Disclaimer]].' },
    ],
  },
  glossary: {
    id: 'glossary', title: 'Glossary',
    blocks: [
      { heading: 'Gross', body: 'Total weight — container plus content together.' },
      { heading: 'Tare', body: 'Weight of the empty container. Storing a tare gives a net-only display. Tool: [[tool:netto|Tare / Net]].' },
      { heading: 'Net', body: 'Gross minus tare — the content alone.' },
      { heading: 'Piece weight', body: 'Weight of a single part. Example: <strong>100</strong> screws weigh <strong>250 g</strong> → <strong>2.5 g</strong> per piece. Tool: [[tool:count|Piece counting]].' },
      { heading: 'Stable', body: 'The value has settled and no longer fluctuates.' },
      { heading: 'Tolerance', body: 'Allowed deviation from the target. With <strong>50 g ± 2 g</strong>, anything between <strong>48 g</strong> and <strong>52 g</strong> is OK. Tool: [[tool:tolerance|Quality control]].' },
      { heading: 'Resolution', body: 'Smallest display step of the scale. Active model: <strong>{{resolutionG}}</strong>.' },
      { heading: 'Maximum capacity', body: 'Highest load the scale can measure. Active model: <strong>{{maxG}}</strong>.' },
      { heading: 'Session', body: 'Name for a measurement series — groups several weighings under a label. Tool: [[tool:samples|Capture values]].' },
      { heading: 'Mean / standard deviation', body: 'Average of several weighings and their spread.' },
    ],
  },
  wiegen: {
    id: 'wiegen', title: 'Weighing',
    blocks: [
      { heading: 'Function', body: 'Pure reading of the live value. Click on the large value to copy it to the clipboard.' },
      { heading: 'Submodes', body: 'Free (read only) or with target hint: enter the desired weight, see how close you are while loading.' },
      { heading: 'Range', body: 'Active model <strong>{{modelName}}</strong> — up to <strong>{{maxG}}</strong> at <strong>{{resolutionG}}</strong> resolution.' },
      { heading: 'Related', body: 'Set tare see [[help:tare|Set to zero]], switch unit see [[help:unit|Unit]].' },
    ],
  },
  netto: {
    id: 'netto', title: 'Tare / Net',
    blocks: [
      { heading: 'What does it do?', body: 'Stores a container weight (tare) in the software and shows only the content from then on — net = gross − tare.' },
      { heading: 'Variant 1: place the container', body: 'Empty vessel on the scale, „freeze tare". From now on net display.' },
      { heading: 'Variant 2: tare as a number', body: 'Enter the container weight directly, e.g. <strong>23.4 g</strong>. „Set" stores it.' },
      { heading: 'Bakery example', body: 'Bowl on, tare — flour up to <strong>500 g</strong>, water up to <strong>250 g</strong>. Everything weighed in the same vessel without doing arithmetic.' },
      { heading: 'Multiple tares?', body: 'For stacking layers (multiple containers on top of each other), use [[tool:differenz|Differential weighing]].' },
    ],
  },
  count: {
    id: 'count', title: 'Piece counting',
    blocks: [
      { heading: 'How it works', body: 'Calibrate with a known number of identical parts. The app computes the piece weight and shows the count for every new weight.' },
      { heading: 'Manage templates', body: 'Templates are fully manageable — add, edit, delete. Hover a template to reveal the small edit and delete icons. Picking a template applies a stored piece weight without re-calibrating.' },
      { heading: 'Recurring items', body: 'After calibration, <strong>„Save as template"</strong> appears — for those who regularly count the same screw type or tablet batch, this stores the piece weight permanently. Next time, one click on the template is enough.' },
      { heading: 'Workshop example', body: 'Place <strong>10</strong> screws, enter <strong>10</strong>, calibrate. Loading more parts shows the live count. „Save as template" puts the variant into the list.' },
      { heading: 'Pharmacy example', body: '<strong>50</strong> tablets as reference. While filling an order the app shows the current count.' },
      { heading: 'Accuracy', body: 'More reference parts = more accurate. For parts below <strong>1 g</strong>, use at least <strong>{{minPiecesUnder1g}}</strong> pieces — otherwise the display jumps because of the <strong>{{resolutionG}}</strong> resolution.' },
    ],
  },
  tolerance: {
    id: 'tolerance', title: 'Quality control',
    blocks: [
      { heading: 'What is this?', body: 'Specify a target with tolerance limits. A large traffic light shows green, yellow or red depending on deviation.' },
      { heading: 'Pharmacy example', body: 'Recipe requires <strong>2.000 g</strong> ± <strong>0.05 g</strong>. The light reacts immediately — no calculation, no second look. (Provided the scale resolves finely enough.)' },
      { heading: 'Packaging example', body: 'Bag of <strong>50 g</strong> ± <strong>2 g</strong>. Anything between <strong>48 g</strong> and <strong>52 g</strong> is green.' },
      { heading: 'Min-only tip', body: 'If you only want to check for under-weight, set tol+ to a very large number.' },
      { heading: 'Related', body: 'Capture values see [[tool:samples|Capture]].' },
    ],
  },
  samples: {
    id: 'samples', title: 'Capture values',
    blocks: [
      { heading: 'What gets stored?', body: 'Current weight with label and note, in a database — survives backend restarts.' },
      { heading: 'Sessions', body: 'Group several weighings under one session name, e.g. „Batch-2026-05-07".' },
      { heading: 'Statistics', body: 'Count, min, max, mean, standard deviation and sum computed automatically.' },
      { heading: 'Lab example', body: 'Series with sample-A1, A2, A3 … CSV export delivers the row as a file for analysis.' },
    ],
  },
  differenz: {
    id: 'differenz', title: 'Differential weighing',
    blocks: [
      { heading: 'Multi-tare', body: 'Stack several tare layers. Content = gross minus sum of all tares.' },
      { heading: 'Example', body: 'Place container, „as tare" — <strong>53 g</strong>. Place carrier, „as tare" — another <strong>20 g</strong>. The actual content shows up as net, without the containers being weighed in.' },
      { heading: 'Manage layers', body: 'Each layer in a list — individual tares can be removed without losing the rest.' },
      { heading: 'Single tare?', body: 'For just one layer, [[tool:netto|Tare / Net]] is faster.' },
    ],
  },
  history: {
    id: 'history', title: 'Measurement log',
    blocks: [
      { heading: 'What is this?', body: 'A list of value <strong>changes</strong>: every new load, every removal, every tare event becomes one entry with difference and resulting value.' },
      { heading: 'Why not all frames?', body: 'A still scale delivers the same value many times per second — that would not help. The list reacts only to real changes.' },
    ],
  },
  sparkline: {
    id: 'sparkline', title: 'Mini timeline',
    blocks: [{ heading: 'Note', body: 'In this version the mini timeline has been replaced by the [[help:history|measurement log]].' }],
  },
  tare: {
    id: 'tare', title: 'Set to zero (Tare)',
    blocks: [
      { heading: 'Function', body: 'Resets the scale display to zero — equivalent to the tare button on the device.' },
      { heading: 'What for?', body: 'Place container, tare, fill content — the display shows the net directly.' },
      { heading: 'Software tare', body: 'If you do not want to wipe the hardware tare, use [[tool:netto|Tare / Net]].' },
    ],
  },
  unit: {
    id: 'unit', title: 'Switch unit',
    blocks: [
      { heading: 'Function', body: 'The scale switches between grams, kilograms, carats, ounces and pounds — depending on model.' },
      { heading: 'Tip', body: 'The app always computes internally in grams.' },
    ],
  },
  light: {
    id: 'light', title: 'Backlight',
    blocks: [
      { heading: 'Function', body: 'Turns the backlight on the scale display on or off.' },
      { heading: 'Diagnostics', body: 'When the backlight toggles, your commands reach the scale — a good function test.' },
    ],
  },
  copy: {
    id: 'copy', title: 'Copy values',
    blocks: [
      { heading: 'Click copies', body: 'Tap or click the large weight value. The value is copied to the clipboard; a brief hint confirms.' },
      { heading: 'Take over', body: 'In [[tool:tolerance|Tolerance]], [[tool:netto|Tare]] and [[tool:count|Counting]] there are „take current value" buttons. Saves typing, avoids typos.' },
    ],
  },
  settings: {
    id: 'settings', title: 'Settings',
    blocks: [
      { heading: 'Model', body: 'Pick your scale from the list. The model affects display units, maximum and resolution. Active: <strong>{{modelName}}</strong>.' },
      { heading: 'Theme', body: 'Light, dark or automatic (follows system setting).' },
      { heading: 'Language', body: 'DE or EN — choice persists across sessions.' },
      { heading: 'Connection', body: 'Serial port and baudrate. With default „auto" the app finds the USB-serial adapter on its own.' },
      { heading: 'Polling', body: 'How often the app sends the print command to the scale — default <strong>0.5 s</strong>.' },
    ],
  },
  donate: {
    id: 'donate', title: 'Thanks',
    blocks: [
      { heading: 'What is this?', body: 'Open source, but intended for <strong>private, non-commercial</strong> use only. If you like the application, you can support me via Ko-fi or crypto.' },
      { heading: 'License', body: 'CC BY-NC-ND 4.0 with additional terms — private modification and private forks allowed, no commercial use and no publication of modified versions. Full text in the repository under <code>LICENSE</code>.' },
      { heading: 'Crypto', body: 'Three cards — BTC, DOGE, ETH. Click shows the QR code and the address. One-click copy button.' },
    ],
  },
  architecture: {
    id: 'architecture', title: 'Scale ↔ App architecture',
    blocks: [
      { heading: 'What is separated?', body: 'The <strong>scale module</strong> (endpoint /scale/*) does only the readout and control of the scale. It can run on its own — third-party systems can integrate it without the app layer.' },
      { heading: 'What is optional?', body: 'The <strong>app module</strong> (/app/*) provides tolerance, net, counting, capture, differential and the measurement log — UI conveniences. Requires the scale module.' },
      { heading: 'Consequence', body: 'For just the weight in your workflow, only /scale/* is needed. UI updates to /app/* leave the scale module untouched.' },
    ],
  },
  disclaimer: {
    id: 'disclaimer', title: 'Disclaimer',
    blocks: [
      { heading: 'No warranty', body: 'This software is provided free of charge — <strong>without warranty</strong> as to accuracy, completeness or timeliness. No fitness for a particular purpose is assured.' },
      { heading: 'Not legal-for-trade', body: 'The software is <strong>not a legal-for-trade measurement system</strong>. For sale by weight, official quantity declarations, medical dosing with statutory tolerances, customs or tax-relevant data it <strong>may not be used</strong>.' },
      { heading: 'No liability', body: 'To the extent permitted by law, any liability for indirect damages, lost profits, loss of data or consequential damages is excluded. Liability for injury to life, body or health, or for gross negligence or wilful misconduct, remains unaffected.' },
      { heading: 'User responsibility', body: 'The user alone is responsible for proper use, regular verification with calibrated reference weights and plausibility-checking the values. Full text: <code>DISCLAIMER.md</code> in the repo.' },
    ],
  },
  containers: {
    id: 'containers', title: 'Container library',
    blocks: [
      { heading: 'What is this?', body: 'Pre-define frequently used vessels — name plus weight. In [[tool:netto|Tare / Net]] or [[tool:differenz|Differential weighing]] you pick them from a list instead of entering the tare value every time.' },
      { heading: 'Add', body: 'Place the vessel on the scale, hit „take current weight" — the value lands in the form. Give it a name (e.g. „Erlenmeyer 100 ml"), an optional note, „Add". Default weight is <strong>0 g</strong>.' },
      { heading: 'Edit and delete', body: 'Click the pen icon on an entry to open the form with current values. The trash icon deletes after a confirmation prompt.' },
      { heading: 'Lab example', body: 'Five standard vessels — beaker S/M/L, flask 100 ml, flask 250 ml. Defined once, picked from the drop-down for every following weighing. The app subtracts the container weight automatically.' },
    ],
  },
};

/** Locale-spezifische Hilfe-Bäume — werden im Layer reaktiv ausgewählt. */
export const helpEntriesByLang: Record<'de' | 'en', HelpTree> = { de: helpDe, en: helpEn };

/**
 * Default-Export für Suche/Index/Search-Test: deutsche Bäume mit
 * unaufgelösten Platzhaltern. Konsumenten, die Texte rendern, gehen
 * über `getHelpEntries(lang)`.
 */
export const helpEntries: HelpTree = helpDe;

export function getHelpEntries(lang: 'de' | 'en'): HelpTree {
  return helpEntriesByLang[lang] ?? helpDe;
}

/** Substituiert {{platzhalter}} im Text. */
export function fillTemplate(
  text: string,
  vars: Record<string, string | number>,
): string {
  return text.replace(/\{\{(\w+)\}\}/g, (_m, key) =>
    key in vars ? String(vars[key]) : `{{${key}}}`,
  );
}
