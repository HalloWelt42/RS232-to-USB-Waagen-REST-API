/**
 * Theme-Verwaltung mit Hell-, Dunkel- und Auto-Modus.
 *
 * Speichert die Auswahl des Anwenders im ``localStorage`` und reagiert
 * im Auto-Modus auf Änderungen der System-Einstellung
 * (``prefers-color-scheme``).
 */

export type Theme = 'auto' | 'dark' | 'light';

const STORAGE_KEY = 'waage.theme';

export class ThemeManager {
  private current: Theme = 'auto';
  private listeners: Set<(t: Theme, resolved: 'dark' | 'light') => void> = new Set();
  private mql: MediaQueryList | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
      if (stored === 'auto' || stored === 'dark' || stored === 'light') {
        this.current = stored;
      }
      this.mql = window.matchMedia('(prefers-color-scheme: dark)');
      this.mql.addEventListener('change', () => this.apply());
      this.apply();
    }
  }

  get(): Theme {
    return this.current;
  }

  resolved(): 'dark' | 'light' {
    if (this.current === 'auto') {
      return this.mql?.matches ? 'dark' : 'light';
    }
    return this.current;
  }

  set(theme: Theme): void {
    this.current = theme;
    localStorage.setItem(STORAGE_KEY, theme);
    this.apply();
  }

  cycle(): Theme {
    const order: Theme[] = ['auto', 'light', 'dark'];
    const next = order[(order.indexOf(this.current) + 1) % order.length];
    this.set(next);
    return next;
  }

  subscribe(fn: (t: Theme, resolved: 'dark' | 'light') => void): () => void {
    this.listeners.add(fn);
    fn(this.current, this.resolved());
    return () => this.listeners.delete(fn);
  }

  private apply(): void {
    const resolved = this.resolved();
    document.documentElement.dataset.theme = resolved;
    document.documentElement.dataset.themeChoice = this.current;
    for (const fn of this.listeners) {
      fn(this.current, resolved);
    }
  }
}

export const theme = new ThemeManager();
