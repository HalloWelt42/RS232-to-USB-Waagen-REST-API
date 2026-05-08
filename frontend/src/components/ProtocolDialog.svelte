<script lang="ts">
  /**
   * Protokoll-Dialog.
   *
   * Vollbild-Modal, das das aktuelle Messprotokoll in vier Ansichten
   * darstellt:
   *   1. Tabelle    — bildschirmoptimierte Anzeige aller Werte
   *   2. Druck      — minimales Druck-Layout (Header, Tabelle, Footer)
   *   3. Export     — Format-Auswahl mit Live-Vorschau
   *   4. Speichern  — direkter Datei-Download
   *
   * Eigene App-spezifische Konvention statt Industrie-Standards
   * (siehe `.waage`-Format unten und docs/HARDWARE.md). Keine
   * Operator-/Firma-/Audit-Trail-Felder — das ist eine Werkstatt-
   * App, kein 21-CFR-11-System.
   */
  import { t } from '../lib/i18n';
  import { formatDiff, formatGrams, formatTime } from '../lib/format';
  import { modelStore } from '../lib/modelStore.svelte';
  import type { MesslogEntry } from '../lib/types';

  interface Props {
    open: boolean;
    entries: MesslogEntry[];
    onClose: () => void;
  }
  let { open, entries, onClose }: Props = $props();

  type Tab = 'table' | 'print' | 'export' | 'save';
  let activeTab = $state<Tab>('table');

  let printDate = $derived(new Date().toLocaleString());
  let activeModel = $derived(modelStore.active);

  // Statistik der Liste — aus den change-Einträgen (Mess-Werte ohne
  // Tara-/Start-Marker), für Footer/Tabelle.
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

  // ---------- Eigene .waage-Format-Definition ----------
  // App-spezifisches JSON-Format mit Format-Marker und Schema-Version.
  // Kann später vom Backend wieder eingelesen werden, ohne dass wir
  // an irgendwelche Industrie-Standards gebunden sind.
  type WaageDoc = {
    format: 'waage-protocol-v1';
    created_at: string;
    app_version: string;
    scale: {
      manufacturer: string;
      series: string;
      name: string;
      max_g: number;
      resolution_g: number;
    };
    stats: ReturnType<typeof statsObj> | null;
    entries: Array<{
      id: number;
      ts: string;
      kind: string;
      value_g: number;
      diff_g: number | null;
    }>;
  };
  function statsObj() {
    return stats ? { ...stats } : null;
  }
  function buildWaageDoc(): WaageDoc {
    const m = activeModel;
    return {
      format: 'waage-protocol-v1',
      created_at: new Date().toISOString(),
      app_version: __APP_VERSION__,
      scale: {
        manufacturer: m.manufacturer,
        series: m.series,
        name: m.name,
        max_g: m.max_g,
        resolution_g: m.resolution_g,
      },
      stats: stats ? { ...stats } : null,
      entries: entries.map(e => ({
        id: e.id,
        ts: e.ts,
        kind: e.kind,
        value_g: e.value_g,
        diff_g: e.diff_g ?? null,
      })),
    };
  }

  // ---------- Export-Logik ----------
  type Fmt = 'csv' | 'tsv' | 'json' | 'md' | 'waage';
  let exportFmt = $state<Fmt>('csv');
  let exportDelim = $state<','|';'>(',');

  function buildExportText(fmt: Fmt): string {
    if (fmt === 'waage') {
      return JSON.stringify(buildWaageDoc(), null, 2);
    }
    if (fmt === 'json') {
      return JSON.stringify(
        entries.map(e => ({
          id: e.id, ts: e.ts, kind: e.kind,
          value_g: e.value_g, diff_g: e.diff_g ?? null,
        })),
        null, 2,
      );
    }
    const cols = ['id', 'ts', 'kind', 'value_g', 'diff_g'];
    const rows = entries.map(e => ({
      id: e.id, ts: e.ts, kind: e.kind,
      value_g: e.value_g, diff_g: e.diff_g ?? '',
    }));
    if (fmt === 'md') {
      const head = `| ${cols.join(' | ')} |`;
      const sep = `| ${cols.map(() => '---').join(' | ')} |`;
      const body = rows.map(r => `| ${cols.map(c => String((r as any)[c])).join(' | ')} |`).join('\n');
      return ['# Messprotokoll', `_${printDate}_`, '', head, sep, body].join('\n');
    }
    const sep = fmt === 'tsv' ? '\t' : exportDelim;
    const lines = [cols.join(sep)];
    for (const r of rows) lines.push(cols.map(c => String((r as any)[c])).join(sep));
    return '﻿' + lines.join('\n');
  }

  function downloadAs(fmt: Fmt): void {
    const content = buildExportText(fmt);
    const mime = {
      csv:   'text/csv',
      tsv:   'text/tab-separated-values',
      json:  'application/json',
      md:    'text/markdown',
      waage: 'application/json',
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
    window.print();
  }

  function onKey(ev: KeyboardEvent): void {
    if (open && ev.key === 'Escape') onClose();
  }
</script>

<svelte:document onkeydown={onKey} />

{#if open}
  <div class="overlay" role="dialog" aria-modal="true" aria-label={t('protocol.title')}>
    <div class="dialog">
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
        <!-- TAB 1: Tabelle -->
        {#if activeTab === 'table'}
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
        {/if}

        <!-- TAB 2: Druck — minimales eigenes Layout -->
        {#if activeTab === 'print'}
          <div class="print-controls no-print">
            <p class="hint">{t('protocol.printHint')}</p>
            <button class="btn-primary" onclick={doPrint}>
              <i class="fa-solid fa-print"></i> {t('protocol.doPrint')}
            </button>
          </div>

          <div class="print-area">
            <header class="protocol-header">
              <h1>{t('protocol.title')}</h1>
              <div class="header-meta">
                <span>{printDate}</span>
                <span>{activeModel.manufacturer} {activeModel.series}-{activeModel.name}</span>
                <span class="num">max {activeModel.max_g} g · ±{activeModel.resolution_g} g</span>
              </div>
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

            {#if stats}
              <footer class="protocol-footer">
                <span><strong>n</strong> {stats.count}</span>
                <span><strong>{t('panels.statMin')}</strong> {formatGrams(stats.min)}</span>
                <span><strong>{t('panels.statMax')}</strong> {formatGrams(stats.max)}</span>
                <span><strong>{t('panels.statMean')}</strong> {formatGrams(stats.mean)}</span>
                <span><strong>σ</strong> {formatGrams(stats.stdev)}</span>
                <span><strong>{t('panels.statSum')}</strong> {formatGrams(stats.sum)}</span>
              </footer>
            {/if}
          </div>
        {/if}

        <!-- TAB 3: Export -->
        {#if activeTab === 'export'}
          <p class="hint">{t('protocol.exportHint')}</p>
          <div class="format-row">
            <label><input type="radio" bind:group={exportFmt} value="csv"   /> CSV (UTF-8 + BOM)</label>
            <label><input type="radio" bind:group={exportFmt} value="tsv"   /> TSV</label>
            <label><input type="radio" bind:group={exportFmt} value="json"  /> JSON</label>
            <label><input type="radio" bind:group={exportFmt} value="md"    /> Markdown</label>
            <label><input type="radio" bind:group={exportFmt} value="waage" /> .waage <small>{t('protocol.waageFormatHint')}</small></label>
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
        {/if}

        <!-- TAB 4: Speichern (Schnellzugriff) -->
        {#if activeTab === 'save'}
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
            <button class="save-btn featured" onclick={() => downloadAs('waage')}>
              <i class="fa-solid fa-scale-balanced"></i>
              <span>.waage</span>
              <small>{t('protocol.waageFormatHint')}</small>
            </button>
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

  .meta { margin: 0 0 var(--sp-3); color: var(--fg-dim); font-size: var(--fs-sm); }
  .hint { margin: 0 0 var(--sp-2); color: var(--fg-mute); font-size: var(--fs-sm); }
  .actions { display: flex; gap: var(--sp-2); margin-top: var(--sp-3); }

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

  /* Druck-Vorschau / Layout — schlicht, ohne Industrie-Schnickschnack */
  .print-controls { margin-bottom: var(--sp-4); display: flex; align-items: center; gap: var(--sp-3); }
  .print-area {
    background: #ffffff;
    color: #000000;
    padding: var(--sp-4);
    border: 1px solid var(--border);
  }
  .protocol-header {
    display: flex; flex-direction: column;
    gap: 4px;
    border-bottom: 1px solid #888;
    padding-bottom: var(--sp-2);
    margin-bottom: var(--sp-3);
  }
  .protocol-header h1 { margin: 0; font-size: 16pt; color: #000; }
  .header-meta {
    display: flex; flex-wrap: wrap; gap: 4px var(--sp-3);
    font-size: 9pt; color: #555;
  }
  .entries th, .entries td { color: #000; border-color: #888; }
  .protocol-footer {
    margin-top: var(--sp-3);
    padding-top: var(--sp-2);
    border-top: 1px solid #888;
    display: flex; flex-wrap: wrap; gap: 6px 18px;
    font-size: 10pt; color: #000;
  }

  /* Export */
  .format-row { display: flex; flex-wrap: wrap; gap: var(--sp-3); margin-bottom: var(--sp-2); }
  .format-row label {
    font-size: var(--fs-sm); color: var(--fg);
    display: inline-flex; align-items: center; gap: 6px;
    cursor: pointer;
  }
  .format-row label small { color: var(--fg-mute); font-size: var(--fs-xs); margin-left: 4px; }
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

  /* Save (Schnellzugriffe) */
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
    gap: 6px;
    font-size: var(--fs-md);
  }
  .save-btn i { font-size: 28px; color: var(--accent); }
  .save-btn small { color: var(--fg-mute); font-size: var(--fs-xs); }
  .save-btn:hover { border-color: var(--accent); color: var(--accent); }
  .save-btn.featured {
    background: color-mix(in srgb, var(--accent) 10%, var(--bg-card-2));
    border-color: var(--accent);
  }
  .save-btn.featured i { color: var(--accent-strong, var(--accent)); }

  @media print {
    .overlay { position: static; background: #fff; padding: 0; }
    .dialog { box-shadow: none; border: none; max-width: none; }
    .no-print { display: none !important; }
    .body { padding: 0; overflow: visible; }
    .print-area { border: none; padding: 0; }
  }
</style>
