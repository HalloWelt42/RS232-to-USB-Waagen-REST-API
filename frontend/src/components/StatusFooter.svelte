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
    <span class="cell">Port <code>{health.port}</code></span>
    <span class="cell">{health.baudrate} Baud</span>
    <span class="cell">Uptime {formatDuration(health.uptime_seconds)}</span>
  {:else}
    <span class="cell">Backend lädt...</span>
  {/if}
  <span class="cell version">v{__APP_VERSION__}</span>
</footer>

<style>
  footer {
    height: var(--footer-h);
    background: var(--bg-card);
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 1.25rem;
    padding: 0 1rem;
    font-size: 0.78rem;
    color: var(--fg-dim);
    flex: 0 0 auto;
  }
  .cell {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  .cell.version { margin-left: auto; }
  .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--fg-dim);
  }
  .dot.open { background: var(--green); }
  .dot.connecting { background: var(--orange); animation: pulse 1.2s infinite; }
  .dot.closed, .dot.error { background: var(--red); }
  code { background: transparent; padding: 0; font-size: inherit; }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.4; }
  }
</style>
