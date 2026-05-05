import { describe, it, expect } from 'vitest';
import { formatGrams, formatTime } from '../src/lib/format.js';

describe('formatGrams', () => {
  it('zeigt Gramm mit einer Nachkommastelle bis 999.9 g', () => {
    expect(formatGrams(0)).toBe('0.0 g');
    expect(formatGrams(123.456)).toBe('123.5 g');
    expect(formatGrams(-50)).toBe('-50.0 g');
  });

  it('schaltet auf kg um ab 1000 g', () => {
    expect(formatGrams(1000)).toBe('1.000 kg');
    expect(formatGrams(2500)).toBe('2.500 kg');
    expect(formatGrams(-1234.5)).toBe('-1.234 kg');
  });

  it('liefert Bindestrich für ungültige Werte', () => {
    expect(formatGrams(null)).toBe('—');
    expect(formatGrams(undefined)).toBe('—');
    expect(formatGrams(NaN)).toBe('—');
  });
});

describe('formatTime', () => {
  it('liefert Bindestrich ohne Wert', () => {
    expect(formatTime(null)).toBe('—');
    expect(formatTime(undefined)).toBe('—');
  });

  it('formatiert ISO-Zeitstempel', () => {
    const t = formatTime('2026-01-02T03:04:05.678');
    expect(t).toMatch(/\d{2}:\d{2}:\d{2}/);
  });
});
