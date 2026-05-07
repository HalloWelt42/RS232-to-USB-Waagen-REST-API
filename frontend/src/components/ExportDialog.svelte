<script lang="ts">
  /**
   * Export-Dialog: Format, Delimiter, Spalten-Auswahl und freie
   * Bezeichner. Backend liefert die Datei in CSV / TSV / JSON / Markdown.
   *
   * Industrie-Praxis: Mess-Daten werden oft in verschiedenen Tools
   * weiterverarbeitet — Excel will UTF-8-CSV mit Semikolon (DE) oder
   * Komma (US/UK), Skripte mögen TSV, REST-Konsumenten JSON, Wiki/
   * GitHub-Doku Markdown. Dieser Dialog deckt alle vier ab.
   */
  import { api } from '../lib/api';
  import { t } from '../lib/i18n';

  type Fmt = 'csv' | 'tsv' | 'json' | 'md';
  type Delim = 'comma' | 'semicolon';

  interface Props {
    open: boolean;
    session: string | null;
    onClose: () => void;
  }
  let { open, session, onClose }: Props = $props();

  const COLUMNS: ReadonlyArray<{ key: string; defaultLabel: string }> = [
    { key: 'id',       defaultLabel: 'ID' },
    { key: 'ts',       defaultLabel: 'Zeit' },
    { key: 'weight_g', defaultLabel: 'Gewicht (g)' },
    { key: 'unit',     defaultLabel: 'Einheit' },
    { key: 'stable',   defaultLabel: 'Stabil' },
    { key: 'label',    defaultLabel: 'Label' },
    { key: 'note',     defaultLabel: 'Notiz' },
    { key: 'session',  defaultLabel: 'Session' },
  ];

  let fmt = $state<Fmt>('csv');
  let delim = $state<Delim>('semicolon');     // DE-Excel-Default
  let chosen = $state<Record<string, boolean>>(
    Object.fromEntries(COLUMNS.map(c => [c.key, true]))
  );
  let labels = $state<Record<string, string>>(
    Object.fromEntries(COLUMNS.map(c => [c.key, c.defaultLabel]))
  );

  function toggleAll(value: boolean): void {
    chosen = Object.fromEntries(COLUMNS.map(c => [c.key, value]));
  }

  function resetLabels(): void {
    labels = Object.fromEntries(COLUMNS.map(c => [c.key, c.defaultLabel]));
  }

  let downloadUrl = $derived(api.app.samplesExportFormatUrl({
    session,
    fmt,
    delim: fmt === 'csv' ? delim : undefined,
    cols: COLUMNS.filter(c => chosen[c.key]).map(c => c.key),
    labels,
  }));

  function onKey(ev: KeyboardEvent): void {
    if (ev.key === 'Escape' && open) onClose();
  }
</script>

<svelte:document onkeydown={onKey} />

