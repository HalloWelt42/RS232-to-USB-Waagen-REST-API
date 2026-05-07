<script lang="ts">
  import { formatGrams, formatTime } from '../lib/format';
  import type { Reading } from '../lib/types';

  interface Props {
    history: Reading[];
  }

  let { history = [] }: Props = $props();

  // Neueste zuerst, max 50 Einträge anzeigen
  let recent = $derived(history.slice(-50).reverse());
</script>

<section class="history">
  <header>
    <h3>Verlauf (Änderungen)</h3>
    <span class="count">{history.length}</span>
  </header>

  <div class="scroll">
    {#if recent.length === 0}
      <div class="empty">Noch keine Werte-Änderungen</div>
    {:else}
      <table>
        <tbody>
          {#each recent as r (r.timestamp + r.raw)}
            <tr class:stable={r.stable}>
              <td class="time">{formatTime(r.timestamp)}</td>
              <td class="weight">{formatGrams(r.weight_g)}</td>
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
    padding: 0.75rem 1rem;
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-height: 0;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 0.4rem;
    flex: 0 0 auto;
  }
  h3 { margin: 0; font-size: 0.9rem; color: var(--fg-dim); font-weight: 500; }
  .count {
    color: var(--fg-dim);
    font-size: 0.75rem;
    font-family: var(--mono);
  }
  .scroll {
    overflow-y: auto;
    flex: 1 1 auto;
    min-height: 0;
  }
  .empty {
    color: var(--fg-dim);
    text-align: center;
    padding: 1rem 0;
    font-size: 0.85rem;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--mono);
    font-size: 0.85rem;
  }
  td {
    padding: 0.3rem 0;
    border-bottom: 1px solid var(--border);
  }
  tr:last-child td { border-bottom: none; }
  td.time   { color: var(--fg-dim); }
  td.weight { text-align: right; color: var(--fg-dim); }
  tr.stable td.weight { color: var(--fg); }
  td.flag {
    text-align: right;
    width: 20px;
  }
  .dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
  }
  .dot.ok   { background: var(--green); }
  .dot.warn { background: var(--orange); }
</style>
