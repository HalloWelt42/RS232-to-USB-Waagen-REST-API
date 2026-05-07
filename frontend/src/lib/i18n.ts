/**
 * Re-Export-Schicht. Die echte Implementierung liegt in
 * `i18n.svelte.ts` mit Svelte-5-Runes — alle bestehenden Importe
 * `import { t } from '../lib/i18n'` funktionieren weiter.
 */
export { t, i18n, LANG_META, LANG_ORDER, type Lang, type LangMeta } from './i18n.svelte';

export function setLanguage(lang: 'de' | 'en'): void {
  // Lazy-Import vermeidet Zyklus mit Komponenten, die i18n bereits laden.
  void import('./i18n.svelte').then(m => m.i18n.set(lang));
}
