/**
 * Reaktiver Speicher für die Stückzähl-Vorlagen.
 *
 * Lädt die Liste vom Backend (das beim ersten Aufruf vier Default-
 * Vorlagen seedet) und stellt CRUD-Operationen bereit. Komponenten
 * lesen `list` direkt — bei jeder Mutation refresh-en wir, damit
 * abhängige `$derived`/`$effect` neu rendern.
 */

import { api } from './api';
import type {
  CountTemplateRecord,
  CountTemplateInput,
  CountTemplatePatch,
} from './types';

class CountTemplateStore {
  list = $state<CountTemplateRecord[]>([]);
  loaded = $state(false);
  busy = $state(false);

  async refresh(): Promise<void> {
    this.busy = true;
    try {
      const r = await api.app.countTemplatesList();
      this.list = r.items;
      this.loaded = true;
    } finally {
      this.busy = false;
    }
  }

  async add(payload: CountTemplateInput): Promise<CountTemplateRecord> {
    const t = await api.app.countTemplatesAdd(payload);
    await this.refresh();
    return t;
  }

  async update(id: number, patch: CountTemplatePatch): Promise<CountTemplateRecord> {
    const t = await api.app.countTemplatesUpdate(id, patch);
    await this.refresh();
    return t;
  }

  async remove(id: number): Promise<void> {
    await api.app.countTemplatesDelete(id);
    await this.refresh();
  }

  byId(id: number | null): CountTemplateRecord | null {
    if (id === null) return null;
    return this.list.find(t => t.id === id) ?? null;
  }
}

export const countTemplateStore = new CountTemplateStore();
