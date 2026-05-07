/**
 * Frontend-eigener Diff-Tracker — registriert nur Werte-Änderungen,
 * läuft seit Mount-Zeit. Wird vom Server-Messlog ergänzt (siehe AppApi.messlog).
 */
import type { MesslogEntry, Reading } from './types';

export class DiffTracker {
  private items: MesslogEntry[] = [];
  private lastValue: number | null = null;
  private nextId: number = -1;   // Frontend-IDs negativ, um nicht mit Server zu kollidieren

  constructor(
    private readonly maxItems = 200,
    private readonly epsilonG = 0.05,
  ) {}

  push(reading: Reading): MesslogEntry | null {
    if (!reading.stable) return null;
    if (this.lastValue === null) {
      const e: MesslogEntry = {
        id: this.nextId--, ts: reading.timestamp, kind: 'start',
        diff_g: null, value_g: reading.weight_g, unit: reading.unit, stable: true,
      };
      this.items = [...this.items, e].slice(-this.maxItems);
      this.lastValue = reading.weight_g;
      return e;
    }
    const diff = reading.weight_g - this.lastValue;
    if (Math.abs(diff) <= this.epsilonG) return null;
    const e: MesslogEntry = {
      id: this.nextId--, ts: reading.timestamp, kind: 'change',
      diff_g: diff, value_g: reading.weight_g, unit: reading.unit, stable: true,
    };
    this.items = [...this.items, e].slice(-this.maxItems);
    this.lastValue = reading.weight_g;
    return e;
  }

  markTare(reading: Reading): MesslogEntry {
    const e: MesslogEntry = {
      id: this.nextId--, ts: reading.timestamp, kind: 'tare',
      diff_g: null, value_g: reading.weight_g, unit: reading.unit, stable: reading.stable,
    };
    this.items = [...this.items, e].slice(-this.maxItems);
    this.lastValue = reading.weight_g;
    return e;
  }

  get(): MesslogEntry[] { return this.items; }

  hydrate(server: MesslogEntry[]): void {
    // Server hat neueste zuerst; intern sortieren wir alt -> neu.
    const chronological = [...server].reverse();
    this.items = chronological.slice(-this.maxItems);
    if (this.items.length > 0) {
      this.lastValue = this.items[this.items.length - 1].value_g;
    }
  }

  clear(): void {
    this.items = [];
    this.lastValue = null;
  }
}
