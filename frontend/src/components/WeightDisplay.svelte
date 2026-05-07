<script lang="ts">
  import { formatGrams, formatTime } from '../lib/format';
  import type { ConnectionState, Reading } from '../lib/types';

  interface Props {
    reading: Reading | null;
    connection: ConnectionState;
  }

  let { reading = null, connection = 'connecting' }: Props = $props();

  const connectionLabel: Record<ConnectionState, string> = {
    open:       'Live',
    connecting: 'Verbinde',
    closed:     'Getrennt',
    error:      'Fehler',
  };

  let stateClass = $derived.by<'stable' | 'unstable' | 'idle'>(() => {
    if (!reading) return 'idle';
    return reading.stable ? 'stable' : 'unstable';
  });
</script>

<section class="display {stateClass}">
  <div class="connection">
    <span class="dot {connection}"></span>
    <span class="conn-label">{connectionLabel[connection]}</span>
  </div>

  <div class="weight" class:stable={reading?.stable}>
    {reading ? formatGrams(reading.weight_g) : '—'}
  </div>

  <div class="status-line">
    {#if reading}
      <span class="badge {reading.stable ? 'ok' : 'warn'}">
        {reading.stable ? 'STABIL' : 'INSTABIL'}
      </span>
      <span class="ts">{formatTime(reading.timestamp)}</span>
    {:else}
      <span class="ts">Warte auf erstes Reading</span>
    {/if}
  </div>
</section>

<style>
  .display {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    padding: 1.5rem 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    flex: 0 0 auto;
    transition: border-color 0.3s;
  }
  .display.stable   { border-color: var(--green); }
  .display.unstable { border-color: var(--orange); }

  .connection {
    align-self: flex-end;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.78rem;
    color: var(--fg-dim);
  }
  .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--fg-dim);
  }
  .dot.open       { background: var(--green); box-shadow: 0 0 5px var(--green); }
  .dot.connecting { background: var(--orange); animation: pulse 1.2s infinite; }
  .dot.closed     { background: var(--red); }
  .dot.error      { background: var(--red); }

  .weight {
    font-family: var(--mono);
    font-size: clamp(2.2rem, 6vw, 4rem);
    font-weight: 600;
    color: var(--fg-dim);
    line-height: 1.1;
    transition: color 0.3s;
  }
  .weight.stable { color: var(--green); }

  .status-line {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
  }
  .badge {
    font-family: var(--mono);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.18rem 0.6rem;
    border-radius: 999px;
    letter-spacing: 0.08em;
  }
  .badge.ok   { background: rgba(63, 185, 80, 0.2);  color: var(--green); }
  .badge.warn { background: rgba(210, 153, 34, 0.2); color: var(--orange); }

  .ts {
    color: var(--fg-dim);
    font-family: var(--mono);
    font-size: 0.8rem;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.4; }
  }
</style>
