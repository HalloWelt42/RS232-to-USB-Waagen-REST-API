<script lang="ts">
  import { api } from '../lib/api';
  import { copyText } from '../lib/clipboard';
  import { formatTime } from '../lib/format';
  import { toast } from '../lib/toast.svelte';
  import { live } from '../lib/liveStore.svelte';
  import { t } from '../lib/i18n';
  import StableValue from './StableValue.svelte';

  type CmdKey = 'tare' | 'unit' | 'light';

  let busy = $state<CmdKey | null>(null);

  let r = $derived(live.reading);
  let conn = $derived(live.connection);

  let stable = $derived(r?.stable ?? false);
  let weightG = $derived(r?.weight_g ?? null);
  let timeText = $derived(r ? formatTime(r.timestamp) : '—');

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
        key === 'tare' ? 'Tara gesetzt'
        : key === 'unit' ? 'Einheit gewechselt'
        : 'Beleuchtung umgeschaltet', 'ok');
    } catch (e) {
      toast.show((e as Error).message, 'error');
    } finally {
      busy = null;
    }
  }

  const connLabel: Record<string, string> = {
    open: 'LIVE', connecting: 'VERBINDE', closed: 'GETRENNT', error: 'FEHLER',
  };
</script>

<section class="live-card" class:stable>
  <div class="topline">
    <span class="conn">
      <span class="dot" data-state={conn}></span>
      <span class="num">{connLabel[conn]}</span>
    </span>
    {#if r}<span class="ts num">{timeText}</span>{/if}
  </div>

  <button class="display" onclick={copyValue} disabled={!r}
          title="Wert in die Zwischenablage kopieren" aria-label="Wert kopieren">
    <span class="value">
      <StableValue g={weightG} />
    </span>
    <span class="label num">
      {r ? (stable ? t('status.stable') : t('status.unstable')) : '—'}
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
  .live-card.stable { border-color: var(--green); }
  .topline {
    display: flex; justify-content: space-between; align-items: center;
    font-size: var(--fs-xs); color: var(--fg-dim);
  }
  .conn { display: flex; align-items: center; gap: 6px; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--fg-dim); }
  .dot[data-state="open"]       { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .dot[data-state="connecting"] { background: var(--orange); animation: pulse 1.2s infinite; }
  .dot[data-state="closed"], .dot[data-state="error"] { background: var(--red); }

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
    color: var(--green);
    line-height: 1;
    letter-spacing: 0;
    overflow: hidden;
    text-overflow: clip;
  }
  .value :global(.stable-value) { color: inherit; }
  .stable .value { color: var(--green); }
  .live-card:not(.stable) .value { color: var(--fg-dim); }
  .label {
    display: block;
    margin-top: var(--sp-2);
    font-size: var(--fs-sm);
    letter-spacing: 0.18em;
    color: var(--green);
  }
  .live-card:not(.stable) .label { color: var(--orange); }

  .actions { display: flex; gap: var(--sp-2); }
  .actions button {
    flex: 1; min-height: var(--tap);
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
  }
  .actions button:hover:not(:disabled) {
    border-color: var(--accent); color: var(--accent);
  }
  .actions button i { color: var(--fg-dim); }
  .actions button:hover:not(:disabled) i { color: var(--accent); }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
</style>
