<script lang="ts">
  import { api } from '../lib/api';
  import { formatGrams, formatTime } from '../lib/format';
  import type { Reading, Sample, SampleStats } from '../lib/types';

  interface Props { reading: Reading | null; }
  let { reading = null }: Props = $props();

  let session = $state<string>('default');
  let label   = $state<string>('');
  let note    = $state<string>('');
  let busy    = $state(false);
  let errorMsg = $state<string | null>(null);

  let samples = $state<Sample[]>([]);
  let stats   = $state<SampleStats | null>(null);

  $effect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 3000);
    return () => clearInterval(t);
  });

  async function refresh(): Promise<void> {
    try {
      const [list, st] = await Promise.allSettled([
        api.sampleList(session, 100),
        api.sampleStats(session),
      ]);
      if (list.status === 'fulfilled') samples = list.value.items;
      if (st.status   === 'fulfilled') stats   = st.value;
      errorMsg = null;
    } catch (e) {
      errorMsg = (e as Error).message;
    }
  }

  async function capture(): Promise<void> {
    if (busy) return;
    busy = true; errorMsg = null;
    try {
      await api.sampleAdd(label, note, session);
      label = ''; note = '';
      await refresh();
    } catch (e) { errorMsg = (e as Error).message; }
    finally { busy = false; }
  }

  async function removeSample(id: number): Promise<void> {
    try { await api.sampleDelete(id); await refresh(); }
    catch (e) { errorMsg = (e as Error).message; }
  }

  async function clearAll(): Promise<void> {
    if (!confirm(`Alle Samples der Session "${session}" loeschen?`)) return;
    try { await api.sampleClear(session); await refresh(); }
    catch (e) { errorMsg = (e as Error).message; }
  }
</script>

<section class="panel">
  <div class="header-row">
    <input class="session-input" type="text" bind:value={session} maxlength="80" placeholder="Session" />
  </div>

  <div class="capture-row">
    <input type="text" placeholder="Label" bind:value={label} maxlength="120" disabled={busy} />
    <input type="text" placeholder="Notiz" bind:value={note} maxlength="200" disabled={busy} />
    <button class="primary" onclick={capture} disabled={busy || !reading}>
      {busy ? '...' : 'Erfassen'}
    </button>
  </div>

  {#if reading}
    <p class="hint">
      Aktuell: <code>{formatGrams(reading.weight_g)}</code>
      {reading.stable ? '· stabil' : '· wartet'}
    </p>
  {/if}

  {#if stats && stats.count > 0}
    <dl class="stats">
      <div><dt>Anzahl</dt><dd>{stats.count}</dd></div>
      <div><dt>Min</dt><dd>{formatGrams(stats.min_g)}</dd></div>
      <div><dt>Max</dt><dd>{formatGrams(stats.max_g)}</dd></div>
      <div><dt>Mittel</dt><dd>{formatGrams(stats.mean_g)}</dd></div>
      <div><dt>Stdabw</dt><dd>{formatGrams(stats.stdev_g)}</dd></div>
      <div><dt>Summe</dt><dd>{formatGrams(stats.sum_g)}</dd></div>
    </dl>
  {/if}

  <div class="toolbar">
    <a class="export-btn" href={api.sampleExportUrl(session)} download
       aria-disabled={!stats || stats.count === 0}>CSV-Export</a>
    {#if stats && stats.count > 0}
      <button class="warn-btn" onclick={clearAll}>Session leeren</button>
    {/if}
  </div>

  <div class="list">
    {#if samples.length === 0}
      <p class="empty">Noch keine erfassten Werte.</p>
    {:else}
      <table>
        <tbody>
          {#each samples as s (s.id)}
            <tr class:stable={s.stable}>
              <td class="ts">{formatTime(s.ts)}</td>
              <td class="w">{formatGrams(s.weight_g)}</td>
              <td class="lbl">
                <strong>{s.label || '—'}</strong>
                {#if s.note}<span class="note">{s.note}</span>{/if}
              </td>
              <td class="del-col">
                <button class="del" title="Löschen" onclick={() => removeSample(s.id)}>x</button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>

  {#if errorMsg}<p class="error">{errorMsg}</p>{/if}
</section>

<style>
  .panel { display: flex; flex-direction: column; gap: 0.7rem; height: 100%; min-height: 0; }
  .header-row { display: flex; justify-content: flex-end; }
  .session-input {
    width: 12rem;
    text-align: right;
    color: var(--fg-dim);
  }
  .capture-row {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    gap: 0.5rem;
  }
  .capture-row input { font-family: var(--sans); }
  button.primary { background: var(--bg-card-2); border-color: var(--accent); }
  button.warn-btn { color: var(--orange); }
  .hint { margin: 0; color: var(--fg-dim); font-size: 0.85rem; }
  dl.stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.4rem 0.8rem;
    margin: 0;
    padding: 0.6rem 0.8rem;
    background: var(--bg);
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
  }
  dl.stats div { display: flex; flex-direction: column; gap: 0.05rem; }
  dl.stats dt { color: var(--fg-dim); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; }
  dl.stats dd { margin: 0; font-family: var(--mono); font-size: 0.85rem; }
  .toolbar { display: flex; gap: 0.5rem; align-items: center; }
  a.export-btn {
    display: inline-block;
    padding: 0.4rem 0.8rem;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--bg-card);
    color: var(--fg);
    font-size: 0.85rem;
  }
  a.export-btn:hover { border-color: var(--accent); text-decoration: none; }
  a.export-btn[aria-disabled="true"] { opacity: 0.4; pointer-events: none; }
  .list { flex: 1 1 auto; min-height: 0; overflow-y: auto; }
  .empty { color: var(--fg-dim); text-align: center; padding: 0.8rem 0; font-size: 0.85rem; margin: 0; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  td { padding: 0.35rem 0.4rem; border-bottom: 1px solid var(--border); vertical-align: top; }
  td.ts  { color: var(--fg-dim); font-family: var(--mono); width: 5.5rem; }
  td.w   { font-family: var(--mono); text-align: right; width: 6rem; color: var(--fg-dim); }
  tr.stable td.w { color: var(--fg); }
  td.lbl strong { display: block; font-weight: 500; }
  td.lbl .note  { display: block; color: var(--fg-dim); font-size: 0.78rem; margin-top: 0.05rem; }
  .del-col { width: 1.8rem; text-align: right; }
  button.del { padding: 0.15rem 0.45rem; font-size: 0.85rem; color: var(--fg-dim); }
  button.del:hover { color: var(--red); border-color: var(--red); }
  .error { color: var(--red); font-size: 0.85rem; margin: 0; }
</style>
