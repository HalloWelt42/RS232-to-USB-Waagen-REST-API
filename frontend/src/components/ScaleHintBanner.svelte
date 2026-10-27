<script lang="ts">
  /**
   * Anschluss-Hinweis unter der Topbar, solange im Live-Betrieb keine
   * Werte kommen. Unterscheidet, was zu tun ist:
   *
   *   noAdapter  kein USB-Seriell-Adapter angeschlossen: einstecken,
   *              das Backend erkennt ihn ohne Neustart
   *   offline    Adapter steckt, die Waage antwortet nicht: einschalten,
   *              Kabel prüfen
   *
   * Zustand aus dem healthStore (eine Ableitung für Statuslampe,
   * Anzeige und Hinweis). Wie beim Simulator-Hinweis ist der ganze
   * Kasten ein Knopf; er öffnet die Hilfe "Anschluss".
   */
  import { t } from '../lib/i18n';
  import { route } from '../lib/routing.svelte';
  import { healthStore } from '../lib/healthStore.svelte';

  let scaleState = $derived(healthStore.scaleState);
  let visible = $derived(
    healthStore.info !== null &&
    (scaleState === 'noAdapter' || scaleState === 'offline'),
  );
  let noAdapter = $derived(scaleState === 'noAdapter');

  function openHelp(): void { route.openHelp('connection'); }
</script>

{#if visible}
  <button class="banner" type="button" data-state={scaleState}
          onclick={openHelp} title={t('scaleHint.helpTitle')}>
    <i class="fa-solid {noAdapter ? 'fa-plug-circle-xmark' : 'fa-power-off'}"
       aria-hidden="true"></i>
    <span class="msg">
      <strong>{t(noAdapter ? 'scaleHint.noAdapterTitle' : 'scaleHint.offlineTitle')}</strong>
      {t(noAdapter ? 'scaleHint.noAdapterText' : 'scaleHint.offlineText')}
    </span>
    <span class="action">
      <i class="fa-solid fa-circle-info" aria-hidden="true"></i>
      <span class="action-label">{t('scaleHint.help')}</span>
    </span>
  </button>
{/if}

<style>
  /* Hinweiskasten mit Rahmen rundum, eingerückt wie der Inhalt darunter
     (gleiche Seitenabstände wie .body in App.svelte). */
  .banner {
    --tone: var(--orange);
    flex: 0 0 auto;
    display: flex; align-items: center; gap: var(--sp-3);
    margin: var(--sp-3) var(--sp-3) 0;
    padding: var(--sp-2) var(--sp-3);
    background: color-mix(in srgb, var(--tone) 14%, var(--bg-card));
    border: 1px solid var(--tone);
    border-radius: var(--radius);
    color: var(--fg);
    font-family: var(--sans);
    font-size: var(--fs-md);
    line-height: 1.35;
    text-align: left;
    cursor: pointer;
  }
  .banner[data-state="noAdapter"] { --tone: var(--red); }
  /* Rahmenfarbe auch beim Überfahren halten (die globale Knopfregel
     färbt sonst den Rahmen in Akzentfarbe). */
  .banner:hover {
    background: color-mix(in srgb, var(--tone) 22%, var(--bg-card));
    border-color: var(--tone);
  }
  .banner > i { font-size: 18px; flex: 0 0 auto; color: var(--tone); }
  .msg { flex: 1 1 auto; min-width: 0; }
  .msg strong { color: var(--tone); font-weight: 600; }
  .action {
    margin-left: auto;
    flex: 0 0 auto;
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px;
    border: 1px solid var(--tone);
    border-radius: var(--radius-sm);
    background: var(--bg-card);
    color: var(--tone);
    font-size: var(--fs-sm);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .banner:hover .action {
    background: var(--tone);
    color: var(--bg-card);
  }

  /* Telefon: Knopf nur als Symbol, damit der Text die Breite bekommt
     und der Kasten flach bleibt; tippen lässt sich der ganze Kasten. */
  @media (max-width: 900px) {
    .banner { margin: var(--sp-2) var(--sp-2) 0; gap: var(--sp-2); }
    .action { padding: 6px 8px; }
    .action-label { display: none; }
  }
</style>
