import { describe, it, expect } from 'vitest';
import { formatGrams, formatDiff, formatTime, formatDuration } from '../src/lib/format';

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
