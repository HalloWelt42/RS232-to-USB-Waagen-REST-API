<script lang="ts">
  /**
   * Container für alle offenen Hilfe-Fenster.
   *
   * Texte werden zur Laufzeit aufgelöst:
   *  - Platzhalter wie {{modelName}}/{{maxG}} aus dem Modell-Store
   *  - Cross-Links [[tool:...]] / [[help:...]] zu Buttons mit
   *    `data-route-*` Attributen
   *
   * Klicks auf die Cross-Link-Buttons werden hier abgefangen und an
   * den `route`-Store weitergeleitet — das hält die App PWA-konform,
   * kein Page-Reload, keine externe Navigation.
   */
  import { helpStore } from '../lib/helpStore.svelte';
  import { getHelpEntries } from '../lib/help';
  import { buildHelpVars, renderHelpBody } from '../lib/helpRender';
  import { i18n } from '../lib/i18n';
  import { modelStore } from '../lib/modelStore.svelte';
  import { route } from '../lib/routing.svelte';
  import type { HelpId, HelpBlock } from '../lib/help';
  import type { ToolKey } from '../lib/routing.svelte';
  import DraggableWindow from './DraggableWindow.svelte';

  let entries = $derived(getHelpEntries(i18n.current));
  let vars = $derived(buildHelpVars(modelStore.active));

  function renderedHeading(s: string): string {
    return renderHelpBody(s, vars);
  }
  function renderedBody(s: string): string {
    return renderHelpBody(s, vars);
  }

  // PWA-konformer Cross-Link-Handler: fängt Klicks auf .xlink-Buttons
  // ab und navigiert via route. Kein href, kein Reload.
  function onContainerClick(ev: MouseEvent): void {
    const t = ev.target as HTMLElement | null;
    if (!t) return;
    const btn = t.closest('button.xlink') as HTMLButtonElement | null;
    if (!btn) return;
    ev.preventDefault();
    const tool = btn.dataset.routeTool;
    const help = btn.dataset.routeHelp;
    if (tool) {
      route.go(tool as ToolKey);
    } else if (help) {
      route.openHelp(help as HelpId);
    }
  }
</script>

<div class="help-layer" onclick={onContainerClick} role="presentation">
  {#each helpStore.windows as w (w.id)}
    {@const entry = entries[w.id]}
    <DraggableWindow id={w.id} title={entry.title}
                     x={w.x} y={w.y} w={w.w} h={w.h} z={w.z}>
      {#each entry.blocks as b (b.heading)}
        {@const block = b as HelpBlock}
        <section class="block">
          <h4>{@html renderedHeading(block.heading)}</h4>
          <p>{@html renderedBody(block.body)}</p>
        </section>
      {/each}
    </DraggableWindow>
  {/each}
</div>

<style>
  .help-layer { display: contents; }
  /* Cross-Link-Buttons als Inline-Tags im Hilfe-Text */
  .help-layer :global(button.xlink) {
    background: transparent;
    border: none;
    padding: 0 2px;
    cursor: pointer;
    font: inherit;
    text-decoration: underline;
    text-underline-offset: 2px;
    border-radius: 0;
  }
  .help-layer :global(button.xlink-tool) { color: var(--accent); }
  .help-layer :global(button.xlink-tool:hover) {
    color: var(--accent-strong);
    text-decoration-thickness: 2px;
  }
  .help-layer :global(button.xlink-help) { color: var(--info-blue); }
  .help-layer :global(button.xlink-help:hover) {
    color: var(--info-blue-hover);
    text-decoration-thickness: 2px;
  }
</style>
