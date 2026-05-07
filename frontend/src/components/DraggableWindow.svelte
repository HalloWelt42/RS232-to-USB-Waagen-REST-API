<script lang="ts">
  /**
   * Frei verschiebbares Fenster für Hilfe-Inhalte.
   *
   * - Maus oder Touch zieht am Header.
   * - Position wird pro ID im localStorage gemerkt (über helpStore).
   * - Klick irgendwo bringt das Fenster nach vorne.
   * - Esc oder Schließen-Knopf schließt das Fenster.
   */
  import { helpStore } from '../lib/helpStore.svelte';
  import type { HelpId } from '../lib/help';

  interface Props {
    id: HelpId;
    title: string;
    x: number;
    y: number;
    z: number;
    children?: import('svelte').Snippet;
  }

  let { id, title, x, y, z, children }: Props = $props();

  let dragOffset: { x: number; y: number } | null = null;
  let element: HTMLDivElement | undefined = $state();

  function startDrag(ev: PointerEvent): void {
    if (!element) return;
    helpStore.bringToFront(id);
    const rect = element.getBoundingClientRect();
    dragOffset = { x: ev.clientX - rect.left, y: ev.clientY - rect.top };
    (ev.target as HTMLElement).setPointerCapture(ev.pointerId);
    ev.preventDefault();
  }

  function moveDrag(ev: PointerEvent): void {
    if (!dragOffset) return;
    const newX = clamp(ev.clientX - dragOffset.x, 0, window.innerWidth  - 80);
    const newY = clamp(ev.clientY - dragOffset.y, 0, window.innerHeight - 50);
    helpStore.setPosition(id, newX, newY);
  }

  function endDrag(ev: PointerEvent): void {
    if (!dragOffset) return;
    dragOffset = null;
    (ev.target as HTMLElement).releasePointerCapture(ev.pointerId);
  }

  function clamp(v: number, lo: number, hi: number): number {
    return Math.max(lo, Math.min(hi, v));
  }

  function close(): void {
    helpStore.close(id);
  }

  function onKeydown(ev: KeyboardEvent): void {
    if (ev.key === 'Escape') close();
  }

  function bringForward(): void {
    helpStore.bringToFront(id);
  }
</script>

<svelte:window onkeydown={onKeydown} />

<div
  bind:this={element}
  class="window"
  style="left: {x}px; top: {y}px; z-index: {z};"
  role="dialog"
  aria-labelledby="help-title-{id}"
  onpointerdown={bringForward}
>
  <header
    onpointerdown={startDrag}
    onpointermove={moveDrag}
    onpointerup={endDrag}
    onpointercancel={endDrag}
  >
    <span class="grip" aria-hidden="true">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <circle cx="9"  cy="6"  r="0.5" />
        <circle cx="15" cy="6"  r="0.5" />
        <circle cx="9"  cy="12" r="0.5" />
        <circle cx="15" cy="12" r="0.5" />
        <circle cx="9"  cy="18" r="0.5" />
        <circle cx="15" cy="18" r="0.5" />
      </svg>
    </span>
    <h2 id="help-title-{id}">{title}</h2>
    <button class="close-btn" onclick={close} aria-label="Hilfe schließen" title="Schließen (Esc)">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <line x1="6" y1="6" x2="18" y2="18" />
        <line x1="18" y1="6" x2="6" y2="18" />
      </svg>
    </button>
  </header>
  <div class="body">
    {@render children?.()}
  </div>
</div>

<style>
  .window {
    position: fixed;
    width: 420px;
    max-width: calc(100vw - 32px);
    max-height: calc(100vh - 60px);
    background: var(--bg-elev);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    /* goldener Schnitt: Window-Verhältnis Höhe:Breite ~ 1:φ */
  }
  header {
    display: flex;
    align-items: center;
    gap: var(--sp-2);
    padding: var(--sp-2) var(--sp-3);
    background: var(--bg-card);
    border-bottom: 1px solid var(--border);
    cursor: grab;
    user-select: none;
    flex: 0 0 auto;
  }
  header:active { cursor: grabbing; }
  .grip {
    color: var(--fg-mute);
    flex: 0 0 auto;
    display: inline-flex;
  }
  h2 {
    margin: 0;
    flex: 1 1 auto;
    font-size: var(--fs-md);
    font-weight: 600;
  }
  .close-btn {
    flex: 0 0 auto;
    padding: 4px;
    color: var(--fg-dim);
    background: transparent;
    border: none;
    border-radius: var(--radius-sm);
  }
  .close-btn:hover { color: var(--red); background: var(--bg-card-2); }
  .body {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    padding: var(--sp-3) var(--sp-4);
    line-height: 1.55;
    font-size: var(--fs-sm);
  }
</style>
