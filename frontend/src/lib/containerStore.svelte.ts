/**
 * Reaktiver Speicher für die Behälter-Bibliothek.
 *
 * Lädt beim ersten Zugriff alle Behälter vom Backend, hält sie als
 * sortierte Liste und bietet `add` / `update` / `remove`.
 * Komponenten greifen über `containerStore.list` darauf zu — bei
 * jeder Mutation laufen alle abhängigen `$derived`/`$effect` mit.
 */

import { api } from './api';
import type { Container, ContainerInput, ContainerPatch } from './types';

class ContainerStore {
  list = $state<Container[]>([]);
  loaded = $state(false);
  busy = $state(false);

  async refresh(): Promise<void> {
    this.busy = true;
    try {
      const r = await api.app.containersList();
      this.list = r.items;
      this.loaded = true;
    } finally {
      this.busy = false;
    }
  }

  async add(payload: ContainerInput): Promise<Container> {
    const c = await api.app.containersAdd(payload);
    await this.refresh();
    return c;
  }

  async update(id: number, patch: ContainerPatch): Promise<Container> {
    const c = await api.app.containersUpdate(id, patch);
    await this.refresh();
    return c;
  }

  async remove(id: number): Promise<void> {
    await api.app.containersDelete(id);
    await this.refresh();
  }

  byId(id: number | null): Container | null {
    if (id === null) return null;
    return this.list.find(c => c.id === id) ?? null;
  }
}

export const containerStore = new ContainerStore();
