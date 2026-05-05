<script>
  import { formatDate } from '../lib/format.js';

  let { health = null } = $props();

  function fmtUptime(s) {
    if (s == null) return '—';
    const d = Math.floor(s / 86400);
    const h = Math.floor((s % 86400) / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = Math.floor(s % 60);
    if (d) return `${d}d ${h}h ${m}m`;
    if (h) return `${h}h ${m}m ${sec}s`;
    if (m) return `${m}m ${sec}s`;
    return `${sec}s`;
  }
</script>

<section class="health">
  <h3>Status</h3>
  {#if health}
    <dl>
      <dt>API</dt>
      <dd class:ok={health.ok} class:warn={!health.ok}>
        {health.ok ? 'OK' : 'wartet'}
      </dd>
      <dt>Reader</dt>
      <dd class:ok={health.reader_alive} class:warn={!health.reader_alive}>
        {health.reader_alive ? 'aktiv' : 'aus'}
      </dd>
      <dt>Port</dt>
      <dd><code>{health.port}</code></dd>
      <dt>Baud</dt>
      <dd><code>{health.baudrate}</code></dd>
      <dt>Uptime</dt>
      <dd>{fmtUptime(health.uptime_seconds)}</dd>
      <dt>Letztes Frame</dt>
      <dd>{health.last_seen ? formatDate(health.last_seen) : '—'}</dd>
    </dl>
  {:else}
    <div class="loading">Lade...</div>
  {/if}
</section>

<style>
  .health {
    background:    var(--bg-card);
    border:        1px solid var(--border);
    border-radius: var(--radius);
    padding:       1.25rem 1.5rem;
    box-shadow:    var(--shadow);
    width:         min(28rem, 90vw);
  }
  h3 {
    margin: 0 0 0.75rem 0;
    font-size: 1.05rem;
  }
  dl {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.4rem 1rem;
    margin: 0;
    font-size: 0.9rem;
  }
  dt {
    color: var(--fg-dim);
  }
  dd {
    margin: 0;
    text-align: right;
    font-family: var(--mono);
  }
  dd.ok   { color: var(--green); }
  dd.warn { color: var(--red); }
  .loading {
    color: var(--fg-dim);
    font-size: 0.9rem;
  }
</style>
