<script lang="ts">
  import { route } from '../lib/routing.svelte';
  import { t } from '../lib/i18n';
  import { searchStore } from '../lib/searchStore.svelte';
  import { modelStore } from '../lib/modelStore.svelte';
  import ThemeToggle from './ThemeToggle.svelte';
  import LanguageToggle from './LanguageToggle.svelte';
  import HelpButton from './HelpButton.svelte';

  function backToDashboard(): void { route.go(null); }
  function openDonate(): void { route.go('donate'); }
  function openGlossary(): void { route.openHelp('glossary'); }
  function openSearch(): void { searchStore.show(); }
  function openSettings(): void { route.go('settings'); }

  let isTool = $derived(route.mode === 'tool');
  let activeTitle = $derived.by(() => {
    if (route.activeTool) return t(`tools.${route.activeTool}`);
    return '';
  });
  let modelLabel = $derived(modelStore.compactLabel);
</script>

<header class="topbar">
  <div class="brand">
    {#if isTool}
      <button class="hdr-btn icon-only" onclick={backToDashboard}
              title={t('general.back')} aria-label={t('general.back')}>
        <i class="fa-solid fa-arrow-left"></i>
      </button>
    {/if}
    <span class="name only-desktop">WAAGE</span>
    {#if isTool}
      <span class="model">› {activeTitle}</span>
    {:else}
      <button class="model-btn" onclick={openSettings}
              title={t('topbar.openSettings')}>
        {modelLabel}
        <i class="fa-solid fa-gear" aria-hidden="true"></i>
      </button>
    {/if}
  </div>

  <div class="actions">
    <button class="hdr-btn search-btn only-desktop" onclick={openSearch}
            title={t('topbar.search')} aria-label={t('topbar.search')}>
      <i class="fa-solid fa-magnifying-glass"></i>
      <span class="kbd">⌘K</span>
    </button>
    <LanguageToggle />
    <ThemeToggle />
    <a class="hdr-btn only-desktop" href="/docs" target="_blank" rel="noopener" title={t('app.apiDocs')}>
      <i class="fa-solid fa-code"></i> {t('app.apiDocs')}
    </a>
    <button class="hdr-btn icon-only only-desktop" onclick={openGlossary}
            title={t('topbar.glossary')} aria-label={t('topbar.glossary')}>
      <i class="fa-solid fa-book"></i>
    </button>
    <HelpButton id="overview" label={t('topbar.info')} />
    <button class="donate-btn" onclick={openDonate}
            title={t('topbar.donate')} aria-label={t('topbar.donate')}>
      <i class="fa-solid fa-heart"></i>
    </button>
  </div>
</header>

<style>
  .topbar {
    height: var(--header-h);
    flex: 0 0 auto;
    display: flex; align-items: center; justify-content: space-between;
    gap: var(--sp-3);
    padding: 0 var(--sp-4);
    background: var(--bg-card);
    border-bottom: 1px solid var(--border);
  }
  .brand {
    display: flex; align-items: baseline; gap: var(--sp-2);
    min-width: 0;
  }
  .brand .name {
    font-weight: 700; letter-spacing: 0.05em; font-size: var(--fs-md);
  }
  .brand .model {
    color: var(--fg-dim); font-size: var(--fs-sm);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .model-btn {
    background: transparent;
    border: none;
    padding: 0;
    color: var(--fg-dim);
    font-family: var(--sans);
    font-size: var(--fs-sm);
    cursor: pointer;
    display: inline-flex; align-items: baseline; gap: 6px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    min-width: 0;
  }
  .model-btn i { font-size: 11px; opacity: 0.6; }
  .model-btn:hover { color: var(--accent); }
  .model-btn:hover i { opacity: 1; }
  .actions { display: flex; align-items: center; gap: var(--sp-2); }
  .search-btn { gap: 6px; }
  .kbd {
    font-family: var(--num);
    font-size: 10px;
    color: var(--fg-mute);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1px 5px;
    margin-left: 4px;
  }
  /* Mobile: Brand-Schriftzug, Suche, API-Doku und Glossar-Knopf
     ausblenden — diese Funktionen sind über Settings / Cmd+K-Shortcut
     bzw. Hilfe-Karten alternativ erreichbar und kosten am Handy
     wertvolle Topbar-Breite. */
  @media (max-width: 900px) {
    .kbd { display: none; }
    .only-desktop { display: none !important; }
  }
</style>
