<script lang="ts">
  import { helpStore } from '../lib/helpStore.svelte';
  import type { HelpId } from '../lib/help';

  interface Props { id: HelpId; label?: string; }
  let { id, label = 'Information und Hilfe' }: Props = $props();

  function open(): void { helpStore.open(id); }
</script>

<button class="info-btn" onclick={open} title={label} aria-label={label}>
  <i class="fa-solid fa-circle-info" aria-hidden="true"></i>
</button>
