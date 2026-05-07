<script lang="ts">
  /**
   * Warn-Banner unter der Topbar, wenn die App im Simulator-Modus läuft.
   * Liest den Status aus dem Health-Polling (App.svelte) und blendet
   * sich nur ein, wenn der Backend-Reader die SimulatedWaage nutzt.
   */
  import { t } from '../lib/i18n';
  import { route } from '../lib/routing.svelte';
  import type { HealthInfo } from '../lib/types';

  interface Props { health: HealthInfo | null; }
  let { health = null }: Props = $props();

  let visible = $derived(!!(health && health.simulated));

  function openSettings(): void { route.go('settings'); }
</script>

{#if visible}
  <div class="banner" role="status" aria-live="polite">
    <i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i>
    <span>{t('topbar.simulatedWarning')}</span>
    <button class="link" onclick={openSettings}>
      <i class="fa-solid fa-gear"></i>
      {t('tools.settings')}
    </button>
  </div>
{/if}

<style>
  .banner {
    flex: 0 0 auto;
    background: color-mix(in srgb, var(--orange) 18%, var(--bg-card));
    border-bottom: 1px solid var(--orange);
    color: var(--orange);
    font-size: var(--fs-sm);
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 6px var(--sp-4);
    display: flex; align-items: center; gap: var(--sp-3);
  }
  .banner i { font-size: 16px; }
  .link {
    margin-left: auto;
    background: transparent; border: none;
    color: var(--orange); cursor: pointer;
    padding: 0; font: inherit;
    text-decoration: underline; text-underline-offset: 2px;
    display: inline-flex; align-items: center; gap: 6px;
  }
  .link:hover { color: var(--fg); }
</style>
