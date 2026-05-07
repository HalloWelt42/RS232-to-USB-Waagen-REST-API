<script lang="ts">
  /**
   * Hilfe-Übersicht. Listet alle Hilfe-Inhalte und öffnet sie als
   * verschiebbare/größenveränderbare Fenster.
   *
   * Öffnen läuft über `route.openHelp()`, nicht direkt über den
   * helpStore — sonst würde der zentrale URL→Store-Sync-Effekt in
   * App.svelte das Fenster im nächsten Tick wieder schließen, weil
   * der URL-Querystring `?help=…` leer wäre.
   */
  import { getHelpEntries, type HelpId } from '../../lib/help';
  import { route } from '../../lib/routing.svelte';
  import { i18n, t } from '../../lib/i18n';

  // Lokal-spezifische Hilfe-Bäume — Titel und Vorschau-Texte folgen
  // der aktuellen Sprache.
  let entries = $derived(getHelpEntries(i18n.current));

  function open(id: HelpId): void {
    route.openHelp(id);
  }

  // Stabile Reihenfolge für die Anzeige
  const sections: readonly HelpId[] = [
    'overview', 'glossary', 'wiegen', 'netto', 'count', 'tolerance',
    'samples', 'differenz', 'containers', 'history', 'tolerances',
    'tare', 'unit', 'light', 'copy', 'settings', 'donate',
    'architecture', 'disclaimer',
  ] as const;

  function previewOf(id: HelpId): string {
    const e = entries[id];
    if (!e || e.blocks.length === 0) return '';
    return e.blocks[0].body.replace(/\[\[[^\]]+\]\]/g, '')   // Cross-Links entfernen
                            .replace(/<[^>]+>/g, '')          // HTML entfernen
                            .replace(/\{\{[^}]+\}\}/g, '…')   // Platzhalter
                            .slice(0, 120) + '…';
  }
</script>

<section class="panel">
  <header>
    <h2>{t('tools.help')}</h2>
  </header>

  <p class="intro">{t('helpPanel.intro')}</p>

  <div class="grid">
    {#each sections as id (id)}
      {@const entry = entries[id]}
      {#if entry}
        <!-- Innerhalb des <button> nur Phrasing-Content: <h3>/<p>
             wären Flow-Content und damit per HTML-Spec verboten.
             Stattdessen <span class="title|preview"> mit display:block. -->
        <button class="card" onclick={() => open(id)}>
          <span class="title">{entry.title}</span>
          <span class="preview">{previewOf(id)}</span>
          <span class="open-hint">
            <i class="fa-solid fa-up-right-from-square"></i>
            {t('helpPanel.open')}
          </span>
        </button>
      {/if}
    {/each}
  </div>
</section>

<style>
  .panel {
    flex: 1 1 auto; min-height: 0; overflow-y: auto;
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  header h2 { margin: 0; font-size: var(--fs-xl); font-weight: 600; }
  .intro {
    max-width: 720px; color: var(--fg-dim);
    font-size: 18px;       /* Hilfe-Texte mind. 18 px */
    line-height: 1.6;
    margin: 0;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(260px, 100%), 1fr));
    gap: var(--sp-3);
  }
  .card {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-3) var(--sp-4);
    color: var(--fg);
    text-align: left;
    cursor: pointer;
    display: flex; flex-direction: column;
    gap: var(--sp-2);
    transition: border-color 0.15s, transform 0.15s;
  }
  .card:hover { border-color: var(--accent); transform: translateY(-2px); }
  .card .title {
    display: block;
    font-size: var(--fs-md);
    color: var(--accent);
    letter-spacing: 0.02em;
  }
  .card .preview {
    display: block;
    font-size: var(--fs-sm);
    color: var(--fg-dim);
    line-height: 1.5;
  }
  .open-hint {
    font-size: var(--fs-xs);
    color: var(--fg-mute);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    display: inline-flex; align-items: center; gap: 4px;
  }
</style>
