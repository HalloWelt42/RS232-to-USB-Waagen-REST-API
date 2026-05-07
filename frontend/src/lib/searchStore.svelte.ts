/**
 * Reaktiver Zustand für die globale Suche — Sichtbarkeit,
 * Eingabe-Text und Ergebnisliste.
 */
import { search, type SearchResult } from './search';

class SearchStore {
  open = $state(false);
  query = $state('');
  highlight = $state(0);

  show(): void { this.open = true; }
  hide(): void { this.open = false; this.query = ''; this.highlight = 0; }
  toggle(): void { this.open ? this.hide() : this.show(); }

  results = $derived<SearchResult[]>(search(this.query));
  setHighlight(i: number): void {
    const n = this.results.length;
    if (n === 0) { this.highlight = 0; return; }
    this.highlight = ((i % n) + n) % n;
  }
  next(): void { this.setHighlight(this.highlight + 1); }
  prev(): void { this.setHighlight(this.highlight - 1); }
}

export const searchStore = new SearchStore();
