/**
 * Reaktiver Speicher für den Health-Status des Backends.
 *
 * App.svelte pollt das Backend alle paar Sekunden und schreibt die
 * Antwort in diesen Store; Komponenten lesen ihn direkt aus.
 *
 * Daraus leiten Status-Indikatoren zwei getrennte Aussagen ab:
 *
 *   • backendOk  — REST/WS antwortet überhaupt
 *   • scaleOk    — der Reader liest aktiv echte Hardware (NICHT der
 *                  SimulatedWaage). Im Simulator-Modus ist diese
 *                  LED nie grün, auch wenn Werte fließen.
 */
import type { HealthInfo } from './types';

class HealthStore {
  info = $state<HealthInfo | null>(null);

  set(h: HealthInfo | null): void { this.info = h; }

  /** True nur, wenn die Hardware-Waage echt erreichbar ist. */
  get scaleOk(): boolean {
    const h = this.info;
    return !!(h && h.reader_alive && !h.simulated);
  }

  /** True wenn das Backend ansprechbar ist und aktuell Werte liefert. */
  get backendOk(): boolean {
    const h = this.info;
    return !!(h && h.ok);
  }

  get simulated(): boolean {
    return !!this.info?.simulated;
  }
}

export const healthStore = new HealthStore();
