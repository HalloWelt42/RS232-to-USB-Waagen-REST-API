<script lang="ts">
  import { route, type ToolKey } from '../lib/routing.svelte';
  import { t } from '../lib/i18n';

  interface Tab {
    key: ToolKey;
    icon: string;
    color?: 'accent' | 'donate' | 'info';
  }

  const tabs: Tab[] = [
    { key: 'wiegen',    icon: 'fa-solid fa-scale-balanced' },
    { key: 'netto',     icon: 'fa-solid fa-flask' },
    { key: 'count',     icon: 'fa-solid fa-hashtag' },
    { key: 'tolerance', icon: 'fa-solid fa-bullseye' },
    { key: 'samples',   icon: 'fa-solid fa-clipboard-list' },
    { key: 'differenz', icon: 'fa-solid fa-arrow-right-arrow-left' },
    { key: 'help',      icon: 'fa-solid fa-book',  color: 'info' },
    { key: 'settings',  icon: 'fa-solid fa-gear' },
    { key: 'donate',    icon: 'fa-solid fa-heart', color: 'donate' },
  ];

  let active = $derived(route.activeTool);
</script>

<nav class="tabbar" aria-label="Werkzeug-Auswahl">
  {#each tabs as tab (tab.key)}
    <button
      aria-pressed={active === tab.key}
      class:active={active === tab.key}
      data-color={tab.color ?? 'accent'}
      onclick={() => route.go(tab.key)}
      title={t(`tools.${tab.key}`)}
    >
      <i class={tab.icon} aria-hidden="true"></i>
      <span>{t(`toolsShort.${tab.key}`)}</span>
    </button>
  {/each}
</nav>

<style>
  .tabbar {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    display: flex;
    box-shadow: var(--shadow);
    overflow: hidden;
    flex: 0 0 auto;
  }
  button {
    flex: 1 1 0;
    padding: var(--sp-2) var(--sp-2);
    background: transparent;
    border: none;
    color: var(--fg-dim);
    font-family: var(--sans);
    font-size: var(--fs-sm);
    letter-spacing: 0.04em;
    cursor: pointer;
    display: inline-flex; align-items: center; justify-content: center;
    gap: 8px;
    border-right: 1px solid var(--border);
    min-height: var(--tap);
    text-transform: uppercase;
  }
  button:last-child { border-right: none; }
  button:hover { color: var(--fg); background: var(--bg-card-2); }
  button.active {
    color: var(--accent);
    background: color-mix(in srgb, var(--accent) 10%, transparent);
    border-bottom: 2px solid var(--accent);
  }
  button[data-color="donate"].active { color: var(--donate); border-bottom-color: var(--donate); background: color-mix(in srgb, var(--donate) 10%, transparent); }
  button[data-color="info"].active   { color: var(--info-blue); border-bottom-color: var(--info-blue); background: color-mix(in srgb, var(--info-blue) 10%, transparent); }
  button i { font-size: var(--fs-md); }

  @media (max-width: 800px) {
    button span { display: none; }
    button i { font-size: var(--fs-lg); }
  }
</style>
