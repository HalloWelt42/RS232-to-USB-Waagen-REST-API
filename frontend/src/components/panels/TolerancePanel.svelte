<script lang="ts">
  /**
   * Qualitätskontrolle / Toleranz mit Ampel grün/gelb/rot.
   * status === 'ok' bei Wert innerhalb [min, max], 'low' bei < min,
   * 'high' bei > max, 'idle' wenn keine Toleranz aktiv.
   */
  import { onMount } from 'svelte';
  import { api } from '../../lib/api';
  import { live } from '../../lib/liveStore.svelte';
  import { toast } from '../../lib/toast.svelte';
  import { formatGrams, formatDiff } from '../../lib/format';
  import { t } from '../../lib/i18n';
  import HelpButton from '../HelpButton.svelte';
  import StableValue from '../StableValue.svelte';
  import type { ToleranceState } from '../../lib/types';

  let info = $state<ToleranceState | null>(null);
  let busy = $state(false);

  let targetText = $state('50');
  let minusText  = $state('2');
  let plusText   = $state('2');

  async function refresh(): Promise<void> {
    try { info = await api.app.tolerance(); }
    catch (e) { toast.show((e as Error).message, 'error'); }
  }

  async function activate(): Promise<void> {
    const target = parseFloat(targetText.replace(',', '.'));
    const minus  = parseFloat(minusText.replace(',', '.'));
    const plus   = parseFloat(plusText.replace(',', '.'));
    if (![target, minus, plus].every(Number.isFinite)) {
      toast.show('Werte ungültig', 'error'); return;
    }
    busy = true;
    try { info = await api.app.toleranceSet(target, minus, plus); toast.show('Toleranz aktiv', 'ok'); }
    catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  async function clear(): Promise<void> {
    busy = true;
    try { info = await api.app.toleranceClear(); toast.show('Toleranz aus', 'ok'); }
    catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  function takeOver(): void {
    if (!live.reading) return;
    targetText = live.reading.weight_g.toFixed(1);
    toast.show(t('toast.valueTakenOver'), 'ok');
  }

  // Live-Status berechnen
  let liveGross = $derived(live.reading?.weight_g ?? null);
  let liveStatus = $derived.by<'idle'|'low'|'ok'|'high'>(() => {
    if (!info?.active || liveGross === null
        || info.min_g === null || info.max_g === null) return 'idle';
    if (liveGross < info.min_g) return 'low';
    if (liveGross > info.max_g) return 'high';
    return 'ok';
  });
  let liveDeviation = $derived.by<number | null>(() => {
    if (!info?.active || liveGross === null || info.target_g === null) return null;
    return liveGross - info.target_g;
  });

  onMount(refresh);
</script>

<section class="panel">
  <header>
    <h2>{t('tools.tolerance')}</h2>
    <HelpButton id="tolerance" />
  </header>

  <div class="lamp-area" data-status={liveStatus}>
    <div class="lamp">
      <span class="main"><StableValue g={liveGross} /></span>
      {#if info?.active}
        <span class="num dev"
              class:plus={liveDeviation !== null && liveDeviation >= 0}
              class:minus={liveDeviation !== null && liveDeviation < 0}>
          {formatDiff(liveDeviation)}
        </span>
        <span class="status-text">
          {liveStatus === 'ok'   ? 'INNERHALB TOLERANZ' :
           liveStatus === 'low'  ? 'UNTER MINIMUM'      :
           liveStatus === 'high' ? 'ÜBER MAXIMUM'       : 'NICHT AKTIV'}
        </span>
      {:else}
        <span class="status-text idle">TOLERANZ NICHT AKTIV</span>
      {/if}
    </div>
  </div>

  <div class="form">
    <div class="grid">
      <label>
        Sollwert (g)
        <div class="row-flex">
          <input type="text" inputmode="decimal" bind:value={targetText} />
          <button class="btn-primary small" onclick={takeOver} disabled={liveGross === null}
                  title="Aktuellen Wert übernehmen">
            <i class="fa-solid fa-circle-down"></i>
          </button>
        </div>
      </label>
      <label>
        Toleranz minus (g)
        <input type="text" inputmode="decimal" bind:value={minusText} />
      </label>
      <label>
        Toleranz plus (g)
        <input type="text" inputmode="decimal" bind:value={plusText} />
      </label>
    </div>

    {#if info?.active}
      <div class="info">
        <div class="i-row"><span class="key">Min</span><span class="num val">{formatGrams(info.min_g)}</span></div>
        <div class="i-row"><span class="key">Soll</span><span class="num val">{formatGrams(info.target_g)}</span></div>
        <div class="i-row"><span class="key">Max</span><span class="num val">{formatGrams(info.max_g)}</span></div>
      </div>
    {/if}

    <div class="actions-row">
      <button class="btn-primary" onclick={activate} disabled={busy}>
        <i class="fa-solid fa-bullseye"></i>
        {info?.active ? 'Aktualisieren' : 'Aktivieren'}
      </button>
      {#if info?.active}
        <button class="btn-warn" onclick={clear} disabled={busy}>
          <i class="fa-solid fa-power-off"></i>
          Deaktivieren
        </button>
      {/if}
    </div>
  </div>
</section>

<style>
  .panel {
    flex: 1 1 auto; min-height: 0; overflow-y: auto;
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-4);
  }
  header { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3); }
  header h2 { margin: 0; font-size: var(--fs-xl); font-weight: 600; }

  .lamp-area {
    display: flex; justify-content: center;
  }
  .lamp {
    width: 100%; max-width: 480px;
    border-radius: var(--radius-soft);
    container-type: inline-size;
    padding: var(--sp-5) var(--sp-4);
    text-align: center;
    border: 2px solid var(--border);
    background: var(--bg-card-2);
    box-shadow: inset 0 2px 12px rgba(0,0,0,0.25);
    transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
  }
  .lamp .main {
    display: block;
    /* Skaliert mit Container, max. 67 px — passt auch -30.000,0 g rein. */
    font-size: clamp(36px, 13cqi, 67px);
    line-height: 1;
    color: var(--fg-dim);
    overflow: hidden;
  }
  .lamp .main :global(.stable-value) { color: inherit; }
  .lamp .dev {
    display: block;
    margin-top: var(--sp-2);
    font-size: var(--fs-xl);
    color: var(--fg-dim);
  }
  .lamp .dev.plus { color: var(--green); }
  .lamp .dev.minus { color: var(--orange); }
  .lamp .status-text {
    display: block;
    margin-top: var(--sp-2);
    font-size: var(--fs-sm);
    letter-spacing: 0.18em;
    color: var(--fg-mute);
    font-weight: 600;
  }
  .lamp-area[data-status="ok"]   .lamp { border-color: var(--green);  background: color-mix(in srgb, var(--green) 14%, transparent); }
  .lamp-area[data-status="low"]  .lamp { border-color: var(--orange); background: color-mix(in srgb, var(--orange) 14%, transparent); }
  .lamp-area[data-status="high"] .lamp { border-color: var(--red);    background: color-mix(in srgb, var(--red) 14%, transparent); }
  .lamp-area[data-status="ok"]   .lamp .main, .lamp-area[data-status="ok"]   .lamp .status-text { color: var(--green); }
  .lamp-area[data-status="low"]  .lamp .main, .lamp-area[data-status="low"]  .lamp .status-text { color: var(--orange); }
  .lamp-area[data-status="high"] .lamp .main, .lamp-area[data-status="high"] .lamp .status-text { color: var(--red); }

  .form {
    max-width: 480px; margin-inline: auto; width: 100%;
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  /* Drei Spalten mit kompakten Zahleneingaben — Sollwert bekommt
     mehr Platz wegen Übernehmen-Knopf, Tol- und Tol+ kompakt. */
  .grid {
    display: grid;
    grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr) minmax(0, 1fr);
    gap: var(--sp-2);
    align-items: end;
  }
  label {
    display: flex; flex-direction: column; gap: 6px;
    font-size: var(--fs-xs); color: var(--fg-dim);
    letter-spacing: 0.05em; text-transform: uppercase;
    min-width: 0;
  }
  label input { width: 100%; min-width: 0; }
  .row-flex { display: flex; gap: var(--sp-2); min-width: 0; }
  .row-flex input { flex: 1 1 auto; min-width: 0; }
  .btn-primary.small {
    flex: 0 0 auto;
    padding: 0 10px;
    min-width: var(--tap);
  }

  .info {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: var(--sp-3) var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-2);
  }
  .i-row { display: flex; justify-content: space-between; }
  .key {
    font-size: var(--fs-sm); color: var(--fg-dim);
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .val { font-size: var(--fs-md); }

  .actions-row { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
  .actions-row .btn-primary, .actions-row .btn-warn {
    flex: 1 1 auto;
    display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  }
  .btn-warn {
    min-height: var(--tap); padding: 0 var(--sp-3);
    background: transparent; border: 1px solid var(--orange);
    color: var(--orange); border-radius: var(--radius-sm);
    font-family: var(--sans); font-size: var(--fs-sm); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;
  }
  .btn-warn:hover:not(:disabled) {
    background: color-mix(in srgb, var(--orange) 14%, transparent);
  }

  @media (max-width: 600px) {
    .grid { grid-template-columns: 1fr; }
  }
</style>
