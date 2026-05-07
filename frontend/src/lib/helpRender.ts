/**
 * Rendert einen Hilfe-Text mit Platzhaltern und Cross-Link-Markup
 * in HTML-Fragmente, die der HelpLayer anzeigen kann.
 *
 *   Eingabe:  Aktives Modell <strong>{{modelName}}</strong> mit
 *             [[tool:settings|Einstellungen]] und [[help:wiegen|Wiegen]].
 *   Ausgabe:  Aktives Modell <strong>G&G PLC-6000</strong> mit
 *             <button data-route-tool="settings">Einstellungen</button>
 *             und <button data-route-help="wiegen">Wiegen</button>.
 *
 * Cross-Links werden als spezielle Buttons mit `data-route-*`
 * Attributen gerendert. Der HelpLayer fängt Klicks darauf ab und
 * leitet via `route.go()` / `route.openHelp()` weiter — kein
 * Page-Reload, sondern saubere SPA-Navigation.
 */

import type { ScaleModel } from './types';
import { fillTemplate } from './help';

/** Schätzt eine sinnvolle Mindest-Referenzmenge für die Stückzählung. */
function minPiecesUnder1g(resolutionG: number): number {
  if (!Number.isFinite(resolutionG) || resolutionG <= 0) return 20;
  // Faustregel: mindestens so viele Stück, dass das Gesamt-Gewicht klar
  // über der Auflösung liegt. Bei 0,1 g => 20, bei 0,01 g => 5, bei 1 g => 50.
  return Math.max(5, Math.min(50, Math.round(2 / resolutionG)));
}

function formatGramsForHelp(g: number): string {
  if (g >= 1000) return `${(g / 1000).toString().replace('.', ',')} kg`;
  return `${g.toString().replace('.', ',')} g`;
}

/** Modell-bezogene Variablen für die Platzhalter-Ersetzung. */
export function buildHelpVars(m: ScaleModel): Record<string, string | number> {
  return {
    modelName: m.manufacturer && (m.series || m.name)
      ? `${m.manufacturer} ${m.series ? m.series : ''}${m.series && m.name ? '-' : ''}${m.name.split(' ')[0]}`.trim()
      : (m.name || 'Waage'),
    maxG: formatGramsForHelp(m.max_g),
    resolutionG: formatGramsForHelp(m.resolution_g),
    minPiecesUnder1g: minPiecesUnder1g(m.resolution_g),
  };
}

/**
 * Wandelt `[[tool:KEY|Label]]` und `[[help:KEY|Label]]` in
 * Button-Tags mit `data-route-*` Attributen.
 */
function replaceCrossLinks(html: string): string {
  return html.replace(
    /\[\[(tool|help):([a-z]+)\|([^\]]+)\]\]/g,
    (_m, kind: string, key: string, label: string) => {
      const attr = kind === 'tool' ? 'data-route-tool' : 'data-route-help';
      const cls = kind === 'tool' ? 'xlink xlink-tool' : 'xlink xlink-help';
      return `<button type="button" class="${cls}" ${attr}="${key}">${label}</button>`;
    },
  );
}

/**
 * Komplettes Rendering: Platzhalter ersetzen, dann Cross-Links in
 * Button-Tags überführen.
 */
export function renderHelpBody(text: string, vars: Record<string, string | number>): string {
  return replaceCrossLinks(fillTemplate(text, vars));
}
