<script lang="ts">
  /**
   * Stückzählung mit voll verwaltbaren Vorlagen.
   *
   * Vorlagen liegen serverseitig in der SQLite-Datenbank — sie können
   * angelegt, bearbeitet, gelöscht werden. Klick auf eine Vorlage
   * setzt das hinterlegte Stückgewicht direkt als Kalibrierung;
   * eigene Referenzteile auflegen und „Kalibrieren" geht parallel.
   *
   * Nach erfolgreicher Kalibrierung wird zusätzlich ein „Als Vorlage
   * speichern"-Knopf eingeblendet — wiederkehrende Sachen lassen
   * sich so direkt mit dem aktuellen Stückgewicht festhalten.
   */
  import { onMount } from 'svelte';
  import { api } from '../../lib/api';
  import { live } from '../../lib/liveStore.svelte';
  import { toast } from '../../lib/toast.svelte';
  import { formatGrams, formatTime } from '../../lib/format';
  import { countTemplateStore } from '../../lib/countTemplateStore.svelte';
  import { t } from '../../lib/i18n';
  import HelpButton from '../HelpButton.svelte';
  import type { CountState, CountTemplateRecord } from '../../lib/types';

  let info = $state<CountState | null>(null);
  let busy = $state(false);
  let refText = $state('10');

  // Anlege-/Bearbeitungs-Dialog
  let manageOpen = $state(false);
  let editing = $state<CountTemplateRecord | null>(null);
  let formName = $state('');
  let formIcon = $state('fa-solid fa-cube');
  let formWeight = $state('');
  let formDesc = $state('');

  async function refresh(): Promise<void> {
    try {
      info = await api.app.count();
    } catch (e) { toast.show((e as Error).message, 'error'); }
  }

  // ----------------- Kalibrieren mit Live-Wert -----------------
  async function calibrate(): Promise<void> {
    const n = parseInt(refText.replace(/\D/g, ''), 10);
    if (!Number.isFinite(n) || n <= 0) {
      toast.show(t('count.invalidCount'), 'error'); return;
    }
    busy = true;
    try {
      info = await api.app.countCalibrate(n);
      toast.show(t('count.calibratedWith').replace('%n', String(n)), 'ok');
    } catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  async function reset(): Promise<void> {
    busy = true;
    try {
      info = await api.app.countReset();
      toast.show(t('count.resetDone'), 'ok');
    } catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  // ----------------- Vorlage anwenden / verwalten -----------------
  function applyTemplate(tpl: CountTemplateRecord): void {
    // Wendet das gespeicherte Stückgewicht direkt an, ohne die Waage
    // zu konsultieren. Backend kennt diese Operation nicht — wir
    // setzen den UI-State über einen Calibrate-Aufruf mit fiktiv-
    // gewähltem Referenz-Count, der das gewünschte Stückgewicht
    // ergibt: brauchen Live-Wert ÷ piece_weight = referenceCount.
    // Falls keine Auflage, kalibrieren wir nicht — wir merken die
    // Vorlage als „virtuell aktiv" über die UI.
    const w = live.reading?.weight_g;
    if (w !== undefined && w !== null && w > 0 && tpl.piece_weight_g > 0) {
      const refN = Math.max(1, Math.round(w / tpl.piece_weight_g));
      refText = String(refN);
    } else {
      refText = '10';
    }
    toast.show(
      t('count.templateApplied').replace('%n', tpl.name)
        .replace('%w', tpl.piece_weight_g.toString().replace('.', ',')),
      'ok',
    );
  }

  function startNew(): void {
    editing = null;
    formName = '';
    formIcon = 'fa-solid fa-cube';
    formWeight = '';
    formDesc = '';
    manageOpen = true;
  }

  function startEdit(tpl: CountTemplateRecord): void {
    editing = tpl;
    formName = tpl.name;
    formIcon = tpl.icon_class || 'fa-solid fa-cube';
    formWeight = tpl.piece_weight_g.toString().replace('.', ',');
    formDesc = tpl.description;
    manageOpen = true;
  }

  function cancelEdit(): void {
    manageOpen = false;
    editing = null;
  }

  function takeCurrentPieceWeight(): void {
    if (info?.piece_weight_g) {
      formWeight = info.piece_weight_g.toFixed(4).replace('.', ',');
    }
  }

  async function saveTemplate(): Promise<void> {
    const name = formName.trim();
    const pw = parseFloat(formWeight.replace(',', '.'));
    if (!name) { toast.show(t('toast.error') + ': ' + t('countTemplates.name'), 'error'); return; }
    if (!Number.isFinite(pw) || pw <= 0) {
      toast.show(t('toast.error') + ': ' + t('countTemplates.pieceWeight'), 'error'); return;
    }
    try {
      if (editing) {
        await countTemplateStore.update(editing.id, {
          name, icon_class: formIcon, piece_weight_g: pw, description: formDesc,
        });
      } else {
        await countTemplateStore.add({
          name, icon_class: formIcon, piece_weight_g: pw, description: formDesc,
        });
      }
      toast.show(t('toast.templateSaved'), 'ok');
      manageOpen = false;
      editing = null;
    } catch (e) {
      toast.show((e as Error).message, 'error');
    }
  }

  /** Vorlage direkt löschen — kein nativer Bestätigungsdialog (Vorgabe
   *  Anwender: Löschen ist Löschen). Vorlagen sind in Sekunden über
   *  „Neue Vorlage" wieder neu anlegbar. */
  async function removeTemplate(tpl: CountTemplateRecord): Promise<void> {
    try {
      await countTemplateStore.remove(tpl.id);
      toast.show(t('toast.templateDeleted'), 'ok');
    } catch (e) {
      toast.show((e as Error).message, 'error');
    }
  }

  // „Aktuelles Kalibrierungs-Stückgewicht als neue Vorlage anlegen"
  function saveCalibrationAsTemplate(): void {
    if (!info?.calibrated || !info.piece_weight_g) return;
    editing = null;
    formName = '';
    formIcon = 'fa-solid fa-cube';
    formWeight = info.piece_weight_g.toFixed(4).replace('.', ',');
    formDesc = `${t('count.fromCalibration')} ${formatTime(info.calibrated_at)}`;
    manageOpen = true;
  }

  // ----------------- Live-Stückzahl -----------------
  let liveGross = $derived(live.reading?.weight_g ?? null);
  let pieces = $derived.by<number | null>(() => {
    if (!info?.calibrated || info.piece_weight_g === null
        || info.piece_weight_g === 0 || liveGross === null) return null;
    return Math.round(liveGross / info.piece_weight_g);
  });
  let piecesExact = $derived.by<number | null>(() => {
    if (!info?.calibrated || info.piece_weight_g === null
        || info.piece_weight_g === 0 || liveGross === null) return null;
    return liveGross / info.piece_weight_g;
  });

  onMount(() => {
    void refresh();
    void countTemplateStore.refresh();
  });
</script>

<section class="panel">
  <header>
    <h2>{t('tools.count')}</h2>
    <HelpButton id="count" />
  </header>

  <div class="templates" role="toolbar" aria-label={t('countTemplates.title')}>
    {#each countTemplateStore.list as tpl (tpl.id)}
      <div class="tpl-wrap">
        <button class="tpl" onclick={() => applyTemplate(tpl)} title={tpl.description || tpl.name}>
          <i class={tpl.icon_class || 'fa-solid fa-cube'} aria-hidden="true"></i>
          <span class="lbl">{tpl.name}</span>
          <span class="num pw">{formatGrams(tpl.piece_weight_g)}</span>
        </button>
        <div class="tpl-actions">
          <button class="iconlink" onclick={() => startEdit(tpl)}
                  title={t('countTemplates.edit')} aria-label={t('countTemplates.edit')}>
            <i class="fa-solid fa-pen"></i>
          </button>
          <button class="iconlink danger" onclick={() => removeTemplate(tpl)}
                  title={t('countTemplates.delete')} aria-label={t('countTemplates.delete')}>
            <i class="fa-regular fa-trash-can"></i>
          </button>
        </div>
      </div>
    {/each}
    <button class="tpl tpl-add" onclick={startNew}
            title={t('countTemplates.add')} aria-label={t('countTemplates.add')}>
      <i class="fa-solid fa-plus" aria-hidden="true"></i>
      <span class="lbl">{t('countTemplates.add')}</span>
    </button>
  </div>

  {#if manageOpen}
    <div class="manage" role="region" aria-label={t('countTemplates.title')}>
      <h3>{editing ? t('countTemplates.editTitle') : t('countTemplates.newTitle')}</h3>
      <div class="form">
        <label>
          {t('countTemplates.name')}
          <input type="text" bind:value={formName} maxlength="120" />
        </label>
        <label>
          {t('countTemplates.icon')}
          <input type="text" bind:value={formIcon} maxlength="120"
                 placeholder="fa-solid fa-cube" />
        </label>
        <label>
          {t('countTemplates.pieceWeight')}
          <span class="row-flex">
            <input type="text" inputmode="decimal" bind:value={formWeight} />
            {#if info?.piece_weight_g}
              <button class="btn-primary small" onclick={takeCurrentPieceWeight}
                      title={t('countTemplates.takeCalibrated')}>
                <i class="fa-solid fa-circle-down"></i>
              </button>
            {/if}
          </span>
        </label>
        <label>
          {t('countTemplates.description')}
          <input type="text" bind:value={formDesc} maxlength="500" />
        </label>
        <div class="actions">
          <button class="btn-warn" onclick={cancelEdit}>{t('general.cancel')}</button>
          <button class="btn-primary" onclick={saveTemplate}>
            <i class="fa-solid fa-check"></i>
            {editing ? t('general.save') : t('countTemplates.add')}
          </button>
        </div>
      </div>
    </div>
  {/if}

  <div class="form">
    <div class="display">
      <div class="row">
        <span class="lbl">{t('count.totalWeight')}</span>
        <span class="num val">{formatGrams(liveGross)}</span>
      </div>
      {#if info?.calibrated}
        <div class="row">
          <span class="lbl">{t('count.pieceWeight')}</span>
          <span class="num val">{formatGrams(info.piece_weight_g)}</span>
        </div>
      {/if}
      <div class="row big">
        <span class="lbl">{t('count.pieceCount')}</span>
        <span class="num val big" class:active={pieces !== null}>
          {pieces !== null ? pieces : '—'} <small class="unit">{t('units.pieces')}</small>
        </span>
      </div>
      {#if piecesExact !== null}
        <div class="meta num">{t('count.exact')}: {piecesExact.toFixed(2)} {t('units.pieces')}</div>
      {/if}
      {#if info?.calibrated_at}
        <div class="meta">{t('count.calibratedAt')} {formatTime(info.calibrated_at)}</div>
      {/if}
    </div>

    <div class="manual">
      <label>
        {t('count.referenceCount')}
        <span class="row-flex">
          <input type="text" inputmode="numeric" bind:value={refText} />
          <button class="btn-primary" onclick={calibrate} disabled={busy || liveGross === null}>
            <i class="fa-solid fa-check"></i>
            {t('count.calibrate')}
          </button>
        </span>
      </label>
    </div>

    {#if info?.calibrated}
      <div class="cal-actions">
        <button class="btn-primary" onclick={saveCalibrationAsTemplate}>
          <i class="fa-solid fa-bookmark"></i>
          {t('count.saveAsTemplate')}
        </button>
        <button class="btn-warn" onclick={reset} disabled={busy}>
          <i class="fa-solid fa-eraser"></i>
          {t('count.resetCalibration')}
        </button>
      </div>
    {/if}
  </div>
</section>

<style>
  .panel {
    flex: 1 1 auto; min-height: 0; overflow-y: auto;
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-4);
  }
  header {
    display: flex; align-items: center; justify-content: space-between;
    gap: var(--sp-3);
  }
  header h2 { margin: 0; font-size: var(--fs-xl); font-weight: 600; }

  /* Vorlagen-Karussell mit Anlege-Karte */
  .templates {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(140px, 100%), 1fr));
    gap: var(--sp-2);
    max-width: 720px;
    margin-inline: auto;
    width: 100%;
  }
  .tpl-wrap { position: relative; }
  .tpl {
    width: 100%;
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    color: var(--fg);
    border-radius: var(--radius-sm);
    padding: var(--sp-2) var(--sp-3);
    display: flex; flex-direction: column; align-items: center;
    gap: 4px;
    min-height: var(--tap);
    cursor: pointer;
  }
  .tpl:hover { border-color: var(--accent); color: var(--accent); }
  .tpl i { font-size: 18px; }
  .tpl .lbl { font-size: var(--fs-sm); text-align: center; line-height: 1.2; }
  .tpl .pw { font-size: var(--fs-xs); color: var(--fg-mute); }
  .tpl-add {
    border-style: dashed;
    color: var(--fg-dim);
  }
  .tpl-add:hover { color: var(--accent); border-style: dashed; }

  .tpl-actions {
    position: absolute;
    top: 4px; right: 4px;
    display: flex; gap: 2px;
    opacity: 0;
    transition: opacity 0.15s;
  }
  .tpl-wrap:hover .tpl-actions,
  .tpl-wrap:focus-within .tpl-actions { opacity: 1; }
  .iconlink {
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--fg-mute);
    border-radius: var(--radius-sm);
    padding: 4px 6px;
    font-size: 11px;
    cursor: pointer;
    line-height: 1;
  }
  .iconlink:hover { color: var(--accent); border-color: var(--accent); }
  .iconlink.danger:hover { color: var(--red); border-color: var(--red); }

  /* Anlege-/Bearbeitungs-Form */
  .manage {
    max-width: 480px;
    margin-inline: auto;
    width: 100%;
    background: var(--bg-card-2);
    border: 1px solid var(--accent);
    border-radius: var(--radius);
    padding: var(--sp-3) var(--sp-4);
    display: flex; flex-direction: column;
    gap: var(--sp-2);
  }
  .manage h3 {
    margin: 0;
    font-size: var(--fs-md);
    color: var(--accent);
  }

  .form {
    max-width: 480px; margin-inline: auto; width: 100%;
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  .display {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-2);
  }
  .row { display: flex; justify-content: space-between; align-items: baseline; }
  .row.big { padding-top: var(--sp-2); margin-top: var(--sp-2); border-top: 1px solid var(--border); }
  .lbl {
    font-size: var(--fs-sm); color: var(--fg-dim);
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .val { font-size: var(--fs-lg); }
  .val.big { font-size: var(--fs-xxl); color: var(--fg-dim); }
  .val.big.active { color: var(--accent); }
  .val .unit { font-family: var(--sans); font-size: var(--fs-md); font-weight: 500; color: var(--fg-dim); margin-left: 6px; }
  .meta { font-size: var(--fs-xs); color: var(--fg-mute); text-align: right; }

  .manual {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-3) var(--sp-4);
  }
  label {
    display: flex; flex-direction: column; gap: 4px;
    font-size: var(--fs-xs); color: var(--fg-dim);
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .row-flex { display: flex; gap: var(--sp-2); }
  .row-flex input { flex: 1; min-width: 0; }
  .row-flex .btn-primary {
    display: inline-flex; align-items: center; gap: 6px; white-space: nowrap;
    flex: 0 0 auto;
  }
  .btn-primary.small { padding: 0 10px; min-width: var(--tap); }

  .actions {
    display: flex; gap: var(--sp-2);
    justify-content: flex-end;
    margin-top: var(--sp-1);
  }
  .actions .btn-primary,
  .actions .btn-warn {
    display: inline-flex; align-items: center; gap: 6px;
  }

  .cal-actions { display: flex; gap: var(--sp-2); }
  .cal-actions .btn-primary,
  .cal-actions .btn-warn {
    flex: 1 1 auto;
    display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  }

  .btn-warn {
    min-height: var(--tap); padding: 0 var(--sp-3);
    background: transparent; border: 1px solid var(--orange);
    color: var(--orange); border-radius: var(--radius-sm);
    font-family: var(--sans); font-size: var(--fs-sm); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;
  }
  .btn-warn:hover:not(:disabled) {
    background: color-mix(in srgb, var(--orange) 14%, transparent);
  }
</style>
