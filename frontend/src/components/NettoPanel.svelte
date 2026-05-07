<script lang="ts">
  import { api } from '../lib/api';
  import { formatGrams } from '../lib/format';
  import type { NettoState, Reading } from '../lib/types';

  interface Props { reading: Reading | null; }
  let { reading = null }: Props = $props();

  let cfg = $state<NettoState | null>(null);
  let manualTare = $state<string>('');
  let busy = $state(false);
  let errorMsg = $state<string | null>(null);

  $effect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 2000);
    return () => clearInterval(t);
  });

  async function refresh(): Promise<void> {
    try {
      cfg = await api.netto();
      errorMsg = null;
    } catch (e) {
      errorMsg = (e as Error).message;
    }
  }

  async function tareCurrent(): Promise<void> {
    if (busy) return;
    busy = true; errorMsg = null;
    try { cfg = await api.nettoTareCurrent(); }
    catch (e) { errorMsg = (e as Error).message; }
    finally { busy = false; }
  }

  async function tareManual(): Promise<void> {
    const v = Number(manualTare);
    if (Number.isNaN(v)) { errorMsg = 'Zahl eingeben'; return; }
    busy = true; errorMsg = null;
    try { cfg = await api.nettoTareValue(v); manualTare = ''; }
    catch (e) { errorMsg = (e as Error).message; }
    finally { busy = false; }
  }

  async function clearTare(): Promise<void> {
    busy = true;
    try { cfg = await api.nettoTareClear(); }
    finally { busy = false; }
  }

  let liveNetto = $derived.by<number | null>(() => {
    if (!cfg?.active || !reading || cfg.tare_g === null) return null;
    return reading.weight_g - cfg.tare_g;
  });
</script>

<section class="panel">
  {#if !cfg?.active}
    <p class="hint">
      Behälter aufstellen, "Tara einfrieren" — danach Netto-Anzeige.
      Alternativ ein bekanntes Tara-Gewicht eintragen.
    </p>
    <button class="primary" onclick={tareCurrent} disabled={busy || !reading}>
      {busy ? '...' : 'Aktuelles Gewicht als Tara einfrieren'}
    </button>
    <div class="manual-row">
      <input type="number" step="0.01" placeholder="Tara [g]" bind:value={manualTare} disabled={busy} />
      <button onclick={tareManual} disabled={busy || manualTare === ''}>Setzen</button>
    </div>
    {#if reading}
      <p class="current">Aktuell: <code>{formatGrams(reading.weight_g)}</code></p>
    {/if}
  {:else}
    <div class="netto-display">
      <span class="big" class:stable={reading?.stable}>{formatGrams(liveNetto)}</span>
      <span class="big-label">Netto</span>
    </div>
    <dl>
      <div><dt>Brutto</dt><dd>{reading ? formatGrams(reading.weight_g) : '—'}</dd></div>
      <div><dt>Tara</dt><dd>{formatGrams(cfg.tare_g)}</dd></div>
      <div><dt>Gesetzt am</dt><dd class="ts">{cfg.tare_set_at?.replace('T', ' ') ?? '—'}</dd></div>
    </dl>
    <div class="row">
      <button onclick={tareCurrent} disabled={busy}>Tara neu setzen</button>
      <button class="warn-btn" onclick={clearTare} disabled={busy}>Deaktivieren</button>
    </div>
  {/if}
  {#if errorMsg}<p class="error">{errorMsg}</p>{/if}
</section>

<style>
  .panel { display: flex; flex-direction: column; gap: 0.85rem; height: 100%; }
  .hint { margin: 0; color: var(--fg-dim); font-size: 0.9rem; line-height: 1.4; }
  button.primary { background: var(--bg-card-2); border-color: var(--accent); }
  button.warn-btn { color: var(--orange); }
  .manual-row { display: flex; gap: 0.5rem; }
  .manual-row input { flex: 1; }
  .row { display: flex; gap: 0.5rem; }
  .row button { flex: 1; }
  .current { margin: 0; color: var(--fg-dim); font-size: 0.85rem; }
  .netto-display {
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem 0;
  }
  .big {
    font-family: var(--mono);
    font-size: 2.5rem;
    font-weight: 600;
    color: var(--fg-dim);
    transition: color 0.3s;
  }
  .big.stable { color: var(--green); }
  .big-label { font-size: 0.85rem; color: var(--fg-dim); text-transform: uppercase; letter-spacing: 0.1em; }
  dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.4rem 1rem; margin: 0; font-size: 0.9rem; }
  dl div { display: contents; }
  dt { color: var(--fg-dim); }
  dd { margin: 0; text-align: right; font-family: var(--mono); }
  dd.ts { font-size: 0.8rem; color: var(--fg-dim); }
  .error { color: var(--red); font-size: 0.85rem; margin: 0; }
</style>
