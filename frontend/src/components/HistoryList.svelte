<script lang="ts">
  import { formatGrams, formatTime } from '../lib/format';
  import HelpButton from './HelpButton.svelte';
  import type { Reading } from '../lib/types';

  interface Props { history: Reading[]; }
  let { history = [] }: Props = $props();

  let recent = $derived(history.slice(-50).reverse());
</script>

<section class="history">
  <header>
    <h3>Verlauf der Änderungen</h3>
    <div class="meta">
      <span class="count num">{history.length}</span>
      <HelpButton id="history" label="Hilfe zum Verlauf" />
    </div>
  </header>

  <div class="scroll">
    {#if recent.length === 0}
      <div class="empty">Noch keine Werte-Änderungen</div>
    {:else}
      <table>
        <tbody>
          {#each recent as r (r.timestamp + r.raw)}
            <tr class:stable={r.stable}>
              <td class="time num">{formatTime(r.timestamp)}</td>
              <td class="weight num">{formatGrams(r.weight_g)}</td>
              <td class="flag">
                {#if r.stable}<span class="dot ok"></span>
                {:else}<span class="dot warn"></span>{/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</section>

<style>
  .history {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-2) var(--sp-3);
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-height: 0;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--sp-1);
    flex: 0 0 auto;
    gap: var(--sp-2);
  }
  h3 { margin: 0; font-size: var(--fs-sm); color: var(--fg-dim); font-weight: 500; }
  .meta {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
  }
  .count {
    color: var(--fg-dim);
    font-size: var(--fs-xs);
  }
  .scroll {
    overflow-y: auto;
    flex: 1 1 auto;
    min-height: 0;
  }
  .empty {
    color: var(--fg-dim);
    text-align: center;
    padding: var(--sp-3) 0;
    font-size: var(--fs-sm);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--fs-sm);
  }
  td {
    padding: 5px 0;
    border-bottom: 1px solid var(--border);
  }
  tr:last-child td { border-bottom: none; }
  td.time   { color: var(--fg-dim); }
  td.weight { text-align: right; color: var(--fg-dim); }
  tr.stable td.weight { color: var(--fg); }
  td.flag {
    text-align: right;
    width: 18px;
  }
  .dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
  }
  .dot.ok   { background: var(--green); }
  .dot.warn { background: var(--orange); }
</style>
