<script lang="ts">
  /**
   * Werte erfassen — Snapshot des aktuellen Live-Werts mit Label und Notiz,
   * gruppierbar in Sessions, mit Statistik und CSV-Export.
   */
  import { onMount } from 'svelte';
  import { api } from '../../lib/api';
  import { live } from '../../lib/liveStore.svelte';
  import { toast } from '../../lib/toast.svelte';
  import { formatGrams, formatTime } from '../../lib/format';
  import { t } from '../../lib/i18n';
  import HelpButton from '../HelpButton.svelte';
  import ExportDialog from '../ExportDialog.svelte';
  import type { Sample, SampleStats } from '../../lib/types';

  let exportOpen = $state(false);

  let samples = $state<Sample[]>([]);
  let stats = $state<SampleStats | null>(null);
  let busy = $state(false);

  let session = $state('default');
  let label = $state('');
  let note = $state('');

  // Auto-Capture-Modi:
  //   manual    — Klick erfasst sofort (Default)
  //   half-auto — Klick „auf nächsten Stable" wartet bis stable + erfasst
  //   auto      — automatisch erfassen, sobald nach unstable wieder stable
  type Mode = 'manual' | 'half-auto' | 'auto';
  let mode = $state<Mode>('manual');

  let waitingForStable = $state(false);
  let lastAutoCapture: number | null = $state(null);   // letzter erfasster Wert
  let autoArmed = $state(false);                       // erst nach unstable wieder armed

  async function refresh(): Promise<void> {
    try {
      const list = await api.app.samplesList(session, 500);
      samples = list.items;
      stats = await api.app.samplesStats(session);
    } catch (e) { toast.show((e as Error).message, 'error'); }
  }

  async function add(): Promise<void> {
    busy = true;
    try {
      await api.app.samplesAdd(label, note, session);
      toast.show(t('samples.captured'), 'ok');
      label = ''; note = '';
      await refresh();
    } catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  /** Halb-Auto-Modus: bis zum nächsten Stable-Wert warten und dann erfassen. */
  function armHalfAuto(): void {
    if (!live.reading) return;
    if (live.reading.stable) {
      // Schon stable — direkt erfassen
      void add();
    } else {
      waitingForStable = true;
      toast.show(t('samples.waitingForStable'), 'ok');
    }
  }

  // Reaktive Auto-Capture-Logik
  $effect(() => {
    const r = live.reading;
    if (!r) return;

    if (mode === 'half-auto' && waitingForStable && r.stable) {
      waitingForStable = false;
      void add();
      return;
    }

    if (mode === 'auto') {
      // Bei jeder Unstable-Phase wird die „autoArmed"-Markierung gesetzt;
      // sobald der nächste Stable-Wert kommt, der sich vom letzten erfassten
      // Wert unterscheidet, wird automatisch erfasst.
      if (!r.stable) {
        autoArmed = true;
        return;
      }
      if (r.stable && autoArmed && r.weight_g !== lastAutoCapture) {
        autoArmed = false;
        lastAutoCapture = r.weight_g;
        void add();
      }
    } else {
      // Andere Modi: Tracking zurücksetzen, damit beim Wechsel sauber startet
      autoArmed = false;
      lastAutoCapture = null;
    }
  });

  async function del(id: number): Promise<void> {
    busy = true;
    try { await api.app.samplesDelete(id); await refresh(); }
    catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  async function clearAll(): Promise<void> {
    if (!confirm(`Alle Werte der Session „${session}" wirklich löschen?`)) return;
    busy = true;
    try {
      await api.app.samplesClear(session);
      toast.show('Session geleert', 'ok');
      await refresh();
    } catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  let exportUrl = $derived(api.app.samplesExportUrl(session));
  let liveGross = $derived(live.reading?.weight_g ?? null);

  onMount(refresh);
</script>

<section class="panel">
  <header>
    <h2>{t('tools.samples')}</h2>
    <HelpButton id="samples" />
  </header>

  <div class="form">
    <div class="grid">
      <label>
        Session
        <input type="text" bind:value={session} onchange={refresh} />
      </label>
      <label>
        Label (optional)
        <input type="text" placeholder="z.B. Probe A1" bind:value={label} />
      </label>
    </div>
    <label class="full">
      Notiz (optional)
      <input type="text" placeholder="kurze Bemerkung" bind:value={note} />
    </label>

    <div class="modes" role="radiogroup" aria-label={t('samples.modeLabel')}>
      <button class:active={mode==='manual'}     onclick={() => mode='manual'}>
        <i class="fa-solid fa-hand-pointer"></i> {t('samples.modeManual')}
      </button>
      <button class:active={mode==='half-auto'}  onclick={() => mode='half-auto'}>
        <i class="fa-solid fa-stopwatch"></i> {t('samples.modeHalfAuto')}
      </button>
      <button class:active={mode==='auto'}       onclick={() => mode='auto'}>
        <i class="fa-solid fa-bolt"></i> {t('samples.modeAuto')}
      </button>
    </div>

    <div class="actions-row">
      <div class="live-info">
        {t('samples.liveValue')}: <span class="num">{formatGrams(liveGross)}</span>
        {#if mode === 'auto'}
          · <span class="auto-hint">{t('samples.autoHint')}</span>
        {:else if mode === 'half-auto' && waitingForStable}
          · <span class="auto-hint">{t('samples.waitingForStable')}</span>
        {/if}
      </div>
      {#if mode === 'half-auto'}
        <button class="btn-primary" onclick={armHalfAuto} disabled={busy || liveGross === null}>
          <i class="fa-solid fa-stopwatch"></i>
          {t('samples.captureOnStable')}
        </button>
      {:else if mode === 'manual'}
        <button class="btn-primary" onclick={add} disabled={busy || liveGross === null}>
          <i class="fa-solid fa-circle-down"></i>
          {t('samples.captureNow')}
        </button>
      {/if}
    </div>
  </div>

  {#if stats && stats.count > 0}
    <div class="stats">
      <div class="s-cell"><span class="key">Anzahl</span><span class="num val">{stats.count}</span></div>
      <div class="s-cell"><span class="key">Min</span><span class="num val">{formatGrams(stats.min_g)}</span></div>
      <div class="s-cell"><span class="key">Max</span><span class="num val">{formatGrams(stats.max_g)}</span></div>
      <div class="s-cell"><span class="key">Mittel</span><span class="num val">{formatGrams(stats.mean_g)}</span></div>
      <div class="s-cell"><span class="key">σ</span><span class="num val">{formatGrams(stats.stdev_g)}</span></div>
      <div class="s-cell"><span class="key">Summe</span><span class="num val">{formatGrams(stats.sum_g)}</span></div>
    </div>

    <div class="bulk">
      <button class="btn-primary" onclick={() => exportOpen = true}>
        <i class="fa-solid fa-file-export"></i>
        {t('samples.exportOpen')}
      </button>
      <button class="btn-warn" onclick={clearAll} disabled={busy}>
        <i class="fa-solid fa-trash"></i>
        {t('samples.clearSession')}
      </button>
    </div>
  {/if}

  <ExportDialog open={exportOpen}
                {session}
                onClose={() => exportOpen = false} />

  <ul class="list">
    {#if samples.length === 0}
      <li class="empty">Noch keine Werte erfasst</li>
    {:else}
      {#each samples as s (s.id)}
        <li class="row">
          <span class="ts num">{formatTime(s.ts)}</span>
          <span class="num weight">{formatGrams(s.weight_g)}</span>
          <span class="lbl">{s.label || '—'}</span>
          <span class="note">{s.note || ''}</span>
          <button class="x" onclick={() => del(s.id)} disabled={busy}
                  title="Eintrag löschen" aria-label="Eintrag löschen">
            <i class="fa-regular fa-circle-xmark"></i>
          </button>
        </li>
      {/each}
    {/if}
  </ul>
</section>

<style>
  .panel {
    flex: 1 1 auto; min-height: 0; overflow-y: auto;
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  header { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3); }
  header h2 { margin: 0; font-size: var(--fs-xl); font-weight: 600; }

  .form {
    max-width: 480px; margin-inline: auto; width: 100%;
    display: flex; flex-direction: column; gap: var(--sp-3);
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-3) var(--sp-4);
  }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-2); }
  label {
    display: flex; flex-direction: column; gap: 6px;
    font-size: var(--fs-sm); color: var(--fg-dim);
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .full { width: 100%; }
  .actions-row {
    display: flex; align-items: center; justify-content: space-between;
    gap: var(--sp-2); flex-wrap: wrap;
  }
  .live-info { color: var(--fg-dim); font-size: var(--fs-sm); }
  .auto-hint { color: var(--accent); font-style: italic; }
  .modes { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
  .modes button {
    flex: 1 1 auto;
    min-height: var(--tap);
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--fg-dim);
    border-radius: var(--radius-sm);
    cursor: pointer;
    display: inline-flex; align-items: center; justify-content: center;
    gap: 6px;
    font-size: var(--fs-sm);
  }
  .modes button.active {
    color: var(--accent); border-color: var(--accent);
    background: color-mix(in srgb, var(--accent) 10%, transparent);
  }
  .actions-row .btn-primary {
    display: inline-flex; align-items: center; gap: 6px;
  }

  .stats {
    max-width: 720px; margin-inline: auto; width: 100%;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(120px, 100%), 1fr));
    gap: var(--sp-2);
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-3);
  }
  .s-cell {
    display: flex; flex-direction: column; gap: 2px;
    align-items: center; text-align: center;
  }
  .key { font-size: var(--fs-xs); color: var(--fg-mute); letter-spacing: 0.05em; text-transform: uppercase; }
  .val { font-size: var(--fs-md); }

  .bulk {
    max-width: 720px; margin-inline: auto; width: 100%;
    display: flex; gap: var(--sp-2); flex-wrap: wrap;
  }
  .bulk .btn-primary, .bulk .btn-warn {
    flex: 1 1 auto;
    display: inline-flex; align-items: center; justify-content: center; gap: 6px;
    text-decoration: none;
  }
  .btn-warn {
    min-height: var(--tap); padding: 0 var(--sp-3);
    background: transparent; border: 1px solid var(--orange);
    color: var(--orange); border-radius: var(--radius-sm);
    font-family: var(--sans); font-size: var(--fs-sm); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;
  }
  .btn-warn:hover:not(:disabled) { background: color-mix(in srgb, var(--orange) 14%, transparent); }

  .list {
    list-style: none; margin: 0; padding: 0;
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    max-width: 920px; margin-inline: auto; width: 100%;
  }
  .row {
    display: grid;
    grid-template-columns: max-content max-content 1fr 1fr max-content;
    gap: var(--sp-3);
    align-items: center;
    padding: 8px var(--sp-3);
    border-bottom: 1px solid var(--border);
    font-size: var(--fs-sm);
  }
  .row:last-child { border-bottom: none; }
  .ts { color: var(--fg-mute); font-size: var(--fs-xs); }
  .weight { font-size: var(--fs-md); color: var(--accent); }
  .lbl { color: var(--fg); font-size: var(--fs-sm); }
  .note { color: var(--fg-dim); font-size: var(--fs-sm); }
  .x {
    background: transparent; border: none; padding: 0;
    color: var(--fg-mute); font-size: 16px; cursor: pointer;
  }
  .x:hover { color: var(--red); }
  .empty {
    padding: var(--sp-4); text-align: center;
    color: var(--fg-mute); font-size: var(--fs-sm);
  }
</style>
