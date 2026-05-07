<script>
  import { api } from '../lib/api.js';
  import { formatGrams } from '../lib/format.js';

  let { reading = null } = $props();

  let countState   = $state(null);
  let referenceCount = $state(10);
  let busy         = $state(false);
  let errorMsg     = $state(null);
  let lastFetch    = $state(0);

  // Beim Mount und alle 2 s den Server-Status holen, damit die Kalibrier-
  // Information erhalten bleibt, auch wenn der Tab neu geladen wurde.
  $effect(() => {
    refreshState();
    const t = setInterval(refreshState, 2000);
    return () => clearInterval(t);
  });

  async function refreshState() {
    try {
      countState = await api.count();
      errorMsg = null;
    } catch (e) {
      errorMsg = e.message;
    }
  }

  // Live-Berechnung der Stückzahl aus dem WebSocket-Reading, ohne dafür
  // jedes Mal den Server zu fragen. Der Server-State liefert das Stück-
  // gewicht, das WebSocket-Reading das Gesamtgewicht — das reicht.
  let livePieces = $derived.by(() => {
    if (!countState?.calibrated || !reading) return null;
    if (!countState.piece_weight_g || countState.piece_weight_g <= 0) return null;
    return reading.weight_g / countState.piece_weight_g;
  });

  let livePiecesRounded = $derived.by(() => {
    if (livePieces === null) return null;
    return Math.round(livePieces);
  });

  async function calibrate() {
    if (busy) return;
    busy = true;
    errorMsg = null;
    try {
      countState = await api.countCalibrate(referenceCount);
    } catch (e) {
      errorMsg = e.message;
    } finally {
      busy = false;
    }
  }

  async function reset() {
    if (busy) return;
    busy = true;
    errorMsg = null;
    try {
      countState = await api.countReset();
    } catch (e) {
      errorMsg = e.message;
    } finally {
      busy = false;
    }
  }

  function fmtPieceWeight(g) {
    if (g == null) return '—';
    if (g >= 1) return `${g.toFixed(3)} g`;
    return `${(g * 1000).toFixed(2)} mg`;
  }
</script>

<section class="count">
  <header>
    <h3>Zählwaage</h3>
    {#if countState?.calibrated}
      <button class="reset" onclick={reset} disabled={busy}>Zurücksetzen</button>
    {/if}
  </header>

  {#if !countState?.calibrated}
    <p class="hint">
      Lege eine bekannte Anzahl gleicher Teile auf die Waage, gib die Stückzahl
      ein und kalibriere.
    </p>
    <div class="calibrate-row">
      <input
        type="number"
        min="1"
        max="100000"
        step="1"
        bind:value={referenceCount}
        disabled={busy}
        aria-label="Anzahl Referenzteile"
      />
      <span class="unit">Stück</span>
      <button onclick={calibrate} disabled={busy}>
        {busy ? 'Kalibriere...' : 'Kalibrieren'}
      </button>
    </div>
    {#if reading}
      <p class="current">
        Aktuell auf der Waage: <code>{formatGrams(reading.weight_g)}</code>
      </p>
    {/if}
  {:else}
    <div class="result">
      <div class="big-count" class:stable={reading?.stable}>
        {livePiecesRounded ?? '—'}
        <span class="big-unit">Stück</span>
      </div>
      <div class="exact">
        {#if livePieces !== null}
          rechnerisch {livePieces.toFixed(2)}
        {/if}
      </div>
    </div>
    <dl class="details">
      <dt>Stückgewicht</dt>
      <dd>{fmtPieceWeight(countState.piece_weight_g)}</dd>
      <dt>Referenz</dt>
      <dd>{countState.reference_count} Stück</dd>
      <dt>Gesamtgewicht</dt>
      <dd>{reading ? formatGrams(reading.weight_g) : '—'}</dd>
      <dt>Status</dt>
      <dd>{reading?.stable ? 'stabil' : '...'}</dd>
    </dl>
    <div class="recalibrate-row">
      <input
        type="number"
        min="1"
        max="100000"
        step="1"
        bind:value={referenceCount}
        disabled={busy}
        aria-label="Anzahl Referenzteile"
      />
      <span class="unit">Stück</span>
      <button onclick={calibrate} disabled={busy}>
        {busy ? 'Kalibriere...' : 'Neu kalibrieren'}
      </button>
    </div>
  {/if}

  {#if errorMsg}
    <p class="error">{errorMsg}</p>
  {/if}
</section>

<style>
  .count {
    background:    var(--bg-card);
    border:        1px solid var(--border);
    border-radius: var(--radius);
    padding:       1.25rem 1.5rem;
    box-shadow:    var(--shadow);
    width:         min(28rem, 90vw);
    display:       flex;
    flex-direction: column;
    gap:           1rem;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }
  h3 {
    margin: 0;
    font-size: 1.05rem;
  }
  .reset {
    font-size: 0.78rem;
    padding: 0.3rem 0.7rem;
  }
  .hint {
    margin: 0;
    color: var(--fg-dim);
    font-size: 0.9rem;
    line-height: 1.4;
  }
  .calibrate-row, .recalibrate-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  input[type="number"] {
    flex: 0 0 6rem;
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.45rem 0.6rem;
    font-family: var(--mono);
    font-size: 1rem;
  }
  input[type="number"]:focus {
    outline: none;
    border-color: var(--accent);
  }
  .unit {
    color: var(--fg-dim);
    font-size: 0.9rem;
  }
  .current {
    margin: 0;
    color: var(--fg-dim);
    font-size: 0.9rem;
  }
  .result {
    text-align: center;
    padding: 0.5rem 0;
  }
  .big-count {
    font-family: var(--mono);
    font-size: clamp(2rem, 6vw, 3.5rem);
    font-weight: 600;
    color: var(--fg-dim);
    transition: color 0.3s;
    line-height: 1;
  }
  .big-count.stable {
    color: var(--green);
  }
  .big-unit {
    font-size: 0.4em;
    margin-left: 0.3em;
    color: var(--fg-dim);
  }
  .exact {
    color: var(--fg-dim);
    font-family: var(--mono);
    font-size: 0.85rem;
    margin-top: 0.2rem;
  }
  dl.details {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.4rem 1rem;
    margin: 0;
    font-size: 0.9rem;
    border-top: 1px solid var(--border);
    padding-top: 0.75rem;
  }
  dt {
    color: var(--fg-dim);
  }
  dd {
    margin: 0;
    text-align: right;
    font-family: var(--mono);
  }
  .error {
    margin: 0;
    color: var(--red);
    font-size: 0.85rem;
  }
  .recalibrate-row {
    border-top: 1px solid var(--border);
    padding-top: 0.75rem;
  }
</style>
