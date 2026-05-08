<script lang="ts">
  /**
   * Visueller FontAwesome-Icon-Picker mit Suche und Klick-Auswahl.
   *
   * Wird in CountPanel beim Anlegen/Bearbeiten einer Stückzähl-Vorlage
   * benutzt, kann aber jeder Stelle im Frontend gegeben werden, die
   * eine FA-Klasse braucht. Die kuratierte Icon-Liste liegt in
   * `lib/icons.ts` (~80 Einträge mit DE/EN-Suchbegriffen) — der
   * Anwender muss nichts tippen, kann aber im Bedarfsfall ein
   * eigenes Klassen-String per „Erweitert" einklappen.
   *
   * Props:
   *   value      — aktuell gewählte FA-Klasse (z.B. „fa-solid fa-cube")
   *   onPick(c)  — Callback, wenn der Anwender ein Icon wählt
   */
  import { ICONS, filterIcons } from '../lib/icons';
  import { t } from '../lib/i18n';

  interface Props {
    value: string;
    onPick: (cls: string) => void;
  }

  let { value, onPick }: Props = $props();

  let query = $state('');
  let advancedOpen = $state(false);
  // customText spiegelt initial den aktuellen `value`-Prop wider und
  // bleibt unabhängig editierbar. Bei externem Wert-Wechsel (z.B. wenn
  // ein anderes Template ediert wird) zieht der $effect das Feld mit.
  let customText = $state('');
  $effect(() => { customText = value; });

  let visible = $derived(filterIcons(query));

  function pick(cls: string): void {
    onPick(cls);
  }

  function applyCustom(): void {
    const trimmed = customText.trim();
    if (trimmed) onPick(trimmed);
  }
</script>

<div class="picker">
  <!-- Suchfeld + sichtbarer aktueller Wert -->
  <div class="search-row">
    <input
      type="search"
      placeholder={t('iconPicker.searchPlaceholder')}
      bind:value={query}
      autocomplete="off"
      spellcheck="false"
    />
    <span class="current" title={value}>
      <i class={value} aria-hidden="true"></i>
    </span>
  </div>

  <!-- Icon-Grid -->
  {#if visible.length === 0}
    <p class="empty">{t('iconPicker.noResults')}</p>
  {:else}
    <div class="grid" role="listbox">
      {#each visible as icon (icon.cls)}
        <button
          type="button"
          class="cell"
          class:active={icon.cls === value}
          onclick={() => pick(icon.cls)}
          title={icon.label}
          aria-label={icon.label}
        >
          <i class={icon.cls} aria-hidden="true"></i>
        </button>
      {/each}
    </div>
  {/if}

  <!-- Erweitert-Bereich: manueller Klassen-String als Fallback -->
  <div class="advanced">
    <button
      type="button"
      class="advanced-toggle"
      onclick={() => (advancedOpen = !advancedOpen)}
    >
      <i class="fa-solid fa-chevron-{advancedOpen ? 'down' : 'right'}" aria-hidden="true"></i>
      {t('iconPicker.advanced')}
    </button>
    {#if advancedOpen}
      <div class="advanced-form">
        <p class="hint">{t('iconPicker.advancedHint')}</p>
        <div class="advanced-row">
          <input
            type="text"
            bind:value={customText}
            placeholder="fa-solid fa-cube"
            maxlength="120"
            spellcheck="false"
          />
          <button type="button" class="apply" onclick={applyCustom}>
            {t('iconPicker.apply')}
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .picker {
    display: flex; flex-direction: column;
    gap: var(--sp-2);
    width: 100%;
  }
  .search-row {
    display: flex; gap: var(--sp-2);
    align-items: stretch;
  }
  .search-row input {
    flex: 1;
    min-width: 0;
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 8px 11px;
    min-height: var(--tap);
    font-family: var(--sans);
    font-size: var(--fs-sm);
  }
  .search-row input:focus { outline: none; border-color: var(--accent); }
  .current {
    flex: 0 0 auto;
    width: var(--tap); min-height: var(--tap);
    display: inline-flex; align-items: center; justify-content: center;
    border: 1px solid var(--accent);
    border-radius: var(--radius-sm);
    background: color-mix(in srgb, var(--accent) 12%, transparent);
    color: var(--accent);
    font-size: 18px;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(44px, 1fr));
    gap: 4px;
    max-height: 220px;
    overflow-y: auto;
    padding: 6px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
  }
  .cell {
    aspect-ratio: 1 / 1;
    background: var(--bg-card-2);
    border: 1px solid transparent;
    color: var(--fg-dim);
    border-radius: var(--radius-sm);
    cursor: pointer;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 17px;
    transition: background 0.1s, color 0.1s, border-color 0.1s;
  }
  .cell:hover {
    background: var(--bg-elev);
    color: var(--accent);
    border-color: var(--accent);
  }
  .cell.active {
    background: color-mix(in srgb, var(--accent) 18%, transparent);
    color: var(--accent);
    border-color: var(--accent);
  }
  .empty {
    margin: 0; padding: var(--sp-3);
    text-align: center;
    color: var(--fg-mute);
    font-size: var(--fs-sm);
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
  }

  .advanced {
    display: flex; flex-direction: column;
    gap: var(--sp-1);
  }
  .advanced-toggle {
    align-self: flex-start;
    background: transparent; border: none;
    color: var(--fg-mute);
    font-size: var(--fs-xs);
    letter-spacing: 0.05em; text-transform: uppercase;
    cursor: pointer;
    padding: 4px 0;
    display: inline-flex; align-items: center; gap: 6px;
  }
  .advanced-toggle:hover { color: var(--accent); }
  .advanced-form {
    display: flex; flex-direction: column;
    gap: var(--sp-2);
    padding: var(--sp-2);
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
  }
  .advanced-form .hint {
    margin: 0; font-size: var(--fs-xs); color: var(--fg-mute);
  }
  .advanced-row {
    display: flex; gap: var(--sp-2);
  }
  .advanced-row input {
    flex: 1; min-width: 0;
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 6px 10px;
    color: var(--fg);
    font-family: var(--num);
    font-size: var(--fs-sm);
  }
  .apply {
    flex: 0 0 auto;
    background: transparent;
    border: 1px solid var(--accent);
    color: var(--accent);
    border-radius: var(--radius-sm);
    padding: 0 var(--sp-3);
    cursor: pointer;
    font-size: var(--fs-sm);
  }
  .apply:hover {
    background: color-mix(in srgb, var(--accent) 12%, transparent);
  }
</style>
