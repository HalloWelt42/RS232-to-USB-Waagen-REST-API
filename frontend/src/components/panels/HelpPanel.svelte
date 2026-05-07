<script lang="ts">
  /**
   * Hilfe-Übersicht. Listet alle Hilfe-Inhalte und öffnet sie als
   * verschiebbare/größenveränderbare Fenster über den helpStore.
   */
  import { helpEntries } from '../../lib/help';
  import { helpStore } from '../../lib/helpStore.svelte';
  import { t } from '../../lib/i18n';

  function open(id: keyof typeof helpEntries): void {
    helpStore.open(id);
  }

  // Stabile Reihenfolge für die Anzeige
  const sections: ReadonlyArray<keyof typeof helpEntries> = [
    'overview', 'glossary', 'wiegen', 'netto', 'count', 'tolerance',
    'samples', 'differenz', 'containers', 'history', 'tare', 'unit',
    'light', 'copy', 'settings', 'donate', 'architecture', 'disclaimer',
  ] as const;
</script>

<section class="panel">
  <header>
    <h2>{t('tools.help')}</h2>
  </header>

  <p class="intro">
    Klicken Sie auf einen Eintrag — die Hilfe öffnet sich in einem Fenster, das
    sich frei verschieben und in der Größe verändern lässt. Mehrere Fenster
    können gleichzeitig offen sein.
  </p>

  <div class="grid">
    {#each sections as id}
      {@const entry = helpEntries[id]}
      <button class="card" onclick={() => open(id)}>
        <h3>{entry.title}</h3>
        <p>{entry.blocks[0].body.replace(/<[^>]+>/g, '').slice(0, 110)}…</p>
        <span class="open-hint">
          <i class="fa-solid fa-up-right-from-square"></i>
          Öffnen
        </span>
      </button>
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
  .card h3 {
    margin: 0;
    font-size: var(--fs-md);
    color: var(--accent);
    letter-spacing: 0.02em;
  }
  .card p {
    margin: 0;
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
