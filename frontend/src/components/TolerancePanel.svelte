<script>
  import { api } from '../lib/api.js';
  import { formatGrams } from '../lib/format.js';

  let { reading = null } = $props();

  let cfg = $state(null);
  let target  = $state(100);
  let tolMin  = $state(1);
  let tolPlus = $state(1);
  let busy = $state(false);
  let errorMsg = $state(null);

  $effect(() => {
    refresh();
    const t = setInterval(refresh, 2000);
    return () => clearInterval(t);
  });

  async function refresh() {
    try {
      cfg = await api.tolerance();
      if (cfg.active) {
        target = cfg.target_g;
        tolMin = cfg.tolerance_minus_g;
        tolPlus = cfg.tolerance_plus_g;
      }
      errorMsg = null;
    } catch (e) {
      errorMsg = e.message;
    }
  }

  async function setTolerance() {
    if (busy) return;
    busy = true;
    errorMsg = null;
    try {
      cfg = await api.toleranceSet(Number(target), Number(tolMin), Number(tolPlus));
    } catch (e) {
      errorMsg = e.message;
    } finally {
      busy = false;
    }
  }

  async function clearTolerance() {
    if (busy) return;
    busy = true;
    errorMsg = null;
    try {
      cfg = await api.toleranceClear();
    } catch (e) {
      errorMsg = e.message;
    } finally {
      busy = false;
    }
  }

  // Live-Status aus aktuellem Reading + Backend-Konfig berechnen,
  // damit die Ampel sofort beim WebSocket-Frame umschaltet.
  let liveStatus = $derived.by(() => {
    if (!cfg?.active || !reading) return cfg?.status ?? 'idle';
    const w = reading.weight_g;
    if (w < cfg.min_g) return 'low';
    if (w > cfg.max_g) return 'high';
    return 'ok';
  });

  let liveDeviation = $derived.by(() => {
    if (!cfg?.active || !reading) return null;
    return reading.weight_g - cfg.target_g;
  });
</script>

<section class="qc">
  <header>
    <h3>QC-Toleranz</h3>
    {#if cfg?.active}
      <button class="off" onclick={clearTolerance} disabled={busy}>aus</button>
    {/if}
  </header>

  {#if !cfg?.active}
    <p class="hint">Sollwert + Toleranzgrenzen vorgeben — die Anzeige
      zeigt grün/gelb/rot je nach Abweichung.</p>
    <div class="cfg-row">
      <label>
        <span>Soll [g]</span>
        <input type="number" step="0.1" bind:value={target} />
      </label>
      <label>
        <span>Tol- [g]</span>
        <input type="number" step="0.01" min="0" bind:value={tolMin} />
      </label>
      <label>
        <span>Tol+ [g]</span>
        <input type="number" step="0.01" min="0" bind:value={tolPlus} />
      </label>
      <button class="set" onclick={setTolerance} disabled={busy}>
        {busy ? '...' : 'Aktivieren'}
      </button>
    </div>
  {:else}
    <div class="lamp" class:ok={liveStatus === 'ok'}
                     class:low={liveStatus === 'low'}
                     class:high={liveStatus === 'high'}
                     class:idle={liveStatus === 'idle'}>
      <span class="label">
        {liveStatus === 'ok'   ? 'IN ORDNUNG'
       : liveStatus === 'low'  ? 'ZU LEICHT'
       : liveStatus === 'high' ? 'ZU SCHWER'
       : '...'}
      </span>
    </div>
    <dl class="info">
      <div><dt>Soll</dt><dd>{formatGrams(cfg.target_g)}</dd></div>
      <div><dt>Bereich</dt><dd>{formatGrams(cfg.min_g)} ... {formatGrams(cfg.max_g)}</dd></div>
      <div><dt>Aktuell</dt><dd>{reading ? formatGrams(reading.weight_g) : '—'}</dd></div>
      <div><dt>Abweichung</dt>
        <dd class:ok={liveStatus === 'ok'}
            class:warn={liveStatus === 'low' || liveStatus === 'high'}>
          {liveDeviation === null
            ? '—'
            : (liveDeviation >= 0 ? '+' : '') + liveDeviation.toFixed(2) + ' g'}
        </dd>
      </div>
    </dl>
    <div class="reconfig">
      <label><span>Soll</span><input type="number" step="0.1" bind:value={target} /></label>
      <label><span>Tol-</span><input type="number" step="0.01" min="0" bind:value={tolMin} /></label>
      <label><span>Tol+</span><input type="number" step="0.01" min="0" bind:value={tolPlus} /></label>
      <button onclick={setTolerance} disabled={busy}>Übernehmen</button>
    </div>
  {/if}
  {#if errorMsg}<p class="error">{errorMsg}</p>{/if}
</section>

<style>
  .qc {
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
  button.off {
    font-size: 0.78rem;
    padding: 0.3rem 0.7rem;
  }
  .hint { margin: 0; color: var(--fg-dim); font-size: 0.9rem; }
  .cfg-row, .reconfig {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr auto;
    gap: 0.5rem;
    align-items: end;
  }
  .reconfig {
    border-top: 1px solid var(--border);
    padding-top: 0.75rem;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    font-size: 0.75rem;
    color: var(--fg-dim);
  }
  input[type="number"] {
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.4rem 0.5rem;
    font-family: var(--mono);
    font-size: 0.9rem;
    width: 100%;
  }
  input[type="number"]:focus { outline: none; border-color: var(--accent); }
  button.set { background: var(--bg-card-2); border-color: var(--accent); }

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
    transition: background 0.2s, border-color 0.2s, color 0.2s;
  }
  .lamp.ok    { border-color: var(--green);  background: rgba(63, 185, 80, 0.15);  color: var(--green); }
  .lamp.low   { border-color: var(--orange); background: rgba(210, 153, 34, 0.15); color: var(--orange); }
  .lamp.high  { border-color: var(--red);    background: rgba(248, 81, 73, 0.15);  color: var(--red); }
  .lamp.idle  { color: var(--fg-dim); }

  dl.info {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.4rem 1rem;
    margin: 0;
    font-size: 0.9rem;
  }
  dl.info div { display: contents; }
  dl.info dt { color: var(--fg-dim); }
  dl.info dd { margin: 0; text-align: right; font-family: var(--mono); }
  dl.info dd.ok   { color: var(--green); }
  dl.info dd.warn { color: var(--orange); }
  .error { margin: 0; color: var(--red); font-size: 0.85rem; }
</style>
