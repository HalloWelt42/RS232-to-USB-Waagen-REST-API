/**
 * Zentrale Domain-Typen für das Frontend.
 *
 * Spiegeln die Pydantic-Schemas im Backend (siehe ``backend/src/waage/api.py``)
 * wider und bilden die einzige Quelle der Wahrheit für TypeScript-Konsumenten.
 */

export type Status = 'ok' | 'low' | 'high' | 'idle';
export type ConnectionState = 'connecting' | 'open' | 'closed' | 'error';

/** Ein einzelner Wägewert mit Metadaten. */
export interface Reading {
  weight_g: number;
  unit: string;
  stable: boolean;
  timestamp: string;
  raw: string;
}

/** Lebenszyklus-Information aus ``/health``. */
export interface HealthInfo {
  ok: boolean;
  reader_alive: boolean;
  last_seen: string | null;
  port: string;
  baudrate: number;
  uptime_seconds: number;
}

/** Bezeichnung eines Endpoints in der ``/``-Übersicht. */
export interface ApiInfo {
  name: string;
  version: string;
  description: string;
  endpoints: Record<string, string>;
}

/** Ringpuffer-Liste vom Server. */
export interface HistoryResponse {
  count: number;
  items: Reading[];
}

/** Status des QC-Toleranzmodus. */
export interface ToleranceState {
  active: boolean;
  target_g: number | null;
  tolerance_minus_g: number | null;
  tolerance_plus_g: number | null;
  min_g: number | null;
  max_g: number | null;
  current_g: number | null;
  deviation_g: number | null;
  status: Status;
}

/** Brutto-Tara-Netto-Status. */
export interface NettoState {
  active: boolean;
  tare_g: number | null;
  gross_g: number | null;
  netto_g: number | null;
  tare_set_at: string | null;
  stable: boolean | null;
}

/** Zählmodus-Status. */
export interface CountState {
  pieces: number | null;
  pieces_exact: number | null;
  piece_weight_g: number | null;
  total_weight_g: number | null;
  reference_count: number | null;
  calibrated_at: string | null;
  stable: boolean | null;
  calibrated: boolean;
}

/** Ein gespeicherter Snapshot. */
export interface Sample {
  id: number;
  ts: string;
  weight_g: number;
  unit: string;
  stable: boolean;
  label: string;
  note: string;
  session: string;
}

export interface SampleListResponse {
  count: number;
  items: Sample[];
}

export interface SampleStats {
  count: number;
  min_g: number | null;
  max_g: number | null;
  mean_g: number | null;
  stdev_g: number | null;
  sum_g: number | null;
  session: string | null;
}

/** Ergebnis eines Hardware-Kommandos. */
export interface CommandResult {
  ok: boolean;
  command: string;
  hex: string;
}
