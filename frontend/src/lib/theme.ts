/** Theme-Manager: auto / dark / light, persistiert in localStorage. */

export type Theme = 'auto' | 'dark' | 'light';
const KEY = 'waage.theme';

export class ThemeManager {
  private current: Theme = 'auto';
  private listeners: Set<(t: Theme, resolved: 'dark' | 'light') => void> = new Set();
  private mql: MediaQueryList | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(KEY) as Theme | null;
      if (stored === 'auto' || stored === 'dark' || stored === 'light') this.current = stored;
      this.mql = window.matchMedia('(prefers-color-scheme: dark)');
      this.mql.addEventListener('change', () => this.apply());
      this.apply();
    }
  }

  get(): Theme { return this.current; }
  resolved(): 'dark' | 'light' {
    if (this.current === 'auto') return this.mql?.matches ? 'dark' : 'light';
    return this.current;
  }
  set(t: Theme): void {
    this.current = t;
    localStorage.setItem(KEY, t);
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
    const r = this.resolved();
    document.documentElement.dataset.theme = r;
    document.documentElement.dataset.themeChoice = this.current;
    for (const fn of this.listeners) fn(this.current, r);
  }
}

export const theme = new ThemeManager();
