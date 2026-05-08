<script lang="ts">
  /**
   * Protokoll-Dialog.
   *
   * Vollbild-Modal, das das aktuelle Messprotokoll in vier Ansichten
   * darstellt:
   *   1. Tabelle           — bildschirmoptimierte Anzeige aller Werte
   *   2. Druck-Layout      — industrieller Header / Body / Footer
   *                          (orientiert an ALCOA-Pflichtfeldern und
   *                          dem typischen Mettler/Sartorius-Layout)
   *   3. Export            — Format-Auswahl (CSV/TSV/JSON/Markdown),
   *                          Spalten-Toggle, freie Header
   *   4. Speichern         — direkter Datei-Download
   *
   * Unbedingt die Recherche `docs/HARDWARE.md` und die
   * Industriestandards-Tabelle im Hinterkopf:
   *   - ALCOA: Attributable, Legible, Contemporaneous, Original,
     Accurate (+ Complete, Consistent, Enduring, Available, +Traceable)
   *   - SHA-256-Hash der gesamten Listen-Daten als „Tamper-Evidence"
   *     wird im Druck-Footer und im Export-Manifest mitgeliefert.
   */
  import { t } from '../lib/i18n';
  import { formatDiff, formatGrams, formatTime } from '../lib/format';
  import { modelStore } from '../lib/modelStore.svelte';
  import { healthStore } from '../lib/healthStore.svelte';
  import type { MesslogEntry } from '../lib/types';

  interface Props {
    open: boolean;
    entries: MesslogEntry[];
    onClose: () => void;
  }
  let { open, entries, onClose }: Props = $props();

  type Tab = 'table' | 'print' | 'export' | 'save';
  let activeTab = $state<Tab>('table');

  // Industrielle Header-Felder (ALCOA: attributable). Werden in
  // localStorage gespiegelt, damit der Anwender sie nur einmal
  // tippen muss und sie auf jedem Druck wieder erscheinen.
  let operator = $state(loadField('protocol.operator'));
  let company = $state(loadField('protocol.company'));
  let location = $state(loadField('protocol.location'));
  let methodId = $state(loadField('protocol.methodId'));
  let calibrationDate = $state(loadField('protocol.calibrationDate'));

  function loadField(key: string): string {
    if (typeof localStorage === 'undefined') return '';
    return localStorage.getItem(key) ?? '';
  }
  function saveField(key: string, value: string): void {
    try { localStorage.setItem(key, value); } catch { /* ignore */ }
  }
  $effect(() => { saveField('protocol.operator', operator); });
  $effect(() => { saveField('protocol.company', company); });
  $effect(() => { saveField('protocol.location', location); });
  $effect(() => { saveField('protocol.methodId', methodId); });
  $effect(() => { saveField('protocol.calibrationDate', calibrationDate); });

  // Datum jetzt — wird in den Header eingesetzt
  let printDate = $derived(new Date().toLocaleString());

  // Statistik der Liste — ALCOA "complete" und üblich im Footer
  // industrieller Wäge-Protokolle.
  let stats = $derived.by(() => {
    const changes = entries.filter(e => e.kind === 'change');
    const values = changes.map(e => e.value_g);
    if (values.length === 0) return null;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const sum = values.reduce((a, b) => a + b, 0);
    const mean = sum / values.length;
    const variance = values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length;
    const stdev = Math.sqrt(variance);
    return { count: values.length, min, max, mean, stdev, sum };
  });

  // Hash der Liste — Tamper-Evidence im Footer (SHA-256 der ID-Werte-
  // Sequenz). Stammt aus der WebCrypto-API, asynchron.
  let hashHex = $state('—');
  $effect(() => {
    if (!open || entries.length === 0) { hashHex = '—'; return; }
    const text = entries
      .map(e => `${e.id}|${e.ts}|${e.kind}|${e.value_g}|${e.diff_g ?? ''}`)
      .join('\n');
    void crypto.subtle
      .digest('SHA-256', new TextEncoder().encode(text))
      .then(buf => {
        hashHex = Array.from(new Uint8Array(buf))
          .map(b => b.toString(16).padStart(2, '0'))
          .join('');
      });
  });

  // ----- Export-Logik -----
  type Fmt = 'csv' | 'tsv' | 'json' | 'md';
  let exportFmt = $state<Fmt>('csv');
  let exportDelim = $state<','|';'>(',');

  function buildExportText(fmt: Fmt): string {
    const cols = ['id', 'ts', 'kind', 'value_g', 'diff_g'];
    const rows = entries.map(e => ({
      id: e.id,
      ts: e.ts,
      kind: e.kind,
      value_g: e.value_g,
      diff_g: e.diff_g ?? '',
    }));
    if (fmt === 'json') {
      return JSON.stringify({
        meta: { operator, company, location, methodId, calibrationDate, printDate, hash: hashHex },
        entries: rows,
        stats,
      }, null, 2);
    }
    if (fmt === 'md') {
      const head = `| ${cols.join(' | ')} |`;
      const sep = `| ${cols.map(() => '---').join(' | ')} |`;
      const body = rows.map(r => `| ${cols.map(c => String((r as any)[c])).join(' | ')} |`).join('\n');
      return [`# Messprotokoll`, `**Operator:** ${operator}  `, `**Datum:** ${printDate}`, '', head, sep, body, '', `_Hash: ${hashHex}_`].join('\n');
    }
    const sep = fmt === 'tsv' ? '\t' : exportDelim;
    const lines = [cols.join(sep)];
    for (const r of rows) lines.push(cols.map(c => String((r as any)[c])).join(sep));
    return '﻿' + lines.join('\n');
  }

  function downloadAs(fmt: Fmt): void {
    const content = buildExportText(fmt);
    const mime = {
      csv: 'text/csv',
      tsv: 'text/tab-separated-values',
      json: 'application/json',
      md: 'text/markdown',
    }[fmt];
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const filename = `messprotokoll-${ts}.${fmt}`;
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function doPrint(): void {
    // Browser-Print öffnet den Druck-Dialog mit der aktuellen Seite —
    // unser print-CSS in ProtocolDialog.svelte zeigt nur den
    // .print-area-Block.
    window.print();
  }

  // Esc schließt den Dialog
  function onKey(ev: KeyboardEvent): void {
    if (open && ev.key === 'Escape') onClose();
  }

  let activeModel = $derived(modelStore.active);
</script>

<svelte:document onkeydown={onKey} />

{#if open}
  <div class="overlay" role="dialog" aria-modal="true" aria-label="Messprotokoll">
    <div class="dialog">
      <!-- Tab-Bar -->
      <header class="tabs no-print">
        <h2>{t('protocol.title')}</h2>
        <div class="tab-row" role="tablist">
          <button class:active={activeTab==='table'}  onclick={() => (activeTab='table')}  role="tab">
            <i class="fa-solid fa-table"></i> {t('protocol.tabTable')}
          </button>
          <button class:active={activeTab==='print'}  onclick={() => (activeTab='print')}  role="tab">
            <i class="fa-solid fa-print"></i> {t('protocol.tabPrint')}
          </button>
          <button class:active={activeTab==='export'} onclick={() => (activeTab='export')} role="tab">
            <i class="fa-solid fa-file-export"></i> {t('protocol.tabExport')}
          </button>
          <button class:active={activeTab==='save'}   onclick={() => (activeTab='save')}   role="tab">
            <i class="fa-solid fa-floppy-disk"></i> {t('protocol.tabSave')}
          </button>
        </div>
        <button class="close" onclick={onClose} title={t('general.close')} aria-label={t('general.close')}>
          <i class="fa-regular fa-circle-xmark"></i>
        </button>
      </header>

      <main class="body">
        <!-- ============================== TAB: TABELLE ============================== -->
        {#if activeTab === 'table'}
          <div class="table-view">
            <p class="meta">
              {t('protocol.entries')}: <strong class="num">{entries.length}</strong>
              {#if stats}
                · n: <strong class="num">{stats.count}</strong>
                · {t('panels.statMin')}: <strong class="num">{formatGrams(stats.min)}</strong>
                · {t('panels.statMax')}: <strong class="num">{formatGrams(stats.max)}</strong>
                · {t('panels.statMean')}: <strong class="num">{formatGrams(stats.mean)}</strong>
                · σ: <strong class="num">{formatGrams(stats.stdev)}</strong>
              {/if}
            </p>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>{t('protocol.colTime')}</th>
                    <th>{t('protocol.colKind')}</th>
                    <th class="num">{t('protocol.colValue')}</th>
                    <th class="num">{t('protocol.colDiff')}</th>
                  </tr>
                </thead>
                <tbody>
                  {#each entries as e (e.id)}
                    <tr>
                      <td class="num">{e.id}</td>
                      <td class="num">{formatTime(e.ts)}</td>
                      <td>{e.kind}</td>
                      <td class="num">{formatGrams(e.value_g)}</td>
                      <td class="num">{e.diff_g !== null && e.diff_g !== undefined ? formatDiff(e.diff_g) : '—'}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        {/if}

        <!-- ============================== TAB: DRUCK ============================== -->
        {#if activeTab === 'print'}
          <div class="print-controls no-print">
            <p class="hint">{t('protocol.printHint')}</p>
            <div class="header-fields">
              <label>{t('protocol.operator')} <input bind:value={operator} placeholder="z.B. Max Müller" /></label>
              <label>{t('protocol.company')}  <input bind:value={company}  placeholder="Firma / Abteilung" /></label>
              <label>{t('protocol.location')} <input bind:value={location} placeholder="Standort / Werkbank" /></label>
              <label>{t('protocol.method')}   <input bind:value={methodId} placeholder="Verfahren / Method-ID" /></label>
              <label>{t('protocol.lastCal')}  <input bind:value={calibrationDate} placeholder="JJJJ-MM-TT" /></label>
            </div>
            <div class="actions">
              <button class="btn-primary" onclick={doPrint}>
                <i class="fa-solid fa-print"></i> {t('protocol.doPrint')}
              </button>
            </div>
          </div>

          <!-- Druck-Layout (auch am Bildschirm sichtbar als Vorschau) -->
          <div class="print-area">
            <header class="protocol-header">
              <div class="brand">
                <h1>{t('protocol.title')}</h1>
                <small>{t('protocol.notLegalForTrade')}</small>
              </div>
              <table class="meta-table">
                <tbody>
                  <tr><th>{t('protocol.operator')}</th><td>{operator || '—'}</td></tr>
                  <tr><th>{t('protocol.company')}</th><td>{company || '—'}</td></tr>
                  <tr><th>{t('protocol.location')}</th><td>{location || '—'}</td></tr>
                  <tr><th>{t('protocol.method')}</th><td>{methodId || '—'}</td></tr>
                  <tr><th>{t('protocol.printedAt')}</th><td>{printDate}</td></tr>
                  <tr><th>{t('protocol.scaleModel')}</th><td>{activeModel.manufacturer} {activeModel.series}-{activeModel.name}</td></tr>
                  <tr><th>{t('protocol.scaleSpec')}</th><td>max {activeModel.max_g} g · ±{activeModel.resolution_g} g</td></tr>
                  <tr><th>{t('protocol.lastCal')}</th><td>{calibrationDate || '—'}</td></tr>
                  <tr><th>{t('protocol.hardwareLive')}</th><td>{healthStore.scaleOk ? t('protocol.yes') : t('protocol.no')}</td></tr>
                </tbody>
              </table>
            </header>

            <table class="entries">
              <thead>
                <tr>
                  <th>#</th>
                  <th>{t('protocol.colTime')}</th>
                  <th>{t('protocol.colKind')}</th>
                  <th class="num">{t('protocol.colValue')}</th>
                  <th class="num">{t('protocol.colDiff')}</th>
                </tr>
              </thead>
              <tbody>
                {#each entries as e (e.id)}
                  <tr>
                    <td class="num">{e.id}</td>
                    <td class="num">{formatTime(e.ts)}</td>
                    <td>{e.kind}</td>
                    <td class="num">{formatGrams(e.value_g)}</td>
                    <td class="num">{e.diff_g !== null && e.diff_g !== undefined ? formatDiff(e.diff_g) : '—'}</td>
                  </tr>
                {/each}
              </tbody>
            </table>

            <footer class="protocol-footer">
              {#if stats}
                <div class="stats">
                  <span><strong>n</strong> {stats.count}</span>
                  <span><strong>{t('panels.statMin')}</strong> {formatGrams(stats.min)}</span>
                  <span><strong>{t('panels.statMax')}</strong> {formatGrams(stats.max)}</span>
                  <span><strong>{t('panels.statMean')}</strong> {formatGrams(stats.mean)}</span>
                  <span><strong>σ</strong> {formatGrams(stats.stdev)}</span>
                  <span><strong>{t('panels.statSum')}</strong> {formatGrams(stats.sum)}</span>
                </div>
              {/if}
              <div class="signatures">
                <div class="sig-slot"><span class="line"></span><small>{t('protocol.signOperator')}</small></div>
                <div class="sig-slot"><span class="line"></span><small>{t('protocol.signSecond')}</small></div>
              </div>
              <div class="hash">
                <small>{t('protocol.hashLabel')}: <code class="num">{hashHex}</code></small>
              </div>
            </footer>
          </div>
        {/if}

        <!-- ============================== TAB: EXPORT ============================== -->
        {#if activeTab === 'export'}
          <div class="export-view">
            <p class="hint">{t('protocol.exportHint')}</p>
            <div class="format-row">
              <label><input type="radio" bind:group={exportFmt} value="csv"  /> CSV (UTF-8 + BOM)</label>
              <label><input type="radio" bind:group={exportFmt} value="tsv"  /> TSV</label>
              <label><input type="radio" bind:group={exportFmt} value="json" /> JSON</label>
              <label><input type="radio" bind:group={exportFmt} value="md"   /> Markdown</label>
            </div>
            {#if exportFmt === 'csv'}
              <label class="delim">
                CSV-Trenner:
                <select bind:value={exportDelim}>
                  <option value=",">, (Komma)</option>
                  <option value=";">; (Semikolon — DE-Excel)</option>
                </select>
              </label>
            {/if}
            <pre class="preview">{buildExportText(exportFmt)}</pre>
            <div class="actions">
              <button class="btn-primary" onclick={() => downloadAs(exportFmt)}>
                <i class="fa-solid fa-file-export"></i> {t('protocol.doDownload')}
              </button>
            </div>
          </div>
        {/if}

        <!-- ============================== TAB: SPEICHERN ============================== -->
        {#if activeTab === 'save'}
          <div class="save-view">
            <p class="hint">{t('protocol.saveHint')}</p>
            <div class="save-grid">
              <button class="save-btn" onclick={() => downloadAs('csv')}>
                <i class="fa-solid fa-file-csv"></i><span>CSV</span>
              </button>
              <button class="save-btn" onclick={() => downloadAs('tsv')}>
                <i class="fa-solid fa-file-lines"></i><span>TSV</span>
              </button>
              <button class="save-btn" onclick={() => downloadAs('json')}>
                <i class="fa-solid fa-file-code"></i><span>JSON</span>
              </button>
              <button class="save-btn" onclick={() => downloadAs('md')}>
                <i class="fa-brands fa-markdown"></i><span>Markdown</span>
              </button>
            </div>
            <p class="meta">{t('protocol.saveMeta').replace('%hash', hashHex.slice(0, 16) + '…')}</p>
          </div>
        {/if}
      </main>
    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.55);
    z-index: 100;
    display: flex; align-items: stretch; justify-content: center;
    padding: 20px;
  }
  .dialog {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow-lg);
    width: 100%; max-width: 1100px;
    display: flex; flex-direction: column;
    overflow: hidden;
  }
  .tabs {
    display: flex; align-items: center;
    gap: var(--sp-3);
    padding: var(--sp-2) var(--sp-3);
    border-bottom: 1px solid var(--border);
    background: var(--bg-card-2);
  }
  .tabs h2 { margin: 0; font-size: var(--fs-md); flex: 0 0 auto; }
  .tab-row { display: flex; flex: 1 1 auto; gap: 4px; }
  .tab-row button {
    background: transparent;
    border: 1px solid transparent;
    color: var(--fg-dim);
    padding: 6px var(--sp-3);
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: var(--fs-sm);
    display: inline-flex; align-items: center; gap: 6px;
  }
  .tab-row button:hover { color: var(--fg); }
  .tab-row button.active {
    color: var(--accent);
    border-color: var(--accent);
    background: color-mix(in srgb, var(--accent) 12%, transparent);
  }
  .close {
    background: transparent; border: none;
    color: var(--fg-dim);
    font-size: 22px;
    cursor: pointer;
    padding: 4px 8px;
  }
  .close:hover { color: var(--red); }

  .body {
    flex: 1 1 auto; min-height: 0;
    overflow-y: auto;
    padding: var(--sp-4);
  }

  /* --- Tabelle --- */
  .meta { margin: 0 0 var(--sp-3); color: var(--fg-dim); font-size: var(--fs-sm); }
  .table-wrap { overflow-x: auto; }
  table {
    width: 100%; border-collapse: collapse;
    font-size: var(--fs-sm);
  }
  th, td {
    padding: 6px var(--sp-2);
    border-bottom: 1px solid var(--border);
    text-align: left;
  }
  th { color: var(--fg-mute); font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; font-size: var(--fs-xs); }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }

  /* --- Druck-Vorschau / Layout --- */
  .print-controls { margin-bottom: var(--sp-4); }
  .header-fields {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: var(--sp-2) var(--sp-3);
    margin: var(--sp-2) 0;
  }
  .header-fields label {
    display: flex; flex-direction: column; gap: 4px;
    font-size: var(--fs-xs); color: var(--fg-dim);
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  .header-fields input {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 6px 10px;
    color: var(--fg);
    font-family: var(--sans);
    font-size: var(--fs-sm);
  }
  .actions { display: flex; gap: var(--sp-2); margin-top: var(--sp-2); }
  .hint { margin: 0 0 var(--sp-2); color: var(--fg-mute); font-size: var(--fs-sm); }

  .print-area {
    background: #ffffff;
    color: #000000;
    padding: var(--sp-4);
    border: 1px solid var(--border);
  }
  .protocol-header {
    display: flex; gap: var(--sp-4);
    border-bottom: 2px solid #000;
    padding-bottom: var(--sp-2);
    margin-bottom: var(--sp-3);
  }
  .protocol-header .brand { flex: 1; }
  .protocol-header h1 { margin: 0 0 4px; font-size: 18pt; color: #000; }
  .protocol-header small { color: #666; font-style: italic; }
  .meta-table { font-size: 9pt; border-collapse: collapse; }
  .meta-table th { text-align: left; padding-right: 12px; color: #555; font-weight: 600; text-transform: none; letter-spacing: 0; border: none; }
  .meta-table td { padding-right: 0; border: none; color: #000; }
  .entries th, .entries td { color: #000; border-color: #888; }
  .protocol-footer { margin-top: var(--sp-3); border-top: 1px solid #888; padding-top: var(--sp-2); }
  .protocol-footer .stats {
    display: flex; flex-wrap: wrap; gap: 12px 24px;
    font-size: 10pt; color: #000;
  }
  .protocol-footer .signatures {
    display: flex; gap: var(--sp-5);
    margin: var(--sp-4) 0 var(--sp-2);
  }
  .sig-slot { flex: 1; }
  .sig-slot .line { display: block; border-top: 1px solid #000; margin-bottom: 4px; height: 30px; }
  .sig-slot small { color: #555; font-size: 9pt; }
  .protocol-footer .hash {
    margin-top: var(--sp-2);
    font-size: 8pt; color: #555;
    word-break: break-all;
  }
  .protocol-footer .hash code { background: transparent; }

  /* --- Export --- */
  .format-row { display: flex; flex-wrap: wrap; gap: var(--sp-3); margin-bottom: var(--sp-2); }
  .format-row label { font-size: var(--fs-sm); color: var(--fg); display: inline-flex; align-items: center; gap: 6px; cursor: pointer; }
  .delim { display: inline-flex; align-items: center; gap: 8px; margin-bottom: var(--sp-2); }
  .delim select {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 4px 8px;
    color: var(--fg);
  }
  .preview {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: var(--sp-2);
    font-family: var(--num); font-size: 12px;
    max-height: 320px; overflow: auto;
    white-space: pre;
  }

  /* --- Save (Schnellzugriffe) --- */
  .save-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: var(--sp-2);
    margin: var(--sp-3) 0;
  }
  .save-btn {
    aspect-ratio: 1.6 / 1;
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    color: var(--fg);
    border-radius: var(--radius-sm);
    cursor: pointer;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 8px;
    font-size: var(--fs-md);
  }
  .save-btn i { font-size: 32px; color: var(--accent); }
  .save-btn:hover { border-color: var(--accent); color: var(--accent); }

  /* Druck: alles außer dem Print-Area-Block ausblenden */
  @media print {
    .overlay { position: static; background: #fff; padding: 0; }
    .dialog { box-shadow: none; border: none; max-width: none; }
    .no-print { display: none !important; }
    .body { padding: 0; overflow: visible; }
    .print-area { border: none; padding: 0; }
  }
</style>
