/**
 * REST-Client für das Waagen-Backend.
 *
 * Klassischer OOP-Wrapper: alle Methoden sind Mitglieder einer einzigen
 * Klasse, die mit dem Basis-Pfad ``/api`` arbeitet. Im Dev-Modus reicht
 * Vite die Anfragen weiter an ``http://localhost:8200``, in Produktion
 * übernimmt nginx den Proxy.
 */

import type {
  ApiInfo,
  CommandResult,
  CountState,
  HealthInfo,
  HistoryResponse,
  NettoState,
  Reading,
  Sample,
  SampleListResponse,
  SampleStats,
  ToleranceState,
} from './types';

export class WaageApi {
  constructor(private readonly base: string = '/api') {}

  /** Generische JSON-Anfrage mit einheitlicher Fehlerbehandlung. */
  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...((init.headers as Record<string, string>) ?? {}),
    };
    const res = await fetch(`${this.base}${path}`, { ...init, headers });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    if (res.status === 204) {
      return undefined as T;
    }
    return res.json() as Promise<T>;
  }

  private async post<T>(path: string, body?: unknown): Promise<T> {
    const init: RequestInit = { method: 'POST' };
    if (body !== undefined) {
      init.headers = { 'Content-Type': 'application/json' };
      init.body = JSON.stringify(body);
    }
    return this.request<T>(path, init);
  }

  private del<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' });
  }

  // ---------------- Meta -----------------------------------------
  info(): Promise<ApiInfo>     { return this.request('/'); }
  health(): Promise<HealthInfo> { return this.request('/health'); }

  // ---------------- Wägung ---------------------------------------
  weight(): Promise<Reading> { return this.request('/weight'); }
  stable(timeout = 5): Promise<Reading> {
    return this.request(`/weight/stable?timeout=${timeout}`);
  }
  history(limit = 100): Promise<HistoryResponse> {
    return this.request(`/history?limit=${limit}`);
  }

  // ---------------- Kommandos -----------------------------------
  cmdTare(): Promise<CommandResult>  { return this.post('/command/tare'); }
  cmdUnit(): Promise<CommandResult>  { return this.post('/command/unit'); }
  cmdLight(): Promise<CommandResult> { return this.post('/command/light'); }

  // ---------------- Zählmodus -----------------------------------
  count(): Promise<CountState> { return this.request('/count'); }
  countCalibrate(referenceCount: number): Promise<CountState> {
    return this.post('/count/calibrate', { reference_count: referenceCount });
  }
  countReset(): Promise<CountState> { return this.post('/count/reset'); }

  // ---------------- Snapshots -----------------------------------
  sampleAdd(label = '', note = '', session = 'default'): Promise<Sample> {
    return this.post('/samples', { label, note, session });
  }
  sampleList(session: string | null = null, limit = 500): Promise<SampleListResponse> {
    const q = new URLSearchParams();
    if (session !== null && session !== '') q.set('session', session);
    q.set('limit', String(limit));
    return this.request(`/samples?${q.toString()}`);
  }
  sampleDelete(id: number): Promise<{ ok: boolean; id: number }> {
    return this.del(`/samples/${id}`);
  }
  sampleClear(session: string | null = null): Promise<{ ok: boolean; deleted: number }> {
    const q = session ? `?session=${encodeURIComponent(session)}` : '';
    return this.del(`/samples${q}`);
  }
  sampleStats(session: string | null = null): Promise<SampleStats> {
    const q = session ? `?session=${encodeURIComponent(session)}` : '';
    return this.request(`/samples/stats${q}`);
  }
  sampleExportUrl(session: string | null = null): string {
    const q = session ? `?session=${encodeURIComponent(session)}` : '';
    return `${this.base}/samples/export.csv${q}`;
  }

  // ---------------- QC-Toleranz ---------------------------------
  tolerance(): Promise<ToleranceState> { return this.request('/tolerance'); }
  toleranceSet(target_g: number, minus: number, plus: number): Promise<ToleranceState> {
    return this.post('/tolerance', {
      target_g, tolerance_minus_g: minus, tolerance_plus_g: plus,
    });
  }
  toleranceClear(): Promise<ToleranceState> { return this.del('/tolerance'); }

  // ---------------- Software-Tara / Netto -----------------------
  netto(): Promise<NettoState> { return this.request('/netto'); }
  nettoTareCurrent(): Promise<NettoState> {
    return this.post('/netto/tare', {});
  }
  nettoTareValue(tare_g: number): Promise<NettoState> {
    return this.post('/netto/tare', { tare_g });
  }
  nettoTareClear(): Promise<NettoState> { return this.del('/netto/tare'); }
}

/** Default-Instanz, von Komponenten direkt importiert. */
export const api = new WaageApi();
