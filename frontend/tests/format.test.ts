import { describe, it, expect } from 'vitest';
import { formatGrams, formatDiff, formatTime, formatDuration,
         decimalsForResolution, setDefaultResolution } from '../src/lib/format';

describe('formatGrams', () => {
  it('formats grams below 1 kg with one decimal', () => {
    expect(formatGrams(123.45)).toBe('123.5 g');
    expect(formatGrams(0)).toBe('0.0 g');
  });

  it('switches to kg above 1000 g with three decimals', () => {
    expect(formatGrams(1234.5)).toBe('1.234 kg');
    expect(formatGrams(1000)).toBe('1.000 kg');
  });

  it('returns dash for null and undefined', () => {
    expect(formatGrams(null)).toBe('—');
    expect(formatGrams(undefined)).toBe('—');
    expect(formatGrams(NaN)).toBe('—');
  });

  it('handles negative values correctly', () => {
    expect(formatGrams(-50.0)).toBe('-50.0 g');
    expect(formatGrams(-2000.0)).toBe('-2.000 kg');
  });
});

describe('formatDiff', () => {
  it('prefixes positive values with plus sign', () => {
    expect(formatDiff(5.5)).toBe('+5.5 g');
    expect(formatDiff(0)).toBe('+0.0 g');
  });

  it('prefixes negative values with minus sign (proper minus character)', () => {
    expect(formatDiff(-5.5)).toBe('−5.5 g');
  });

  it('switches to kg above 1000 g', () => {
    expect(formatDiff(1500)).toBe('+1.500 kg');
    expect(formatDiff(-2500)).toBe('−2.500 kg');
  });

  it('returns dash for null', () => {
    expect(formatDiff(null)).toBe('—');
  });
});

describe('formatTime', () => {
  it('returns dash for falsy input', () => {
    expect(formatTime(null)).toBe('—');
    expect(formatTime('')).toBe('—');
  });
});

describe('decimalsForResolution', () => {
  it('returns 0 for whole-gram resolutions', () => {
    expect(decimalsForResolution(1)).toBe(0);
    expect(decimalsForResolution(10)).toBe(0);
  });
  it('returns 1 for 0.1 g', () => { expect(decimalsForResolution(0.1)).toBe(1); });
  it('returns 2 for 0.01 g', () => { expect(decimalsForResolution(0.01)).toBe(2); });
  it('returns 3 for 0.001 g', () => { expect(decimalsForResolution(0.001)).toBe(3); });
  it('returns 4 for 0.0001 g', () => { expect(decimalsForResolution(0.0001)).toBe(4); });
  it('falls back to 1 for invalid', () => {
    expect(decimalsForResolution(0)).toBe(1);
    expect(decimalsForResolution(-0.1)).toBe(1);
    expect(decimalsForResolution(NaN)).toBe(1);
  });
});

describe('formatGrams with model resolution', () => {
  it('respects per-call resolution argument', () => {
    expect(formatGrams(12.345, 0.001)).toBe('12.345 g');
    expect(formatGrams(12.345, 0.01)).toBe('12.35 g');
    expect(formatGrams(12.345, 1)).toBe('12 g');
  });

  it('uses default resolution after setDefaultResolution', () => {
    setDefaultResolution(0.001);
    expect(formatGrams(1.234567)).toBe('1.235 g');
    setDefaultResolution(0.1);     // restore default
    expect(formatGrams(1.234567)).toBe('1.2 g');
  });
});

describe('formatDuration', () => {
  it('formats seconds, minutes, hours, days', () => {
    expect(formatDuration(45)).toBe('45s');
    expect(formatDuration(125)).toBe('2m 5s');
    expect(formatDuration(3725)).toBe('1h 2m 5s');
    expect(formatDuration(90000)).toBe('1d 1h 0m');
  });

  it('returns dash for null', () => {
    expect(formatDuration(null)).toBe('—');
    expect(formatDuration(undefined)).toBe('—');
  });
});
