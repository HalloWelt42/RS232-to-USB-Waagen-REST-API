/**
 * WebSocket-Client mit automatischem Reconnect.
 *
 * Klassen-basierter Wrapper um den nativen ``WebSocket``: pusht eingehende
 * ``Reading``-Frames an den ``onReading``-Callback und meldet Verbindungs-
 * zustände an ``onState``. Bei Verbindungsabbruch reconnectet die Klasse
 * mit exponentiellem Backoff bis maximal zehn Sekunden.
 */

import type { ConnectionState, Reading } from './types';

export type ReadingCallback = (reading: Reading) => void;
export type StateCallback   = (state: { status: ConnectionState; error?: unknown }) => void;

export class WaageStream {
  private ws: WebSocket | null = null;
  private closed = false;
  private backoffMs = 500;
  private readonly maxBackoffMs = 10_000;

  constructor(
    private readonly path: string = '/stream',
    private readonly onReading: ReadingCallback = () => undefined,
    private readonly onState: StateCallback = () => undefined,
  ) {}

  start(): void {
    this.closed = false;
    this.connect();
  }

  stop(): void {
    this.closed = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private connect(): void {
    if (this.closed) return;
    this.onState({ status: 'connecting' });

    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${proto}://${location.host}${this.path}`;
    const ws = new WebSocket(url);
    this.ws = ws;

    ws.addEventListener('open', () => {
      this.backoffMs = 500;
      this.onState({ status: 'open' });
    });

    ws.addEventListener('message', (ev: MessageEvent<string>) => {
      try {
        const reading = JSON.parse(ev.data) as Reading;
        this.onReading(reading);
      } catch (e) {
        console.error('Bad WS message', e, ev.data);
      }
    });

    ws.addEventListener('close', () => {
      this.onState({ status: 'closed' });
      if (this.closed) return;
      window.setTimeout(() => this.connect(), this.backoffMs);
      this.backoffMs = Math.min(this.backoffMs * 2, this.maxBackoffMs);
    });

    ws.addEventListener('error', (ev: Event) => {
      this.onState({ status: 'error', error: ev });
      ws.close();
    });
  }
}
