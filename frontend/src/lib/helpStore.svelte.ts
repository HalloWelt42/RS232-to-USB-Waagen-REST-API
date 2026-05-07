/**
 * Reaktiver Speicher für offene Hilfe-Fenster.
 *
 * Geometrie wird vor dem Anwenden immer auf den aktuellen Viewport
 * geclampt, damit Fenster nie hinter dem Rand verschwinden — auch
 * dann nicht, wenn der Anwender den Browser zwischen Sessions
 * verkleinert hat.
 */
import type { HelpId } from './help';

export interface OpenWindow {
  id: HelpId;
  x: number; y: number;
  w: number; h: number;
  z: number;
}

const POS_KEY = 'waage.help.windows';

// Mindestabstand zum Bildschirmrand und Mindestmaße der Fenster
const PAD = 8;
const MIN_W = 280;
const MIN_H = 200;
const DEFAULT_W = 420;
const DEFAULT_H = 380;

interface SavedGeo { [id: string]: { x: number; y: number; w: number; h: number } }

interface Viewport { w: number; h: number; }

function viewport(): Viewport {
  if (typeof window === 'undefined') return { w: 1024, h: 768 };
  return { w: window.innerWidth, h: window.innerHeight };
}

/**
 * Sicherstellen, dass eine Geometrie vollständig im sichtbaren
 * Bereich liegt. Wenn die Maße größer als der Viewport sind, werden
 * sie verkleinert; wenn die Position außerhalb liegt, wird sie
 * zurückgeholt.
 */
function clamp(g: { x: number; y: number; w: number; h: number }, vp: Viewport):
    { x: number; y: number; w: number; h: number } {
  const w = Math.max(MIN_W, Math.min(g.w, vp.w - 2 * PAD));
  const h = Math.max(MIN_H, Math.min(g.h, vp.h - 2 * PAD));
  const maxX = Math.max(PAD, vp.w - w - PAD);
  const maxY = Math.max(PAD, vp.h - h - PAD);
  const x = Math.max(PAD, Math.min(g.x, maxX));
  const y = Math.max(PAD, Math.min(g.y, maxY));
  return { x, y, w, h };
}

class HelpStore {
  windows = $state<OpenWindow[]>([]);
  private nextZ = 100;

  open(id: HelpId): void {
    const existing = this.windows.find(w => w.id === id);
    if (existing) {
      existing.z = ++this.nextZ;
      this.reflow();
      return;
    }
    const vp = viewport();
    const saved = this.loadGeo()[id];
    const initial = saved
      ? saved
      : {
          x: Math.max(PAD, vp.w - DEFAULT_W - 40),
          y: 90,
          w: DEFAULT_W,
          h: DEFAULT_H,
        };
    const c = clamp(initial, vp);
    this.windows = [...this.windows, { id, ...c, z: ++this.nextZ }];
  }

  close(id: HelpId): void {
    this.windows = this.windows.filter(w => w.id !== id);
  }

  bringToFront(id: HelpId): void {
    const w = this.windows.find(x => x.id === id);
    if (w) w.z = ++this.nextZ;
  }

  setGeometry(id: HelpId, x: number, y: number, w: number, h: number): void {
    const c = clamp({ x, y, w, h }, viewport());
    const item = this.windows.find(it => it.id === id);
    if (item) {
      item.x = c.x; item.y = c.y; item.w = c.w; item.h = c.h;
    }
    const all = this.loadGeo();
    all[id] = c;
    try { localStorage.setItem(POS_KEY, JSON.stringify(all)); } catch { /* ignore */ }
  }

  /**
   * Alle offenen Fenster auf den aktuellen Viewport zurückzwängen.
   * Wird vom App-Root bei window.resize aufgerufen.
   */
  reflow(): void {
    const vp = viewport();
    for (const win of this.windows) {
      const c = clamp(win, vp);
      win.x = c.x; win.y = c.y; win.w = c.w; win.h = c.h;
    }
  }

  /** Welche Hilfe-IDs sind gerade offen — für die URL-Synchronisierung. */
  openIds(): HelpId[] {
    return this.windows.map(w => w.id);
  }

  /** Liste der gewünschten IDs offen halten, alle anderen schließen. */
  syncOpenIds(ids: HelpId[]): void {
    const wanted = new Set(ids);
    // Schließen, was nicht mehr gewünscht ist
    for (const w of [...this.windows]) {
      if (!wanted.has(w.id)) this.close(w.id);
    }
    // Öffnen, was neu dabei ist
    for (const id of ids) {
      if (!this.windows.some(w => w.id === id)) this.open(id);
    }
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
