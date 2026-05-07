/**
 * Mini-i18n: aktuell nur Deutsch.
 * Vorgesehen für späteres Lazy-Loading weiterer Sprachen wie in
 * RadioHub. Bis dahin: ``t('bereich.key')`` mit Path-Lookup.
 */
import de from '../locales/de';

type AnyDict = { [k: string]: AnyDict | string | ((...args: unknown[]) => string) };

const locales: Record<string, AnyDict> = { de: de as unknown as AnyDict };
let current: AnyDict = locales.de;

export function t(key: string, ...args: unknown[]): string {
  const path = key.split('.');
  let node: AnyDict | string | ((...args: unknown[]) => string) | undefined = current;
  for (const p of path) {
    if (node && typeof node === 'object' && p in (node as AnyDict)) {
      node = (node as AnyDict)[p];
    } else {
      return key;
    }
  }
  if (typeof node === 'function') return node(...args);
  if (typeof node === 'string') return node;
  return key;
}

export function setLanguage(lang: string): void {
  if (locales[lang]) current = locales[lang];
}
