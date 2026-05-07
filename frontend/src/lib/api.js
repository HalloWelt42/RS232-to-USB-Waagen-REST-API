/**
 * Mini-Client für das Waage-Backend.
 * Im Dev-Modus läuft das Backend hinter dem Vite-Proxy unter /api/*.
 * In Production hängt nginx /api/ ans Backend.
 */

const BASE = '/api';

async function request(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Accept': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

export const api = {
  info:    ()              => request('/'),
  health:  ()              => request('/health'),
  weight:  ()              => request('/weight'),
  stable:  (timeout = 5)   => request(`/weight/stable?timeout=${timeout}`),
  history: (limit = 100)   => request(`/history?limit=${limit}`),
  count:   ()              => request('/count'),
  countCalibrate: (referenceCount) =>
    request('/count/calibrate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reference_count: referenceCount }),
    }),
  countReset: () =>
    request('/count/reset', { method: 'POST' }),
  cmdTare:  () => request('/command/tare',  { method: 'POST' }),
  cmdUnit:  () => request('/command/unit',  { method: 'POST' }),
  cmdLight: () => request('/command/light', { method: 'POST' }),
  // Samples (festgehaltene Werte)
  sampleAdd: (label = '', note = '', session = 'default') =>
    request('/samples', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label, note, session }),
    }),
  sampleList: (session = null, limit = 500) => {
    const q = new URLSearchParams();
    if (session) q.set('session', session);
    q.set('limit', String(limit));
    return request(`/samples?${q.toString()}`);
  },
  sampleDelete: (id) => request(`/samples/${id}`, { method: 'DELETE' }),
  sampleClear:  (session = null) => {
    const q = session ? `?session=${encodeURIComponent(session)}` : '';
    return request(`/samples${q}`, { method: 'DELETE' });
  },
  sampleStats:  (session = null) => {
    const q = session ? `?session=${encodeURIComponent(session)}` : '';
    return request(`/samples/stats${q}`);
  },
  sampleExportUrl: (session = null) => {
    const q = session ? `?session=${encodeURIComponent(session)}` : '';
    return `/api/samples/export.csv${q}`;
  },
};

/**
 * WebSocket-Stream mit automatischem Reconnect.
 * Aufruf: const close = subscribe((reading) => ...);
 */
export function subscribe(onReading, onState = () => {}) {
  let ws = null;
  let closed = false;
  let backoff = 500;

  function connect() {
    if (closed) return;
    onState({ status: 'connecting' });
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${location.host}/stream`);

    ws.addEventListener('open', () => {
      backoff = 500;
      onState({ status: 'open' });
    });
    ws.addEventListener('message', (ev) => {
      try {
        onReading(JSON.parse(ev.data));
      } catch (e) {
        console.error('Bad message', e, ev.data);
      }
    });
    ws.addEventListener('close', () => {
      onState({ status: 'closed' });
      if (closed) return;
      setTimeout(connect, backoff);
      backoff = Math.min(backoff * 2, 10_000);
    });
    ws.addEventListener('error', (ev) => {
      onState({ status: 'error', error: ev });
      ws.close();
    });
  }

  connect();

  return () => {
    closed = true;
    if (ws) ws.close();
  };
}
