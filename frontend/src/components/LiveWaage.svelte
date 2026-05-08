<script lang="ts">
  import { api } from '../lib/api';
  import { copyText } from '../lib/clipboard';
  import { toast } from '../lib/toast.svelte';
  import { live } from '../lib/liveStore.svelte';
  import { healthStore } from '../lib/healthStore.svelte';
  import { t } from '../lib/i18n';
  import StableValue from './StableValue.svelte';

  type CmdKey = 'tare' | 'unit' | 'light';

  let busy = $state<CmdKey | null>(null);

  let r = $derived(live.reading);

  // Hardware-Status zentral aus dem healthStore — der Footer zeigt
  // BACKEND/WAAGE-LEDs prominent an, hier in der LiveWaage steuern
  // wir damit nur noch die Anzeige des Wert-Displays selbst.
  let scaleState = $derived<'live' | 'simulated' | 'offline'>(
    healthStore.simulated ? 'simulated'
    : healthStore.scaleOk ? 'live'
    : 'offline'
  );

  // Reaktivität: ist die Hardware aktuell offline (USB-Adapter weg,
  // Waage abgeschaltet, …), zeigen wir den letzten Wert NICHT mehr an —
  // sonst klebt eine "61,9 g STABIL" auf dem Display, obwohl gar nichts
  // mehr gemessen wird. healthStore.scaleOk ist seit 0.5.12 ehrlich.
  let scaleOffline = $derived(scaleState === 'offline');
  let stable = $derived(scaleOffline ? false : (r?.stable ?? false));
  let weightG = $derived(scaleOffline ? null : (r?.weight_g ?? null));

  async function copyValue(): Promise<void> {
    if (!r) return;
    const text = r.weight_g.toFixed(1);
    const ok = await copyText(text);
    toast.show(ok ? t('toast.valueCopiedG', text + ' g') : t('toast.copyError'),
      ok ? 'ok' : 'error');
  }

  async function send(key: CmdKey): Promise<void> {
    if (busy) return;
    busy = key;
    try {
      if (key === 'tare') await api.scale.cmdTare();
      else if (key === 'unit') await api.scale.cmdUnit();
      else if (key === 'light') await api.scale.cmdLight();
      toast.show(
        key === 'tare' ? t('commands.tareDone')
        : key === 'unit' ? t('commands.unitDone')
        : t('commands.lightDone'), 'ok');
    } catch (e) {
      toast.show((e as Error).message, 'error');
    } finally {
      busy = null;
    }
  }

</script>

<section class="live-card" class:stable>
  <button class="display" onclick={copyValue} disabled={!r || scaleOffline}
          title={t('commands.copyValueTitle')} aria-label={t('commands.copyValueAria')}>
    <span class="value">
      <StableValue g={weightG} />
    </span>
    <span class="label num">
      {scaleOffline ? t('live.scaleOffline') :
       r ? (stable ? t('status.stable') : t('status.unstable')) : '—'}
    </span>
  </button>

  <div class="actions">
    <button onclick={() => send('tare')} disabled={busy !== null}
            title={t('commands.tareTooltip')}>
      <i class="fa-solid fa-arrow-rotate-left"></i>
      {t('commands.tare')}
    </button>
    <button onclick={() => send('unit')} disabled={busy !== null}
            title={t('commands.unitTooltip')}>
      <i class="fa-solid fa-ruler"></i>
      {t('commands.unit')}
    </button>
    <button onclick={() => send('light')} disabled={busy !== null}
            title={t('commands.lightTooltip')}>
      <i class="fa-solid fa-lightbulb"></i>
      {t('commands.light')}
    </button>
  </div>
</section>

<style>
  .live-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-4);
    display: flex; flex-direction: column;
    gap: var(--sp-3);
    box-shadow: var(--shadow);
    flex: 0 0 auto;
    transition: border-color 0.3s;
    /* Container-Query-Basis, damit das Display sich an die Sidebar-
       Breite anpasst (280–400 px). */
    container-type: inline-size;
  }
  .live-card.stable { border-color: var(--display-green); }
  /* Topline mit BACKEND/WAAGE-LEDs ist seit 0.5.14 entfernt — der
     Footer zeigt diesen Status zentral an. Live-Wert beginnt direkt
     mit dem Display, darunter die drei Hardware-Aktions-Knöpfe. */

  .display {
    background: rgba(0,0,0,0.25);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: var(--radius-soft);
    padding: var(--sp-4);
    text-align: center;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.3);
    cursor: copy;
    transition: background 0.15s;
  }
  :global(:root[data-theme="light"]) .display {
    background: rgba(0,0,0,0.04);
    border-color: rgba(0,0,0,0.05);
  }
  .display:hover:not(:disabled) {
    background: rgba(0,0,0,0.32);
  }
  .display:disabled { cursor: default; }
  .value {
    display: block;
    /* Schrift adaptive zur Container-Breite — bei einer 280-px-Sidebar
       wird sie etwa 36 px, bei einer 400-px-Sidebar 56 px. */
    font-size: clamp(28px, 14cqi, 56px);
    color: var(--display-green);
    line-height: 1;
    letter-spacing: 0;
    overflow: hidden;
    text-overflow: clip;
    text-shadow: 0 0 4px color-mix(in srgb, var(--display-green) 35%, transparent);
  }
  .value :global(.stable-value) { color: inherit; }
  .stable .value { color: var(--display-green); }
  .live-card:not(.stable) .value {
    color: var(--fg-dim);
    text-shadow: none;
  }
  .label {
    display: block;
    margin-top: var(--sp-2);
    font-size: var(--fs-sm);
    letter-spacing: 0.18em;
    color: var(--display-green);
  }
  .live-card:not(.stable) .label { color: var(--orange); }

  .actions { display: flex; gap: var(--sp-2); }
  .actions button {
    flex: 1 1 0;
    min-width: 0;                 /* Schrumpfen erlauben — sonst läuft */
                                  /* z.B. „Beleuchtung" über den rechten Rand */
    min-height: var(--tap);
    padding: 6px var(--sp-2);
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    color: var(--fg);
    font-family: var(--sans);
    font-size: var(--fs-sm);
    font-weight: 500;
    border-radius: var(--radius-sm);
    cursor: pointer;
    display: inline-flex; align-items: center; justify-content: center;
    gap: 6px;
    /* Lange Wörter an Zeilenbruch erlauben — „Auf Null setzen" landet
       z.B. auf zwei Zeilen, statt aus der Karte zu laufen. */
    text-align: center;
    line-height: 1.15;
    overflow-wrap: anywhere;
    word-break: break-word;
  }
  .actions button:hover:not(:disabled) {
    border-color: var(--accent); color: var(--accent);
  }
  .actions button i { color: var(--fg-dim); }
  .actions button:hover:not(:disabled) i { color: var(--accent); }

  /* Sticky-Verhalten auf Mobile: das Live-Display klebt am oberen
     Rand des scrollenden Body-Bereichs, während Messprotokoll und
     Karten darunter durchscrollen. Höhere z-Achse, damit der
     Display-Schatten nicht von darunterliegenden Karten überdeckt
     wird. */
  @media (max-width: 900px) {
    .live-card {
      position: sticky;
      top: 0;
      z-index: 5;
    }
  }
</style>
