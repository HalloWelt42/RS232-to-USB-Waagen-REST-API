<script lang="ts">
  import { api } from '../lib/api';
  import { helpStore } from '../lib/helpStore.svelte';
  import type { HelpId } from '../lib/help';

  type CommandKey = 'tare' | 'unit' | 'light';

  let busy = $state<CommandKey | null>(null);
  let lastResult = $state<string | null>(null);
  let errorMsg = $state<string | null>(null);

  async function runCommand(
    key: CommandKey,
    fn: () => Promise<unknown>,
    label: string,
  ): Promise<void> {
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

  function help(id: HelpId, ev: MouseEvent): void {
    ev.stopPropagation();
    helpStore.open(id);
  }
</script>

<div class="actions" role="toolbar" aria-label="Schnellaktionen">
  <div class="action-cell">
    <button
      onclick={() => void runCommand('tare', () => api.cmdTare(), 'Tara gesetzt')}
      disabled={busy !== null}
      class:active={busy === 'tare'}
      title="Anzeige der Waage auf Null setzen"
    >Tara</button>
    <button
      class="hint-btn"
      onclick={(e) => help('tare', e)}
      title="Hilfe zu Tara"
      aria-label="Hilfe zu Tara"
    >?</button>
  </div>
  <div class="action-cell">
    <button
      onclick={() => void runCommand('unit', () => api.cmdUnit(), 'Einheit gewechselt')}
      disabled={busy !== null}
      class:active={busy === 'unit'}
      title="Einheit an der Waage umschalten"
    >Einheit</button>
    <button
      class="hint-btn"
      onclick={(e) => help('unit', e)}
      title="Hilfe zur Einheit"
      aria-label="Hilfe zur Einheit"
    >?</button>
  </div>
  <div class="action-cell">
    <button
      onclick={() => void runCommand('light', () => api.cmdLight(), 'Licht umgeschaltet')}
      disabled={busy !== null}
      class:active={busy === 'light'}
      title="Display-Beleuchtung umschalten"
    >Licht</button>
    <button
      class="hint-btn"
      onclick={(e) => help('light', e)}
      title="Hilfe zur Beleuchtung"
      aria-label="Hilfe zur Beleuchtung"
    >?</button>
  </div>

  {#if lastResult}
    <span class="status ok">{lastResult}</span>
  {:else if errorMsg}
    <span class="status err">{errorMsg}</span>
  {/if}
</div>

<style>
  .actions {
    display: flex;
    gap: var(--sp-2);
    align-items: center;
  }
  .action-cell {
    display: inline-flex;
    align-items: center;
  }
  .action-cell > button:first-child {
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    border-right: none;
    min-width: 64px;
    font-family: var(--mono);
    font-size: var(--fs-xs);
    padding: 6px 12px;
  }
  .action-cell > button:first-child.active {
    border-color: var(--accent);
    background: var(--bg-card-2);
  }
  .hint-btn {
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
    padding: 6px 8px;
    font-family: var(--mono);
    font-size: var(--fs-xs);
    color: var(--fg-mute);
    width: 26px;
    line-height: 1;
  }
  .hint-btn:hover {
    color: var(--accent);
  }
  .status {
    font-family: var(--mono);
    font-size: var(--fs-xs);
    margin-left: var(--sp-2);
  }
  .status.ok  { color: var(--green); }
  .status.err { color: var(--red); }
</style>
