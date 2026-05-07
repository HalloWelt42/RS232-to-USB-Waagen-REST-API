/** Reaktiver Speicher für offene Hilfe-Fenster. */
import type { HelpId } from './help';

export interface OpenWindow {
  id: HelpId;
  x: number; y: number;
  w: number; h: number;
  z: number;
}

const POS_KEY = 'waage.help.windows';

interface SavedGeo { [id: string]: { x: number; y: number; w: number; h: number } }

class HelpStore {
  windows = $state<OpenWindow[]>([]);
  private nextZ = 100;

  open(id: HelpId): void {
    const existing = this.windows.find(w => w.id === id);
    if (existing) { existing.z = ++this.nextZ; return; }
    const saved = this.loadGeo()[id];
    const x = saved?.x ?? Math.max(40, window.innerWidth  - 460);
    const y = saved?.y ?? 90;
    const w = saved?.w ?? 420;
    const h = saved?.h ?? 380;
    this.windows = [...this.windows, { id, x, y, w, h, z: ++this.nextZ }];
  }

  close(id: HelpId): void {
    this.windows = this.windows.filter(w => w.id !== id);
  }

  bringToFront(id: HelpId): void {
    const w = this.windows.find(x => x.id === id);
    if (w) w.z = ++this.nextZ;
  }

  setGeometry(id: HelpId, x: number, y: number, w: number, h: number): void {
    const item = this.windows.find(it => it.id === id);
    if (item) { item.x = x; item.y = y; item.w = w; item.h = h; }
    const all = this.loadGeo();
    all[id] = { x, y, w, h };
    try { localStorage.setItem(POS_KEY, JSON.stringify(all)); } catch {}
  }

  private loadGeo(): SavedGeo {
    if (typeof localStorage === 'undefined') return {};
    try {
      const raw = localStorage.getItem(POS_KEY);
      return raw ? (JSON.parse(raw) as SavedGeo) : {};
    } catch { return {}; }
  }
}

export const helpStore = new HelpStore();
