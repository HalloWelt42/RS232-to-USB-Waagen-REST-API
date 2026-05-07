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

  <div class="weight num" class:stable={reading?.stable}>
    {reading ? formatGrams(reading.weight_g) : '—'}
  </div>

  <div class="status-line">
    {#if reading}
      <span class="badge {reading.stable ? 'ok' : 'warn'}">
        {reading.stable ? 'STABIL' : 'INSTABIL'}
      </span>
      <span class="ts num">{formatTime(reading.timestamp)}</span>
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
    padding: var(--sp-3) var(--sp-4);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--sp-2);
    flex: 0 0 auto;
    transition: border-color 0.3s;
  }
  .display.stable   { border-color: var(--green); }
  .display.unstable { border-color: var(--orange); }

  .connection {
    align-self: flex-end;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: var(--fs-xs);
    color: var(--fg-dim);
  }
  .conn-label { font-family: var(--mono); }
  .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--fg-dim);
  }
  .dot.open       { background: var(--green); box-shadow: 0 0 5px var(--green); }
  .dot.connecting { background: var(--orange); animation: pulse 1.2s infinite; }
  .dot.closed, .dot.error { background: var(--red); }

  .weight {
    /* goldener Schnitt: knapp unter --fs-xxxl */
    font-size: clamp(2.6rem, 7vw, 4.2rem);
    font-weight: 600;
    color: var(--fg-dim);
    line-height: 1.05;
    transition: color 0.25s;
    letter-spacing: -0.02em;
  }
  .weight.stable { color: var(--green); }

  .status-line {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: var(--fs-xs);
  }
  .badge {
    font-family: var(--mono);
    font-size: var(--fs-xs);
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 999px;
    letter-spacing: 0.08em;
  }
  .badge.ok   { background: color-mix(in srgb, var(--green)  20%, transparent); color: var(--green); }
  .badge.warn { background: color-mix(in srgb, var(--orange) 20%, transparent); color: var(--orange); }

  .ts {
    color: var(--fg-dim);
    font-size: var(--fs-xs);
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.4; }
  }
</style>
