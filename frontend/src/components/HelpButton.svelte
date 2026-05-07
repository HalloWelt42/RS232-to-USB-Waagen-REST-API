<script lang="ts">
  import { route } from '../lib/routing.svelte';
  import type { HelpId } from '../lib/help';

  interface Props { id: HelpId; label?: string; }
  let { id, label = 'Information und Hilfe' }: Props = $props();

  // Über die Route öffnen — die URL ist die einzige Quelle der Wahrheit,
  // helpStore wird zentral aus dem App-Root synchronisiert.
  function open(): void { route.openHelp(id); }
</script>

<button class="info-btn" onclick={open} title={label} aria-label={label}>
  <i class="fa-solid fa-circle-info" aria-hidden="true"></i>
</button>
