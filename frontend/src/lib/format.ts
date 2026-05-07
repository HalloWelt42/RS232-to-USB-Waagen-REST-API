/**
 * Formatierungs-Hilfen.
 *
 * `formatGrams` zeigt so viele Nachkommastellen, wie das aktive
 * Waagen-Modell auflösen kann — bei einer Analysewaage mit 0,001 g
 * stehen drei Nachkommastellen, bei einer Plattform mit 1 g Auflösung
 * keine. Wert ab 1000 g wird auf Kilogramm umgerechnet.
 *
 * Die globale Standard-Auflösung wird bei App-Start aus dem aktiven
 * Modell gesetzt (siehe App.svelte: setDefaultResolution).
 */

let defaultResolutionG = 0.1;

/** Anzahl Nachkommastellen, die zur Auflösung passen. */
export function decimalsForResolution(resolutionG: number): number {
  if (!Number.isFinite(resolutionG) || resolutionG <= 0) return 1;
  if (resolutionG >= 1) return 0;
  return Math.min(6, Math.ceil(-Math.log10(resolutionG)));
}

/**
 * Setzt die Default-Auflösung für alle nachfolgenden Format-Aufrufe
 * ohne explizites Modell. Wird von App.svelte beim Start und nach
 * jedem Modell-Wechsel aufgerufen.
 */
export function setDefaultResolution(resolutionG: number): void {
  if (Number.isFinite(resolutionG) && resolutionG > 0) {
    defaultResolutionG = resolutionG;
  }
}

/** kg-Anzeige immer mit 3 Nachkommastellen — für die UI ausreichend
 *  präzise, nicht überfrachtet. Bei feinen Auflösungen (mg-Bereich)
 *  ist der g-Pfad zuständig, weil solche Waagen nicht über 1 kg gehen. */
const KG_DECIMALS = 3;

export function formatGrams(g: number | null | undefined, resolutionG?: number): string {
  if (g === null || g === undefined || Number.isNaN(g)) return '—';
  const res = resolutionG ?? defaultResolutionG;
  if (Math.abs(g) >= 1000) {
    return `${(g / 1000).toFixed(KG_DECIMALS)} kg`;
  }
  return `${g.toFixed(decimalsForResolution(res))} g`;
}

export function formatDiff(g: number | null | undefined, resolutionG?: number): string {
  if (g === null || g === undefined || Number.isNaN(g)) return '—';
  const sign = g >= 0 ? '+' : '−';
  const abs = Math.abs(g);
  const res = resolutionG ?? defaultResolutionG;
  if (abs >= 1000) {
    return `${sign}${(abs / 1000).toFixed(KG_DECIMALS)} kg`;
  }
  return `${sign}${abs.toFixed(decimalsForResolution(res))} g`;
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
