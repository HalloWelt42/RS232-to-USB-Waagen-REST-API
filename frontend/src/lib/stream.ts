/**
 * WebSocket-Client für /scale/stream mit automatischem Reconnect.
 */
import type { ConnectionState, Reading } from './types';

export type ReadingCallback = (r: Reading) => void;
export type StateCallback   = (s: { status: ConnectionState; error?: unknown }) => void;

export class WaageStream {
  private ws: WebSocket | null = null;
  private closed = false;
  private backoffMs = 500;
  private readonly maxBackoffMs = 10_000;

  constructor(
    private readonly url: string,
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

    const ws = new WebSocket(this.url);
    this.ws = ws;

    ws.addEventListener('open', () => {
      this.backoffMs = 500;
      this.onState({ status: 'open' });
    });

    ws.addEventListener('message', (ev: MessageEvent<string>) => {
      try {
        this.onReading(JSON.parse(ev.data) as Reading);
      } catch (e) {
        console.error('Bad WS message', e);
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
