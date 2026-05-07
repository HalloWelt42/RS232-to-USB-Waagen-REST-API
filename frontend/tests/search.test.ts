import { describe, it, expect, beforeEach } from 'vitest';
import { search } from '../src/lib/search';
import { i18n } from '../src/lib/i18n';

describe('search', () => {
  beforeEach(() => i18n.set('de'));

  it('returns no results for empty query', () => {
    expect(search('')).toEqual([]);
    expect(search('   ')).toEqual([]);
  });

  it('finds tools by name', () => {
    const results = search('Differenz');
    expect(results.length).toBeGreaterThan(0);
    const tool = results.find(r => r.kind === 'tool' && r.ref === 'differenz');
    expect(tool).toBeTruthy();
  });

  it('finds glossary terms', () => {
    const results = search('Brutto');
    const term = results.find(r => r.kind === 'term');
    expect(term).toBeTruthy();
  });

  it('finds help entries by content', () => {
    const results = search('Sollwert');
    const hasWiegenHit = results.some(r => r.action.kind === 'help' && r.action.help === 'wiegen');
    expect(hasWiegenHit).toBe(true);
  });

  it('handles umlauts case-insensitively', () => {
    const upper = search('STÜCK');
    const lower = search('stück');
    expect(upper.length).toBeGreaterThan(0);
    expect(lower.length).toBeGreaterThan(0);
  });

  it('limits results to max', () => {
    const results = search('a', 5);
    expect(results.length).toBeLessThanOrEqual(5);
  });
});
