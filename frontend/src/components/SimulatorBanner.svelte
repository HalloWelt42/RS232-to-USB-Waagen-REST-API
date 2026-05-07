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
  <button class="banner" type="button" onclick={openSettings}
          aria-label={t('topbar.simulatedWarning')}>
    <i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i>
    <span class="msg">{t('topbar.simulatedWarning')}</span>
    <span class="action">
      <i class="fa-solid fa-arrow-right-arrow-left"></i>
      {t('topbar.switchToLive')}
    </span>
  </button>
{/if}

<style>
  .banner {
    flex: 0 0 auto;
    width: 100%;
    background: color-mix(in srgb, var(--orange) 18%, var(--bg-card));
    border: none;
    border-bottom: 1px solid var(--orange);
    color: var(--orange);
    font-family: var(--sans);
    font-size: var(--fs-sm);
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 8px var(--sp-4);
    display: flex; align-items: center; gap: var(--sp-3);
    cursor: pointer;
    text-align: left;
  }
  .banner:hover {
    background: color-mix(in srgb, var(--orange) 28%, var(--bg-card));
  }
  .banner > i { font-size: 16px; flex: 0 0 auto; }
  .msg { flex: 1 1 auto; }
  .action {
    margin-left: auto;
    flex: 0 0 auto;
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px;
    border: 1px solid var(--orange);
    border-radius: var(--radius-sm);
    background: var(--bg-card);
    color: var(--orange);
    font-size: var(--fs-xs);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .banner:hover .action {
    background: var(--orange);
    color: var(--bg-card);
  }
</style>
