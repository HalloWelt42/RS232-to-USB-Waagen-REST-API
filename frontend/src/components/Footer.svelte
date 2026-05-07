<script lang="ts">
  import { formatDuration } from '../lib/format';
  import { t } from '../lib/i18n';
  import type { ConnectionState, HealthInfo } from '../lib/types';

  interface Props {
    health: HealthInfo | null;
    connection: ConnectionState;
  }

  let { health = null, connection = 'connecting' }: Props = $props();

  const labels: Record<ConnectionState, string> = {
    open:       'status.live',
    connecting: 'status.connecting',
    closed:     'status.closed',
    error:      'status.error',
  };
</script>

<footer>
  <span class="cell"><span class="dot {connection}"></span> {t(labels[connection])}</span>
  {#if health}
    <span class="cell">{health.reader_alive ? t('status.readerActive') : t('status.readerInactive')}</span>
    <span class="cell">{t('status.port')} <code class="num">{health.port}</code></span>
    <span class="cell num">{health.baudrate} Baud</span>
    <span class="cell num">{t('status.uptime')} {formatDuration(health.uptime_seconds)}</span>
  {:else}
    <span class="cell">{t('general.loading')}</span>
  {/if}
  <span class="cell version num">v{__APP_VERSION__}</span>
</footer>

<style>
  footer {
    height: var(--footer-h);
    flex: 0 0 auto;
    display: flex; align-items: center; gap: var(--sp-4);
    padding: 0 var(--sp-3);
    background: var(--bg-card);
    border-top: 1px solid var(--border);
    font-size: var(--fs-xs);
    color: var(--fg-dim);
  }
  .cell { display: flex; align-items: center; gap: 6px; }
  .cell.version { margin-left: auto; }
  .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--fg-dim);
  }
  .dot.open { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .dot.connecting { background: var(--orange); animation: pulse 1.2s infinite; }
  .dot.closed, .dot.error { background: var(--red); }
  code { background: transparent; padding: 0; border: none; font-size: inherit; }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
</style>
