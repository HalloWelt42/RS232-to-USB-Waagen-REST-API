<script>
  import { api } from '../lib/api.js';

  let busy = $state(null);
  let lastResult = $state(null);
  let errorMsg   = $state(null);

  async function runCommand(name, fn, label) {
    if (busy) return;
    busy = name;
    errorMsg = null;
    lastResult = null;
    try {
      await fn();
      lastResult = label;
    } catch (e) {
      errorMsg = e.message;
    } finally {
      busy = null;
      // Erfolgsanzeige nach kurzer Zeit ausblenden
      if (lastResult) {
        setTimeout(() => { if (lastResult === label) lastResult = null; }, 2000);
      }
    }
  }

  const tare  = () => runCommand('tare',  api.cmdTare,  'Tara gesetzt');
  const unit  = () => runCommand('unit',  api.cmdUnit,  'Einheit gewechselt');
  const light = () => runCommand('light', api.cmdLight, 'Beleuchtung umgeschaltet');
</script>

<section class="actions">
  <button onclick={tare}  disabled={busy !== null} class:active={busy === 'tare'}>
    {busy === 'tare'  ? '...' : 'Tara'}
  </button>
  <button onclick={unit}  disabled={busy !== null} class:active={busy === 'unit'}>
    {busy === 'unit'  ? '...' : 'Einheit'}
  </button>
  <button onclick={light} disabled={busy !== null} class:active={busy === 'light'}>
    {busy === 'light' ? '...' : 'Licht'}
  </button>

  {#if lastResult}
    <span class="status ok">{lastResult}</span>
  {:else if errorMsg}
    <span class="status err">{errorMsg}</span>
  {/if}
</section>

<style>
  .actions {
    display: flex;
    gap: 0.6rem;
    align-items: center;
    flex-wrap: wrap;
  }
  button {
    min-width: 5rem;
    font-family: var(--mono);
    font-size: 0.85rem;
  }
  button.active {
    border-color: var(--accent);
    background: var(--bg-card-2);
  }
  .status {
    font-family: var(--mono);
    font-size: 0.85rem;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
  }
  .status.ok  { color: var(--green); }
  .status.err { color: var(--red); }
</style>
