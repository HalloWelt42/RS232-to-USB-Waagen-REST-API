<script lang="ts">
  /**
   * Sprach-Umschalter im Header.
   *
   * Bei zwei Sprachen ein direkter Wechsel-Klick, bei drei oder mehr
   * Sprachen ein kleines Dropdown-Menü direkt unter dem Knopf. Im
   * Knopf selbst sehen wir die landestypische Flagge plus Kürzel der
   * aktuell aktiven Sprache.
   *
   * Erweiterbar: neue Sprachen werden ausschließlich in
   * `lib/i18n.svelte.ts` (LANG_META + LANG_ORDER + LOCALES) plus
   * einer neuen Datei `locales/<code>.ts` registriert. Der Toggle
   * zeigt sie automatisch.
   */
  import { i18n, LANG_META, LANG_ORDER, type Lang } from '../lib/i18n';
  import { t } from '../lib/i18n';

  let menuOpen = $state(false);
  let host: HTMLElement | null = $state(null);

  let activeMeta = $derived(LANG_META[i18n.current]);
  let langs = $derived(LANG_ORDER.map(c => LANG_META[c]));

  function pick(code: Lang): void {
    i18n.set(code);
    menuOpen = false;
  }

  function toggle(): void {
    if (LANG_ORDER.length <= 2) {
      // Zwei Sprachen → direkt umschalten, kein Menü nötig
      i18n.toggle();
      return;
    }
    menuOpen = !menuOpen;
  }

  function onKey(ev: KeyboardEvent): void {
    if (ev.key === 'Escape' && menuOpen) menuOpen = false;
  }

  // Klick außerhalb schließt das Menü
  function onDocClick(ev: MouseEvent): void {
    if (!menuOpen || !host) return;
    if (!host.contains(ev.target as Node)) menuOpen = false;
  }
</script>

<svelte:document onclick={onDocClick} onkeydown={onKey} />

<div class="lang-host" bind:this={host}>
  <button class="hdr-btn lang" onclick={toggle}
          title={t(`topbar.language${i18n.current === 'de' ? 'De' : 'En'}`)}
          aria-label={activeMeta.nativeName}
          aria-haspopup={LANG_ORDER.length > 2 ? 'menu' : undefined}
          aria-expanded={menuOpen}>
    <span class="flag" aria-hidden="true">{activeMeta.flag}</span>
    <span class="num code">{activeMeta.short}</span>
    {#if LANG_ORDER.length > 2}
      <i class="fa-solid fa-caret-down caret" aria-hidden="true"></i>
    {/if}
  </button>

  {#if menuOpen && LANG_ORDER.length > 2}
    <ul class="menu" role="menu">
      {#each langs as l (l.code)}
        <li>
          <button role="menuitem" class:active={l.code === i18n.current}
                  onclick={() => pick(l.code)}>
            <span class="flag" aria-hidden="true">{l.flag}</span>
            <span class="name">{l.nativeName}</span>
            <span class="num code">{l.short}</span>
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .lang-host {
    position: relative;
    display: inline-flex;
  }
  .lang { gap: 6px; }
  .lang .flag {
    /* Emojis bekommen ihre eigene Schriftart, sonst werden sie auf
       manchen Systemen mit Color-Glyphs anders gerendert als die
       Header-Beschriftungen. */
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
    font-size: 14px;
    line-height: 1;
  }
  .lang .code {
    font-size: var(--fs-xs);
    letter-spacing: 0.1em;
    color: var(--fg);
  }
  .lang .caret { font-size: 10px; opacity: 0.6; }
  .lang:hover .code { color: var(--accent); }

  .menu {
    position: absolute;
    top: calc(100% + 4px);
    right: 0;
    z-index: 200;
    list-style: none;
    margin: 0;
    padding: 4px;
    background: var(--bg-elev);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-sm);
    box-shadow: var(--shadow-lg);
    min-width: 180px;
    display: flex; flex-direction: column;
    gap: 1px;
  }
  .menu button {
    width: 100%;
    background: transparent;
    border: none;
    color: var(--fg);
    padding: 8px 12px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    display: flex; align-items: center; gap: 10px;
    font-family: var(--sans);
    font-size: var(--fs-sm);
    text-align: left;
    line-height: 1.2;
  }
  .menu button:hover { background: var(--bg-card-2); color: var(--accent); }
  .menu button.active {
    background: color-mix(in srgb, var(--accent) 14%, transparent);
    color: var(--accent);
  }
  .menu .flag {
    font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
    font-size: 16px;
    flex: 0 0 auto;
  }
  .menu .name { flex: 1; }
  .menu .code {
    font-size: var(--fs-xs);
    color: var(--fg-mute);
    letter-spacing: 0.1em;
  }
</style>
