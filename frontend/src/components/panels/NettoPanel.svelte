<script lang="ts">
  /**
   * Behälter wiegen / Tara — Variante 1 (aktuelles Gewicht einfrieren)
   * und Variante 2 (Tara als Zahl angeben).
   */
  import { onMount } from 'svelte';
  import { api } from '../../lib/api';
  import { live } from '../../lib/liveStore.svelte';
  import { toast } from '../../lib/toast.svelte';
  import { formatGrams, formatTime } from '../../lib/format';
  import { t } from '../../lib/i18n';
  import HelpButton from '../HelpButton.svelte';
  import ContainerPicker from '../ContainerPicker.svelte';
  import type { NettoState, Container } from '../../lib/types';

  let info = $state<NettoState | null>(null);
  let busy = $state(false);
  let tareText = $state('');
  let pickedContainerId = $state<number | null>(null);

  async function pickContainer(c: Container | null): Promise<void> {
    pickedContainerId = c?.id ?? null;
    busy = true;
    try {
      // Default 0 g — bei „Kein Behälter" wird die Tara entfernt.
      info = c === null
        ? await api.app.nettoTareClear()
        : await api.app.nettoTareValue(c.weight_g);
    } catch (e) {
      toast.show((e as Error).message, 'error');
    } finally {
      busy = false;
    }
  }

  async function refresh(): Promise<void> {
    try { info = await api.app.netto(); }
    catch (e) { toast.show((e as Error).message, 'error'); }
  }

  async function tareCurrent(): Promise<void> {
    if (busy) return;
    busy = true;
    try { info = await api.app.nettoTareCurrent(); toast.show('Tara gesetzt', 'ok'); }
    catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  async function tareValue(): Promise<void> {
    const v = parseFloat(tareText.replace(',', '.'));
    if (!Number.isFinite(v)) { toast.show('Ungültige Zahl', 'error'); return; }
    busy = true;
    try { info = await api.app.nettoTareValue(v); toast.show('Tara gesetzt', 'ok'); }
    catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  async function clear(): Promise<void> {
    busy = true;
    try { info = await api.app.nettoTareClear(); toast.show('Tara entfernt', 'ok'); }
    catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  // Live-Werte einspielen — Frontend zeigt aktuelle Werte ohne dauerndes Polling.
  let liveGross = $derived(live.reading?.weight_g ?? null);
  let liveNetto = $derived.by<number | null>(() => {
    if (!info || info.tare_g === null || liveGross === null) return null;
    return liveGross - info.tare_g;
  });

  onMount(refresh);
</script>

<section class="panel">
  <header>
    <h2>{t('tools.netto')}</h2>
    <HelpButton id="netto" />
  </header>

  <div class="form">
    <div class="display">
      <div class="row">
        <span class="lbl">Brutto</span>
        <span class="num val">{formatGrams(liveGross)}</span>
      </div>
      <div class="row">
        <span class="lbl">Tara</span>
        <span class="num val">{formatGrams(info?.tare_g ?? null)}</span>
      </div>
      <div class="row big">
        <span class="lbl">Netto</span>
        <span class="num val big" class:active={info?.active}>{formatGrams(liveNetto)}</span>
      </div>
      {#if info?.tare_set_at}
        <div class="meta">Tara gesetzt {formatTime(info.tare_set_at)}</div>
      {/if}
    </div>

    <div class="actions-row">
      <button class="btn-primary" onclick={tareCurrent} disabled={busy || liveGross === null}>
        <i class="fa-solid fa-circle-down"></i>
        Aktuelles Gewicht als Tara
      </button>
      {#if info?.active}
        <button class="btn-warn" onclick={clear} disabled={busy}>
          <i class="fa-solid fa-eraser"></i>
          Tara entfernen
        </button>
      {/if}
    </div>

    <div class="manual">
      <label>
        Oder Tara als Zahl eintragen (Gramm)
        <div class="row-flex">
          <input type="text" inputmode="decimal" placeholder="z.B. 23,4"
                 bind:value={tareText} />
          <button class="btn-primary" onclick={tareValue} disabled={busy}>Setzen</button>
        </div>
      </label>
    </div>

    <div class="manual">
      <label>
        {t('containers.title')}
        <ContainerPicker selectedId={pickedContainerId} onPick={pickContainer} />
      </label>
    </div>
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

  .form {
    max-width: 480px; margin-inline: auto; width: 100%;
    display: flex; flex-direction: column; gap: var(--sp-4);
  }
  .display {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-2);
  }
  .row {
    display: flex; justify-content: space-between; align-items: baseline;
  }
  .row.big { padding-top: var(--sp-2); border-top: 1px solid var(--border); margin-top: var(--sp-2); }
  .lbl {
    font-size: var(--fs-sm); color: var(--fg-dim);
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .val { font-size: var(--fs-lg); }
  .val.big { font-size: var(--fs-xxl); color: var(--fg-dim); }
  .val.big.active { color: var(--accent); }
  .meta {
    font-size: var(--fs-xs); color: var(--fg-mute);
    text-align: right; margin-top: var(--sp-1);
  }

  .actions-row { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
  .actions-row .btn-primary,
  .actions-row .btn-warn {
    flex: 1 1 auto;
    display: inline-flex; align-items: center; justify-content: center;
    gap: 6px;
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
</style>
