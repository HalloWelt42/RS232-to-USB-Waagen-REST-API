<script lang="ts">
  /**
   * Wiederverwendbarer Behälter-Picker mit eingebauter Verwaltung.
   *
   * Anwendung: bindet ein `selectedId` als Prop und ruft `onPick(c)`
   * mit dem gewählten Behälter auf — oder `null` für „Kein Behälter".
   * Das Backend speichert die Bibliothek; Anlegen/Bearbeiten/Löschen
   * passiert direkt hier über den Reactive-Store.
   *
   * Default-Auswahl ist immer `null` → 0 g, damit ein leeres
   * Picker-Feld keinen Wert vorgibt.
   */
  import { onMount } from 'svelte';
  import { containerStore } from '../lib/containerStore.svelte';
  import { live } from '../lib/liveStore.svelte';
  import { toast } from '../lib/toast.svelte';
  import { t } from '../lib/i18n';
  import { formatGrams } from '../lib/format';
  import type { Container } from '../lib/types';

  interface Props {
    selectedId: number | null;
    onPick: (c: Container | null) => void;
  }
  let { selectedId, onPick }: Props = $props();

  let manageOpen = $state(false);
  let editing = $state<Container | null>(null);
  let formName = $state('');
  let formWeight = $state('');
  let formNote = $state('');

  function startNew(): void {
    editing = null;
    formName = '';
    formWeight = '';
    formNote = '';
    manageOpen = true;
  }

  function startEdit(c: Container): void {
    editing = c;
    formName = c.name;
    formWeight = c.weight_g.toString().replace('.', ',');
    formNote = c.note;
    manageOpen = true;
  }

  function cancelEdit(): void {
    manageOpen = false;
    editing = null;
  }

  function takeCurrent(): void {
    const w = live.reading?.weight_g;
    if (w === undefined || w === null) return;
    formWeight = w.toFixed(1).replace('.', ',');
  }

  async function save(): Promise<void> {
    const name = formName.trim();
    const weight = parseFloat(formWeight.replace(',', '.'));
    if (!name) { toast.show(t('toast.error') + ': Name', 'error'); return; }
    if (!Number.isFinite(weight) || weight < 0) {
      toast.show(t('toast.error') + ': Gewicht', 'error'); return;
    }
    try {
      if (editing) {
        await containerStore.update(editing.id, {
          name, weight_g: weight, note: formNote,
        });
      } else {
        await containerStore.add({ name, weight_g: weight, note: formNote });
      }
      toast.show(t('toast.containerSaved'), 'ok');
      manageOpen = false;
      editing = null;
    } catch (e) {
      toast.show((e as Error).message, 'error');
    }
  }

  async function remove(c: Container): Promise<void> {
    const msg = t('containers.deleteConfirm').replace('%s', c.name);
    if (!confirm(msg)) return;
    try {
      await containerStore.remove(c.id);
      if (selectedId === c.id) onPick(null);
      toast.show(t('toast.containerDeleted'), 'ok');
    } catch (e) {
      toast.show((e as Error).message, 'error');
    }
  }

  function pickFromList(idStr: string): void {
    if (idStr === '') {
      onPick(null);
      return;
    }
    const id = parseInt(idStr, 10);
    const c = containerStore.byId(id);
    if (c) {
      onPick(c);
      toast.show(t('toast.containerSelected'), 'ok');
    }
  }

  onMount(() => { void containerStore.refresh(); });
</script>

