<script lang="ts">
  /**
   * Frei verschieb- und in der Größe veränderbares Hilfe-Fenster.
   *
   * - Verschieben: Mausziehen am Header oder am Grip-Symbol.
   * - Größe ändern: native CSS-resize unten rechts (resize: both).
   * - Position und Maße landen in helpStore und damit im localStorage.
   * - Klick irgendwo im Fenster bringt es nach vorn.
   * - Pinch/Touch wird unterstützt (Pointer Events).
   */
  import { helpStore } from '../lib/helpStore.svelte';
  import { route } from '../lib/routing.svelte';
  import type { HelpId } from '../lib/help';
  import type { Snippet } from 'svelte';

  interface Props {
    id: HelpId;
    title: string;
    x: number; y: number;
    w: number; h: number;
    z: number;
    children: Snippet;
  }

  let { id, title, x, y, w, h, z, children }: Props = $props();

  let win: HTMLDivElement | null = $state(null);
  let dragging = false;
  let startX = 0; let startY = 0;
  let originX = 0; let originY = 0;

  let curX = $state(0);
  let curY = $state(0);
  let curW = $state(0);
  let curH = $state(0);

  // Externer Geometrie-Sync — auch beim ersten Mounten
  $effect(() => { curX = x; curY = y; curW = w; curH = h; });

  /**
   * Lokales Begrenzen während des Ziehens — der helpStore wendet
   * beim Speichern noch einmal eine konsistente Clamping-Regel an,
   * sodass das Fenster bei späteren Sessions garantiert wieder im
   * sichtbaren Bereich erscheint.
   */
  function clamp(): void {
    const PAD = 8;
    const maxX = Math.max(PAD, window.innerWidth  - curW - PAD);
    const maxY = Math.max(PAD, window.innerHeight - curH - PAD);
    if (curX < PAD) curX = PAD;
    if (curY < PAD) curY = PAD;
    if (curX > maxX) curX = maxX;
    if (curY > maxY) curY = maxY;
  }

  function onPointerDownHeader(ev: PointerEvent): void {
    if (!win) return;
    helpStore.bringToFront(id);
    dragging = true;
    startX = ev.clientX; startY = ev.clientY;
    originX = curX; originY = curY;
    (ev.target as Element).setPointerCapture?.(ev.pointerId);
    ev.preventDefault();
  }

  function onPointerMove(ev: PointerEvent): void {
    if (!dragging) return;
    curX = originX + (ev.clientX - startX);
    curY = originY + (ev.clientY - startY);
    clamp();
  }

  function onPointerUp(): void {
    if (!dragging) return;
    dragging = false;
    helpStore.setGeometry(id, curX, curY, curW, curH);
  }

  function onContainerPointerDown(): void {
    helpStore.bringToFront(id);
  }

  function onResizeEnd(): void {
    if (!win) return;
    const rect = win.getBoundingClientRect();
    curW = Math.round(rect.width);
    curH = Math.round(rect.height);
    helpStore.setGeometry(id, curX, curY, curW, curH);
  }

  function close(): void {
    // Über die Route schließen — die URL bleibt damit konsistent.
    route.closeHelp(id);
  }

  $effect(() => {
    const onResize = (): void => clamp();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  });
</script>

<svelte:window onpointermove={onPointerMove} onpointerup={onPointerUp} />

<div bind:this={win}
     class="window"
     style:left="{curX}px"
     style:top="{curY}px"
     style:width="{curW}px"
     style:height="{curH}px"
     style:z-index={z}
     onpointerdowncapture={onContainerPointerDown}
     role="dialog" aria-label={title}>
  <header class="grip" onpointerdown={onPointerDownHeader} role="presentation">
    <span class="grip-icon"><i class="fa-solid fa-grip-vertical"></i></span>
    <h3>{title}</h3>
    <button class="close" onclick={close}
            title="Hilfe-Fenster schließen" aria-label="Schließen">
      <i class="fa-regular fa-circle-xmark"></i>
    </button>
  </header>

  <div class="body" onpointerup={onResizeEnd} role="document">
    {@render children()}
  </div>
</div>

<style>
  .window {
    position: fixed;
    background: var(--bg-elev);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius);
    box-shadow: var(--shadow-lg);
    display: flex; flex-direction: column;
    min-width: 280px; min-height: 200px;
    max-width: calc(100vw - 16px);
    max-height: calc(100vh - 16px);
    overflow: hidden;
    resize: both;        /* native Größenänderung unten rechts */
  }
  /* Vollbild-Hilfe auf Smartphones: das schwebende Mini-Fenster mit
     Verschieben/Resize ist auf 380-px-Bildschirmen unbrauchbar. Wir
     ignorieren die gespeicherte Geometrie und decken den ganzen
     Viewport ab — Hilfetexte bleiben so lesbar groß. */
  @media (max-width: 900px) {
    .window {
      left: 0 !important;
      top: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      max-width: 100vw;
      max-height: 100vh;
      border-radius: 0;
      border: none;
      resize: none;
    }
    .grip { cursor: default; }
  }
  .grip {
    flex: 0 0 auto;
    height: 36px;
    padding: 0 12px;
    display: flex; align-items: center; gap: 10px;
    background: var(--bg-card);
    border-bottom: 1px solid var(--border);
    cursor: grab;
    user-select: none;
    touch-action: none;
  }
  .grip:active { cursor: grabbing; }
  .grip-icon {
    color: var(--fg-mute);
    font-size: 14px;
  }
  .grip h3 {
    margin: 0;
    font-size: var(--fs-md);
    font-weight: 600;
    flex: 1;
    color: var(--fg);
    letter-spacing: 0.01em;
  }
  .close {
    height: 28px; width: 28px;
    background: transparent;
    border: none;
    color: var(--fg-dim);
    border-radius: var(--radius-sm);
    display: inline-flex; align-items: center; justify-content: center;
    cursor: pointer;
    font-size: 18px;
    padding: 0;
  }
  .close:hover { color: var(--red); background: transparent; }
  .body {
    flex: 1 1 auto;
    overflow: auto;
    padding: var(--sp-4);
    font-size: 18px;       /* Anwender-Vorgabe: Hilfe-Texte mind. 18 px */
    line-height: 1.6;
    color: var(--fg);
  }
  .body :global(h4) {
    margin: 0 0 var(--sp-2);
    font-size: 18px;
    font-weight: 600;
    color: var(--accent);
    letter-spacing: 0.02em;
  }
  .body :global(p) {
    margin: 0 0 var(--sp-3);
  }
  .body :global(strong) {
    font-family: var(--num);
    font-variant-numeric: tabular-nums lining-nums slashed-zero;
    font-weight: 700;
    color: var(--fg);
  }
  .body :global(.block) {
    margin-bottom: var(--sp-4);
    padding-bottom: var(--sp-3);
    border-bottom: 1px solid var(--border);
  }
  .body :global(.block:last-child) {
    border-bottom: none;
    padding-bottom: 0;
    margin-bottom: 0;
  }
</style>
