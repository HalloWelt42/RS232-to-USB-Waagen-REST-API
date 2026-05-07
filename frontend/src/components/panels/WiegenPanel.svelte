<script lang="ts">
  /**
   * Wiegen — reines Ablesen.
   * Untermodi:
   *   frei      = nur Live-Wert sehen, klicken kopiert.
   *   sollwert  = man trägt einen Soll-Wert ein und sieht den
   *               aktuellen Live-Wert relativ dazu (Differenz und Anteil in Prozent).
   */
  import { live } from '../../lib/liveStore.svelte';
  import { copyText } from '../../lib/clipboard';
  import { toast } from '../../lib/toast.svelte';
  import { formatDiff, formatGrams } from '../../lib/format';
  import { t } from '../../lib/i18n';
  import { modelStore } from '../../lib/modelStore.svelte';
  import HelpButton from '../HelpButton.svelte';
  import StableValue from '../StableValue.svelte';

  type Mode = 'frei' | 'sollwert';
  let mode = $state<Mode>('frei');

  let sollText = $state('');
  let soll = $derived.by<number | null>(() => {
    const v = parseFloat(sollText.replace(',', '.'));
    return Number.isFinite(v) ? v : null;
  });

  let r = $derived(live.reading);
  let weight = $derived(r?.weight_g ?? null);

  let diff = $derived.by<number | null>(() => {
    if (weight === null || soll === null) return null;
    return weight - soll;
  });

  let percent = $derived.by<number | null>(() => {
    if (weight === null || soll === null || soll === 0) return null;
    return (weight / soll) * 100;
  });

  async function copyValue(): Promise<void> {
    if (weight === null) return;
    const ok = await copyText(weight.toFixed(1));
    toast.show(ok ? t('toast.valueCopiedG', weight.toFixed(1) + ' g') : t('toast.copyError'),
      ok ? 'ok' : 'error');
  }

  function takeOver(): void {
    if (weight === null) return;
    sollText = weight.toFixed(1);
    toast.show(t('toast.valueTakenOver'), 'ok');
  }

  // Modell-Toleranz-Warnung: Auflage unter Mindestlast
  let underMinLoad = $derived.by<boolean>(() => {
    const m = modelStore.active;
    if (m.min_load_g <= 0 || weight === null) return false;
    return weight > 0 && weight < m.min_load_g;
  });
</script>

<section class="panel">
  <header>
    <h2>{t('tools.wiegen')}</h2>
    <HelpButton id="wiegen" />
  </header>

  <div class="modes">
    <button class:active={mode==='frei'}     onclick={() => mode='frei'}>{t('panels.modeFree')}</button>
    <button class:active={mode==='sollwert'} onclick={() => mode='sollwert'}>{t('panels.modeTarget')}</button>
  </div>

  <button class="display" onclick={copyValue} disabled={weight === null}
          title={t('panels.copyValue')} aria-label={t('panels.copyValue')}>
    <span class="value">
      <StableValue g={weight} />
    </span>
    <span class="hint">{r ? (r.stable ? t('status.stable') : t('status.unstable')) : '—'}</span>
  </button>

  {#if underMinLoad}
    <p class="min-warning">
      <i class="fa-solid fa-triangle-exclamation"></i>
      {t('tolerances.belowMinWarning').replace('%w', formatGrams(modelStore.active.min_load_g))}
    </p>
  {/if}

  {#if mode === 'sollwert'}
    <div class="form">
      <label>
        {t('panels.targetGrams')}
        <span class="row">
          <input type="text" inputmode="decimal" placeholder={t('panels.targetPlaceholder')}
                 bind:value={sollText} />
          <button class="btn-primary" onclick={takeOver} disabled={weight === null}>
            <i class="fa-solid fa-circle-down"></i>
            {t('panels.takeOverCurrent')}
          </button>
        </span>
      </label>

      {#if soll !== null && diff !== null}
        <div class="info">
          <div class="info-row"><span class="key">{t('panels.difference')}</span>
            <span class="num val" class:plus={diff >= 0} class:minus={diff < 0}>{formatDiff(diff)}</span></div>
          {#if percent !== null}
            <div class="info-row"><span class="key">{t('panels.share')}</span>
              <span class="num val">{percent.toFixed(1)} %</span></div>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</section>

<style>
  .panel {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    padding: var(--sp-4);
    display: flex; flex-direction: column;
    gap: var(--sp-4);
  }
  header {
    display: flex; align-items: center; justify-content: space-between;
    gap: var(--sp-3);
  }
  header h2 {
    margin: 0; font-size: var(--fs-xl); font-weight: 600;
    letter-spacing: 0.02em;
  }
  .modes { display: flex; gap: var(--sp-2); }
  .modes button {
    min-height: var(--tap);
    padding: 0 var(--sp-3);
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    color: var(--fg-dim);
    border-radius: var(--radius-sm);
    cursor: pointer;
  }
  .modes button.active {
    color: var(--accent);
    border-color: var(--accent);
    background: color-mix(in srgb, var(--accent) 10%, transparent);
  }

  .display {
    background: rgba(0,0,0,0.25);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: var(--radius);
    padding: var(--sp-5) var(--sp-4);
    text-align: center;
    cursor: copy;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.3);
    container-type: inline-size;
  }
  :global(:root[data-theme="light"]) .display {
    background: rgba(0,0,0,0.04);
    border-color: rgba(0,0,0,0.05);
  }
  .display:hover:not(:disabled) { background: rgba(0,0,0,0.32); }
  .value {
    display: block;
    /* Schrift skaliert mit Container — bei einer 480-px-Display-Karte
       wird sie ~62 px, auf schmaleren Containern entsprechend kleiner. */
    font-size: clamp(36px, 13cqi, 67px);
    color: var(--display-green);
    line-height: 1;
    letter-spacing: 0;
    overflow: hidden;
    text-shadow: 0 0 4px color-mix(in srgb, var(--display-green) 35%, transparent);
  }
  .value :global(.stable-value) { color: inherit; }
  .hint {
    display: block; margin-top: var(--sp-2);
    font-size: var(--fs-sm);
    letter-spacing: 0.18em;
    color: var(--display-green);
  }

  .form {
    max-width: 480px;
    margin-inline: auto;
    width: 100%;
    display: flex; flex-direction: column;
    gap: var(--sp-3);
  }
  label {
    display: flex; flex-direction: column; gap: var(--sp-2);
    font-size: var(--fs-sm); color: var(--fg-dim);
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  .row { display: flex; gap: var(--sp-2); }
  .row input { flex: 1; }
  .row .btn-primary {
    display: inline-flex; align-items: center; gap: 6px; white-space: nowrap;
  }

  .info {
    display: flex; flex-direction: column;
    gap: var(--sp-2);
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: var(--sp-3) var(--sp-4);
  }
  .info-row {
    display: flex; justify-content: space-between; align-items: baseline;
  }
  .key {
    font-size: var(--fs-sm); color: var(--fg-dim);
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .val { font-size: var(--fs-lg); }
  .val.plus  { color: var(--green); }
  .val.minus { color: var(--orange); }

  .min-warning {
    max-width: 480px; margin: 0 auto;
    padding: var(--sp-2) var(--sp-3);
    background: color-mix(in srgb, var(--orange) 14%, transparent);
    border: 1px solid var(--orange);
    border-radius: var(--radius-sm);
    color: var(--orange);
    font-size: var(--fs-sm);
    display: inline-flex; align-items: center; gap: 6px;
    align-self: center;
  }
</style>
