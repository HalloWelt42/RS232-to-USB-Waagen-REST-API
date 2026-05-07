import { describe, it, expect } from 'vitest';
import { HistoryTracker } from '../src/lib/historyTracker';
import type { Reading } from '../src/lib/types';

const r = (w: number): Reading => ({
  weight_g: w, unit: 'g', stable: true,
  timestamp: new Date().toISOString(), raw: '',
});

describe('HistoryTracker', () => {
  it('nimmt nur Werte-Änderungen auf', () => {
    const t = new HistoryTracker();
    expect(t.push(r(1.0))).toBe(true);
    expect(t.push(r(1.0))).toBe(false); // gleicher Wert
    expect(t.push(r(1.04))).toBe(false); // unter epsilon
    expect(t.push(r(2.0))).toBe(true);
    expect(t.get().map(x => x.weight_g)).toEqual([1.0, 2.0]);
  });
  it('respektiert maxItems', () => {
    const t = new HistoryTracker(3);
    for (let i = 0; i < 10; i++) t.push(r(i));
    const items = t.get();
    expect(items.length).toBe(3);
    expect(items.map(x => x.weight_g)).toEqual([7, 8, 9]);
  });
  it('hydrate filtert Wiederholungen aus Server-Response', () => {
    const t = new HistoryTracker();
    t.hydrate([r(0), r(0), r(0), r(1), r(1), r(2)]);
    expect(t.get().map(x => x.weight_g)).toEqual([0, 1, 2]);
  });
  it('clear entfernt alles', () => {
    const t = new HistoryTracker();
    t.push(r(1)); t.push(r(2));
    t.clear();
    expect(t.get()).toEqual([]);
  });
});
