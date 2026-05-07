<script lang="ts">
  /**
   * Einheitlicher Panel-Header mit Titel rechts vom Hilfe-Knopf.
   *
   * Hält das Layout aller rechten Tab-Panels konsistent.
   */
  import HelpButton from './HelpButton.svelte';
  import type { HelpId } from '../lib/help';

  interface Props {
    title: string;
    help: HelpId;
    children?: import('svelte').Snippet;
  }
  let { title, help, children }: Props = $props();
</script>

<header class="panel-header">
  <h2>{title}</h2>
  <div class="extras">
    {@render children?.()}
    <HelpButton id={help} label="Hilfe zu {title}" />
  </div>
</header>

<style>
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--sp-2);
    margin-bottom: var(--sp-3);
    flex: 0 0 auto;
  }
  h2 {
    margin: 0;
    font-size: var(--fs-md);
    font-weight: 600;
    letter-spacing: 0.01em;
  }
  .extras {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
  }
</style>
