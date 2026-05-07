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

<nav class="tabbar" aria-label={t('topbar.toolNav') || 'Werkzeug-Auswahl'}>
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
  /* Eckige Industrial-TabBar — keine Rundungen am Container,
     Buttons ohne Außen-Border, nur durch Trennstriche separiert. */
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
    border-radius: 0;            /* Tab-Knöpfe selbst eckig */
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
    position: relative;
  }
  button:last-child { border-right: none; }
  button:hover { color: var(--fg); background: var(--bg-card-2); }
  button.active {
    color: var(--accent);
    background: color-mix(in srgb, var(--accent) 10%, transparent);
  }
  /* Aktiver Tab als Akzent-Strich am unteren Rand — ohne Box rundherum. */
  button.active::after {
    content: '';
    position: absolute;
    left: 0; right: 0; bottom: 0;
    height: 2px;
    background: var(--accent);
  }
  button[data-color="donate"].active {
    color: var(--donate);
    background: color-mix(in srgb, var(--donate) 10%, transparent);
  }
  button[data-color="donate"].active::after { background: var(--donate); }
  button[data-color="info"].active {
    color: var(--info-blue);
    background: color-mix(in srgb, var(--info-blue) 10%, transparent);
  }
  button[data-color="info"].active::after { background: var(--info-blue); }
  button i { font-size: var(--fs-md); }

  /* Focus-Ring innerhalb der Button-Fläche — kein Außen-Box-Effekt
     mehr, der über die Topbar hinausragt. */
  button:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: -2px;
  }

  @media (max-width: 900px) {
    button span { display: none; }
    button i { font-size: var(--fs-lg); }
  }
</style>
