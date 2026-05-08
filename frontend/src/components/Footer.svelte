<script lang="ts">
  /**
   * Footer-Statusleiste.
   *
   * Linker Bereich: BACKEND- und WAAGE-LEDs — gleiches Schema wie in
   * LiveWaage.svelte (zwei getrennte Aussagen, scaleSimulated kennt
   * den Simulator-Modus). Mittlerer Bereich: Reader-Status, Port,
   * Baudrate, Uptime (nur Desktop, sonst zu eng). Rechter Bereich:
   * Live-Backend-Version aus /scale/health (= zentrale VERSION-Datei).
   */
  import { formatDuration } from '../lib/format';
  import { t } from '../lib/i18n';
  import { healthStore } from '../lib/healthStore.svelte';
  import { versionStore } from '../lib/versionStore.svelte';
  import type { ConnectionState, HealthInfo } from '../lib/types';

  interface Props {
    health: HealthInfo | null;
    connection: ConnectionState;
  }

  let { health = null, connection = 'connecting' }: Props = $props();

  // Backend-WS-Status: open/connecting/closed/error → LED-Stilus
  let backendState = $derived<'open' | 'connecting' | 'closed' | 'error'>(connection);
  // Waagen-Status: live/simulated/offline analog zu LiveWaage
  let scaleState = $derived<'live' | 'simulated' | 'offline'>(
    healthStore.simulated ? 'simulated'
    : healthStore.scaleOk ? 'live'
    : 'offline'
  );

  const backendLabelKey: Record<string, string> = {
    open: 'live.backendOk',
    connecting: 'live.backendConnecting',
    closed: 'live.backendOff',
    error: 'live.backendError',
  };
  const scaleLabelKey: Record<string, string> = {
    live: 'live.scaleConnected',
    simulated: 'live.scaleSimulated',
    offline: 'live.scaleOffline',
  };
</script>

<footer>
  <span class="cell status">
    <span class="led" data-state={backendState} aria-hidden="true"></span>
    <span class="num lbl">{t(backendLabelKey[backendState])}</span>
  </span>
  <span class="cell status">
    <span class="led" data-scale={scaleState} aria-hidden="true"></span>
    <span class="num lbl">{t(scaleLabelKey[scaleState])}</span>
  </span>

  {#if health}
    <span class="cell only-desktop">{t('status.port')} <code class="num">{health.port}</code></span>
    <span class="cell num only-desktop">{health.baudrate} Baud</span>
    <span class="cell num only-desktop">{t('status.uptime')} {formatDuration(health.uptime_seconds)}</span>
  {/if}

  <!-- Versionsanzeige zieht die robusteste verfügbare Quelle:
       1) /version.json (statisch, von bump.sh aktualisiert,
          Cache-Buster beim Fetch — also IMMER aktuell), dann
       2) /scale/health (Backend), dann
       3) __APP_VERSION__ (Vite-Build-Zeit-Konstante).
       Bei Mismatch zwischen (1) und (2) wird ein Hinweis-Title
       gesetzt, damit Deployment-Diskrepanzen sichtbar werden. -->
  <span class="cell version num"
        title={versionStore.hasMismatch
          ? `Frontend v${versionStore.fromFile} ≠ Backend v${versionStore.fromBackend}`
          : ''}
        class:mismatch={versionStore.hasMismatch}>
    v{versionStore.value}
  </span>
</footer>

<style>
  footer {
    height: var(--footer-h);
    flex: 0 0 auto;
    display: flex; align-items: center; gap: var(--sp-4);
    padding: 0 var(--sp-3);
    background: var(--bg-card);
    border-top: 1px solid var(--border);
    font-size: var(--fs-xs);
    color: var(--fg-dim);
  }
  .cell { display: flex; align-items: center; gap: 6px; }
  .cell.version { margin-left: auto; }
  .cell.version.mismatch {
    color: var(--orange);
    cursor: help;
    text-decoration: underline dotted;
  }
  .status .lbl { letter-spacing: 0.06em; }

  /* LED — gleiches Schema wie in LiveWaage.svelte */
  .led {
    width: 9px; height: 9px; border-radius: 50%;
    background: var(--fg-mute);
  }
  .led[data-state="open"]       { background: var(--display-green); box-shadow: 0 0 6px var(--display-green); }
  .led[data-state="connecting"] { background: var(--orange); animation: pulse 1.2s infinite; }
  .led[data-state="closed"], .led[data-state="error"] { background: var(--red); }
  .led[data-scale="live"]       { background: var(--display-green); box-shadow: 0 0 6px var(--display-green); }
  .led[data-scale="simulated"]  { background: var(--orange); box-shadow: 0 0 6px color-mix(in srgb, var(--orange) 60%, transparent); }
  .led[data-scale="offline"]    { background: var(--red); }

  code { background: transparent; padding: 0; border: none; font-size: inherit; }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  /* Auf Mobile bleiben nur die zwei wichtigen Status-LEDs sichtbar
     (BACKEND + WAAGE) plus die Version. Reader-Detail, Port, Baud
     und Uptime verschwinden — passt sonst nicht in die Höhe und ist
     im täglichen Werkstatt-Betrieb auch sekundär. */
  @media (max-width: 900px) {
    .only-desktop { display: none; }
    footer { gap: var(--sp-3); padding: 0 var(--sp-2); }
  }
</style>
