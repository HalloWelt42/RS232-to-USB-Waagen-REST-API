<script>
  import { formatGrams, formatTime } from '../lib/format.js';

  let { reading = null, connection = 'connecting' } = $props();

  let displayText = $derived.by(() => {
    if (!reading) return '—';
    return formatGrams(reading.weight_g);
  });

  let stateClass = $derived.by(() => {
    if (!reading) return 'idle';
    return reading.stable ? 'stable' : 'unstable';
  });
</script>

<section class="display {stateClass}">
  <div class="connection-row">
    <span class="dot {connection}"></span>
    <span class="conn-label">{connectionLabel(connection)}</span>
  </div>

  <div class="weight" class:stable={reading?.stable}>
    {displayText}
  </div>

  <div class="meta">
    <div class="status-line">
      {#if reading}
        <span class="badge {reading.stable ? 'ok' : 'warn'}">
          {reading.stable ? 'STABLE' : 'INSTABIL'}
        </span>
        <span class="ts">{formatTime(reading.timestamp)}</span>
      {:else}
        <span class="ts">Warte auf erstes Reading...</span>
      {/if}
    </div>
  </div>
</section>

<script module>
  function connectionLabel(s) {
    return {
      'open':       'Live',
      'connecting': 'Verbinde...',
      'closed':     'Getrennt',
      'error':      'Fehler',
    }[s] || s;
  }
</script>

<style>
  .display {
    background:    var(--bg-card);
    border:        1px solid var(--border);
    border-radius: var(--radius);
    box-shadow:    var(--shadow);
    padding:       2rem 2.5rem;
    display:       flex;
    flex-direction: column;
    align-items:   center;
    gap:           1rem;
    min-width:     min(28rem, 90vw);
    transition:    border-color 0.3s;
  }
  .display.stable   { border-color: var(--green); }
  .display.unstable { border-color: var(--orange); }
  .display.idle     { border-color: var(--border); }

  .connection-row {
    display:     flex;
    align-items: center;
    gap:         0.5rem;
    align-self:  flex-end;
    font-size:   0.85rem;
    color:       var(--fg-dim);
  }

  .dot {
    width:        10px;
    height:       10px;
    border-radius: 50%;
    background:   var(--fg-dim);
  }
  .dot.open       { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .dot.connecting { background: var(--orange); animation: pulse 1.2s infinite; }
  .dot.closed     { background: var(--red); }
  .dot.error      { background: var(--red); }

  .weight {
    font-family:    var(--mono);
    font-size:      clamp(2.4rem, 8vw, 5rem);
    font-weight:    600;
    letter-spacing: 0.03em;
    color:          var(--fg-dim);
    transition:     color 0.3s;
    text-align:     center;
    line-height:    1.1;
  }
  .weight.stable {
    color: var(--green);
  }

  .meta {
    width:      100%;
    display:    flex;
    justify-content: space-between;
    align-items:     center;
  }
  .status-line {
    width:           100%;
    display:         flex;
    justify-content: space-between;
    align-items:     center;
    font-size:       0.9rem;
  }
  .badge {
    font-family:   var(--mono);
    font-size:     0.78rem;
    font-weight:   700;
    padding:       0.18rem 0.6rem;
    border-radius: 999px;
    letter-spacing: 0.08em;
  }
  .badge.ok   { background: rgba(63, 185, 80, 0.2);  color: var(--green); }
  .badge.warn { background: rgba(210, 153, 34, 0.2); color: var(--orange); }

  .ts {
    color:       var(--fg-dim);
    font-family: var(--mono);
    font-size:   0.85rem;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.4; }
  }
</style>
