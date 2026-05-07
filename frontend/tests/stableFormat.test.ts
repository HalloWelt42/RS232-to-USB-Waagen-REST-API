import { describe, it, expect, beforeEach } from 'vitest';
import { buildStableSegments, intDigitsForMax, formatGrams, formatGramsCompact } from '../src/lib/format';
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

  // Hilfsfunktion: ohne den reservierten Minus-Slot joinen — der ist
  // bei positivem Wert ghost und nicht teil des „lesbaren" Strings.
  function joinNoSign(segs: { text: string; kind: string }[]): string {
    return segs.filter(s => s.kind !== 'sign').map(s => s.text).join('');
  }

  it('renders 12.3 g on a 6000g/0.1g scale as 0.012,3 g with ghosts', () => {
    const segs = buildStableSegments(12.3, PLC_6000);
    expect(joinNoSign(segs)).toBe('0.012,3 g');
    // Sign-Slot ist da, aber ghost
    const sign = segs.find(s => s.kind === 'sign');
    expect(sign?.text).toBe('−');
    expect(sign?.ghost).toBe(true);
    // Ghost: Sign + führende '0' + Tausender-Trenner + zweite '0'
    expect(ghostSegs(segs)).toBe('−0.0');
  });

  it('renders 0 g with all leading zeros as ghost except the last digit', () => {
    const segs = buildStableSegments(0, PLC_6000);
    expect(joinNoSign(segs)).toBe('0.000,0 g');
    // Sign + führende Nullen + Tausender-Trenner + zweite Null sind ghost
    expect(ghostSegs(segs)).toBe('−0.00');
  });

  it('renders 1234.5 g with sign-slot ghost, rest opaque', () => {
    const segs = buildStableSegments(1234.5, PLC_6000);
    expect(joinNoSign(segs)).toBe('1.234,5 g');
    // Nur das Vorzeichen ist ghost (positiver Wert)
    expect(ghostSegs(segs)).toBe('−');
  });

  it('renders null as full ghost frame including sign', () => {
    const segs = buildStableSegments(null, PLC_6000);
    expect(joinNoSign(segs)).toBe('0.000,0 g');
    // Alles ist Ghost
    expect(segs.every(s => s.ghost)).toBe(true);
  });

  it('handles analytical balance with 4 decimal places', () => {
    const segs = buildStableSegments(0.1234, ANALYTICAL);
    expect(joinNoSign(segs)).toBe('000,1234 g');
    expect(ghostSegs(segs)).toBe('−00');
  });

  it('handles 30 kg scale (no decimals)', () => {
    const segs = buildStableSegments(2500, HEAVY);
    expect(joinNoSign(segs)).toBe('02.500 g');
    expect(ghostSegs(segs)).toBe('−0');
  });

  it('shows minus opaque for negative values', () => {
    const segs = buildStableSegments(-12.3, PLC_6000);
    const sign = segs.find(s => s.kind === 'sign');
    expect(sign?.text).toBe('−');
    expect(sign?.ghost).toBe(false);
    // Ziffern dahinter haben dieselbe Ghost-Logik wie bei positivem Wert
    expect(ghostSegs(segs)).toBe('0.0');
  });
});

describe('buildStableSegments — EN locale', () => {
  beforeEach(() => i18n.set('en'));

  function joinNoSign(segs: { text: string; kind: string }[]): string {
    return segs.filter(s => s.kind !== 'sign').map(s => s.text).join('');
  }

  it('uses comma as thousand and dot as decimal', () => {
    const segs = buildStableSegments(1234.5, PLC_6000);
    expect(joinNoSign(segs)).toBe('1,234.5 g');
  });

  it('renders 12.3 g with EN separators', () => {
    const segs = buildStableSegments(12.3, PLC_6000);
    expect(joinNoSign(segs)).toBe('0,012.3 g');
    // Ghost: Sign + erste Null + Komma-Trenner + zweite Null
    expect(ghostSegs(segs)).toBe('−0,0');
  });

  it('reset to de after test', () => {
    i18n.set('de');
    expect(i18n.current).toBe('de');
  });
});

describe('formatGramsCompact — Modell-Werte immer in Grundeinheit', () => {
  it('zeigt ganze Gramm ohne Tausender-Trenner — locale-unabhängig', () => {
    i18n.set('de');
    expect(formatGramsCompact(6000)).toBe('6000 g');
    expect(formatGramsCompact(30000)).toBe('30000 g');
    expect(formatGramsCompact(220)).toBe('220 g');
    expect(formatGramsCompact(1)).toBe('1 g');

    i18n.set('en');
    expect(formatGramsCompact(6000)).toBe('6000 g');
    expect(formatGramsCompact(30000)).toBe('30000 g');
    i18n.set('de');
  });

  it('Sub-Gramm-Werte mit Locale-Dezimaltrenner', () => {
    i18n.set('de');
    expect(formatGramsCompact(0.1)).toBe('0,1 g');
    expect(formatGramsCompact(0.001)).toBe('0,001 g');
    expect(formatGramsCompact(0.0001)).toBe('0,0001 g');

    i18n.set('en');
    expect(formatGramsCompact(0.1)).toBe('0.1 g');
    expect(formatGramsCompact(0.0001)).toBe('0.0001 g');
    i18n.set('de');
  });

  it('null/undefined als em-dash', () => {
    expect(formatGramsCompact(null)).toBe('—');
    expect(formatGramsCompact(undefined)).toBe('—');
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
