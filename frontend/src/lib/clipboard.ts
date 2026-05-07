/**
 * Mini-Helper für Werte in die Zwischenablage.
 *
 * Nutzt die moderne Clipboard-API, fällt zurück auf das alte
 * ``execCommand``-Verfahren in Browsern ohne ``navigator.clipboard``.
 */

export async function copyText(text: string): Promise<boolean> {
  if (typeof navigator !== 'undefined' && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // Fallback unten
    }
  }
  // execCommand-Fallback für ältere Browser oder unsichere Kontexte
  if (typeof document === 'undefined') return false;
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  let ok = false;
  try {
    ok = document.execCommand('copy');
  } catch {
    ok = false;
  }
  document.body.removeChild(ta);
  return ok;
}
