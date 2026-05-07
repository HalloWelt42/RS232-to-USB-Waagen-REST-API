<script lang="ts">
  import { api } from '../lib/api';
  import { formatGrams } from '../lib/format';
  import type { Reading, Status, ToleranceState } from '../lib/types';

  interface Props { reading: Reading | null; }
  let { reading = null }: Props = $props();

  let cfg = $state<ToleranceState | null>(null);
  let target  = $state<number>(100);
  let tolMin  = $state<number>(1);
  let tolPlus = $state<number>(1);
  let busy = $state(false);
  let errorMsg = $state<string | null>(null);

  $effect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 2000);
    return () => clearInterval(t);
  });

  async function refresh(): Promise<void> {
    try {
      cfg = await api.tolerance();
      if (cfg.active && cfg.target_g !== null && cfg.tolerance_minus_g !== null && cfg.tolerance_plus_g !== null) {
        target  = cfg.target_g;
        tolMin  = cfg.tolerance_minus_g;
        tolPlus = cfg.tolerance_plus_g;
      }
      errorMsg = null;
    } catch (e) {
      errorMsg = (e as Error).message;
    }
  }

  async function setTolerance(): Promise<void> {
    if (busy) return;
    busy = true; errorMsg = null;
    try {
      cfg = await api.toleranceSet(Number(target), Number(tolMin), Number(tolPlus));
    } catch (e) {
      errorMsg = (e as Error).message;
    } finally {
      busy = false;
    }
  }

  async function clearTolerance(): Promise<void> {
    busy = true;
    try { cfg = await api.toleranceClear(); } finally { busy = false; }
  }

  let liveStatus = $derived.by<Status>(() => {
    if (!cfg?.active || !reading || cfg.min_g === null || cfg.max_g === null) {
      return cfg?.status ?? 'idle';
    }
    if (reading.weight_g < cfg.min_g) return 'low';
    if (reading.weight_g > cfg.max_g) return 'high';
    return 'ok';
  });

  let liveDeviation = $derived.by<number | null>(() => {
    if (!cfg?.active || !reading || cfg.target_g === null) return null;
    return reading.weight_g - cfg.target_g;
  });
</script>

<section class="panel">
  {#if !cfg?.active}
    <p class="hint">Sollwert + Toleranz festlegen — Anzeige zeigt grün, gelb oder rot je nach Abweichung.</p>
    <div class="grid">
      <label><span>Soll [g]</span><input type="number" step="0.1" bind:value={target} /></label>
      <label><span>Tol- [g]</span><input type="number" step="0.01" min="0" bind:value={tolMin} /></label>
      <label><span>Tol+ [g]</span><input type="number" step="0.01" min="0" bind:value={tolPlus} /></label>
    </div>
    <button class="primary" onclick={setTolerance} disabled={busy}>
      {busy ? 'Speichere' : 'Aktivieren'}
    </button>
  {:else}
    <div class="lamp" data-status={liveStatus}>
      <span>{
        liveStatus === 'ok'   ? 'IN ORDNUNG'
      : liveStatus === 'low'  ? 'ZU LEICHT'
      : liveStatus === 'high' ? 'ZU SCHWER'
      : '...'}</span>
    </div>
    <dl>
      <div><dt>Soll</dt><dd>{formatGrams(cfg.target_g)}</dd></div>
      <div><dt>Bereich</dt><dd>{formatGrams(cfg.min_g)} ... {formatGrams(cfg.max_g)}</dd></div>
      <div><dt>Aktuell</dt><dd>{reading ? formatGrams(reading.weight_g) : '—'}</dd></div>
      <div><dt>Abweichung</dt><dd class:ok={liveStatus==='ok'} class:warn={liveStatus!=='ok' && liveStatus!=='idle'}>
        {liveDeviation === null ? '—' : (liveDeviation >= 0 ? '+' : '') + liveDeviation.toFixed(2) + ' g'}
      </dd></div>
    </dl>
    <div class="grid">
      <label><span>Soll [g]</span><input type="number" step="0.1" bind:value={target} /></label>
      <label><span>Tol- [g]</span><input type="number" step="0.01" min="0" bind:value={tolMin} /></label>
      <label><span>Tol+ [g]</span><input type="number" step="0.01" min="0" bind:value={tolPlus} /></label>
    </div>
    <div class="row">
      <button onclick={setTolerance} disabled={busy}>Übernehmen</button>
      <button class="warn-btn" onclick={clearTolerance} disabled={busy}>Deaktivieren</button>
    </div>
  {/if}
  {#if errorMsg}<p class="error">{errorMsg}</p>{/if}
</section>

<style>
  .panel { display: flex; flex-direction: column; gap: 0.85rem; height: 100%; }
  .hint { margin: 0; color: var(--fg-dim); font-size: 0.9rem; }
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 0.5rem;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    font-size: 0.72rem;
    color: var(--fg-dim);
  }
  input[type="number"] { width: 100%; }
  .row { display: flex; gap: 0.5rem; }
  button.primary { background: var(--bg-card-2); border-color: var(--accent); }
  button.warn-btn { color: var(--orange); }
  .lamp {
    border-radius: var(--radius);
    padding: 1.5rem 1rem;
    text-align: center;
    font-family: var(--mono);
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    border: 2px solid var(--border);
    background: var(--bg);
  }
  .lamp[data-status="ok"]   { border-color: var(--green);  background: rgba(63, 185, 80, 0.15);  color: var(--green); }
  .lamp[data-status="low"]  { border-color: var(--orange); background: rgba(210, 153, 34, 0.15); color: var(--orange); }
  .lamp[data-status="high"] { border-color: var(--red);    background: rgba(248, 81, 73, 0.15);  color: var(--red); }
  .lamp[data-status="idle"] { color: var(--fg-dim); }
  dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.4rem 1rem; margin: 0; font-size: 0.9rem; }
  dl div { display: contents; }
  dt { color: var(--fg-dim); }
  dd { margin: 0; text-align: right; font-family: var(--mono); }
  dd.ok { color: var(--green); }
  dd.warn { color: var(--orange); }
  .error { color: var(--red); font-size: 0.85rem; margin: 0; }
</style>
