<script lang="ts">
  import { api } from '../lib/api';
  import { formatGrams } from '../lib/format';
  import type { CountState, Reading } from '../lib/types';
  import PanelHeader from './PanelHeader.svelte';

  interface Props { reading: Reading | null; }
  let { reading = null }: Props = $props();

  let countState = $state<CountState | null>(null);
  let referenceCount = $state<number>(10);
  let busy = $state(false);
  let errorMsg = $state<string | null>(null);

  $effect(() => {
    void refreshState();
    const t = window.setInterval(() => void refreshState(), 2000);
    return () => clearInterval(t);
  });

  async function refreshState(): Promise<void> {
    try {
      countState = await api.count();
      errorMsg = null;
    } catch (e) {
      errorMsg = (e as Error).message;
    }
  }

  async function calibrate(): Promise<void> {
    if (busy) return;
    busy = true; errorMsg = null;
    try { countState = await api.countCalibrate(referenceCount); }
    catch (e) { errorMsg = (e as Error).message; }
    finally { busy = false; }
  }

  async function reset(): Promise<void> {
    busy = true;
    try { countState = await api.countReset(); }
    finally { busy = false; }
  }

  let livePieces = $derived.by<number | null>(() => {
    if (!countState?.calibrated || !reading || !countState.piece_weight_g) return null;
    return reading.weight_g / countState.piece_weight_g;
  });
  let livePiecesRounded = $derived.by<number | null>(() => {
    if (livePieces === null) return null;
    return Math.round(livePieces);
  });

  function fmtPieceWeight(g: number | null): string {
    if (g === null) return '—';
    if (g >= 1) return `${g.toFixed(3)} g`;
    return `${(g * 1000).toFixed(2)} mg`;
  }
</script>

<section class="panel">
  <PanelHeader title="Stückzählung" help="count" />

  {#if !countState?.calibrated}
    <p class="hint">
      Lege bekannte Anzahl gleicher Teile auf, gib die Stückzahl ein, dann „Kalibrieren".
    </p>
    <div class="cal-row">
      <input type="number" min="1" max="100000" step="1" bind:value={referenceCount} disabled={busy} />
      <span class="unit">Stück</span>
      <button class="primary" onclick={calibrate} disabled={busy}>
        {busy ? '…' : 'Kalibrieren'}
      </button>
    </div>
    {#if reading}
      <p class="current">Aktuell auf der Waage: <code class="num">{formatGrams(reading.weight_g)}</code></p>
    {/if}
  {:else}
    <div class="big-count num" class:stable={reading?.stable}>
      {livePiecesRounded ?? '—'}
      <span class="big-unit">Stück</span>
    </div>
    {#if livePieces !== null}
      <div class="exact num">rechnerisch {livePieces.toFixed(2)}</div>
    {/if}
    <dl>
      <div><dt>Stückgewicht</dt><dd class="num">{fmtPieceWeight(countState.piece_weight_g)}</dd></div>
      <div><dt>Referenz</dt><dd class="num">{countState.reference_count} Stück</dd></div>
      <div><dt>Gesamt</dt><dd class="num">{reading ? formatGrams(reading.weight_g) : '—'}</dd></div>
    </dl>
    <div class="cal-row">
      <input type="number" min="1" max="100000" step="1" bind:value={referenceCount} disabled={busy} />
      <span class="unit">Stück</span>
      <button onclick={calibrate} disabled={busy}>Neu kalibrieren</button>
    </div>
    <button class="warn-btn" onclick={reset} disabled={busy}>Zurücksetzen</button>
  {/if}
  {#if errorMsg}<p class="error">{errorMsg}</p>{/if}
</section>

<style>
  .panel { display: flex; flex-direction: column; gap: var(--sp-3); height: 100%; }
  .hint { margin: 0; color: var(--fg-dim); font-size: var(--fs-sm); line-height: 1.55; }
  .cal-row { display: flex; align-items: center; gap: var(--sp-2); }
  .cal-row input { flex: 0 0 6rem; }
  .unit { color: var(--fg-dim); font-size: var(--fs-sm); }
  .cal-row button { flex: 1; }
  button.primary { background: var(--bg-card-2); border-color: var(--accent); color: var(--accent); }
  button.warn-btn { color: var(--orange); }
  .current { margin: 0; color: var(--fg-dim); font-size: var(--fs-sm); }

  .big-count {
    font-size: var(--fs-xxl);
    font-weight: 600;
    color: var(--fg-dim);
    text-align: center;
    line-height: 1;
    padding: var(--sp-3) 0;
    transition: color 0.3s;
  }
  .big-count.stable { color: var(--green); }
  .big-unit { font-size: 0.4em; margin-left: 0.3em; color: var(--fg-dim); }
  .exact { color: var(--fg-dim); font-size: var(--fs-sm); text-align: center; }

  dl { display: grid; grid-template-columns: max-content 1fr; gap: var(--sp-1) var(--sp-3); margin: 0; font-size: var(--fs-sm); }
  dl div { display: contents; }
  dt { color: var(--fg-dim); }
  dd { margin: 0; text-align: right; }
  .error { color: var(--red); font-size: var(--fs-sm); margin: 0; }
</style>
