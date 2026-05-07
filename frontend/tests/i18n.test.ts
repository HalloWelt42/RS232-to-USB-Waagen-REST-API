import { describe, it, expect, beforeEach } from 'vitest';
import { i18n, t } from '../src/lib/i18n';

describe('i18n.t', () => {
  beforeEach(() => i18n.set('de'));

  it('looks up nested keys via dot notation in German', () => {
    expect(t('app.title')).toBe('Waage');
    expect(t('tools.wiegen')).toBe('Wiegen');
    expect(t('tools.differenz')).toBe('Differenz-Wiegen');
  });

  it('returns the key itself if not found', () => {
    expect(t('does.not.exist')).toBe('does.not.exist');
  });

  it('handles function-typed values with arguments', () => {
    expect(t('toast.valueCopiedG', '12.3 g')).toBe('12.3 g kopiert');
  });

  it('switches to English locale', () => {
    i18n.set('en');
    expect(t('tools.wiegen')).toBe('Weighing');
    expect(t('toast.valueCopiedG', '12.3 g')).toBe('12.3 g copied');
    i18n.set('de');
  });

  it('falls back to German for missing English keys', () => {
    // toolsOriginal is identical in both, but tests the fallback path
    i18n.set('en');
    expect(t('app.title')).toBe('Waage');
    i18n.set('de');
  });
});
