/** Globaler reaktiver Live-Wert. */
import type { ConnectionState, Reading } from './types';

class LiveStore {
  reading = $state<Reading | null>(null);
  connection = $state<ConnectionState>('connecting');

  set(r: Reading | null): void { this.reading = r; }
  setConnection(s: ConnectionState): void { this.connection = s; }
  weight(): number | null { return this.reading?.weight_g ?? null; }
}

export const live = new LiveStore();
