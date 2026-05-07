import { describe, it, expect } from 'vitest';
import { t } from '../src/lib/i18n';

describe('i18n.t', () => {
  it('looks up nested keys via dot notation', () => {
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
});
