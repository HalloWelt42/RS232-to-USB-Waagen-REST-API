<script lang="ts">
  /**
   * Hinweis-Band unter der Topbar, sobald der Server eine neue Fassung
   * ausliefert (versionStore). Sagt, wann sie von selbst lädt, und
   * bietet das sofortige Neuladen an.
   */
  import { t } from '../lib/i18n';
  import { versionStore } from '../lib/versionStore.svelte';
</script>

{#if versionStore.available}
  <div class="banner" role="status">
    <i class="fa-solid fa-rotate" aria-hidden="true"></i>
    <span class="msg">
      <strong>{t('update.available', versionStore.available)}</strong>
      {t('update.reloadHint')}
    </span>
    <button class="action" type="button" onclick={() => location.reload()}>
      <i class="fa-solid fa-rotate" aria-hidden="true"></i>
      {t('update.reloadNow')}
    </button>
  </div>
{/if}

<style>
  .banner {
    flex: 0 0 auto;
    width: 100%;
    background: color-mix(in srgb, var(--accent) 14%, var(--bg-card));
    border-bottom: 1px solid var(--accent);
    color: var(--fg);
    font-family: var(--sans);
    font-size: var(--fs-sm);
    padding: 8px var(--sp-4);
    display: flex; align-items: center; gap: var(--sp-3);
    flex-wrap: wrap;
  }
  .banner > i { font-size: 16px; flex: 0 0 auto; color: var(--accent); }
  .msg { flex: 1 1 auto; min-width: 0; }
  .action {
    margin-left: auto;
    flex: 0 0 auto;
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px;
    border: 1px solid var(--accent);
    border-radius: var(--radius-sm);
    background: var(--bg-card);
    color: var(--accent);
    font-family: inherit;
    font-size: var(--fs-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    cursor: pointer;
  }
  .action:hover {
    background: var(--accent);
    color: var(--bg-card);
  }
</style>
