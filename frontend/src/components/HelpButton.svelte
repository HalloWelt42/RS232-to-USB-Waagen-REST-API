<script lang="ts">
  /**
   * Kleiner Hilfe-Knopf, der das passende Hilfe-Fenster öffnet.
   *
   * Wird typischerweise im Header eines Panels platziert. Tooltip
   * benennt den Bereich, damit Tastatur-Anwender wissen, wozu der Knopf
   * gehört.
   */
  import { helpStore } from '../lib/helpStore.svelte';
  import type { HelpId } from '../lib/help';

  interface Props {
    id: HelpId;
    label?: string;
  }

  let { id, label = 'Hilfe öffnen' }: Props = $props();

  function open(): void {
    helpStore.open(id);
  }
</script>

<button
  class="help-btn"
  onclick={open}
  title={label}
  aria-label={label}
>
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="9" />
    <path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 1-1 1.7" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
</button>

<style>
  .help-btn {
    width: 26px;
    height: 26px;
    padding: 0;
    border-radius: 50%;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--fg-dim);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: color 0.15s, border-color 0.15s, background 0.15s;
  }
  .help-btn:hover {
    color: var(--accent);
    border-color: var(--accent);
    background: var(--bg-card-2);
  }
</style>
