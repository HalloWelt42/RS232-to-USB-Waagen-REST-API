import { describe, it, expect, beforeEach } from 'vitest';
import { buildStableSegments, intDigitsForMax, formatGrams } from '../src/lib/format';
import { i18n } from '../src/lib/i18n';

const PLC_6000 = { max_g: 6000, resolution_g: 0.1 };
const ANALYTICAL = { max_g: 220, resolution_g: 0.0001 };
const HEAVY = { max_g: 30000, resolution_g: 1 };

function joinSegs(segs: { text: string }[]): string {
  return segs.map(s => s.text).join('');
}
function ghostSegs(segs: { text: string; ghost: boolean }[]): string {
  return segs.filter(s => s.ghost).map(s => s.text).join('');
}

describe('intDigitsForMax', () => {
  it('counts digits before decimal', () => {
    expect(intDigitsForMax(6000)).toBe(4);
    expect(intDigitsForMax(220)).toBe(3);
    expect(intDigitsForMax(30000)).toBe(5);
    expect(intDigitsForMax(1)).toBe(1);
  });
});

describe('buildStableSegments — DE locale', () => {
  beforeEach(() => i18n.set('de'));

  it('renders 12.3 g on a 6000g/0.1g scale as 0.012,3 g with ghosts', () => {
    const segs = buildStableSegments(12.3, PLC_6000);
    expect(joinSegs(segs)).toBe('0.012,3 g');
    // Ghost: führende '0', der Tausender-Trenner, der zweite '0'
    expect(ghostSegs(segs)).toBe('0.0');
  });

  it('renders 0 g with all leading zeros as ghost except the last digit', () => {
    const segs = buildStableSegments(0, PLC_6000);
    expect(joinSegs(segs)).toBe('0.000,0 g');
    expect(ghostSegs(segs)).toBe('0.00');
  });

  it('renders 1234.5 g with no ghost', () => {
    const segs = buildStableSegments(1234.5, PLC_6000);
    expect(joinSegs(segs)).toBe('1.234,5 g');
    expect(ghostSegs(segs)).toBe('');
  });

  it('renders null as full ghost frame', () => {
    const segs = buildStableSegments(null, PLC_6000);
    expect(joinSegs(segs)).toBe('0.000,0 g');
    // Alle Stellen außer ' g' sind Ghost
    const nonUnit = segs.filter(s => s.kind !== 'unit');
    expect(nonUnit.every(s => s.ghost)).toBe(true);
  });

  it('handles analytical balance with 4 decimal places', () => {
    const segs = buildStableSegments(0.1234, ANALYTICAL);
    expect(joinSegs(segs)).toBe('000,1234 g');
    expect(ghostSegs(segs)).toBe('00');
  });

  it('handles 30 kg scale (no decimals)', () => {
    const segs = buildStableSegments(2500, HEAVY);
    expect(joinSegs(segs)).toBe('02.500 g');
    expect(ghostSegs(segs)).toBe('0');
  });

  it('keeps negative sign visible', () => {
    const segs = buildStableSegments(-12.3, PLC_6000);
    expect(joinSegs(segs)).toBe('-0.012,3 g');
    const sign = segs.find(s => s.kind === 'sign');
    expect(sign?.ghost).toBe(false);
  });
});

describe('buildStableSegments — EN locale', () => {
  beforeEach(() => i18n.set('en'));

  it('uses comma as thousand and dot as decimal', () => {
    const segs = buildStableSegments(1234.5, PLC_6000);
    expect(joinSegs(segs)).toBe('1,234.5 g');
  });

  it('renders 12.3 g with EN separators', () => {
    const segs = buildStableSegments(12.3, PLC_6000);
    expect(joinSegs(segs)).toBe('0,012.3 g');
    expect(ghostSegs(segs)).toBe('0,0');
  });

  it('reset to de after test', () => {
    i18n.set('de');
    expect(i18n.current).toBe('de');
  });
});

describe('formatGrams — locale-aware', () => {
  it('uses DE separators below 1 kg', () => {
    i18n.set('de');
    expect(formatGrams(12.3)).toBe('12,3 g');
    expect(formatGrams(999.5)).toBe('999,5 g');
  });

  it('uses DE thousand separator above 1 kg', () => {
    i18n.set('de');
    // 1234.5 g = 1.2345 kg → toFixed(3) = '1.234'
    expect(formatGrams(1234.5)).toBe('1,234 kg');
  });

  it('uses EN separators after switch', () => {
    i18n.set('en');
    expect(formatGrams(12.3)).toBe('12.3 g');
    expect(formatGrams(1234.5)).toBe('1.234 kg');
    i18n.set('de');
  });
});
