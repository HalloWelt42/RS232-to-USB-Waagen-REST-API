<script lang="ts">
  /**
   * Differenz-Wiegen mit Mehrfach-Tara-Stack.
   * Jede Schicht wird separat gespeichert; einzelne Schichten lassen
   * sich entfernen, ohne den Rest zu verlieren. Netto = Brutto − Σ(Tara).
   */
  import { onMount } from 'svelte';
  import { api } from '../../lib/api';
  import { live } from '../../lib/liveStore.svelte';
  import { toast } from '../../lib/toast.svelte';
  import { formatGrams, formatTime } from '../../lib/format';
  import { t } from '../../lib/i18n';
  import HelpButton from '../HelpButton.svelte';
  import type { DifferenzState } from '../../lib/types';

  let info = $state<DifferenzState | null>(null);
  let busy = $state(false);
  let label = $state('');
  let manualText = $state('');

  async function refresh(): Promise<void> {
    try { info = await api.app.differenz(); }
    catch (e) { toast.show((e as Error).message, 'error'); }
  }

  async function pushCurrent(): Promise<void> {
    busy = true;
    try {
      info = await api.app.differenzPushCurrent(label);
      toast.show('Tara hinzugefügt', 'ok');
      label = '';
    } catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  async function pushManual(): Promise<void> {
    const v = parseFloat(manualText.replace(',', '.'));
    if (!Number.isFinite(v)) { toast.show('Ungültige Zahl', 'error'); return; }
    busy = true;
    try {
      info = await api.app.differenzPushValue(v, label);
      toast.show('Tara hinzugefügt', 'ok');
      label = ''; manualText = '';
    } catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  async function remove(id: number): Promise<void> {
    busy = true;
    try { info = await api.app.differenzRemove(id); }
    catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  async function clear(): Promise<void> {
    if (!confirm('Alle Tara-Schichten entfernen?')) return;
    busy = true;
    try { info = await api.app.differenzClear(); toast.show('Stapel geleert', 'ok'); }
    catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  let liveGross = $derived(live.reading?.weight_g ?? null);
  let liveNetto = $derived.by<number | null>(() => {
    if (!info || liveGross === null) return null;
    return liveGross - info.total_tare_g;
  });

  onMount(refresh);
</script>

<section class="panel">
  <header>
    <h2>{t('tools.differenz')}</h2>
    <HelpButton id="differenz" />
  </header>

  <div class="display">
    <div class="row">
      <span class="lbl">Brutto</span>
      <span class="num val">{formatGrams(liveGross)}</span>
    </div>
    <div class="row">
      <span class="lbl">Σ Tara</span>
      <span class="num val">{formatGrams(info?.total_tare_g ?? null)}</span>
    </div>
    <div class="row big">
      <span class="lbl">Netto</span>
      <span class="num val big" class:active={liveNetto !== null}>{formatGrams(liveNetto)}</span>
    </div>
  </div>

  <div class="form">
    <label class="full">
      Label für nächste Tara (optional)
      <input type="text" placeholder="z.B. Schale, Beutel, Träger ..." bind:value={label} />
    </label>

    <div class="actions-row">
      <button class="btn-primary" onclick={pushCurrent} disabled={busy || liveGross === null}>
        <i class="fa-solid fa-arrow-down-to-bracket"></i>
        Aktuelles Gewicht als Tara
      </button>
    </div>

    <div class="manual">
      <label>
        Oder Tara als Zahl eintragen (Gramm)
        <div class="row-flex">
          <input type="text" inputmode="decimal" placeholder="z.B. 23,4" bind:value={manualText} />
          <button class="btn-primary" onclick={pushManual} disabled={busy}>Hinzufügen</button>
        </div>
      </label>
    </div>
  </div>

  <ul class="layers">
    {#if !info || info.layers.length === 0}
      <li class="empty">Keine Tara-Schicht im Stapel</li>
    {:else}
      {#each info.layers as l (l.id)}
        <li class="layer">
          <span class="num idx">#{l.id}</span>
          <span class="num w">{formatGrams(l.weight_g)}</span>
          <span class="lab">{l.label || '—'}</span>
          <span class="ts num">{formatTime(l.set_at)}</span>
          <button class="x" onclick={() => remove(l.id)} disabled={busy}
                  title="Schicht entfernen" aria-label="Schicht entfernen">
            <i class="fa-regular fa-circle-xmark"></i>
          </button>
        </li>
      {/each}
    {/if}
  </ul>

  {#if info && info.layers.length > 0}
    <button class="btn-warn full" onclick={clear} disabled={busy}>
      <i class="fa-solid fa-trash"></i>
      Stapel leeren
    </button>
  {/if}
</section>

<style>
  .panel {
    flex: 1 1 auto; min-height: 0; overflow-y: auto;
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  header { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3); }
  header h2 { margin: 0; font-size: var(--fs-xl); font-weight: 600; }

  .display {
    max-width: 480px; margin-inline: auto; width: 100%;
    background: var(--bg-card-2); border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-2);
  }
  .row { display: flex; justify-content: space-between; align-items: baseline; }
  .row.big { padding-top: var(--sp-2); margin-top: var(--sp-2); border-top: 1px solid var(--border); }
  .lbl { font-size: var(--fs-sm); color: var(--fg-dim); letter-spacing: 0.05em; text-transform: uppercase; }
  .val { font-size: var(--fs-lg); }
  .val.big { font-size: var(--fs-xxl); color: var(--fg-dim); }
  .val.big.active { color: var(--accent); }

  .form {
    max-width: 480px; margin-inline: auto; width: 100%;
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  label {
    display: flex; flex-direction: column; gap: 6px;
    font-size: var(--fs-sm); color: var(--fg-dim);
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .full { width: 100%; }
  .actions-row { display: flex; gap: var(--sp-2); }
  .actions-row .btn-primary {
    flex: 1 1 auto;
    display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  }

  .manual {
    background: var(--bg-card-2); border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-3) var(--sp-4);
  }
  .row-flex { display: flex; gap: var(--sp-2); }
  .row-flex input { flex: 1; }

  .layers {
    list-style: none; margin: 0; padding: 0;
    background: var(--bg-card-2); border: 1px solid var(--border);
    border-radius: var(--radius);
    max-width: 720px; margin-inline: auto; width: 100%;
  }
  .layer {
    display: grid;
    grid-template-columns: max-content max-content 1fr max-content max-content;
    gap: var(--sp-3);
    align-items: center;
    padding: 8px var(--sp-3);
    border-bottom: 1px solid var(--border);
    font-size: var(--fs-sm);
  }
  .layer:last-child { border-bottom: none; }
  .idx { color: var(--fg-mute); font-size: var(--fs-xs); }
  .w { color: var(--accent); font-size: var(--fs-md); }
  .lab { color: var(--fg); }
  .ts { color: var(--fg-mute); font-size: var(--fs-xs); }
  .x {
    background: transparent; border: none; padding: 0;
    color: var(--fg-mute); font-size: 16px; cursor: pointer;
  }
  .x:hover { color: var(--red); }
  .empty {
    padding: var(--sp-4); text-align: center;
    color: var(--fg-mute); font-size: var(--fs-sm);
  }

  .btn-warn.full {
    max-width: 720px; margin-inline: auto; width: 100%;
    min-height: var(--tap); padding: 0 var(--sp-3);
    background: transparent; border: 1px solid var(--orange);
    color: var(--orange); border-radius: var(--radius-sm);
    font-family: var(--sans); font-size: var(--fs-sm); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;
    display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  }
  .btn-warn.full:hover:not(:disabled) {
    background: color-mix(in srgb, var(--orange) 14%, transparent);
  }
</style>
