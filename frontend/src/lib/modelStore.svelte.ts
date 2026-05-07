/**
 * Reaktiver Speicher für das aktive Waagen-Modell.
 *
 * Liest beim Start `/scale/config` aus und stellt das gewählte Modell
 * der gesamten App zur Verfügung. Ändert der Anwender im Settings-Tab
 * das Modell, schreibt der Store das neue Modell und alle Komponenten
 * werden über $derived/$effect reaktiv aktualisiert.
 */

import { api } from './api';
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

  /** Kompaktes Label mit Eckdaten — „G&G PLC-6000 · 6000 g / 0,1 g". */
  get compactLabel(): string {
    const m = this.active;
    const max = m.max_g >= 1000 ? `${m.max_g / 1000} kg` : `${m.max_g} g`;
    const res = m.resolution_g >= 1
      ? `${m.resolution_g} g`
      : `${m.resolution_g.toString().replace('.', ',')} g`;
    return `${this.displayName} · ${max} / ${res}`;
  }
}

export const modelStore = new ModelStore();
