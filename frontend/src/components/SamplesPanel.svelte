<script>
  import { api } from '../lib/api.js';
  import { formatGrams, formatTime } from '../lib/format.js';

  let { reading = null } = $props();

  let session = $state('default');
  let label   = $state('');
  let note    = $state('');
  let busy    = $state(false);
  let errorMsg = $state(null);

  let samples = $state([]);
  let stats   = $state(null);

  $effect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  });

  async function refresh() {
    try {
      const [list, st] = await Promise.allSettled([
        api.sampleList(session, 100),
        api.sampleStats(session),
      ]);
      if (list.status === 'fulfilled') samples = list.value.items;
      if (st.status   === 'fulfilled') stats   = st.value;
      errorMsg = null;
    } catch (e) {
      errorMsg = e.message;
    }
  }

  async function capture() {
    if (busy) return;
    busy = true;
    errorMsg = null;
    try {
      await api.sampleAdd(label, note, session);
      label = '';
      note = '';
      await refresh();
    } catch (e) {
      errorMsg = e.message;
    } finally {
      busy = false;
    }
  }

  async function removeSample(id) {
    try {
      await api.sampleDelete(id);
      await refresh();
    } catch (e) {
      errorMsg = e.message;
    }
  }

  async function clearAll() {
    if (!confirm(`Alle Samples der Session "${session}" loeschen?`)) return;
    try {
      await api.sampleClear(session);
      await refresh();
    } catch (e) {
      errorMsg = e.message;
    }
  }
</script>

<section class="samples">
  <header>
    <h3>Werte erfassen</h3>
    <input
      class="session"
      type="text"
      bind:value={session}
      maxlength="80"
      aria-label="Session-Name"
    />
  </header>

  <div class="capture-row">
    <input
      type="text"
      placeholder="Label (optional)"
      bind:value={label}
      maxlength="120"
      disabled={busy}
    />
    <input
      type="text"
      placeholder="Notiz (optional)"
      bind:value={note}
      maxlength="200"
      disabled={busy}
    />
    <button class="capture" onclick={capture} disabled={busy || !reading}>
      {busy ? '...' : 'Erfassen'}
    </button>
  </div>

  {#if reading}
    <p class="hint">
      Aktueller Wert: <code>{formatGrams(reading.weight_g)}</code>
      {reading.stable ? '(stabil)' : '(noch nicht stabil)'}
    </p>
  {/if}

  {#if stats && stats.count > 0}
    <dl class="stats">
      <div><dt>Anzahl</dt><dd>{stats.count}</dd></div>
      <div><dt>Min</dt><dd>{formatGrams(stats.min_g)}</dd></div>
      <div><dt>Max</dt><dd>{formatGrams(stats.max_g)}</dd></div>
      <div><dt>Mittel</dt><dd>{formatGrams(stats.mean_g)}</dd></div>
      <div><dt>Standardabw.</dt><dd>{formatGrams(stats.stdev_g)}</dd></div>
      <div><dt>Summe</dt><dd>{formatGrams(stats.sum_g)}</dd></div>
    </dl>
  {/if}

  <div class="toolbar">
    <a class="export"
       href={api.sampleExportUrl(session)}
       download
       aria-disabled={!stats || stats.count === 0}
    >
      CSV-Export
    </a>
    {#if stats && stats.count > 0}
      <button class="clear" onclick={clearAll}>Session leeren</button>
    {/if}
  </div>

  {#if samples.length > 0}
    <table>
      <thead>
        <tr>
          <th class="ts-col">Zeit</th>
          <th class="w-col">Gewicht</th>
          <th class="lbl-col">Label / Notiz</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {#each samples as s (s.id)}
          <tr class:stable={s.stable}>
            <td class="ts">{formatTime(s.ts)}</td>
            <td class="w">{formatGrams(s.weight_g)}</td>
            <td class="lbl">
              <strong>{s.label || '—'}</strong>
              {#if s.note}<span class="note">{s.note}</span>{/if}
            </td>
            <td><button class="del" title="Löschen" onclick={() => removeSample(s.id)}>x</button></td>
          </tr>
        {/each}
      </tbody>
    </table>
  {:else}
    <p class="empty">Noch keine erfassten Werte in dieser Session.</p>
  {/if}

  {#if errorMsg}
    <p class="error">{errorMsg}</p>
  {/if}
</section>

<style>
  .samples {
    background:    var(--bg-card);
    border:        1px solid var(--border);
    border-radius: var(--radius);
    padding:       1.25rem 1.5rem;
    box-shadow:    var(--shadow);
    width:         min(36rem, 95vw);
    display:       flex;
    flex-direction: column;
    gap:           0.85rem;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 0.5rem;
  }
  h3 { margin: 0; font-size: 1.05rem; }
  input.session {
    flex: 0 0 11rem;
    background: var(--bg);
    color: var(--fg-dim);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.3rem 0.6rem;
    font-family: var(--mono);
    font-size: 0.85rem;
    text-align: right;
  }
  input[type="text"]:focus { outline: none; border-color: var(--accent); }
  .capture-row {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    gap: 0.5rem;
  }
  .capture-row input {
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.45rem 0.6rem;
    font-family: var(--sans);
    font-size: 0.9rem;
    min-width: 0;
  }
  button.capture {
    min-width: 6rem;
    background: var(--bg-card-2);
    border-color: var(--accent);
  }
  .hint {
    margin: 0;
    color: var(--fg-dim);
    font-size: 0.85rem;
  }
  dl.stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem 1rem;
    margin: 0;
    padding: 0.75rem 1rem;
    background: var(--bg);
    border-radius: 8px;
    border: 1px solid var(--border);
  }
  dl.stats div { display: flex; flex-direction: column; gap: 0.1rem; }
  dl.stats dt { color: var(--fg-dim); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
  dl.stats dd { margin: 0; font-family: var(--mono); font-size: 0.95rem; }
  .toolbar {
    display: flex;
    gap: 0.6rem;
    align-items: center;
  }
  a.export {
    display: inline-block;
    padding: 0.4rem 0.8rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-card);
    color: var(--fg);
    font-size: 0.85rem;
    text-decoration: none;
  }
  a.export:hover { border-color: var(--accent); }
  a.export[aria-disabled="true"] { opacity: 0.4; pointer-events: none; }
  button.clear {
    font-size: 0.78rem;
    padding: 0.3rem 0.7rem;
    color: var(--orange);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }
  thead th {
    text-align: left;
    color: var(--fg-dim);
    font-weight: 500;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.35rem 0.4rem;
    border-bottom: 1px solid var(--border);
  }
  tbody td {
    padding: 0.4rem;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
  }
  tbody tr:last-child td { border-bottom: none; }
  td.ts  { color: var(--fg-dim); font-family: var(--mono); width: 5.5rem; }
  td.w   { font-family: var(--mono); text-align: right; width: 7rem; color: var(--fg-dim); }
  tr.stable td.w { color: var(--fg); }
  td.lbl strong { display: block; font-weight: 500; }
  td.lbl .note  { display: block; color: var(--fg-dim); font-size: 0.8rem; margin-top: 0.1rem; }
  button.del {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--fg-dim);
    padding: 0.2rem 0.5rem;
    font-size: 0.85rem;
  }
  button.del:hover { color: var(--red); border-color: var(--red); }
  .empty {
    margin: 0;
    color: var(--fg-dim);
    font-size: 0.85rem;
    text-align: center;
    padding: 0.6rem;
  }
  .error { margin: 0; color: var(--red); font-size: 0.85rem; }
</style>
