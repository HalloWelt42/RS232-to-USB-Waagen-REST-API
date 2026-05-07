<script lang="ts">
  import { formatGrams, formatTime } from '../lib/format';
  import { copyText } from '../lib/clipboard';
  import { toast } from '../lib/toast.svelte';
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

  async function copyValue(): Promise<void> {
    if (!reading) return;
    const text = reading.weight_g.toFixed(1);
    const ok = await copyText(text);
    toast.show(ok ? `${text} kopiert` : 'Kopieren nicht möglich', ok ? 'ok' : 'error');
  }

  async function copyJson(): Promise<void> {
    if (!reading) return;
    const text = JSON.stringify({
      weight_g: reading.weight_g,
      unit: reading.unit,
      stable: reading.stable,
      timestamp: reading.timestamp,
    });
    const ok = await copyText(text);
    toast.show(ok ? 'JSON kopiert' : 'Kopieren nicht möglich', ok ? 'ok' : 'error');
  }
</script>

<section class="display {stateClass}">
  <div class="connection">
    <span class="dot {connection}"></span>
    <span class="conn-label">{connectionLabel[connection]}</span>
  </div>

  <button
    class="weight num"
    class:stable={reading?.stable}
    onclick={copyValue}
    disabled={!reading}
    title={reading ? 'Wert kopieren' : 'Wartet auf Reading'}
    aria-label="Wert kopieren"
  >
    {reading ? formatGrams(reading.weight_g) : '—'}
  </button>

  <div class="status-line">
    {#if reading}
      <span class="badge {reading.stable ? 'ok' : 'warn'}">
        {reading.stable ? 'STABIL' : 'INSTABIL'}
      </span>
      <button class="copy-json" onclick={copyJson} title="Als JSON kopieren">
        JSON
      </button>
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

  /* Wert ist ein Knopf — Klick kopiert in die Zwischenablage */
  button.weight {
    background: transparent;
    border: none;
    padding: var(--sp-1) var(--sp-2);
    border-radius: var(--radius-sm);
    cursor: copy;
    font-size: clamp(2.6rem, 7vw, 4.2rem);
    font-weight: 600;
    color: var(--fg-dim);
    line-height: 1.05;
    transition: color 0.25s, background 0.15s;
    letter-spacing: -0.02em;
  }
  button.weight.stable { color: var(--green); }
  button.weight:hover:not(:disabled) {
    background: var(--bg-card-2);
  }
  button.weight:disabled { cursor: default; }

  .status-line {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--sp-2);
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

  button.copy-json {
    font-size: 10px;
    padding: 3px 8px;
    color: var(--fg-mute);
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 999px;
    font-family: var(--mono);
  }
  button.copy-json:hover { color: var(--accent); border-color: var(--accent); }

  .ts {
    color: var(--fg-dim);
    font-size: var(--fs-xs);
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.4; }
  }

  /* Mobile: noch größerer Wägewert */
  @media (max-width: 800px) {
    button.weight {
      font-size: clamp(3.2rem, 14vw, 5rem);
    }
    .display { padding: var(--sp-2) var(--sp-3); }
  }
</style>
