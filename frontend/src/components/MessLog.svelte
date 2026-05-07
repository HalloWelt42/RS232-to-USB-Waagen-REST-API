<script lang="ts">
  import { formatDiff, formatGrams, formatTime } from '../lib/format';
  import HelpButton from './HelpButton.svelte';
  import type { MesslogEntry } from '../lib/types';

  interface Props { entries: MesslogEntry[]; }
  let { entries = [] }: Props = $props();

  // Neueste zuerst — Server liefert auch so, Frontend appended hinten
  let recent = $derived([...entries].reverse());
</script>

<section class="messlog">
  <header>
    <h3>Messprotokoll · letzte Änderungen</h3>
    <div class="meta">
      <span class="num count">{entries.length}</span>
      <HelpButton id="history" label="Hilfe zum Messprotokoll" />
    </div>
  </header>

  <ul class="list">
    {#if recent.length === 0}
      <li class="empty">Noch keine Werte-Änderungen</li>
    {:else}
      {#each recent as e (e.id)}
        <li class="row" data-kind={e.kind}>
          <span class="ts num">{formatTime(e.ts)}</span>
          {#if e.kind === 'change'}
            <span class="diff num" class:plus={e.diff_g !== null && e.diff_g >= 0}
                                    class:minus={e.diff_g !== null && e.diff_g < 0}>
              {formatDiff(e.diff_g)}
            </span>
          {:else if e.kind === 'tare'}
            <span class="diff num tare">Tara</span>
          {:else}
            <span class="diff num start">Start</span>
          {/if}
          <span class="resulting num">→ {formatGrams(e.value_g)}</span>
        </li>
      {/each}
    {/if}
  </ul>
</section>

<style>
  .messlog {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-3);
    box-shadow: var(--shadow);
    flex: 1 1 auto;
    min-height: 0;
    display: flex; flex-direction: column;
  }
  header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: var(--sp-2);
  }
  header h3 {
    margin: 0; font-size: var(--fs-sm); color: var(--fg-dim);
    font-weight: 500; letter-spacing: 0.02em;
  }
  .meta { display: flex; align-items: center; gap: var(--sp-2); }
  .count { font-size: var(--fs-xs); color: var(--fg-mute); }
  .list {
    list-style: none; margin: 0; padding: 0 var(--sp-2) 0 0;  /* Luft zum Scrollbalken */
    overflow-y: auto;
    flex: 1 1 auto; min-height: 0;
  }
  /* Tabellarische Ausrichtung mit drei festen Spalten:
       | Zeit (links) | Differenz (rechts, mit fester Einheits-Spur) | → Resultat (rechts) |
     Die Differenz-Spalte ist rechtsbündig, sodass die Einheiten („g", „kg",
     „Tara", „Start") fluchten und das Ablesen ruhig wird, auch wenn Werte
     zwischen g und kg wechseln. */
  .row {
    display: grid;
    grid-template-columns: 72px minmax(0, 1fr) minmax(0, 1fr);
    gap: var(--sp-3);
    align-items: baseline;
    padding: 7px var(--sp-2) 7px 4px;
    border-bottom: 1px solid var(--border);
    font-variant-numeric: tabular-nums lining-nums slashed-zero;
  }
  .row:last-child { border-bottom: none; }
  .ts {
    font-size: var(--fs-xs);
    color: var(--fg-mute);
    text-align: left;
  }
  .diff {
    font-size: var(--fs-md);
    text-align: right;            /* rechtsbündig — Einheiten untereinander */
    letter-spacing: 0.02em;
    font-variant-numeric: tabular-nums lining-nums slashed-zero;
  }
  .diff.plus { color: var(--green); }
  .diff.minus { color: var(--orange); }
  .diff.tare, .diff.start { color: var(--info-blue); font-size: var(--fs-sm); }
  .resulting {
    font-size: var(--fs-xs);
    color: var(--fg-dim);
    text-align: right;
    white-space: nowrap;
    font-variant-numeric: tabular-nums lining-nums slashed-zero;
  }
  .empty {
    padding: var(--sp-4); text-align: center;
    color: var(--fg-mute); font-size: var(--fs-sm);
  }
</style>