{#if open}
  <div class="backdrop" onclick={onClose} role="presentation"></div>
  <div class="dialog" role="dialog" aria-label={t('export.title')} tabindex="-1">
    <header>
      <h3>{t('export.title')}</h3>
      <button class="x" onclick={onClose} aria-label={t('general.close')}>
        <i class="fa-regular fa-circle-xmark"></i>
      </button>
    </header>

    <div class="body">
      <div class="block">
        <h4>{t('export.format')}</h4>
        <div class="row pillrow">
          {#each ['csv','tsv','json','md'] as f (f)}
            <button class:active={fmt === f}
                    onclick={() => fmt = f as Fmt}>
              {t(`export.fmt_${f}`)}
            </button>
          {/each}
        </div>
      </div>

      {#if fmt === 'csv'}
        <div class="block">
          <h4>{t('export.delimiter')}</h4>
          <div class="row pillrow">
            <button class:active={delim === 'comma'}
                    onclick={() => delim = 'comma'}>
              {t('export.delim_comma')}
            </button>
            <button class:active={delim === 'semicolon'}
                    onclick={() => delim = 'semicolon'}>
              {t('export.delim_semicolon')}
            </button>
          </div>
        </div>
      {/if}

      <div class="block">
        <div class="block-head">
          <h4>{t('export.columns')}</h4>
          <div class="all-toggle">
            <button class="link" onclick={() => toggleAll(true)}>
              {t('export.allOn')}
            </button>
            ·
            <button class="link" onclick={() => toggleAll(false)}>
              {t('export.allOff')}
            </button>
            ·
            <button class="link" onclick={resetLabels}>
              {t('export.resetLabels')}
            </button>
          </div>
        </div>
        <ul class="cols">
          {#each COLUMNS as c (c.key)}
            <li>
              <label class="check">
                <input type="checkbox" bind:checked={chosen[c.key]} />
                <span class="key">{c.key}</span>
              </label>
              <input class="label-input" type="text"
                     bind:value={labels[c.key]}
                     disabled={!chosen[c.key]}
                     placeholder={c.defaultLabel} />
            </li>
          {/each}
        </ul>
      </div>
    </div>

    <footer>
      <span class="info">{t('export.previewHint')}</span>
      <a class="btn-primary" href={downloadUrl} download>
        <i class="fa-solid fa-download"></i>
        {t('export.download')}
      </a>
    </footer>
  </div>
{/if}

<style>
  .backdrop {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.4);
    z-index: 400;
  }
  .dialog {
    position: fixed;
    top: 8vh;
    left: 50%;
    transform: translateX(-50%);
    width: min(640px, calc(100vw - 32px));
    max-height: 84vh;
    background: var(--bg-elev);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius);
    box-shadow: var(--shadow-lg);
    display: flex; flex-direction: column;
    overflow: hidden;
    z-index: 401;
  }
  header {
    padding: var(--sp-3) var(--sp-4);
    border-bottom: 1px solid var(--border);
    background: var(--bg-card);
    display: flex; align-items: center; justify-content: space-between;
  }
  header h3 { margin: 0; font-size: var(--fs-md); color: var(--fg); }
  .x {
    background: transparent; border: none;
    color: var(--fg-mute); cursor: pointer; font-size: 18px; padding: 0;
  }
  .x:hover { color: var(--red); }

  .body {
    padding: var(--sp-3) var(--sp-4);
    overflow-y: auto;
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  .block { display: flex; flex-direction: column; gap: var(--sp-2); }
  .block-head {
    display: flex; align-items: baseline; justify-content: space-between;
    gap: var(--sp-2); flex-wrap: wrap;
  }
  h4 {
    margin: 0; font-size: var(--fs-xs);
    color: var(--accent); letter-spacing: 0.06em; text-transform: uppercase;
  }
  .row { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
  .pillrow button {
    flex: 0 1 auto;
    background: var(--bg-card); border: 1px solid var(--border);
    color: var(--fg-dim);
    padding: 8px 14px; min-height: var(--tap);
    border-radius: var(--radius-sm); cursor: pointer;
    font-family: var(--sans); font-size: var(--fs-sm);
  }
  .pillrow button.active {
    color: var(--accent); border-color: var(--accent);
    background: color-mix(in srgb, var(--accent) 12%, transparent);
  }
  .all-toggle .link {
    background: transparent; border: none; color: var(--fg-dim); cursor: pointer;
    padding: 0 4px; font-family: var(--sans); font-size: var(--fs-xs);
  }
  .all-toggle .link:hover { color: var(--accent); }

  .cols {
    list-style: none; margin: 0; padding: 0;
    display: flex; flex-direction: column; gap: 4px;
  }
  .cols li {
    display: grid;
    grid-template-columns: 160px 1fr;
    gap: var(--sp-2);
    align-items: center;
  }
  .check {
    display: inline-flex; align-items: center; gap: 8px;
    font-size: var(--fs-sm); color: var(--fg);
  }
  .check .key {
    font-family: var(--num);
    font-size: var(--fs-xs);
    color: var(--fg-dim);
    letter-spacing: 0.04em;
  }
  .label-input {
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 6px 10px;
    min-height: 32px;
    font-family: var(--sans); font-size: var(--fs-sm);
  }
  .label-input:disabled { opacity: 0.4; }
  .label-input:focus { outline: none; border-color: var(--accent); }

  footer {
    padding: var(--sp-3) var(--sp-4);
    border-top: 1px solid var(--border);
    background: var(--bg-card);
    display: flex; align-items: center; justify-content: space-between;
    gap: var(--sp-2);
  }
  .info { color: var(--fg-mute); font-size: var(--fs-xs); }
  .btn-primary {
    text-decoration: none;
    display: inline-flex; align-items: center; gap: 6px;
  }
</style>
