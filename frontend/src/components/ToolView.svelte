<script lang="ts">
  /**
   * Tool-Modus: oben Tab-Bar (alle Tools), darunter das aktive Werkzeug.
   * Welches Panel angezeigt wird, entscheidet route.activeTool.
   */
  import { route } from '../lib/routing.svelte';
  import TabBar from './TabBar.svelte';
  import WiegenPanel from './panels/WiegenPanel.svelte';
  import NettoPanel from './panels/NettoPanel.svelte';
  import CountPanel from './panels/CountPanel.svelte';
  import TolerancePanel from './panels/TolerancePanel.svelte';
  import SamplesPanel from './panels/SamplesPanel.svelte';
  import DifferenzPanel from './panels/DifferenzPanel.svelte';
  import HelpPanel from './panels/HelpPanel.svelte';
  import SettingsPanel from './panels/SettingsPanel.svelte';
  import DonatePanel from './panels/DonatePanel.svelte';

  let active = $derived(route.activeTool);
</script>

<div class="tool-view">
  <TabBar />
  <div class="body">
    {#if active === 'wiegen'}    <WiegenPanel />
    {:else if active === 'netto'}     <NettoPanel />
    {:else if active === 'count'}     <CountPanel />
    {:else if active === 'tolerance'} <TolerancePanel />
    {:else if active === 'samples'}   <SamplesPanel />
    {:else if active === 'differenz'} <DifferenzPanel />
    {:else if active === 'help'}      <HelpPanel />
    {:else if active === 'settings'}  <SettingsPanel />
    {:else if active === 'donate'}    <DonatePanel />
    {/if}
  </div>
</div>

<style>
  .tool-view {
    flex: 1 1 auto;
    min-height: 0;
    display: flex; flex-direction: column;
    gap: var(--sp-3);
    padding: var(--sp-3);
    overflow: hidden;
  }
  .body {
    flex: 1 1 auto;
    min-height: 0;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    display: flex; flex-direction: column;
    overflow: hidden;
  }
</style>
