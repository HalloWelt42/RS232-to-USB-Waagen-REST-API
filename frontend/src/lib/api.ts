/**
 * REST-Clients für die getrennten Backend-Bereiche.
 *
 *   ScaleApi    -> /scale/*  reine Hardware-Funktion
 *   AppApi      -> /app/*    UI-Komfort-Features
 *
 * Beide Klassen können einzeln verwendet werden — Drittsysteme können
 * z.B. nur die ScaleApi nehmen, ohne die AppApi mitzuschleppen. Die
 * Default-Instanz ``api`` bündelt beide für die Web-UI.
 */

import type {
  ApiInfo,
  CommandResult,
  Container,
  ContainerInput,
  ContainerListResponse,
  ContainerPatch,
  CountState,
  CountTemplateRecord,
  CountTemplateInput,
  CountTemplateListResponse,
  CountTemplatePatch,
  DifferenzState,
  HealthInfo,
  HistoryResponse,
  MesslogResponse,
  NettoState,
  Reading,
  Sample,
  SampleListResponse,
  SampleStats,
  ScaleConfig,
  ScaleModel,
  SourceState,
  ToleranceState,
} from './types';

// -----------------------------------------------------------------------
//  Basis-Klasse mit fetch + Fehlerbehandlung
// -----------------------------------------------------------------------

class HttpBase {
  constructor(protected readonly base: string) {}

  protected async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...((init.headers as Record<string, string>) ?? {}),
    };
    const res = await fetch(`${this.base}${path}`, { ...init, headers });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  }

  protected post<T>(path: string, body?: unknown): Promise<T> {
    const init: RequestInit = { method: 'POST' };
    if (body !== undefined) {
      init.headers = { 'Content-Type': 'application/json' };
      init.body = JSON.stringify(body);
    }
    return this.request<T>(path, init);
  }

  protected put<T>(path: string, body?: unknown): Promise<T> {
    const init: RequestInit = { method: 'PUT' };
    if (body !== undefined) {
      init.headers = { 'Content-Type': 'application/json' };
      init.body = JSON.stringify(body);
    }
    return this.request<T>(path, init);
  }

  protected del<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' });
  }
}

// -----------------------------------------------------------------------
//  ScaleApi — alle /scale/* Endpoints
// -----------------------------------------------------------------------

export class ScaleApi extends HttpBase {
  constructor(base = '/api') {
    super(base);
  }

  weight(): Promise<Reading>          { return this.request('/scale/weight'); }
  stable(timeout = 5): Promise<Reading> {
    return this.request(`/scale/weight/stable?timeout=${timeout}`);
  }
  history(limit = 100): Promise<HistoryResponse> {
    return this.request(`/scale/history?limit=${limit}`);
  }
  health(): Promise<HealthInfo>       { return this.request('/scale/health'); }

  cmdTare(): Promise<CommandResult>   { return this.post('/scale/command/tare'); }
  cmdUnit(): Promise<CommandResult>   { return this.post('/scale/command/unit'); }
  cmdLight(): Promise<CommandResult>  { return this.post('/scale/command/light'); }

  models(): Promise<ScaleModel[]>     { return this.request('/scale/models'); }
  config(): Promise<ScaleConfig>      { return this.request('/scale/config'); }
  setConfig(modelId: string): Promise<ScaleConfig> {
    return this.put('/scale/config', { model_id: modelId });
  }

  source(): Promise<SourceState>      { return this.request('/scale/source'); }
  setSource(mode: 'live' | 'simulate'): Promise<SourceState> {
    return this.put('/scale/source', { mode });
  }

  /** WebSocket-URL für /scale/stream (Browser-Side) */
  streamUrl(): string {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    return `${proto}://${location.host}${this.base}/scale/stream`;
  }
}

// -----------------------------------------------------------------------
//  AppApi — alle /app/* Endpoints
// -----------------------------------------------------------------------

export class AppApi extends HttpBase {
  constructor(base = '/api') {
    super(base);
  }

  // Toleranz
  tolerance(): Promise<ToleranceState>             { return this.request('/app/tolerance'); }
  toleranceSet(t: number, m: number, p: number): Promise<ToleranceState> {
    return this.post('/app/tolerance',
      { target_g: t, tolerance_minus_g: m, tolerance_plus_g: p });
  }
  toleranceClear(): Promise<ToleranceState>        { return this.del('/app/tolerance'); }

