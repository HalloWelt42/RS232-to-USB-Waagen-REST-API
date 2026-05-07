<script lang="ts">
  /**
   * Sprach-Umschalter im Header. Zeigt das Kürzel der aktuellen
   * Sprache neben einem Globus-Symbol; Klick wechselt zwischen DE
   * und EN. Auswahl wird in localStorage persistiert.
   *
   * Bewusst keine Flaggen-Symbole — politisch neutral, lesbar in
   * jeder Schriftgröße.
   */
  import { i18n, t } from '../lib/i18n';

  function toggle(): void { i18n.toggle(); }

  let label = $derived(i18n.current === 'de' ? 'DE' : 'EN');
  let title = $derived(
    i18n.current === 'de' ? t('topbar.languageDe') : t('topbar.languageEn')
  );
</script>

<button class="hdr-btn lang" onclick={toggle} title={title} aria-label={title}>
  <i class="fa-solid fa-globe" aria-hidden="true"></i>
  <span class="num code">{label}</span>
</button>

<style>
  .lang { gap: 6px; }
  .lang .code {
    font-size: var(--fs-xs);
    letter-spacing: 0.1em;
    color: var(--fg);
  }
  .lang:hover .code { color: var(--accent); }
</style>
