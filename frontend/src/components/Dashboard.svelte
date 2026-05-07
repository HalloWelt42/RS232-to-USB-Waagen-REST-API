<script lang="ts">
  import LiveWaage from './LiveWaage.svelte';
  import MessLog from './MessLog.svelte';
  import ActionCard from './ActionCard.svelte';
  import type { MesslogEntry } from '../lib/types';

  interface Props { messlog: MesslogEntry[]; }
  let { messlog = [] }: Props = $props();
</script>

<div class="dashboard">
  <div class="left">
    <LiveWaage />
    <MessLog entries={messlog} />
  </div>
  <div class="right">
    <ActionCard tool="wiegen"    icon="fa-solid fa-scale-balanced" />
    <ActionCard tool="netto"     icon="fa-solid fa-flask" />
    <ActionCard tool="count"     icon="fa-solid fa-hashtag" />
    <ActionCard tool="tolerance" icon="fa-solid fa-bullseye" />
    <ActionCard tool="samples"   icon="fa-solid fa-clipboard-list" />
    <ActionCard tool="differenz" icon="fa-solid fa-arrow-right-arrow-left" />
    <ActionCard tool="help"      icon="fa-solid fa-book" iconColor="info" />
    <ActionCard tool="settings"  icon="fa-solid fa-gear" />
    <ActionCard tool="donate"    icon="fa-solid fa-heart" iconColor="donate" />
  </div>
</div>

<style>
  .dashboard {
    flex: 1 1 auto;
    min-height: 0;
    display: grid;
    grid-template-columns: 1fr 1.618fr;
    gap: var(--sp-3);
    padding: var(--sp-3);
    overflow: hidden;
  }
  .left {
    display: flex; flex-direction: column;
    gap: var(--sp-3);
    min-height: 0;
  }
  .right {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(220px, 100%), 1fr));
    gap: var(--sp-3);
    align-content: start;
    overflow-y: auto;
  }

  @media (max-width: 800px) {
    .dashboard {
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr;
      overflow-y: auto;
    }
    .left { min-height: 0; }
    .right { overflow-y: visible; }
  }
</style>
