<script lang="ts">
  /**
   * Generischer SVG-Icon-Wrapper. Inhalt kommt als Slot, Größe und
   * Strichstärke konsistent. Keine Emojis — alle Icons sind reine
   * SVG-Pfade auf 24x24-Viewbox.
   */
  interface Props {
    size?: number;
    title?: string;
    children?: import('svelte').Snippet;
  }
  let { size = 16, title, children }: Props = $props();
</script>

<svg
  width={size} height={size}
  viewBox="0 0 24 24"
  fill="none"
  stroke="currentColor"
  stroke-width="1.7"
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-hidden={title ? undefined : 'true'}
  role={title ? 'img' : undefined}
>
  {#if title}<title>{title}</title>{/if}
  {@render children?.()}
</svg>
