<script lang="ts">
  /**
   * Stückzählung mit Vorlagen-Karussell oben.
   * Vorlagen liefern ein typisches Stückgewicht — der Anwender kann
   * direkt loslegen oder mit eigenen Referenz-Teilen kalibrieren.
   */
  import { onMount } from 'svelte';
  import { api } from '../../lib/api';
  import { live } from '../../lib/liveStore.svelte';
  import { toast } from '../../lib/toast.svelte';
  import { formatGrams, formatTime } from '../../lib/format';
  import { COUNT_TEMPLATES, type CountTemplate } from '../../lib/countTemplates';
  import { t } from '../../lib/i18n';
  import HelpButton from '../HelpButton.svelte';
  import type { CountState } from '../../lib/types';

  let info = $state<CountState | null>(null);
  let busy = $state(false);
  let refText = $state('10');

  async function refresh(): Promise<void> {
    try { info = await api.app.count(); }
    catch (e) { toast.show((e as Error).message, 'error'); }
  }

  async function calibrate(): Promise<void> {
    const n = parseInt(refText.replace(/\D/g, ''), 10);
    if (!Number.isFinite(n) || n <= 0) { toast.show('Anzahl ungültig', 'error'); return; }
    busy = true;
    try { info = await api.app.countCalibrate(n); toast.show(`Kalibriert mit ${n} Stück`, 'ok'); }
    catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  async function reset(): Promise<void> {
    busy = true;
    try { info = await api.app.countReset(); toast.show('Zähler zurückgesetzt', 'ok'); }
    catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  function applyTemplate(tpl: CountTemplate): void {
    // Vorlage liefert Schätzung — Anwender muss anschließend selbst
    // kalibrieren. Wir empfehlen eine sinnvolle Referenzanzahl.
    refText = String(Math.max(10, Math.round(20 / tpl.pieceWeightG)));
    toast.show(`Vorlage „${tpl.label}": ca. ${tpl.pieceWeightG} g/Stück`, 'ok');
  }

  // Live-Anzeige der Stückzahl — Backend liefert pieces nur, wenn kalibriert.
  let liveGross = $derived(live.reading?.weight_g ?? null);
  let pieces = $derived.by<number | null>(() => {
    if (!info?.calibrated || info.piece_weight_g === null
        || info.piece_weight_g === 0 || liveGross === null) return null;
    return Math.round(liveGross / info.piece_weight_g);
  });
  let piecesExact = $derived.by<number | null>(() => {
    if (!info?.calibrated || info.piece_weight_g === null
        || info.piece_weight_g === 0 || liveGross === null) return null;
    return liveGross / info.piece_weight_g;
  });

  onMount(refresh);
</script>

<section class="panel">
  <header>
    <h2>{t('tools.count')}</h2>
    <HelpButton id="count" />
  </header>

  <div class="templates">
    {#each COUNT_TEMPLATES as tpl}
      <button class="tpl" onclick={() => applyTemplate(tpl)} title={tpl.description}>
        <i class={tpl.iconClass} aria-hidden="true"></i>
        <span class="lbl">{tpl.label}</span>
        <span class="num pw">~{tpl.pieceWeightG} g</span>
      </button>
    {/each}
  </div>

  <div class="form">
    <div class="display">
      <div class="row">
        <span class="lbl">Gesamtgewicht</span>
        <span class="num val">{formatGrams(liveGross)}</span>
      </div>
      {#if info?.calibrated}
        <div class="row">
          <span class="lbl">Stückgewicht</span>
          <span class="num val">{formatGrams(info.piece_weight_g)}</span>
        </div>
      {/if}
      <div class="row big">
        <span class="lbl">Stückzahl</span>
        <span class="num val big" class:active={pieces !== null}>
          {pieces !== null ? pieces : '—'} <small class="unit">Stück</small>
        </span>
      </div>
      {#if piecesExact !== null}
        <div class="meta num">exakt: {piecesExact.toFixed(2)} Stk</div>
      {/if}
      {#if info?.calibrated_at}
        <div class="meta">kalibriert {formatTime(info.calibrated_at)}</div>
      {/if}
    </div>

    <div class="manual">
      <label>
        Anzahl Referenz-Teile auf der Waage
        <div class="row-flex">
          <input type="text" inputmode="numeric" bind:value={refText} />
          <button class="btn-primary" onclick={calibrate} disabled={busy || liveGross === null}>
            <i class="fa-solid fa-check"></i>
            Kalibrieren
          </button>
        </div>
      </label>
    </div>

    {#if info?.calibrated}
      <button class="btn-warn full" onclick={reset} disabled={busy}>
        <i class="fa-solid fa-eraser"></i>
        Kalibrierung zurücksetzen
      </button>
    {/if}
  </div>
</section>

<style>
  .panel {
    flex: 1 1 auto; min-height: 0; overflow-y: auto;
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-4);
  }
  header {
    display: flex; align-items: center; justify-content: space-between;
    gap: var(--sp-3);
  }
  header h2 { margin: 0; font-size: var(--fs-xl); font-weight: 600; }

  .templates {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(140px, 100%), 1fr));
    gap: var(--sp-2);
    max-width: 720px;
    margin-inline: auto;
    width: 100%;
  }
  .tpl {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    color: var(--fg);
    border-radius: var(--radius-sm);
    padding: var(--sp-2) var(--sp-3);
    display: flex; flex-direction: column; align-items: center;
    gap: 4px;
    min-height: var(--tap);
    cursor: pointer;
  }
  .tpl:hover { border-color: var(--accent); color: var(--accent); }
  .tpl i { font-size: 18px; }
  .tpl .lbl { font-size: var(--fs-sm); }
  .tpl .pw { font-size: var(--fs-xs); color: var(--fg-mute); }

  .form {
    max-width: 480px; margin-inline: auto; width: 100%;
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  .display {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-2);
  }
  .row { display: flex; justify-content: space-between; align-items: baseline; }
  .row.big { padding-top: var(--sp-2); margin-top: var(--sp-2); border-top: 1px solid var(--border); }
  .lbl {
    font-size: var(--fs-sm); color: var(--fg-dim);
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .val { font-size: var(--fs-lg); }
  .val.big { font-size: var(--fs-xxl); color: var(--fg-dim); }
  .val.big.active { color: var(--accent); }
  .val .unit { font-family: var(--sans); font-size: var(--fs-md); font-weight: 500; color: var(--fg-dim); margin-left: 6px; }
  .meta { font-size: var(--fs-xs); color: var(--fg-mute); text-align: right; }

  .manual {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-3) var(--sp-4);
  }
  .manual label {
    display: flex; flex-direction: column; gap: var(--sp-2);
    font-size: var(--fs-sm); color: var(--fg-dim);
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .row-flex { display: flex; gap: var(--sp-2); }
  .row-flex input { flex: 1; }
  .row-flex .btn-primary {
    display: inline-flex; align-items: center; gap: 6px; white-space: nowrap;
  }
  .btn-warn {
    min-height: var(--tap); padding: 0 var(--sp-3);
    background: transparent; border: 1px solid var(--orange);
    color: var(--orange); border-radius: var(--radius-sm);
    font-family: var(--sans); font-size: var(--fs-sm); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;
    display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  }
  .btn-warn.full { width: 100%; }
  .btn-warn:hover:not(:disabled) {
    background: color-mix(in srgb, var(--orange) 14%, transparent);
  }
</style>
