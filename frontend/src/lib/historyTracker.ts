/**
 * History-Tracker: nimmt nur Werte-Änderungen auf.
 *
 * Im Live-Stream kommen viele Frames pro Sekunde mit demselben Wert
 * (z.B. "0,0 g" wenn nichts auf der Waage liegt). Für die Verlaufs-
 * anzeige interessieren nur die Frames, bei denen sich das Gewicht
 * gegenüber dem zuletzt gespeicherten ändert.
 *
 * Optional kann eine ``epsilon``-Schwelle gesetzt werden, damit Mess-
 * Jitter unter z.B. 0,05 g nicht als neuer Eintrag gilt.
 */

import type { Reading } from './types';

export class HistoryTracker {
  private items: Reading[] = [];
  private lastWeight: number | null = null;

  constructor(
    private readonly maxItems: number = 200,
    private readonly epsilon: number = 0.05,
  ) {}

  /** Fügt ein Reading hinzu, wenn es eine echte Werte-Änderung darstellt. */
  push(reading: Reading): boolean {
    if (this.lastWeight === null
        || Math.abs(reading.weight_g - this.lastWeight) > this.epsilon) {
      this.items = [...this.items, reading].slice(-this.maxItems);
      this.lastWeight = reading.weight_g;
      return true;
    }
    return false;
  }

  /** Aktueller Verlauf, neueste Einträge zuletzt. */
  get(): Reading[] {
    return this.items;
  }

  /** Initialisiert den Verlauf aus einer Server-History (z.B. beim Mount). */
  hydrate(items: Reading[]): void {
    // Nur eindeutige Werte aus dem Server-Stream übernehmen
    const out: Reading[] = [];
    let last: number | null = null;
    for (const r of items) {
      if (last === null || Math.abs(r.weight_g - last) > this.epsilon) {
        out.push(r);
        last = r.weight_g;
      }
    }
    this.items = out.slice(-this.maxItems);
    this.lastWeight = last;
  }

  clear(): void {
    this.items = [];
    this.lastWeight = null;
  }
}
