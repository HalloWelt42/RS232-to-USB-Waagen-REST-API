/**
 * Formatierungs-Hilfen mit dynamischer Auflösung und Locale-bewusster
 * Number-Darstellung.
 *
 *   formatGrams(g, resolutionG?)        Standard-Anzeige (kleinere Werte)
 *   formatDiff(g, resolutionG?)         mit Vorzeichen
 *   buildStableSegments(g, model)       Display-stabil mit Ghost-Ziffern
 *
 * Tausender- und Dezimaltrenner kommen aus `i18n.numberFormat`:
 *   DE: 1.234,5     EN: 1,234.5
 */

import { currentNumberFormat } from './i18n.svelte';
import type { ScaleModel } from './types';

let defaultResolutionG = 0.1;

/** Anzahl Nachkommastellen, die zur Auflösung passen. */
export function decimalsForResolution(resolutionG: number): number {
  if (!Number.isFinite(resolutionG) || resolutionG <= 0) return 1;
  if (resolutionG >= 1) return 0;
  return Math.min(6, Math.ceil(-Math.log10(resolutionG)));
}

export function setDefaultResolution(resolutionG: number): void {
  if (Number.isFinite(resolutionG) && resolutionG > 0) {
    defaultResolutionG = resolutionG;
  }
}

/** Anzahl Stellen vor dem Komma für die Maximalkapazität. */
export function intDigitsForMax(maxG: number): number {
  if (!Number.isFinite(maxG) || maxG <= 0) return 1;
  return Math.max(1, Math.floor(Math.log10(maxG)) + 1);
}

/** Lokal-bewusst: Punkt durch Locale-Dezimaltrenner ersetzen, optional
 *  mit Tausender-Trenner versehen. */
function localizeNumber(raw: string, withThousand: boolean): string {
  const fmt = currentNumberFormat();
  const [intPart, fracPart] = raw.split('.');
  let int = intPart;
  if (withThousand && int.length > 3) {
    int = int.replace(/\B(?=(\d{3})+(?!\d))/g, fmt.thousand);
  }
  return fracPart !== undefined ? `${int}${fmt.decimal}${fracPart}` : int;
}

const KG_DECIMALS = 3;

export function formatGrams(g: number | null | undefined, resolutionG?: number): string {
  if (g === null || g === undefined || Number.isNaN(g)) return '—';
  const res = resolutionG ?? defaultResolutionG;
  if (Math.abs(g) >= 1000) {
    return `${localizeNumber((g / 1000).toFixed(KG_DECIMALS), true)} kg`;
  }
  return `${localizeNumber(g.toFixed(decimalsForResolution(res)), true)} g`;
}

export function formatDiff(g: number | null | undefined, resolutionG?: number): string {
  if (g === null || g === undefined || Number.isNaN(g)) return '—';
  const sign = g >= 0 ? '+' : '−';
  const abs = Math.abs(g);
  const res = resolutionG ?? defaultResolutionG;
  if (abs >= 1000) {
    return `${sign}${localizeNumber((abs / 1000).toFixed(KG_DECIMALS), true)} kg`;
  }
  return `${sign}${localizeNumber(abs.toFixed(decimalsForResolution(res)), true)} g`;
}

/**
 * Modell-spezifische Gramm-Anzeige, eindeutig zwischen den Locales.
 *
 * Vermeidet Konstrukte wie „6,000 kg" (im DE-Kontext = 6 kg, wird aber
 * von englischen Lesern als 6000 kg fehlinterpretiert):
 *
 *   - ganze kg                       → „6 kg",  „30 kg"
 *   - krumme Werte ab 1 kg           → „6.500 g" (DE) / „6,500 g" (EN)
 *   - Bruchteile von Gramm           → „0,1 g"  (DE) / „0.1 g"  (EN)
 *   - sonst                          → „220 g"
 *
 * So bleibt die Aussage in jeder Sprache eindeutig: ganze Kilogramm
 * werden ohne Dezimaltrenner geschrieben, krumme Werte komplett in
 * Gramm mit Tausender-Trenner.
 */
