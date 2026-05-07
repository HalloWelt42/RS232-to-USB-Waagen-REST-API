/**
 * Globaler Volltext-Suchindex über Hilfe-Inhalte und Werkzeuge.
 *
 * Die Suche ist case-insensitiv und akzentnormalisierend. Treffer
 * tragen einen Typ (`tool`, `help`, `term`), den die UI zu Icons
 * und Hint-Labels umsetzt, sowie ein optionales Snippet mit
 * Kontext um den ersten Treffer.
 */

import { helpEntries, type HelpId, type HelpBlock } from './help';
import { TOOL_KEYS, type ToolKey } from './routing.svelte';
import { t } from './i18n';

export type ResultKind = 'tool' | 'help' | 'term';

export interface SearchResult {
  kind: ResultKind;
  /** Stabile Kennung — für `tool` ein ToolKey, sonst ein HelpId. */
  ref: string;
  title: string;
  snippet: string;
  /** wo soll geöffnet werden — für tool: Tool öffnen, für help/term: Hilfe-Window */
  action: { kind: 'tool'; tool: ToolKey } | { kind: 'help'; help: HelpId };
  /** Treffer-Score; höher = passender. */
  score: number;
}

function norm(s: string): string {
  return s.toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '');
}

function stripHtml(s: string): string {
  return s.replace(/<[^>]+>/g, '');
}

function snippet(text: string, query: string, max = 140): string {
  const plain = stripHtml(text);
  const idx = norm(plain).indexOf(query);
  if (idx === -1) return plain.slice(0, max) + (plain.length > max ? '…' : '');
  const start = Math.max(0, idx - 40);
  const end = Math.min(plain.length, idx + query.length + 60);
  return (start > 0 ? '… ' : '') + plain.slice(start, end) + (end < plain.length ? ' …' : '');
}

/** Treffer-Score: Treffer in Titel/Heading wiegt schwerer als im Body. */
function score(haystackTitle: string, haystackBody: string, q: string): number {
  const t = norm(haystackTitle).includes(q);
  const b = norm(haystackBody).includes(q);
  if (!t && !b) return 0;
  return (t ? 10 : 0) + (b ? 1 : 0);
}

export function search(query: string, max = 20): SearchResult[] {
  const q = norm(query.trim());
  if (q.length === 0) return [];
  const out: SearchResult[] = [];

  // 1) Werkzeuge — Treffer in Titel und Beschreibung
  for (const tool of TOOL_KEYS) {
    const title = t(`tools.${tool}`);
    const desc = t(`toolsDescription.${tool}`);
    const sc = score(title, desc, q);
    if (sc > 0) {
      out.push({
        kind: 'tool', ref: tool, title,
        snippet: desc, score: sc + 5,
        action: { kind: 'tool', tool },
      });
    }
  }

  // 2) Hilfe-Einträge — Treffer in Titel oder Block-Body
  for (const id of Object.keys(helpEntries) as HelpId[]) {
    const entry = helpEntries[id];
    let bestSc = 0;
    let bestSnippet = '';
    let isTerm = id === 'glossary';
    for (const block of entry.blocks as readonly HelpBlock[]) {
      const sc = score(block.heading, stripHtml(block.body), q);
      if (sc > bestSc) {
        bestSc = sc;
        bestSnippet = snippet(block.body, q);
      }
    }
    const titleSc = score(entry.title, '', q);
    if (titleSc > 0 || bestSc > 0) {
      out.push({
        kind: isTerm ? 'term' : 'help',
        ref: id, title: entry.title,
        snippet: bestSnippet || stripHtml(entry.blocks[0]?.body ?? '').slice(0, 120),
        score: titleSc + bestSc,
        action: { kind: 'help', help: id },
      });
    }
  }

  // 3) Glossar-Begriffe einzeln auflisten
  const glossary = helpEntries.glossary;
  for (const block of glossary.blocks as readonly HelpBlock[]) {
    const sc = score(block.heading, stripHtml(block.body), q);
    if (sc > 0) {
      out.push({
        kind: 'term', ref: `glossary#${block.heading}`,
        title: block.heading,
        snippet: snippet(block.body, q),
        score: sc + 2,
        action: { kind: 'help', help: 'glossary' },
      });
    }
  }

  // Duplikate (gleicher action.kind+ref) reduzieren — Glossar-Eintrag schlägt
  // Hilfe-Eintrag Glossar selbst, falls beide treffen.
  const seen = new Set<string>();
  const dedup: SearchResult[] = [];
  for (const r of out.sort((a, b) => b.score - a.score)) {
    const key = r.kind + ':' + r.ref;
    if (seen.has(key)) continue;
    seen.add(key);
    dedup.push(r);
    if (dedup.length >= max) break;
  }
  return dedup;
}
