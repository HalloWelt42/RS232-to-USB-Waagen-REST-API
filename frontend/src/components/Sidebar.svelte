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
    width: clamp(280px, 32vw, 400px);
    display: flex; flex-direction: column;
    gap: var(--sp-3);
    min-height: 0;
    overflow: hidden;
  }

  @media (max-width: 800px) {
    .sidebar {
      width: 100%;
      flex: 0 0 auto;
    }
  }
</style>
