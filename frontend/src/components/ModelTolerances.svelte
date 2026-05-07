<script lang="ts">
  /**
   * Zeigt die Genauigkeits-Toleranzen des aktiven Modells als kompakte
   * Tabelle. Spezifikationen, die im Datenblatt nicht angegeben sind
   * (Wert 0 oder null), werden mit „—" markiert.
   *
   * Optional: ein Live-Warn-Badge, wenn der aktuelle Wägewert unter
   * der empfohlenen Mindestlast liegt — die Anzeige bleibt da, aber
   * der Anwender sieht, dass die Hersteller-Garantie nicht greift.
   */
  import { modelStore } from '../lib/modelStore.svelte';
  import { live } from '../lib/liveStore.svelte';
  import { formatGrams } from '../lib/format';
  import { t } from '../lib/i18n';

  let m = $derived(modelStore.active);
  let liveG = $derived(live.reading?.weight_g ?? null);

  // Warnung: aktuelle Auflage unter der Mindestlast
  let underMin = $derived.by<boolean>(() => {
    if (m.min_load_g <= 0 || liveG === null) return false;
    return liveG > 0 && liveG < m.min_load_g;
  });

  function fmtTemp(rng: [number, number] | null): string {
    if (!rng) return '—';
    return `${rng[0]} – ${rng[1]} °C`;
  }
  function fmtSec(s: number): string {
    return s > 0 ? `${s.toString().replace('.', ',')} s` : '—';
  }
  function fmtMin(min: number): string {
    return min > 0 ? `${min} min` : '—';
  }
</script>

<div class="tol-card">
  <h4>{t('tolerances.title')}</h4>
  <ul class="kv">
    <li><span class="k">{t('tolerances.maxG')}</span>
      <span class="num v">{formatGrams(m.max_g)}</span></li>
    <li><span class="k">{t('tolerances.resolution')}</span>
      <span class="num v">{formatGrams(m.resolution_g)}</span></li>
    <li class:warn={underMin}>
      <span class="k">{t('tolerances.minLoad')}</span>
      <span class="num v">{m.min_load_g > 0 ? formatGrams(m.min_load_g) : '—'}</span>
    </li>
    <li><span class="k">{t('tolerances.linearity')}</span>
      <span class="num v">{m.linearity_g > 0 ? '±' + formatGrams(m.linearity_g) : '—'}</span></li>
    <li><span class="k">{t('tolerances.repeatability')}</span>
      <span class="num v">{m.repeatability_g > 0 ? formatGrams(m.repeatability_g) : '—'}</span></li>
    <li><span class="k">{t('tolerances.stabilization')}</span>
      <span class="num v">{fmtSec(m.stabilization_s)}</span></li>
    <li><span class="k">{t('tolerances.warmup')}</span>
      <span class="num v">{fmtMin(m.warmup_min)}</span></li>
    <li><span class="k">{t('tolerances.operatingTemp')}</span>
      <span class="num v">{fmtTemp(m.operating_temp_c)}</span></li>
  </ul>

  {#if underMin}
    <p class="warn-banner">
      <i class="fa-solid fa-triangle-exclamation"></i>
      {t('tolerances.belowMinWarning').replace('%w', formatGrams(m.min_load_g))}
    </p>
  {/if}
</div>

<style>
  .tol-card {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-3) var(--sp-4);
    display: flex; flex-direction: column;
    gap: var(--sp-2);
  }
  h4 {
    margin: 0;
    font-size: var(--fs-sm);
    color: var(--accent);
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  .kv {
    list-style: none; margin: 0; padding: 0;
    display: grid;
    grid-template-columns: 1fr max-content;
    gap: 4px var(--sp-3);
    font-size: var(--fs-sm);
  }
  .kv li {
    display: contents;
  }
  .kv li.warn .v { color: var(--orange); }
  .k { color: var(--fg-dim); letter-spacing: 0.04em; }
  .v { color: var(--fg); font-size: var(--fs-sm); }
  .warn-banner {
    margin: 0;
    padding: var(--sp-2) var(--sp-3);
    background: color-mix(in srgb, var(--orange) 14%, transparent);
    border: 1px solid var(--orange);
    border-radius: var(--radius-sm);
    color: var(--orange);
    font-size: var(--fs-sm);
    display: inline-flex; align-items: center; gap: 6px;
  }
</style>