<div class="picker">
  <div class="row">
    <select class="num"
            value={selectedId === null ? '' : String(selectedId)}
            onchange={(e) => pickFromList((e.currentTarget as HTMLSelectElement).value)}
            title={t('containers.pickPlaceholder')}>
      <option value="">{t('containers.none')}</option>
      {#each containerStore.list as c (c.id)}
        <option value={String(c.id)}>{c.name} · {formatGrams(c.weight_g)}</option>
      {/each}
    </select>
    <button class="hdr-btn icon-only" onclick={() => { manageOpen = !manageOpen; if (manageOpen && !editing) startNew(); }}
            title={manageOpen ? t('containers.close') : t('containers.open')}
            aria-label={t('containers.title')}>
      <i class="fa-solid fa-flask-vial"></i>
    </button>
  </div>

  {#if manageOpen}
    <div class="manage" role="region" aria-label={t('containers.title')}>
      <div class="form">
        <label>
          {t('containers.name')}
          <input type="text" bind:value={formName} maxlength="120" />
        </label>
        <label>
          {t('containers.weight')}
          <div class="row-flex">
            <input type="text" inputmode="decimal" bind:value={formWeight} />
            <button class="btn-primary small" onclick={takeCurrent}
                    disabled={!live.reading}
                    title={t('containers.takeCurrent')}>
              <i class="fa-solid fa-arrow-down-to-bracket"></i>
            </button>
          </div>
        </label>
        <label>
          {t('containers.note')}
          <input type="text" bind:value={formNote} maxlength="500" />
        </label>
        <div class="actions">
          <button class="btn-warn" onclick={cancelEdit}>{t('general.cancel')}</button>
          <button class="btn-primary" onclick={save}>
            <i class="fa-solid fa-check"></i>
            {editing ? t('general.save') : t('containers.add')}
          </button>
        </div>
      </div>

      {#if containerStore.list.length === 0}
        <p class="empty">{t('containers.empty')}</p>
      {:else}
        <ul class="list">
          {#each containerStore.list as c (c.id)}
            <li class="entry">
              <span class="ename">{c.name}</span>
              <span class="num eweight">{formatGrams(c.weight_g)}</span>
              <button class="iconlink" onclick={() => startEdit(c)}
                      title={t('containers.edit')} aria-label={t('containers.edit')}>
                <i class="fa-solid fa-pen"></i>
              </button>
              <button class="iconlink danger" onclick={() => remove(c)}
                      title={t('containers.delete')} aria-label={t('containers.delete')}>
                <i class="fa-regular fa-trash-can"></i>
              </button>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  {/if}
</div>

<style>
  .picker {
    display: flex; flex-direction: column;
    gap: var(--sp-2);
    width: 100%;
  }
  .row {
    display: flex; gap: var(--sp-2);
    align-items: stretch;
  }
  select {
    flex: 1 1 auto;
    min-width: 0;
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 8px 11px;
    min-height: var(--tap);
    font-family: var(--num);
    font-variant-numeric: tabular-nums lining-nums slashed-zero;
    font-size: var(--fs-sm);
  }
  select:focus { outline: none; border-color: var(--accent); }

  .manage {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: var(--sp-3);
    display: flex; flex-direction: column;
    gap: var(--sp-3);
  }
  .form {
    display: flex; flex-direction: column;
    gap: var(--sp-2);
  }
  label {
    display: flex; flex-direction: column; gap: 4px;
    font-size: var(--fs-xs); color: var(--fg-dim);
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .row-flex { display: flex; gap: var(--sp-2); }
  .row-flex input { flex: 1; min-width: 0; }
  .btn-primary.small {
    flex: 0 0 auto; padding: 0 10px; min-width: var(--tap);
  }
  .actions {
    display: flex; gap: var(--sp-2);
    justify-content: flex-end;
    margin-top: var(--sp-1);
  }
  .actions .btn-primary,
  .actions .btn-warn {
    display: inline-flex; align-items: center; gap: 6px;
  }
  .btn-warn {
    min-height: var(--tap); padding: 0 var(--sp-3);
    background: transparent; border: 1px solid var(--border);
    color: var(--fg-dim); border-radius: var(--radius-sm);
    font-family: var(--sans); font-size: var(--fs-sm); font-weight: 500;
    cursor: pointer;
  }
  .btn-warn:hover { color: var(--fg); border-color: var(--fg-dim); }

  .list {
    list-style: none; margin: 0; padding: 0;
    display: flex; flex-direction: column;
    border-top: 1px solid var(--border);
  }
  .entry {
    display: grid;
    grid-template-columns: 1fr max-content max-content max-content;
    gap: var(--sp-2);
    align-items: center;
    padding: 6px 4px;
    border-bottom: 1px solid var(--border);
    font-size: var(--fs-sm);
  }
  .entry:last-child { border-bottom: none; }
  .ename { color: var(--fg); }
  .eweight { color: var(--accent); }
  .iconlink {
    background: transparent; border: none; padding: 4px 8px;
    color: var(--fg-mute); cursor: pointer;
    border-radius: var(--radius-sm);
    font-size: 14px;
  }
  .iconlink:hover { color: var(--accent); background: var(--bg-card-2); }
  .iconlink.danger:hover { color: var(--red); }
  .empty {
    margin: 0; padding: var(--sp-2); text-align: center;
    color: var(--fg-mute); font-size: var(--fs-xs);
  }
</style>
