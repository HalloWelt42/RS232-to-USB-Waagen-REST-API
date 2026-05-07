/**
 * Einmalige Begrüßung beim ersten Aufruf — speichert die Information
 * im ``localStorage``, sodass der Hinweis nicht jedes Mal aufpoppt.
 */

const KEY = 'waage.welcome.dismissed';

export function isWelcomeDismissed(): boolean {
  if (typeof localStorage === 'undefined') return true;
  return localStorage.getItem(KEY) === '1';
}

export function dismissWelcome(): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(KEY, '1');
}

export function resetWelcome(): void {
  if (typeof localStorage === 'undefined') return;
  localStorage.removeItem(KEY);
}
