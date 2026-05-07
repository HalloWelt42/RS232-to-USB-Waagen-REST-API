<script lang="ts">
  /**
   * Stabile Display-Anzeige für Wägewerte.
   *
   * Zeigt den Wert mit fester Stellen-Zahl (abgeleitet aus dem aktiven
   * Modell), führende Nullen werden als Ghost dargestellt — visuell
   * abgeschwächt mit 10 % Opazität. Damit bleibt die Position der
   * Ziffern stabil, das Auge muss nicht zwischen Frames neu fokussieren.
   *
   * Verwendung:
   *   <StableValue g={live.reading?.weight_g} />
   *
   * Optional kann ein eigenes Modell mitgegeben werden, sonst wird das
   * aktive Modell aus dem modelStore genutzt.
   */
  import { modelStore } from '../lib/modelStore.svelte';
  import { buildStableSegments, type DisplaySegment } from '../lib/format';
  import { i18n } from '../lib/i18n';

  interface Props {
    g: number | null | undefined;
    model?: { max_g: number; resolution_g: number } | null;
  }
  let { g, model = null }: Props = $props();

  // Reaktive Abhängigkeiten:
  //  - der Wert g
  //  - das aktive Modell (max_g, resolution_g)
  //  - die aktuelle Locale (für Tausender/Dezimal)
  let active = $derived(model ?? modelStore.active);
  let _ = $derived(i18n.current);   // i18n-Locale tracken
  let segments = $derived<DisplaySegment[]>(
    // Zugriff auf _ erzwingt Re-Compute bei Sprachwechsel
    (_ as unknown as null, buildStableSegments(g, active))
  );
</script>

<span class="stable-value num" aria-label={String(g ?? '')}>
  {#each segments as seg, i (i + ':' + seg.text)}
    <span class="seg seg-{seg.kind}" class:ghost={seg.ghost}>{seg.text}</span>
  {/each}
</span>

<style>
  /* Display-Simulation: echte Mono-Schrift mit gleichbreiten Ziffern,
     damit die Stellen-Position pixelgenau steht und die Anzeige nicht
     zappelt. Wird nur in dieser Komponente verwendet. */
  .stable-value {
    display: inline-flex;
    align-items: baseline;
    font-family: var(--mono-display);
    font-weight: 700;
    font-variant-numeric: tabular-nums lining-nums slashed-zero;
    font-feature-settings: 'tnum' 1, 'lnum' 1, 'zero' 1;
    letter-spacing: 0;
    /* Im Container nicht über die Breite schlagen */
    max-width: 100%;
  }
  /* JetBrains Mono ist bereits monospaced — keine zusätzlichen
     min-widths nötig, dadurch passt auch ein langes
     „-30.000,0 g" auf eine 280-px-Sidebar. */
  .seg { display: inline-block; }
  .seg-sign { padding-right: 0.05em; }
  .seg-unit { padding-left: 0.35em; }
  .ghost { opacity: 0.1; }       /* 90 % transparent */
</style>
