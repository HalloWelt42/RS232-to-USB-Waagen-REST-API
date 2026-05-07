/**
 * History-API-Routing ohne Hash, mit Deeplinks zu Werkzeugen und
 * Hilfe-Fenstern.
 *
 * Pfad-Schema:
 *   /                   Dashboard
 *   /<tool>             Tool-Modus (wiegen, netto, count, tolerance, ...)
 *
 * Hilfe als Querystring-Liste (orthogonal zur Tool-Auswahl):
 *   ?help=wiegen,glossary    öffnet zwei Hilfe-Fenster
 *
 * Damit lassen sich aus E-Mails / Chats Deeplinks setzen wie
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
  'samples', 'differenz', 'sparkline', 'history',
  'tare', 'unit', 'light', 'copy', 'settings', 'donate',
  'architecture', 'disclaimer',
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

  /** Eine Hilfe öffnen (URL + Store synchronisieren). */
  openHelp(id: HelpId): void {
    if (!this.helpOpen.includes(id)) {
      this.write(this.activeTool, [...this.helpOpen, id]);
    }
  }

  /** Eine Hilfe schließen. */
  closeHelp(id: HelpId): void {
    if (this.helpOpen.includes(id)) {
      this.write(this.activeTool, this.helpOpen.filter(h => h !== id));
    }
  }

  /** Den vollen Hilfe-Stack der URL überschreiben. */
  setHelp(ids: HelpId[]): void {
    this.write(this.activeTool, ids);
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
    this.helpOpen = ids;
  }
}

export const route = new RouteState();
