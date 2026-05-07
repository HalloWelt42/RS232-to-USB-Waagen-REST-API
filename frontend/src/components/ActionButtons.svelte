<script lang="ts">
  import { api } from '../lib/api';

  type CommandKey = 'tare' | 'unit' | 'light';

  let busy = $state<CommandKey | null>(null);
  let lastResult = $state<string | null>(null);
  let errorMsg = $state<string | null>(null);

  async function runCommand(key: CommandKey, fn: () => Promise<unknown>, label: string) {
    if (busy) return;
    busy = key;
    errorMsg = null;
    lastResult = null;
    try {
      await fn();
      lastResult = label;
      window.setTimeout(() => {
        if (lastResult === label) lastResult = null;
      }, 1500);
    } catch (e) {
      errorMsg = (e as Error).message;
    } finally {
      busy = null;
    }
  }

  const tare  = () => runCommand('tare',  () => api.cmdTare(),  'Tara gesetzt');
  const unit  = () => runCommand('unit',  () => api.cmdUnit(),  'Einheit gewechselt');
  const light = () => runCommand('light', () => api.cmdLight(), 'Licht umgeschaltet');
</script>

<div class="actions">
  <button onclick={tare}  disabled={busy !== null} class:active={busy === 'tare'}>Tara</button>
  <button onclick={unit}  disabled={busy !== null} class:active={busy === 'unit'}>Einheit</button>
  <button onclick={light} disabled={busy !== null} class:active={busy === 'light'}>Licht</button>
  {#if lastResult}<span class="status ok">{lastResult}</span>
  {:else if errorMsg}<span class="status err">{errorMsg}</span>{/if}
</div>

<style>
  .actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  button {
    min-width: 4.5rem;
    font-family: var(--mono);
    font-size: 0.8rem;
    padding: 0.35rem 0.7rem;
  }
  button.active {
    border-color: var(--accent);
    background: var(--bg-card-2);
  }
  .status {
    font-family: var(--mono);
    font-size: 0.78rem;
    margin-left: 0.5rem;
  }
  .status.ok  { color: var(--green); }
  .status.err { color: var(--red); }
</style>
