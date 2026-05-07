<script lang="ts">
  /**
   * Globale Schicht, die alle aktuell offenen Hilfe-Fenster rendert.
   * Wird einmal im App-Root platziert und reagiert auf den helpStore.
   */
  import { helpEntries } from '../lib/help';
  import { helpStore } from '../lib/helpStore.svelte';
  import DraggableWindow from './DraggableWindow.svelte';

  let windows = $derived(helpStore.list());
</script>

{#each windows as w (w.id)}
  {@const entry = helpEntries[w.id]}
  <DraggableWindow id={w.id} title={entry.title} x={w.x} y={w.y} z={w.z}>
    <div class="content">
      {#each entry.blocks as block, i (i)}
        <section class="block">
          <h3>{block.heading}</h3>
          <p>{block.body}</p>
        </section>
      {/each}
    </div>
  </DraggableWindow>
{/each}

<style>
  .content {
    display: flex;
    flex-direction: column;
    gap: var(--sp-3);
  }
  .block h3 {
    margin: 0 0 var(--sp-1) 0;
    font-size: var(--fs-sm);
    font-weight: 600;
    color: var(--accent);
    letter-spacing: 0.02em;
  }
  .block p {
    margin: 0;
    color: var(--fg);
    font-size: var(--fs-sm);
  }
</style>
