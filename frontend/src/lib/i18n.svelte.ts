/**
 * Reaktive Mini-i18n.
 *
 * `t('bereich.key')` greift auf die aktuelle Locale zu; ein Wechsel
 * über `i18n.set('en')` rendert alle abhängigen Komponenten neu, weil
 * `current` ein Svelte-5-State ist.
 *
 * Aktuell unterstützt: Deutsch (Master) und Englisch.
 */
import de from '../locales/de';
import en from '../locales/en';

export type Lang = 'de' | 'en';
type AnyDict = { [k: string]: AnyDict | string | ((...args: unknown[]) => string) };

const LOCALES: Record<Lang, AnyDict> = {
  de: de as unknown as AnyDict,
  en: en as unknown as AnyDict,
};

const KEY = 'waage.lang';

function detect(): Lang {
  if (typeof window === 'undefined') return 'de';
  const stored = window.localStorage.getItem(KEY);
  if (stored === 'de' || stored === 'en') return stored;
  const nav = (window.navigator.language ?? 'de').toLowerCase();
  return nav.startsWith('en') ? 'en' : 'de';
}

class I18n {
  current = $state<Lang>(detect());

  set(lang: Lang): void {
    this.current = lang;
    try { window.localStorage.setItem(KEY, lang); } catch { /* ignore */ }
    if (typeof document !== 'undefined') {
      document.documentElement.lang = lang;
    }
  }

  toggle(): Lang {
    const next: Lang = this.current === 'de' ? 'en' : 'de';
    this.set(next);
    return next;
  }

  /**
   * Lookup mit Punkt-Notation. Bei fehlendem Schlüssel in der aktiven
   * Sprache fällt der Lookup auf Deutsch zurück; bleibt der Schlüssel
   * dort auch unbekannt, kommt der Schlüssel selbst zurück.
   */
  t(key: string, ...args: unknown[]): string {
    return this.lookup(this.current, key, args)
        ?? this.lookup('de', key, args)
        ?? key;
  }

  private lookup(lang: Lang, key: string, args: unknown[]): string | null {
    const path = key.split('.');
    let node: AnyDict | string | ((...args: unknown[]) => string) | undefined = LOCALES[lang];
    for (const p of path) {
      if (node && typeof node === 'object' && p in (node as AnyDict)) {
        node = (node as AnyDict)[p];
      } else {
        return null;
      }
    }
    if (typeof node === 'function') return node(...args);
    if (typeof node === 'string') return node;
    return null;
  }
}

export const i18n = new I18n();

/** Bequemer Funktions-Alias — Komponenten verwenden weiterhin `t(...)`. */
export function t(key: string, ...args: unknown[]): string {
  return i18n.t(key, ...args);
}
