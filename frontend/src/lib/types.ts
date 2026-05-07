/**
 * Domain-Typen, gespiegelt zu den Pydantic-Schemas im Backend
 * (siehe backend/src/waage/scale_api.py und app_api.py).
 */

export type ConnectionState = 'connecting' | 'open' | 'closed' | 'error';
export type Status = 'ok' | 'low' | 'high' | 'idle';
export type MesslogKind = 'change' | 'tare' | 'start';

export interface Reading {
  weight_g: number;
  unit: string;
  stable: boolean;
  timestamp: string;
  raw: string;
}

export interface HealthInfo {
  ok: boolean;
  reader_alive: boolean;
  last_seen: string | null;
  port: string;
  baudrate: number;
  uptime_seconds: number;
  version: string;
}

export interface ApiInfo {
  name: string;
  version: string;
  description: string;
  endpoints: Record<string, string>;
}

export interface HistoryResponse {
  count: number;
  items: Reading[];
}

export interface CommandResult {
  ok: boolean;
  command: string;
  hex: string;
}

export interface ScaleModel {
  id: string;
  manufacturer: string;
  series: string;
  name: string;
  category: string;
  max_g: number;
  resolution_g: number;
  default_baudrate: number;
  rs232: boolean;
  note: string;
}

export interface ScaleConfig {
  active_model_id: string;
  active_model: ScaleModel;
}

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

export interface NettoState {
  active: boolean;
  tare_g: number | null;
  gross_g: number | null;
  netto_g: number | null;
  tare_set_at: string | null;
  stable: boolean | null;
}

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

export interface TareLayer {
  id: number;
  label: string;
  weight_g: number;
  set_at: string;
}

export interface DifferenzState {
  layers: TareLayer[];
  total_tare_g: number;
  gross_g: number | null;
  netto_g: number | null;
}

export interface MesslogEntry {
  id: number;
  ts: string;
  kind: MesslogKind;
  diff_g: number | null;
  value_g: number;
  unit: string;
  stable: boolean;
}

export interface MesslogResponse {
  count: number;
  items: MesslogEntry[];
}
