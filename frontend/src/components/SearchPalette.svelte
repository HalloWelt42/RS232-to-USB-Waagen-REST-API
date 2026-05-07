<script lang="ts">
  /**
   * Globale Suchpalette. Öffnet mit Klick auf das Lupen-Symbol in
   * der Topbar oder per Tastenkombination Cmd/Ctrl+K. Sucht über
   * alle Hilfe-Inhalte, Glossar-Einträge und Werkzeuge — Treffer
   * werden gruppiert angezeigt.
   *
   * Tastatur:
   *   ↑/↓   in der Trefferliste navigieren
   *   Enter Treffer öffnen
   *   Esc   Palette schließen
   */
  import { searchStore } from '../lib/searchStore.svelte';
  import { route } from '../lib/routing.svelte';
  import { t } from '../lib/i18n';
  import type { SearchResult } from '../lib/search';

  let inputEl: HTMLInputElement | null = $state(null);

  // Beim Öffnen Fokus setzen
  $effect(() => {
    if (searchStore.open && inputEl) {
      window.setTimeout(() => inputEl?.focus(), 0);
    }
  });

  // Globale Tastatur-Handler — Cmd/Ctrl+K öffnet/schließt
  $effect(() => {
    function onKey(e: KeyboardEvent): void {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        searchStore.toggle();
      } else if (e.key === 'Escape' && searchStore.open) {
        searchStore.hide();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  function onListKey(e: KeyboardEvent): void {
    if (e.key === 'ArrowDown') { e.preventDefault(); searchStore.next(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); searchStore.prev(); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      const r = searchStore.results[searchStore.highlight];
      if (r) open(r);
    }
  }

  function open(r: SearchResult): void {
    if (r.action.kind === 'tool') {
      route.go(r.action.tool);
    } else {
      route.openHelp(r.action.help);
    }
    searchStore.hide();
  }

  function kindLabel(kind: SearchResult['kind']): string {
    if (kind === 'tool') return t('search.hintTool');
    if (kind === 'help') return t('search.hintHelp');
    return t('search.hintTerm');
  }

  function kindIcon(kind: SearchResult['kind']): string {
    if (kind === 'tool') return 'fa-solid fa-screwdriver-wrench';
    if (kind === 'help') return 'fa-solid fa-circle-info';
    return 'fa-solid fa-book';
  }
</script>

{#if searchStore.open}
  <div class="backdrop"
       onclick={() => searchStore.hide()}
       role="presentation"></div>
  <div class="palette" role="dialog" aria-label={t('topbar.search')}
       tabindex="-1" onkeydown={onListKey}>
    <div class="input-row">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input bind:this={inputEl}
             type="search" autocomplete="off" spellcheck="false"
             placeholder={t('search.placeholder')}
             bind:value={searchStore.query} />
      <button class="hint-btn" onclick={() => searchStore.hide()}
              aria-label={t('general.close')} title={t('general.close')}>
        <i class="fa-regular fa-circle-xmark"></i>
      </button>
    </div>

    <ul class="results">
      {#if searchStore.query.trim().length === 0}
        <li class="hint">{t('search.keys')}</li>
      {:else if searchStore.results.length === 0}
        <li class="hint empty">{t('search.noResults')}</li>
      {:else}
        {#each searchStore.results as r, i (r.kind + r.ref)}
          <li class="row" class:active={i === searchStore.highlight}>
            <button onclick={() => open(r)}
                    onmouseenter={() => searchStore.setHighlight(i)}>
              <span class="kind kind-{r.kind}">
                <i class={kindIcon(r.kind)} aria-hidden="true"></i>
                {kindLabel(r.kind)}
              </span>
              <span class="title">{r.title}</span>
              <span class="snippet">{r.snippet}</span>
            </button>
          </li>
        {/each}
      {/if}
    </ul>

    <div class="footer">
      <span>{t('search.keys')}</span>
    </div>
  </div>
{/if}

<style>
  .backdrop {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.4);
    z-index: 400;
  }
  .palette {
    position: fixed;
    top: 12vh;
    left: 50%;
    transform: translateX(-50%);
    width: min(640px, calc(100vw - 32px));
    max-height: 70vh;
    background: var(--bg-elev);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius);
    box-shadow: var(--shadow-lg);
    display: flex; flex-direction: column;
    overflow: hidden;
    z-index: 401;
  }
  .input-row {
    display: flex; align-items: center;
    gap: 10px;
    padding: var(--sp-3);
    border-bottom: 1px solid var(--border);
    background: var(--bg-card);
  }
  .input-row > i { color: var(--fg-mute); font-size: 18px; }
  .input-row input {
    flex: 1;
    border: none; background: transparent;
    color: var(--fg);
    font-family: var(--sans);
    font-size: var(--fs-md);
    outline: none;
    padding: 4px 0;
    min-height: 32px;
  }
  .hint-btn {
    background: transparent; border: none;
    color: var(--fg-mute);
    cursor: pointer;
    font-size: 18px;
    padding: 0;
  }
  .hint-btn:hover { color: var(--red); }

  .results {
    list-style: none; margin: 0; padding: 4px 0;
    overflow-y: auto;
    flex: 1 1 auto;
  }
  .row { display: block; }
  .row button {
    width: 100%;
    background: transparent;
    border: none;
    text-align: left;
    padding: 10px var(--sp-3);
    cursor: pointer;
    color: var(--fg);
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 4px var(--sp-2);
    align-items: baseline;
  }
  .row.active button { background: color-mix(in srgb, var(--accent) 12%, transparent); }
  .row button:hover { background: var(--bg-card-2); }
  .kind {
    grid-row: 1 / 2;
    font-size: var(--fs-xs);
    color: var(--fg-mute);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    display: inline-flex; align-items: center; gap: 4px;
    width: 96px;
  }
  .kind-tool i { color: var(--accent); }
  .kind-help i { color: var(--info-blue); }
  .kind-term i { color: var(--fg-dim); }
  .title {
    grid-row: 1 / 2;
    font-size: var(--fs-md);
    font-weight: 600;
    color: var(--fg);
  }
  .snippet {
    grid-column: 2 / 3;
    grid-row: 2 / 3;
    font-size: var(--fs-sm);
    color: var(--fg-dim);
    line-height: 1.5;
  }
  .hint {
    padding: var(--sp-3);
    color: var(--fg-mute);
    font-size: var(--fs-sm);
  }
  .hint.empty { text-align: center; color: var(--fg-dim); }

  .footer {
    border-top: 1px solid var(--border);
    padding: 8px var(--sp-3);
    background: var(--bg-card);
    color: var(--fg-mute);
    font-size: var(--fs-xs);
    text-align: center;
  }
</style>
