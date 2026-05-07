/**
 * Kurze, dezente Hinweise (Toasts) für Aktionen wie "Wert kopiert".
 * Reaktiver Store, ein einziger Toast zur Zeit. Verschwindet nach
 * 1,8 Sekunden automatisch.
 */

export interface ToastEntry {
  id: number;
  message: string;
  kind: 'info' | 'ok' | 'error';
}

class ToastBus {
  current = $state<ToastEntry | null>(null);
  private nextId = 1;
  private timeout: number | null = null;

  show(message: string, kind: ToastEntry['kind'] = 'ok', durationMs = 1800): void {
    const id = this.nextId++;
    this.current = { id, message, kind };
    if (this.timeout !== null) window.clearTimeout(this.timeout);
    this.timeout = window.setTimeout(() => {
      if (this.current?.id === id) this.current = null;
    }, durationMs);
  }

  hide(): void {
    this.current = null;
    if (this.timeout !== null) window.clearTimeout(this.timeout);
  }
}

export const toast = new ToastBus();
