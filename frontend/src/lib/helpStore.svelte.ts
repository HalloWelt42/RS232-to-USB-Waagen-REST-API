/**
 * Globaler Speicher für offene Hilfe-Fenster.
 *
 * Mehrere Fenster können parallel offen sein, jedes mit eigener
 * Position. Die Fenster sind frei verschiebbar; ihre Positionen werden
 * pro Hilfe-Bereich im ``localStorage`` gemerkt.
 */

import type { HelpId } from './help';

export interface OpenWindow {
  id: HelpId;
  x: number;
  y: number;
  z: number;
}

const POS_KEY = 'waage.help.positions';

interface SavedPositions {
  [id: string]: { x: number; y: number };
}

class HelpStore {
  private windows = $state<OpenWindow[]>([]);
  private nextZ = 100;

  open(id: HelpId): void {
    const existing = this.windows.find((w) => w.id === id);
    if (existing) {
      existing.z = ++this.nextZ;
      return;
    }
    const saved = this.loadPositions()[id];
    const x = saved?.x ?? this.defaultX();
    const y = saved?.y ?? this.defaultY();
    this.windows = [...this.windows, { id, x, y, z: ++this.nextZ }];
  }

  close(id: HelpId): void {
    this.windows = this.windows.filter((w) => w.id !== id);
  }

  list(): OpenWindow[] {
    return this.windows;
  }

  bringToFront(id: HelpId): void {
    const w = this.windows.find((x) => x.id === id);
    if (w) w.z = ++this.nextZ;
  }

  setPosition(id: HelpId, x: number, y: number): void {
    const w = this.windows.find((x) => x.id === id);
    if (w) {
      w.x = x;
      w.y = y;
    }
    const all = this.loadPositions();
    all[id] = { x, y };
    try {
      localStorage.setItem(POS_KEY, JSON.stringify(all));
    } catch {
      // localStorage voll oder gesperrt — egal
    }
  }

  private loadPositions(): SavedPositions {
    if (typeof localStorage === 'undefined') return {};
    try {
      const raw = localStorage.getItem(POS_KEY);
      return raw ? (JSON.parse(raw) as SavedPositions) : {};
    } catch {
      return {};
    }
  }

  private defaultX(): number {
    const w = typeof window === 'undefined' ? 1280 : window.innerWidth;
    return Math.max(40, w - 460);
  }

  private defaultY(): number {
    return 90;
  }
}

export const helpStore = new HelpStore();
