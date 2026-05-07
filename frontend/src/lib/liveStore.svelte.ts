/**
 * Globaler reaktiver Store für den aktuellen Wägewert.
 *
 * Die App-Komponente schreibt das letzte Reading hinein, alle Tab-Panels
 * lesen es daraus — insbesondere für die "Wert übernehmen"-Aktion, die
 * den Live-Wert in Eingabefelder einsetzt, ohne dass die Panels Props
 * weiterreichen müssen.
 */

import type { Reading } from './types';

class LiveStore {
  reading = $state<Reading | null>(null);

  set(r: Reading | null): void {
    this.reading = r;
  }

  /** Gewicht in Gramm, oder null wenn noch nichts gelesen. */
  weight(): number | null {
    return this.reading?.weight_g ?? null;
  }
}

export const live = new LiveStore();
