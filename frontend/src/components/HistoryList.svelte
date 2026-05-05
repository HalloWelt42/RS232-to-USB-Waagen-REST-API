<script>
  import { formatGrams, formatTime } from '../lib/format.js';

  let { history = [] } = $props();

  let recent = $derived(history.slice(-20).reverse());
</script>

<section class="history">
  <header>
    <h3>Verlauf</h3>
    <span class="count">{history.length} Werte</span>
  </header>

  {#if recent.length === 0}
    <div class="empty">Noch keine Werte</div>
  {:else}
    <ul>
      {#each recent as r (r.timestamp + r.raw)}
        <li class:stable={r.stable}>
          <span class="time">{formatTime(r.timestamp)}</span>
          <span class="weight">{formatGrams(r.weight_g)}</span>
          <span class="flag">
            {#if r.stable}<span class="dot ok"></span>{:else}<span class="dot warn"></span>{/if}
          </span>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .history {
    background:    var(--bg-card);
    border:        1px solid var(--border);
    border-radius: var(--radius);
    padding:       1.25rem 1.5rem;
    box-shadow:    var(--shadow);
    width:         min(28rem, 90vw);
  }
  header {
    display:         flex;
    justify-content: space-between;
    align-items:     baseline;
    margin-bottom:   0.75rem;
  }
  h3 {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 600;
  }
  .count {
    color: var(--fg-dim);
    font-size: 0.8rem;
    font-family: var(--mono);
  }
  .empty {
    color: var(--fg-dim);
    text-align: center;
    padding: 1rem 0;
    font-size: 0.9rem;
  }
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    max-height: 24rem;
    overflow-y: auto;
  }
  li {
    display: grid;
    grid-template-columns: 1fr 2fr auto;
    gap: 0.5rem;
    align-items: center;
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 0.9rem;
  }
  li:last-child {
    border-bottom: none;
  }
  .time {
    color: var(--fg-dim);
  }
  .weight {
    text-align: right;
    color: var(--fg-dim);
    font-weight: 500;
  }
  li.stable .weight {
    color: var(--fg);
  }
  .flag {
    display: flex;
    justify-content: flex-end;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  .dot.ok   { background: var(--green); }
  .dot.warn { background: var(--orange); }
</style>
