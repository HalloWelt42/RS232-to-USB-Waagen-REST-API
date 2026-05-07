/** Toast-Bus: ein einziger Hinweis zur Zeit, automatisch ausblendend. */

export interface ToastEntry {
  id: number;
  message: string;
  kind: 'info' | 'ok' | 'error';
}

class ToastBus {
  current = $state<ToastEntry | null>(null);
  private nextId = 1;
  private timer: number | null = null;

  show(message: string, kind: ToastEntry['kind'] = 'ok', durationMs = 1800): void {
    const id = this.nextId++;
    this.current = { id, message, kind };
    if (this.timer !== null) window.clearTimeout(this.timer);
    this.timer = window.setTimeout(() => {
      if (this.current?.id === id) this.current = null;
    }, durationMs);
  }
  hide(): void {
    this.current = null;
    if (this.timer !== null) window.clearTimeout(this.timer);
  }
}

export const toast = new ToastBus();