  // Netto
  netto(): Promise<NettoState>                     { return this.request('/app/netto'); }
  nettoTareCurrent(): Promise<NettoState>          { return this.post('/app/netto/tare', {}); }
  nettoTareValue(g: number): Promise<NettoState>   { return this.post('/app/netto/tare', { tare_g: g }); }
  nettoTareClear(): Promise<NettoState>            { return this.del('/app/netto/tare'); }

  // Count
  count(): Promise<CountState>                     { return this.request('/app/count'); }
  countCalibrate(n: number): Promise<CountState>   { return this.post('/app/count/calibrate', { reference_count: n }); }
  countReset(): Promise<CountState>                { return this.post('/app/count/reset'); }

  // Samples
  samplesAdd(label='', note='', session='default'): Promise<Sample> {
    return this.post('/app/samples', { label, note, session });
  }
  samplesList(session: string | null = null, limit = 500): Promise<SampleListResponse> {
    const q = new URLSearchParams();
    if (session) q.set('session', session);
    q.set('limit', String(limit));
    return this.request(`/app/samples?${q.toString()}`);
  }
  samplesDelete(id: number): Promise<{ ok: boolean; id: number }> {
    return this.del(`/app/samples/${id}`);
  }
  samplesClear(session: string | null = null): Promise<{ ok: boolean; deleted: number }> {
    const q = session ? `?session=${encodeURIComponent(session)}` : '';
    return this.del(`/app/samples${q}`);
  }
  samplesStats(session: string | null = null): Promise<SampleStats> {
    const q = session ? `?session=${encodeURIComponent(session)}` : '';
    return this.request(`/app/samples/stats${q}`);
  }
  samplesExportUrl(session: string | null = null): string {
    const q = session ? `?session=${encodeURIComponent(session)}` : '';
    return `${this.base}/app/samples/export.csv${q}`;
  }

  // Differenz
  differenz(): Promise<DifferenzState>             { return this.request('/app/differenz'); }
  differenzPushCurrent(label = ''): Promise<DifferenzState> {
    return this.post('/app/differenz/push', { label });
  }
  differenzPushValue(g: number, label = ''): Promise<DifferenzState> {
    return this.post('/app/differenz/push', { weight_g: g, label });
  }
  differenzRemove(id: number): Promise<DifferenzState> {
    return this.del(`/app/differenz/${id}`);
  }
  differenzClear(): Promise<DifferenzState>        { return this.del('/app/differenz'); }

  // Messlog
  messlog(limit = 200): Promise<MesslogResponse>   {
    return this.request(`/app/messlog?limit=${limit}`);
  }
  messlogClear(): Promise<{ ok: boolean; deleted: number }> {
    return this.del('/app/messlog');
  }

  // Behälter-Bibliothek
  containersList(): Promise<ContainerListResponse> {
    return this.request('/app/containers');
  }
  containersAdd(payload: ContainerInput): Promise<Container> {
    return this.post('/app/containers', payload);
  }
  containersUpdate(id: number, patch: ContainerPatch): Promise<Container> {
    return this.put(`/app/containers/${id}`, patch);
  }
  containersDelete(id: number): Promise<{ ok: boolean; id: number }> {
    return this.del(`/app/containers/${id}`);
  }
  containersClear(): Promise<{ ok: boolean; deleted: number }> {
    return this.del('/app/containers');
  }

  // Stückzähl-Vorlagen
  countTemplatesList(): Promise<CountTemplateListResponse> {
    return this.request('/app/count/templates');
  }
  countTemplatesAdd(payload: CountTemplateInput): Promise<CountTemplateRecord> {
    return this.post('/app/count/templates', payload);
  }
  countTemplatesUpdate(id: number, patch: CountTemplatePatch): Promise<CountTemplateRecord> {
    return this.put(`/app/count/templates/${id}`, patch);
  }
  countTemplatesDelete(id: number): Promise<{ ok: boolean; id: number }> {
    return this.del(`/app/count/templates/${id}`);
  }
  countTemplatesClear(): Promise<{ ok: boolean; deleted: number }> {
    return this.del('/app/count/templates');
  }
}

// -----------------------------------------------------------------------
//  Convenience-Bundle für die Web-UI
// -----------------------------------------------------------------------

export class WaageApi extends HttpBase {
  scale: ScaleApi;
  app: AppApi;

  constructor(base = '/api') {
    super(base);
    this.scale = new ScaleApi(base);
    this.app = new AppApi(base);
  }

  info(): Promise<ApiInfo> { return this.request('/'); }
}

export const api = new WaageApi();