export function formatGramsCompact(g: number | null | undefined): string {
  if (g === null || g === undefined || Number.isNaN(g)) return '—';
  const fmt = currentNumberFormat();
  // Ganzzahlige Kilogramm: ohne Dezimaltrenner — eindeutig
  if (g >= 1000 && g % 1000 === 0) {
    return `${g / 1000} kg`;
  }
  // Sub-Gramm und kleine Werte: mit passender Auflösung in Gramm
  const dec = g < 1 ? Math.min(6, decimalsForResolution(Math.abs(g))) : 0;
  if (g < 1 && dec > 0) {
    // 0,001 g, 0,0001 g …  — Locale-Dezimal anwenden
    return `${g.toFixed(dec).replace('.', fmt.decimal)} g`;
  }
  // 1 g … 999 g sowie krumme kg → vollständig in g mit Tausender-Trenner
  const intPart = Math.trunc(g);
  const grouped = intPart >= 1000
    ? String(intPart).replace(/\B(?=(\d{3})+(?!\d))/g, fmt.thousand)
    : String(intPart);
  const fracPart = g % 1;
  if (fracPart === 0) return `${grouped} g`;
  // krummer Wert mit Nachkommastelle (selten bei Modellen)
  const fracStr = String(g).split('.')[1] ?? '';
  return `${grouped}${fmt.decimal}${fracStr} g`;
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

// ===========================================================================
//  Stable Display — Ghost-Ziffern für nicht belegte Stellen
// ===========================================================================

export interface DisplaySegment {
  text: string;
  /** wenn true: 90 % Transparenz — nicht belegte Vorlauf-Stellen. */
  ghost: boolean;
  /** Klassifizierung für CSS-Layout: digit, sep, decimal, sign, unit. */
  kind: 'digit' | 'sep' | 'decimal' | 'sign' | 'unit';
}

/**
 * Zerlegt einen Wägewert in eine stabile Segment-Liste, ohne die
 * Stellen-Zahl zwischen Aufrufen zu verändern. Führende Nullen werden
 * als `ghost` markiert — visuell schwach (10 % Opazität), damit die
 * Anzeige nicht zappelt.
 *
 * Beispiel max=6000, res=0,1:
 *   value=12,3   →  0  .  0  1  2  ,  3  ' g'    (Ghost: 0, ., 0)
 *   value=0      →  0  .  0  0  0  ,  0  ' g'    (Ghost: 0, ., 0, 0)
 *   value=1234,5 →  1  .  2  3  4  ,  5  ' g'    (kein Ghost)
 */
export function buildStableSegments(
  g: number | null | undefined,
  model: { max_g: number; resolution_g: number } | null,
): DisplaySegment[] {
  const fmt = currentNumberFormat();
  const maxG = model?.max_g ?? 6000;
  const resolutionG = model?.resolution_g ?? defaultResolutionG;
  const decimals = decimalsForResolution(resolutionG);
  const intDigits = intDigitsForMax(maxG);
  const segs: DisplaySegment[] = [];

  if (g === null || g === undefined || Number.isNaN(g)) {
    // Komplett-Ghost: alle möglichen Stellen abschwächen
    return buildGhostFrame(intDigits, decimals, fmt);
  }

  const isNeg = g < 0;
  const abs = Math.abs(g);
  // Begrenze auf Modell-Max — alles darüber ist „außerhalb des
  // Anzeige-Bereichs", aber wir zeigen den Wert trotzdem (nicht abschneiden).
  const fixed = abs.toFixed(decimals);              // "12.3"
  const [whole, frac] = fixed.split('.');
  // Wenn der Wert die Anzeige-Breite sprengt, dehnen wir aus.
  const padded = whole.length >= intDigits
    ? whole
    : whole.padStart(intDigits, '0');

  // Index der ersten signifikanten Ziffer (1-9). Bei value=0 ist es
  // die letzte Ziffer vor dem Komma.
  const firstReal = padded.search(/[1-9]/);
  const ghostUntil = firstReal === -1 ? padded.length - 1 : firstReal;

  // Minus-Slot ist immer reserviert — bei positivem Wert ghost,
  // bei negativem Wert opak. Damit zappelt die Stellen-Position
  // nicht, wenn der Wert das Vorzeichen wechselt.
  segs.push({ text: '−', ghost: !isNeg, kind: 'sign' });

  // Tausender-Trenner alle 3 Stellen von rechts; ghost wenn vor erstem real.
  let cursor = 0;
  for (let i = 0; i < padded.length; i++) {
    if (cursor > 0 && (padded.length - cursor) % 3 === 0 && i > 0) {
      segs.push({
        text: fmt.thousand,
        ghost: cursor <= ghostUntil,
        kind: 'sep',
      });
    }
    segs.push({
      text: padded[i],
      ghost: cursor < ghostUntil,
      kind: 'digit',
    });
    cursor++;
  }

  if (decimals > 0 && frac !== undefined) {
    segs.push({ text: fmt.decimal, ghost: false, kind: 'decimal' });
    for (const ch of frac) {
      segs.push({ text: ch, ghost: false, kind: 'digit' });
    }
  }

  segs.push({ text: ' g', ghost: false, kind: 'unit' });
  return segs;
}

/** Wenn kein Wert vorliegt, zeigen wir die Display-Maske komplett ghost. */
function buildGhostFrame(
  intDigits: number,
  decimals: number,
  fmt: NumberFormatOpts,
): DisplaySegment[] {
  const segs: DisplaySegment[] = [];
  segs.push({ text: '−', ghost: true, kind: 'sign' });
  for (let i = 0; i < intDigits; i++) {
    if (i > 0 && (intDigits - i) % 3 === 0) {
      segs.push({ text: fmt.thousand, ghost: true, kind: 'sep' });
    }
    segs.push({ text: '0', ghost: true, kind: 'digit' });
  }
  if (decimals > 0) {
    segs.push({ text: fmt.decimal, ghost: true, kind: 'decimal' });
    for (let i = 0; i < decimals; i++) {
      segs.push({ text: '0', ghost: true, kind: 'digit' });
    }
  }
  segs.push({ text: ' g', ghost: true, kind: 'unit' });
  return segs;
}

interface NumberFormatOpts { decimal: string; thousand: string; }

/** Reine Funktion, Locale-Format explizit übergeben — nutzbar für Tests. */
export function buildStableSegmentsWith(
  g: number | null | undefined,
  model: { max_g: number; resolution_g: number },
  fmt: NumberFormatOpts,
): DisplaySegment[] {
  const decimals = decimalsForResolution(model.resolution_g);
  const intDigits = intDigitsForMax(model.max_g);
  const segs: DisplaySegment[] = [];

  if (g === null || g === undefined || Number.isNaN(g)) {
    return buildGhostFrame(intDigits, decimals, fmt);
  }

  const isNeg = g < 0;
  const abs = Math.abs(g);
  const fixed = abs.toFixed(decimals);
  const [whole, frac] = fixed.split('.');
  const padded = whole.length >= intDigits
    ? whole
    : whole.padStart(intDigits, '0');
  const firstReal = padded.search(/[1-9]/);
  const ghostUntil = firstReal === -1 ? padded.length - 1 : firstReal;

  segs.push({ text: '−', ghost: !isNeg, kind: 'sign' });

  let cursor = 0;
  for (let i = 0; i < padded.length; i++) {
    if (cursor > 0 && (padded.length - cursor) % 3 === 0 && i > 0) {
      segs.push({ text: fmt.thousand, ghost: cursor <= ghostUntil, kind: 'sep' });
    }
    segs.push({ text: padded[i], ghost: cursor < ghostUntil, kind: 'digit' });
    cursor++;
  }
  if (decimals > 0 && frac !== undefined) {
    segs.push({ text: fmt.decimal, ghost: false, kind: 'decimal' });
    for (const ch of frac) {
      segs.push({ text: ch, ghost: false, kind: 'digit' });
    }
  }
  segs.push({ text: ' g', ghost: false, kind: 'unit' });
  return segs;
}
