<script lang="ts">
  /**
   * Persistente Seitenleiste links: LiveWaage und Messprotokoll.
   * Auf Desktop immer sichtbar, auf Mobile als kompakter Header oben.
   */
  import LiveWaage from './LiveWaage.svelte';
  import MessLog from './MessLog.svelte';
  import type { MesslogEntry } from '../lib/types';

  interface Props {
    messlog: MesslogEntry[];
    onMesslogChanged?: () => void;
  }
  let { messlog = [], onMesslogChanged }: Props = $props();
</script>

<aside class="sidebar">
  <LiveWaage />
  <MessLog entries={messlog} onChanged={onMesslogChanged} />
</aside>

<style>
  .sidebar {
    flex: 0 0 auto;
    /* In der Übergangsphase (knapp über dem Mobile-Breakpoint) bleibt
       die Sidebar bei mindestens 320 px — sonst leidet die
       Wäge-Display-Lesbarkeit. Erst auf richtigen Mobile-Breiten
       (siehe App.svelte) wird sie zur kompakten Header-Spalte. */
    width: clamp(320px, 30vw, 400px);
    display: flex; flex-direction: column;
    gap: var(--sp-3);
    min-height: 0;
    overflow: hidden;
  }

  @media (max-width: 900px) {
    /* Auf Mobile löst sich der Sidebar-Container auf: LiveWaage und
       MessLog werden direkte Flex-Kinder von `.body`. Damit kann die
       LiveWaage `position: sticky` zur Body-Scroll-Achse setzen und
       die MessLog ihre eigene `max-height` für internes Scrollen
       greifen lassen, ohne den Sidebar-Wrapper als Flex-Vorfahren. */
    .sidebar {
      display: contents;
    }
  }
</style>
