<script lang="ts">
  import { formatDuration } from '../lib/format';
  import type { ConnectionState, HealthInfo } from '../lib/types';

  interface Props {
    health: HealthInfo | null;
    connection: ConnectionState;
  }

  let { health = null, connection = 'connecting' }: Props = $props();

  const connectionLabel: Record<ConnectionState, string> = {
    open: 'Live', connecting: 'Verbinde', closed: 'Getrennt', error: 'Fehler',
  };
</script>

<footer>
  <span class="cell">
    <span class="dot {connection}"></span>
    {connectionLabel[connection]}
  </span>
  {#if health}
    <span class="cell">Reader {health.reader_alive ? 'aktiv' : 'aus'}</span>
    <span class="cell">Port <code class="num">{health.port}</code></span>
    <span class="cell num">{health.baudrate} Baud</span>
    <span class="cell num">Uptime {formatDuration(health.uptime_seconds)}</span>
  {:else}
    <span class="cell">Backend lädt …</span>
  {/if}
  <span class="cell version num">v{__APP_VERSION__}</span>
</footer>

<style>
  footer {
    height: var(--footer-h);
    background: var(--bg-card);
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: var(--sp-4);
    padding: 0 var(--sp-3);
    font-size: var(--fs-xs);
    color: var(--fg-dim);
    flex: 0 0 auto;
  }
  .cell {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .cell.version { margin-left: auto; }
  .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--fg-dim);
  }
  .dot.open { background: var(--green); }
  .dot.connecting { background: var(--orange); animation: pulse 1.2s infinite; }
  .dot.closed, .dot.error { background: var(--red); }
  code { background: transparent; padding: 0; font-size: inherit; border: none; }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.4; }
  }
</style>
