/**
 * Reaktive i18n mit Locale-spezifischem Number-Format.
 *
 * `t('bereich.key')` greift auf die aktuelle Locale zu; ein Wechsel über
 * `i18n.set('en')` rendert alle abhängigen Komponenten neu, weil
 * `current` ein Svelte-5-State ist.
 *
 * Eine neue Sprache hinzufügen:
 *   1. Übersetzungs-Datei `<lang>.ts` analog zu `de.ts` anlegen
 *   2. `Lang`-Typ erweitern und in `LOCALES` registrieren
 *   3. `LOCALE_FORMAT` für Tausender-/Dezimaltrenner ergänzen
 *   4. `detect()` einen weiteren Browser-Sprach-Branch geben
 *
 * Siehe `locales/README.md`.
 */
import de from '../locales/de';
import en from '../locales/en';

export type Lang = 'de' | 'en';
type AnyDict = { [k: string]: AnyDict | string | ((...args: unknown[]) => string) };

/** Übersetzungs-Bäume, indiziert nach Sprach-Kürzel. */
const LOCALES: Record<Lang, AnyDict> = {
  de: de as unknown as AnyDict,
  en: en as unknown as AnyDict,
};

/** Number-Format pro Sprache — Tausender und Dezimal. */
export interface NumberFormat {
  decimal: string;
  thousand: string;
}

const LOCALE_FORMAT: Record<Lang, NumberFormat> = {
  de: { decimal: ',', thousand: '.' },
  en: { decimal: '.', thousand: ',' },
};

/** Reihenfolge für den LanguageToggle (zyklisches Durchschalten). */
export const LANG_ORDER: readonly Lang[] = ['de', 'en'] as const;

const KEY = 'waage.lang';

function detect(): Lang {
  if (typeof window === 'undefined') return 'de';
  const stored = window.localStorage.getItem(KEY);
  if (stored && (LANG_ORDER as readonly string[]).includes(stored)) return stored as Lang;
  const nav = (window.navigator.language ?? 'de').toLowerCase();
  if (nav.startsWith('en')) return 'en';
  return 'de';
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

  /** Schaltet zyklisch durch alle registrierten Sprachen. */
  toggle(): Lang {
    const idx = LANG_ORDER.indexOf(this.current);
    const next = LANG_ORDER[(idx + 1) % LANG_ORDER.length];
    this.set(next);
    return next;
  }

  /** Aktuelle Locale-Number-Settings (Tausender / Dezimal). */
  get numberFormat(): NumberFormat {
    return LOCALE_FORMAT[this.current];
  }

  /**
   * Lookup mit Punkt-Notation. Bei fehlendem Schlüssel in der aktiven
   * Sprache fällt der Lookup auf Deutsch (Master) zurück; bleibt der
   * Schlüssel dort auch unbekannt, kommt der Schlüssel selbst zurück.
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

/** Aktuelles Number-Format für format.ts. */
export function currentNumberFormat(): NumberFormat {
  return i18n.numberFormat;
}
