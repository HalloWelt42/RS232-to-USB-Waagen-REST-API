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
