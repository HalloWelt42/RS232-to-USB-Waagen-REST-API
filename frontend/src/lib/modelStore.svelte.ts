/**
 * Reaktiver Speicher für das aktive Waagen-Modell.
 *
 * Liest beim Start `/scale/config` aus und stellt das gewählte Modell
 * der gesamten App zur Verfügung. Ändert der Anwender im Settings-Tab
 * das Modell, schreibt der Store das neue Modell und alle Komponenten
 * werden über $derived/$effect reaktiv aktualisiert.
 */

import { api } from './api';
import { formatGramsCompact } from './format';
import type { ScaleModel } from './types';

/**
 * Sicherheitsnetz, falls das Backend im aktuellen Moment nicht
 * erreichbar ist — möglichst neutral, mit konservativer Auflösung.
 */
const FALLBACK_MODEL: ScaleModel = {
  id: 'unknown',
  manufacturer: 'Waage',
  series: '',
  name: 'Modell wird geladen …',
  category: 'precision',
  max_g: 1000,
  resolution_g: 0.1,
  default_baudrate: 9600,
  rs232: true,
  note: '',
  min_load_g: 0,
  linearity_g: 0,
  repeatability_g: 0,
  stabilization_s: 0,
  warmup_min: 0,
  operating_temp_c: null,
};

class ModelStore {
  active = $state<ScaleModel>(FALLBACK_MODEL);
  loaded = $state(false);

  async refresh(): Promise<void> {
    try {
      const cfg = await api.scale.config();
      this.active = cfg.active_model;
      this.loaded = true;
    } catch {
      // offline tolerieren — UI zeigt weiter den letzten bekannten Stand
    }
  }

  setActive(model: ScaleModel): void {
    this.active = model;
    this.loaded = true;
  }

  /** Anzeigename in der Form „Hersteller Serie-Name", z.B. „G&G PLC-6000". */
  get displayName(): string {
    const m = this.active;
    if (!m.series && !m.name) return m.manufacturer || 'Waage';
    const series = m.series ? `${m.series}` : '';
    return [m.manufacturer, series && m.name ? `${series}-${m.name.split(' ')[0]}` : (series || m.name)]
      .filter(Boolean).join(' ');
  }

  /** Kompaktes Label mit Eckdaten — z.B. „G&G PLC-6000 · 6 kg / 0,1 g".
   *
   *  Nutzt `formatGramsCompact`, das ganze Kilogramm ohne Dezimaltrenner
   *  schreibt — vermeidet die mehrdeutige Form „6,000 kg" zwischen DE
   *  und EN. */
  get compactLabel(): string {
    return `${this.displayName} · ${formatGramsCompact(this.active.max_g)} / ${formatGramsCompact(this.active.resolution_g)}`;
  }
}

export const modelStore = new ModelStore();
