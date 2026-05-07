<script lang="ts">
  import { api } from '../lib/api';
  import { toast } from '../lib/toast.svelte';
  import { t } from '../lib/i18n';
  import { formatDiff, formatGrams, formatTime } from '../lib/format';
  import HelpButton from './HelpButton.svelte';
  import type { MesslogEntry } from '../lib/types';

  interface Props {
    entries: MesslogEntry[];
    /** Wird vom App-Root aufgerufen, wenn die Liste sich geändert hat. */
    onChanged?: () => void;
  }
  let { entries = [], onChanged }: Props = $props();

  // Neueste zuerst — Server liefert auch so, Frontend appended hinten
  let recent = $derived([...entries].reverse());

  async function deleteOne(id: number): Promise<void> {
    try {
      await api.app.messlogDelete(id);
      toast.show(t('messlog.entryDeleted'), 'ok');
      onChanged?.();
    } catch (e) {
      toast.show((e as Error).message, 'error');
    }
  }

  async function clearAll(): Promise<void> {
    if (!confirm(t('messlog.clearConfirm'))) return;
    try {
      await api.app.messlogClear();
      toast.show(t('messlog.cleared'), 'ok');
      onChanged?.();
    } catch (e) {
      toast.show((e as Error).message, 'error');
    }
  }
</script>

<section class="messlog">
  <header>
    <h3>{t('messlog.title')}</h3>
    <div class="meta">
      <span class="num count">{entries.length}</span>
      {#if entries.length > 0}
        <button class="hdr-act" onclick={clearAll}
                title={t('messlog.clearAll')} aria-label={t('messlog.clearAll')}>
          <i class="fa-regular fa-trash-can"></i>
        </button>
      {/if}
      <HelpButton id="history" label={t('messlog.helpLabel')} />
    </div>
  </header>

  <ul class="list">
    {#if recent.length === 0}
      <li class="empty">{t('messlog.empty')}</li>
    {:else}
      {#each recent as e (e.id)}
        <li class="row" data-kind={e.kind}>
          <span class="ts num">{formatTime(e.ts)}</span>
          {#if e.kind === 'change'}
            <span class="diff num" class:plus={e.diff_g !== null && e.diff_g >= 0}
                                    class:minus={e.diff_g !== null && e.diff_g < 0}>
              {formatDiff(e.diff_g)}
            </span>
          {:else if e.kind === 'tare'}
            <span class="diff num tare">{t('messlog.tareLabel')}</span>
          {:else}
            <span class="diff num start">{t('messlog.startLabel')}</span>
          {/if}
          <span class="resulting num">→ {formatGrams(e.value_g)}</span>
          <button class="row-del" onclick={() => deleteOne(e.id)}
                  title={t('messlog.deleteEntry')}
                  aria-label={t('messlog.deleteEntry')}>
            <i class="fa-regular fa-circle-xmark"></i>
          </button>
        </li>
      {/each}
    {/if}
  </ul>
</section>

<style>
  .messlog {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-3);
    box-shadow: var(--shadow);
    flex: 1 1 auto;
    min-height: 0;
    display: flex; flex-direction: column;
  }
  header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: var(--sp-2);
  }
  header h3 {
    margin: 0; font-size: var(--fs-sm); color: var(--fg-dim);
    font-weight: 500; letter-spacing: 0.02em;
  }
  .meta { display: flex; align-items: center; gap: var(--sp-2); }
  .count { font-size: var(--fs-xs); color: var(--fg-mute); }
  .list {
    list-style: none; margin: 0; padding: 0 var(--sp-2) 0 0;  /* Luft zum Scrollbalken */
    overflow-y: auto;
    flex: 1 1 auto; min-height: 0;
  }
  /* Tabellarische Ausrichtung mit vier festen Spalten:
       | Zeit | Differenz (rechts) | Resultat (rechts) | × |
     Die Lösch-Spalte erscheint dezent rechts; bei Hover hebt sie sich
     hervor. */
  .row {
    display: grid;
    grid-template-columns: 72px minmax(0, 1fr) minmax(0, 1fr) max-content;
    gap: var(--sp-2) var(--sp-3);
    align-items: baseline;
    padding: 7px var(--sp-2) 7px 4px;
    border-bottom: 1px solid var(--border);
    font-variant-numeric: tabular-nums lining-nums slashed-zero;
  }
  .row-del {
    background: transparent; border: none; padding: 2px 4px;
    color: var(--fg-mute); cursor: pointer;
    font-size: 14px; line-height: 1;
    opacity: 0; transition: opacity 0.15s, color 0.15s;
  }
  .row:hover .row-del,
  .row:focus-within .row-del { opacity: 0.7; }
  .row-del:hover { color: var(--red); opacity: 1; }
  .hdr-act {
    background: transparent; border: none;
    color: var(--fg-mute); cursor: pointer; padding: 2px 6px;
    font-size: 13px;
  }
  .hdr-act:hover { color: var(--red); }
  .row:last-child { border-bottom: none; }
  .ts {
    font-size: var(--fs-xs);
    color: var(--fg-mute);
    text-align: left;
  }
  .diff {
    font-size: var(--fs-md);
    text-align: right;            /* rechtsbündig — Einheiten untereinander */
    letter-spacing: 0.02em;
    font-variant-numeric: tabular-nums lining-nums slashed-zero;
  }
  .diff.plus { color: var(--green); }
  .diff.minus { color: var(--orange); }
  .diff.tare, .diff.start { color: var(--info-blue); font-size: var(--fs-sm); }
  .resulting {
    font-size: var(--fs-xs);
    color: var(--fg-dim);
    text-align: right;
    white-space: nowrap;
    font-variant-numeric: tabular-nums lining-nums slashed-zero;
  }
  .empty {
    padding: var(--sp-4); text-align: center;
    color: var(--fg-mute); font-size: var(--fs-sm);
  }
</style>
