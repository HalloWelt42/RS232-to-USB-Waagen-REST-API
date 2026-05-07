/**
 * Hash-Routing: erlaubt Deeplinks zu Tools (z.B. #/count).
 * Modus 'dashboard' ist der Eingangs-Bildschirm, 'tool' zeigt ein Werkzeug.
 */

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

class RouteState {
  mode = $state<'dashboard' | 'tool'>('dashboard');
  activeTool = $state<ToolKey | null>(null);

  init(): void {
    this.parse();
    window.addEventListener('hashchange', () => this.parse());
  }

  go(tool: ToolKey | null): void {
    if (tool === null) {
      window.location.hash = '';
    } else {
      window.location.hash = `#/${tool}`;
    }
  }

  private parse(): void {
    const hash = window.location.hash.replace(/^#\/?/, '').trim();
    if (hash && (TOOL_KEYS as readonly string[]).includes(hash)) {
      this.mode = 'tool';
      this.activeTool = hash as ToolKey;
    } else {
      this.mode = 'dashboard';
      this.activeTool = null;
    }
  }
}

export const route = new RouteState();
