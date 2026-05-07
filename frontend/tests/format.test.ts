import { describe, it, expect } from 'vitest';
import { formatGrams, formatTime, formatDuration } from '../src/lib/format';

describe('formatGrams', () => {
  it('zeigt Gramm bis 999.9 g', () => {
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
    expect(formatTime('2026-05-06T03:04:05.678')).toMatch(/\d{2}:\d{2}:\d{2}/);
  });
});

describe('formatDuration', () => {
  it('Sekunden bis Tage', () => {
    expect(formatDuration(0)).toBe('0s');
    expect(formatDuration(45)).toBe('45s');
    expect(formatDuration(125)).toBe('2m 5s');
    expect(formatDuration(3725)).toBe('1h 2m 5s');
    expect(formatDuration(86400 + 3725)).toBe('1d 1h 2m');
    expect(formatDuration(null)).toBe('—');
  });
});
