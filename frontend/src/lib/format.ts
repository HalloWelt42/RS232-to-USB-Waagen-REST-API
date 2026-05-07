/**
 * Formatierungs-Hilfen.
 * formatGrams: ab 1000 g auf kg umstellen.
 */

export function formatGrams(g: number | null | undefined): string {
  if (g === null || g === undefined || Number.isNaN(g)) return '—';
  if (Math.abs(g) >= 1000) return `${(g / 1000).toFixed(3)} kg`;
  return `${g.toFixed(1)} g`;
}

export function formatDiff(g: number | null | undefined): string {
  if (g === null || g === undefined || Number.isNaN(g)) return '—';
  const sign = g >= 0 ? '+' : '−';
  const abs = Math.abs(g);
  if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(3)} kg`;
  return `${sign}${abs.toFixed(1)} g`;
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString('de-DE', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('de-DE');
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '—';
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (d) return `${d}d ${h}h ${m}m`;
  if (h) return `${h}h ${m}m ${s}s`;
  if (m) return `${m}m ${s}s`;
  return `${s}s`;
}
