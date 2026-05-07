/**
 * History-API-Routing ohne Hash, mit Deeplinks zu Werkzeugen und
 * Hilfe-Fenstern.
 *
 * Pfad-Schema:
 *   /                   Dashboard
 *   /<tool>             Tool-Modus (wiegen, netto, count, tolerance, ...)
 *
 * Hilfe als Querystring (orthogonal zur Tool-Auswahl):
 *   ?help=wiegen    öffnet das Hilfe-Fenster „Wiegen"
 *
 * Aus Konsistenzgründen ist immer nur eine Hilfe gleichzeitig offen —
 * jeder neue Klick auf einen Info-Knopf oder einen Cross-Link
 * überschreibt das aktuelle Fenster. Damit lassen sich aus E-Mails /
 * Chats Deeplinks setzen wie
 *   https://waage.example/count?help=count
 *   https://waage.example/?help=disclaimer
 *
 * Voraussetzung am Server: alle nicht-statischen Pfade liefern die
 * SPA-`index.html` aus (siehe nginx.conf / Vite-History-Fallback).
 */

import type { HelpId } from './help';

export type ToolKey =
  | 'wiegen'
  | 'netto'
  | 'count'
  | 'tolerance'
  | 'samples'
  | 'differenz'
  | 'help'
  | 'settings'
  | 'donate';

export const TOOL_KEYS: readonly ToolKey[] = [
  'wiegen', 'netto', 'count', 'tolerance',
  'samples', 'differenz', 'help', 'settings', 'donate',
] as const;

const HELP_IDS: readonly HelpId[] = [
  'overview', 'glossary', 'wiegen', 'netto', 'count', 'tolerance',
  'samples', 'differenz', 'sparkline', 'history', 'containers',
  'tare', 'unit', 'light', 'copy', 'settings', 'donate',
  'architecture', 'disclaimer', 'tolerances',
] as const;

class RouteState {
  mode = $state<'dashboard' | 'tool'>('dashboard');
  activeTool = $state<ToolKey | null>(null);
  helpOpen = $state<HelpId[]>([]);

  init(): void {
    this.parse();
    window.addEventListener('popstate', () => this.parse());
  }

  /** Werkzeug wechseln; bestehende Hilfe-Fenster bleiben in der URL. */
  go(tool: ToolKey | null): void {
    this.write(tool, this.helpOpen);
  }

  /**
   * Eine Hilfe öffnen — ersetzt eine bereits offene Hilfe.
   *
   * Es ist immer höchstens ein Hilfe-Fenster gleichzeitig sichtbar:
   * der Klick auf einen Info-Knopf oder einen Cross-Link überschreibt
   * den aktuellen Hilfe-Inhalt. Ist die ID schon offen, passiert nichts.
   */
  openHelp(id: HelpId): void {
    if (this.helpOpen.length === 1 && this.helpOpen[0] === id) return;
    this.write(this.activeTool, [id]);
  }

  /** Die aktuelle Hilfe schließen. */
  closeHelp(id: HelpId): void {
    if (this.helpOpen.includes(id)) {
      this.write(this.activeTool, []);
    }
  }

  /** Hilfe-Stack der URL überschreiben — auf maximal eine ID begrenzt. */
  setHelp(ids: HelpId[]): void {
    this.write(this.activeTool, ids.slice(0, 1));
  }

  // ------------------------------------------------------------------

  private write(tool: ToolKey | null, help: HelpId[]): void {
    const path = tool ? `/${tool}` : '/';
    const search = help.length > 0 ? `?help=${help.join(',')}` : '';
    const target = `${path}${search}`;
    if (window.location.pathname + window.location.search !== target) {
      window.history.pushState({}, '', target);
    }
    this.mode = tool ? 'tool' : 'dashboard';
    this.activeTool = tool;
    this.helpOpen = help;
  }

  private parse(): void {
    const path = window.location.pathname.replace(/^\/+/, '').replace(/\/+$/, '');
    if (path && (TOOL_KEYS as readonly string[]).includes(path)) {
      this.mode = 'tool';
      this.activeTool = path as ToolKey;
    } else {
      this.mode = 'dashboard';
      this.activeTool = null;
    }

    const search = new URLSearchParams(window.location.search);
    const helpParam = search.get('help') ?? '';
    const ids: HelpId[] = helpParam
      .split(',')
      .map(s => s.trim())
      .filter((s): s is HelpId => (HELP_IDS as readonly string[]).includes(s));
    // Es ist immer höchstens eine Hilfe gleichzeitig offen — älterer
    // Deeplink mit mehreren IDs wird auf die erste reduziert.
    this.helpOpen = ids.slice(0, 1);
  }
}

export const route = new RouteState();
