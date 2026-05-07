<script lang="ts">
  /**
   * Container für alle offenen Hilfe-Fenster.
   * Liegt im App-Root und rendert pro offenem Eintrag eine DraggableWindow.
   */
  import { helpStore } from '../lib/helpStore.svelte';
  import { helpEntries } from '../lib/help';
  import DraggableWindow from './DraggableWindow.svelte';
</script>

{#each helpStore.windows as w (w.id)}
  {@const entry = helpEntries[w.id]}
  <DraggableWindow id={w.id} title={entry.title}
                   x={w.x} y={w.y} w={w.w} h={w.h} z={w.z}>
    {#each entry.blocks as b}
      <section class="block">
        <h4>{b.heading}</h4>
        <p>{@html b.body}</p>
      </section>
    {/each}
  </DraggableWindow>
{/each}
