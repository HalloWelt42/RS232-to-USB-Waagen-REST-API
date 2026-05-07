<script>
  import { api } from '../lib/api.js';
  import { formatGrams } from '../lib/format.js';

  let { reading = null } = $props();

  let cfg      = $state(null);
  let manualTare = $state('');
  let busy     = $state(false);
  let errorMsg = $state(null);

  $effect(() => {
    refresh();
    const t = setInterval(refresh, 2000);
    return () => clearInterval(t);
  });

  async function refresh() {
    try {
      cfg = await api.netto();
      errorMsg = null;
    } catch (e) {
      errorMsg = e.message;
    }
  }

  async function tareCurrent() {
    if (busy) return;
    busy = true;
    errorMsg = null;
    try {
      cfg = await api.nettoTareCurrent();
    } catch (e) {
      errorMsg = e.message;
    } finally {
      busy = false;
    }
  }

  async function tareManual() {
    if (busy) return;
    const value = Number(manualTare);
    if (Number.isNaN(value)) {
      errorMsg = 'Bitte eine Zahl eingeben';
      return;
    }
    busy = true;
    errorMsg = null;
    try {
      cfg = await api.nettoTareValue(value);
      manualTare = '';
    } catch (e) {
      errorMsg = e.message;
    } finally {
      busy = false;
    }
  }

  async function clear() {
    if (busy) return;
    busy = true;
    errorMsg = null;
    try {
      cfg = await api.nettoTareClear();
    } catch (e) {
      errorMsg = e.message;
    } finally {
      busy = false;
    }
  }

  let liveNetto = $derived.by(() => {
    if (!cfg?.active || !reading) return null;
    return reading.weight_g - cfg.tare_g;
  });
</script>

<section class="netto">
  <header>
    <h3>Netto / Software-Tara</h3>
    {#if cfg?.active}
      <button class="off" onclick={clear} disabled={busy}>aus</button>
    {/if}
  </header>

  {#if !cfg?.active}
    <p class="hint">Software-Tara: lege z.B. den leeren Behälter auf, klicke
      "Tara einfrieren" — danach zeigt das Panel das Netto-Gewicht.
      Alternativ ein bekanntes Behältergewicht eintragen.</p>
    <div class="row">
      <button class="capture" onclick={tareCurrent}
              disabled={busy || !reading}>
        {busy ? '...' : 'Tara einfrieren'}
      </button>
      <input
        type="number"
        step="0.01"
        placeholder="Tara [g] manuell"
        bind:value={manualTare}
        disabled={busy}
      />
      <button onclick={tareManual} disabled={busy || manualTare === ''}>
        Setzen
      </button>
    </div>
    {#if reading}
      <p class="current">Aktuell: <code>{formatGrams(reading.weight_g)}</code></p>
    {/if}
  {:else}
    <div class="netto-display">
      <span class="big" class:stable={reading?.stable}>
        {liveNetto === null ? '—' : formatGrams(liveNetto)}
      </span>
      <span class="big-label">Netto</span>
    </div>
    <dl>
      <div><dt>Brutto</dt><dd>{reading ? formatGrams(reading.weight_g) : '—'}</dd></div>
      <div><dt>Tara</dt><dd>{formatGrams(cfg.tare_g)}</dd></div>
      <div><dt>Gesetzt am</dt><dd class="ts">{cfg.tare_set_at?.replace('T', ' ') ?? '—'}</dd></div>
    </dl>
    <button class="recapture" onclick={tareCurrent} disabled={busy}>
      Tara aus aktuellem Gewicht neu setzen
    </button>
  {/if}

  {#if errorMsg}<p class="error">{errorMsg}</p>{/if}
</section>

<style>
  .netto {
    background:    var(--bg-card);
    border:        1px solid var(--border);
    border-radius: var(--radius);
    padding:       1.25rem 1.5rem;
    box-shadow:    var(--shadow);
    width:         min(28rem, 90vw);
    display:       flex;
    flex-direction: column;
    gap:           0.85rem;
  }
  header {
    display: flex; justify-content: space-between; align-items: baseline;
  }
  h3 { margin: 0; font-size: 1.05rem; }
  button.off { font-size: 0.78rem; padding: 0.3rem 0.7rem; }
  .hint { margin: 0; color: var(--fg-dim); font-size: 0.85rem; line-height: 1.4; }
  .row {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 0.5rem;
    align-items: center;
  }
  input[type="number"] {
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.45rem 0.6rem;
    font-family: var(--mono);
    font-size: 0.9rem;
    min-width: 0;
  }
  input[type="number"]:focus { outline: none; border-color: var(--accent); }
  .capture { background: var(--bg-card-2); border-color: var(--accent); }
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
    font-size: clamp(1.8rem, 5vw, 2.8rem);
    font-weight: 600;
    color: var(--fg-dim);
    transition: color 0.3s;
  }
  .big.stable { color: var(--green); }
  .big-label {
    font-size: 0.85rem;
    color: var(--fg-dim);
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }
  dl {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.4rem 1rem;
    margin: 0;
    font-size: 0.9rem;
  }
  dl div { display: contents; }
  dt { color: var(--fg-dim); }
  dd { margin: 0; text-align: right; font-family: var(--mono); }
  dd.ts { font-size: 0.8rem; color: var(--fg-dim); }
  .recapture {
    font-size: 0.85rem;
    border-top: 1px solid var(--border);
    margin-top: 0.5rem;
    padding-top: 0.75rem;
    border-radius: 0;
    background: transparent;
    border-left: none;
    border-right: none;
    border-bottom: none;
    color: var(--accent);
  }
  .recapture:hover { background: var(--bg-card-2); }
  .error { margin: 0; color: var(--red); font-size: 0.85rem; }
</style>
