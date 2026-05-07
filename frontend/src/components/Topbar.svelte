<script lang="ts">
  import { route } from '../lib/routing.svelte';
  import { t } from '../lib/i18n';
  import { searchStore } from '../lib/searchStore.svelte';
  import ThemeToggle from './ThemeToggle.svelte';
  import LanguageToggle from './LanguageToggle.svelte';
  import HelpButton from './HelpButton.svelte';

  function backToDashboard(): void { route.go(null); }
  function openDonate(): void { route.go('donate'); }
  function openGlossary(): void { route.openHelp('glossary'); }
  function openSearch(): void { searchStore.show(); }

  let isTool = $derived(route.mode === 'tool');
  let activeTitle = $derived.by(() => {
    if (route.activeTool) return t(`tools.${route.activeTool}`);
    return '';
  });
</script>

<header class="topbar">
  <div class="brand">
    {#if isTool}
      <button class="hdr-btn icon-only" onclick={backToDashboard}
              title={t('general.back')} aria-label={t('general.back')}>
        <i class="fa-solid fa-arrow-left"></i>
      </button>
    {/if}
    <span class="name">WAAGE</span>
    {#if isTool}
      <span class="model">› {activeTitle}</span>
    {:else}
      <span class="model">G&amp;G PLC 6000g/0,1g</span>
    {/if}
  </div>

  <div class="actions">
    <button class="hdr-btn search-btn" onclick={openSearch}
            title={t('topbar.search')} aria-label={t('topbar.search')}>
      <i class="fa-solid fa-magnifying-glass"></i>
      <span class="kbd">⌘K</span>
    </button>
    <LanguageToggle />
    <ThemeToggle />
    <a class="hdr-btn" href="/docs" target="_blank" rel="noopener" title={t('app.apiDocs')}>
      <i class="fa-solid fa-code"></i> {t('app.apiDocs')}
    </a>
    <button class="hdr-btn icon-only" onclick={openGlossary}
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
  @media (max-width: 800px) {
    .kbd { display: none; }
  }
</style>
