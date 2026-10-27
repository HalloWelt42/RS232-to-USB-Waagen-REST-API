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
 *
 * `scaleState` fasst den Zustand der Waage für Statuslampe, Anzeige
 * und Anschluss-Hinweis zusammen; alle lesen dieselbe Ableitung.
 */
import type { HealthInfo } from './types';

/**
 * Zustand der Waage aus Sicht der Oberfläche:
 *   live       echte Hardware liefert Werte
 *   simulated  Simulator statt Hardware
 *   noAdapter  kein USB-Seriell-Adapter angeschlossen
 *   offline    Adapter steckt (oder Backend kennt das Feld noch nicht),
 *              die Waage antwortet aber nicht
 */
export type ScaleState = 'live' | 'simulated' | 'noAdapter' | 'offline';

/** Kurzbeschriftung je Zustand (Statusleiste und Live-Anzeige). */
export const SCALE_LABEL_KEY: Record<ScaleState, string> = {
  live: 'live.scaleConnected',
  simulated: 'live.scaleSimulated',
  noAdapter: 'live.scaleNoAdapter',
  offline: 'live.scaleOffline',
};

class HealthStore {
  info = $state<HealthInfo | null>(null);

  set(h: HealthInfo | null): void { this.info = h; }

  /** True nur, wenn die Hardware-Waage echt erreichbar ist UND
   *  innerhalb der konfigurierten Stale-Schwelle Frames geliefert
   *  hat. `scale_alive` aus dem Backend ist die kanonische Quelle
   *  (führt den Stale-Check selbst aus); `reader_alive` allein ist
   *  irreführend, weil der Reader-Task auch ohne Hardware läuft. */
  get scaleOk(): boolean {
    const h = this.info;
    if (!h || h.simulated) return false;
    // scale_alive ist seit 0.5.x verfügbar; Fallback auf reader_alive
    // für ältere Backends, die das Feld noch nicht ausliefern.
    if (typeof h.scale_alive === 'boolean') return h.scale_alive;
    return !!h.reader_alive;
  }

  get scaleState(): ScaleState {
    const h = this.info;
    if (h?.simulated) return 'simulated';
    if (this.scaleOk) return 'live';
    // Nur ein ausdrückliches false heißt "kein Adapter"; ältere
    // Backends ohne das Feld bleiben bei "Waage aus".
    if (h?.adapter_present === false) return 'noAdapter';
    return 'offline';
  }

  /** Sekunden seit dem letzten Frame — für Diagnose-Anzeigen. */
  get staleForS(): number | null {
    const v = this.info?.stale_for_s;
    return typeof v === 'number' ? v : null;
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
