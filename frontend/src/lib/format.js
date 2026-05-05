/** Hilfen zum Formatieren von Reading-Werten. */

export function formatGrams(g) {
  if (g === null || g === undefined || Number.isNaN(g)) return '—';
  // Bei Werten >= 1000 g auf kg umstellen für bessere Lesbarkeit
  if (Math.abs(g) >= 1000) {
    return `${(g / 1000).toFixed(3)} kg`;
  }
  return `${g.toFixed(1)} g`;
}

export function formatTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleTimeString('de-DE', {
    hour:   '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('de-DE');
}
