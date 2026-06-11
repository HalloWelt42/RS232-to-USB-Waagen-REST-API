<script lang="ts">
  /**
   * Einstellungen — Modell-Auswahl + Theme + Lizenz-Hinweis.
   * Anschluss/Polling sind aktuell server-seitig konfiguriert; der Anwender
   * sieht hier die aktiven Werte und kann das Modell wechseln.
   */
  import { onMount } from 'svelte';
  import { api } from '../../lib/api';
  import { toast } from '../../lib/toast.svelte';
  import { theme as themeManager, type Theme } from '../../lib/theme';
  import { t } from '../../lib/i18n';
  import { modelStore } from '../../lib/modelStore.svelte';
  import HelpButton from '../HelpButton.svelte';
  import ModelTolerances from '../ModelTolerances.svelte';
  import type { ScaleConfig, ScaleModel, HealthInfo, ConnectInfo } from '../../lib/types';

  let models = $state<ScaleModel[]>([]);
  let cfg = $state<ScaleConfig | null>(null);
  let health = $state<HealthInfo | null>(null);
  let busy = $state(false);
  let currentTheme = $state<Theme>(themeManager.get());

  // --- Connect-Modul (Messwert-Weiterleitung) ---------------------------
  let connect = $state<ConnectInfo | null>(null);
  let cEnabled = $state(false);
  let cUrl = $state('');
  let cHeader = $state('X-Device-Token');
  let cToken = $state('');           // leer = bestehendes Token behalten
  let cInterval = $state('1.0');
  let cOnlyStable = $state(true);
  let cSendNetto = $state(false);
  let cBusy = $state(false);
  let cTestResult = $state<string | null>(null);

  async function loadConnect(): Promise<void> {
    try {
      connect = await api.connect.get();
      cEnabled = connect.enabled;
      cUrl = connect.url;
      cHeader = connect.auth_header;
      cInterval = String(connect.interval_s);
      cOnlyStable = connect.only_stable;
      cSendNetto = connect.send_netto;
      cToken = '';
    } catch {
      /* Backend ohne Connect-Modul -- Karte zeigt Ladefehler-Hint */
    }
  }

  async function saveConnect(): Promise<void> {
    cBusy = true;
    cTestResult = null;
    try {
      connect = await api.connect.set({
        enabled: cEnabled,
        url: cUrl.trim(),
        auth_header: cHeader.trim() || 'X-Device-Token',
        auth_token: cToken.trim() === '' ? null : cToken.trim(),
        interval_s: Math.max(0.2, parseFloat(cInterval.replace(',', '.')) || 1),
        only_stable: cOnlyStable,
        send_netto: cSendNetto,
        extra_fields: connect?.extra_fields ?? {},
      });
      cToken = '';
      toast.show(t('toast.settingSaved'), 'ok');
    } catch (e) {
      toast.show((e as Error).message, 'error');
    } finally {
      cBusy = false;
    }
  }

  async function testConnect(): Promise<void> {
    cBusy = true;
    cTestResult = null;
    try {
      const res = await api.connect.test();
      cTestResult = res.detail;
      toast.show(res.ok ? t('connect.testOk') : res.detail, res.ok ? 'ok' : 'error');
      connect = await api.connect.get();
    } catch (e) {
      toast.show((e as Error).message, 'error');
    } finally {
      cBusy = false;
    }
  }

  /**
   * „Alles zurücksetzen": leert alle persistenten Daten — Mess-Snapshots,
   * Messprotokoll, Behälter-Bibliothek, Stückzähl-Vorlagen, Differenz-
   * Schichten und Toleranz/Netto/Count-Zustände. Modell-Wahl und
   * Theme bleiben erhalten.
   *
   * Direkt — kein Bestätigungsdialog (Vorgabe Anwender: Löschen ist
   * Löschen). Der rote Karten-Stil und die Beschriftung „Alles
   * zurücksetzen" sind die einzige Warnstufe; ein versehentlicher
   * Klick lässt sich über die Tools schnell wieder aufbauen.
   */
  async function resetAllData(): Promise<void> {
    busy = true;
    try {
      await Promise.all([
        api.app.samplesClear(null),
        api.app.messlogClear(),
        api.app.containersClear(),
        api.app.countTemplatesClear(),
        api.app.differenzClear(),
        api.app.toleranceClear(),
        api.app.nettoTareClear(),
        api.app.countReset(),
      ]);
      toast.show(t('settings.resetAllDone'), 'ok');
    } catch (e) {
      toast.show((e as Error).message, 'error');
    } finally {
      busy = false;
    }
  }

  async function setSource(mode: 'live' | 'simulate'): Promise<void> {
    busy = true;
    try {
      await api.scale.setSource(mode);
      health = await api.scale.health();
      toast.show(t('toast.settingSaved'), 'ok');
    } catch (e) {
      toast.show((e as Error).message, 'error');
    } finally {
      busy = false;
    }
  }

  async function refresh(): Promise<void> {
    try {
      [models, cfg, health] = await Promise.all([
        api.scale.models(), api.scale.config(), api.scale.health(),
      ]);
    } catch (e) { toast.show((e as Error).message, 'error'); }
  }

  async function pickModel(id: string): Promise<void> {
    busy = true;
    try {
      cfg = await api.scale.setConfig(id);
      modelStore.setActive(cfg.active_model);
      toast.show(t('toast.settingSaved'), 'ok');
    }
    catch (e) { toast.show((e as Error).message, 'error'); }
    finally { busy = false; }
  }

  function setTheme(c: Theme): void {
    currentTheme = c;
    themeManager.set(c);
  }

  onMount(() => themeManager.subscribe((tt) => { currentTheme = tt; }));

  // Modelle nach Hersteller/Serie gruppieren für übersichtliche Anzeige
  let grouped = $derived.by(() => {
    const groups: Record<string, ScaleModel[]> = {};
    for (const m of models) {
      const key = `${m.manufacturer} · ${m.series}`;
      if (!groups[key]) groups[key] = [];
      groups[key].push(m);
    }
    return Object.entries(groups);
  });

  onMount(() => {
    void refresh();
    void loadConnect();
  });
</script>

<section class="panel">
  <header>
    <h2>{t('tools.settings')}</h2>
    <HelpButton id="settings" />
  </header>

  <div class="form">
    <div class="card">
      <h3>{t('settingsPanel.themeMode')}</h3>
      <div class="theme-row">
        <button class:active={currentTheme==='auto'}  onclick={() => setTheme('auto')}>
          <i class="fa-solid fa-circle-half-stroke"></i> {t('settingsPanel.themeAuto')}
        </button>
        <button class:active={currentTheme==='light'} onclick={() => setTheme('light')}>
          <i class="fa-solid fa-sun"></i> {t('settingsPanel.themeLight')}
        </button>
        <button class:active={currentTheme==='dark'}  onclick={() => setTheme('dark')}>
          <i class="fa-solid fa-moon"></i> {t('settingsPanel.themeDark')}
        </button>
      </div>
    </div>

    <div class="card">
      <h3>{t('settingsPanel.activeModel')}</h3>
      {#if cfg}
        <p class="active">
          <span class="num">{cfg.active_model.manufacturer} {cfg.active_model.series}-{cfg.active_model.name}</span>
          <span class="meta">
            {t('settingsPanel.modelMax')} {cfg.active_model.max_g} g · {t('settingsPanel.modelResolution')} {cfg.active_model.resolution_g} g
          </span>
        </p>
      {:else}
        <p>{t('settingsPanel.modelLoading')}</p>
      {/if}

      <ModelTolerances />

      <div class="models">
        {#each grouped as [groupName, list] (groupName)}
          <details>
            <summary>{groupName} <span class="count num">{list.length}</span></summary>
            <ul>
              {#each list as m (m.id)}
                <li>
                  <button class="model-row"
                          class:active={cfg?.active_model_id === m.id}
                          onclick={() => pickModel(m.id)}
                          disabled={busy}>
                    <span class="m-name">{m.name}</span>
                    <span class="num m-max">{t('settingsPanel.modelMax')} {m.max_g} g</span>
                    <span class="num m-res">±{m.resolution_g} g</span>
                  </button>
                </li>
              {/each}
            </ul>
          </details>
        {/each}
      </div>
    </div>

    <div class="card source">
      <h3>{t('settingsPanel.source')}</h3>
      <div class="theme-row">
        <button class:active={health?.source_mode === 'live'}
                onclick={() => setSource('live')} disabled={busy}>
          <i class="fa-solid fa-plug"></i> {t('topbar.sourceLive')}
        </button>
        <button class:active={health?.source_mode === 'simulate'}
                onclick={() => setSource('simulate')} disabled={busy}>
          <i class="fa-solid fa-flask-vial"></i> {t('topbar.sourceSimulate')}
        </button>
      </div>
      {#if health?.simulated}
        <p class="hint warn"><i class="fa-solid fa-triangle-exclamation"></i>
          {t('topbar.simulatedWarning')}</p>
      {/if}
    </div>

    <div class="card">
      <h3>{t('settingsPanel.connection')}</h3>
      {#if health}
        <ul class="kv">
          <li><span class="k">{t('settingsPanel.port')}</span>          <span class="num v">{health.port}</span></li>
          <li><span class="k">{t('settingsPanel.baudrate')}</span>      <span class="num v">{health.baudrate}</span></li>
          <li><span class="k">{t('settingsPanel.reader')}</span>        <span class="num v">{health.reader_alive ? t('settingsPanel.readerActive') : t('settingsPanel.readerInactive')}</span></li>
          <li><span class="k">{t('settingsPanel.backendVersion')}</span><span class="num v">{health.version}</span></li>
        </ul>
      {/if}
      <p class="hint">{t('settingsPanel.connectionInfo')}</p>
    </div>

    <div class="card connect-card">
      <h3>
        <i class="fa-solid fa-tower-broadcast"></i> {t('connect.title')}
        <HelpButton id="connect" />
      </h3>
      <p class="hint">{t('connect.info')}</p>

      <label class="connect-toggle">
        <input type="checkbox" bind:checked={cEnabled} />
        <span>{t('connect.enabled')}</span>
      </label>

      <label class="connect-field">
        <span class="connect-label">{t('connect.url')}</span>
        <input
          type="url"
          bind:value={cUrl}
          placeholder="https://example.org/api/v1/scale/measurement"
          spellcheck="false"
        />
      </label>

      <div class="connect-grid">
        <label class="connect-field">
          <span class="connect-label">{t('connect.authHeader')}</span>
          <input type="text" bind:value={cHeader} spellcheck="false" />
        </label>
        <label class="connect-field">
          <span class="connect-label">
            {t('connect.authToken')}
            {#if connect?.auth_token_set}
              <span class="num connect-token-hint">{connect.auth_token_hint}</span>
            {/if}
          </span>
          <input
            type="password"
            bind:value={cToken}
            placeholder={connect?.auth_token_set ? t('connect.tokenKeep') : t('connect.tokenEmpty')}
            spellcheck="false"
            autocomplete="off"
          />
        </label>
        <label class="connect-field">
          <span class="connect-label">{t('connect.interval')}</span>
          <input type="text" inputmode="decimal" bind:value={cInterval} />
        </label>
      </div>

      <div class="connect-options">
        <label><input type="checkbox" bind:checked={cOnlyStable} /> {t('connect.onlyStable')}</label>
        <label><input type="checkbox" bind:checked={cSendNetto} /> {t('connect.sendNetto')}</label>
      </div>

      <div class="connect-actions">
        <button class="btn" onclick={saveConnect} disabled={cBusy}>
          <i class="fa-solid fa-floppy-disk"></i> {t('connect.save')}
        </button>
        <button class="btn" onclick={testConnect} disabled={cBusy || !connect?.url}>
          <i class="fa-solid fa-paper-plane"></i> {t('connect.test')}
        </button>
      </div>

      {#if cTestResult}
        <p class="hint num">{cTestResult}</p>
      {/if}

      {#if connect}
        <ul class="kv">
          <li>
            <span class="k">{t('connect.statusLabel')}</span>
            <span class="num v">
              {connect.status.running ? t('connect.statusRunning') : t('connect.statusIdle')}
            </span>
          </li>
          {#if connect.status.last_sent_at}
            <li>
              <span class="k">{t('connect.lastSent')}</span>
              <span class="num v">
                {connect.status.last_sent_at}
                {#if connect.status.last_http_status}
                  · HTTP {connect.status.last_http_status}
                {/if}
                · {connect.status.sent_count}x
              </span>
            </li>
          {/if}
          {#if connect.status.last_error}
            <li>
              <span class="k">{t('connect.lastError')}</span>
              <span class="num v">{connect.status.last_error}</span>
            </li>
          {/if}
        </ul>
      {/if}
    </div>

    <div class="card reset-card">
      <h3>{t('settings.resetAllTitle')}</h3>
      <p class="hint">{t('settings.resetAllInfo')}</p>
      <button class="btn-warn full" onclick={resetAllData} disabled={busy}>
        <i class="fa-solid fa-eraser"></i>
        {t('settings.resetAllButton')}
      </button>
    </div>

    <div class="card disclaimer-card">
      <h3>{t('disclaimer.title')}</h3>
      <p class="disclaimer-short">{t('disclaimer.short')}</p>
      <p class="disclaimer-body">{t('disclaimer.body')}</p>
      <p class="hint">
        <a href="https://github.com/HalloWelt42/RS232-to-USB-Waagen-REST-API/blob/main/DISCLAIMER.md"
           target="_blank" rel="noopener">{t('disclaimer.fullTextLink')}</a>
      </p>
    </div>

    <div class="card license">
      <h3>{t('settingsPanel.licenseTitle')}</h3>
      <p class="license-line">{t('contact.license')}</p>
      <ul class="license-list">
        <li><i class="fa-solid fa-check"></i> {t('settingsPanel.licenseRule_privateUse')}</li>
        <li><i class="fa-solid fa-check"></i> {t('settingsPanel.licenseRule_privateMod')}</li>
        <li><i class="fa-solid fa-check"></i> {t('settingsPanel.licenseRule_pullRequests')}</li>
        <li><i class="fa-solid fa-xmark warn"></i> {t('settingsPanel.licenseRule_noCommercial')}</li>
        <li><i class="fa-solid fa-xmark warn"></i> {t('settingsPanel.licenseRule_noPublish')}</li>
      </ul>
      <p class="hint">
        {t('settingsPanel.licenseFulltext')} <a href="https://github.com/HalloWelt42/RS232-to-USB-Waagen-REST-API/blob/main/LICENSE"
                                    target="_blank" rel="noopener">LICENSE</a>
        · {t('settingsPanel.sourceCode')} <a href="https://github.com/HalloWelt42/RS232-to-USB-Waagen-REST-API"
                        target="_blank" rel="noopener">github.com/HalloWelt42</a>
      </p>
    </div>
  </div>
</section>

<style>
  .panel {
    flex: 1 1 auto; min-height: 0; overflow-y: auto;
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  header { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3); }
  header h2 { margin: 0; font-size: var(--fs-xl); font-weight: 600; }

  .form {
    max-width: 720px; margin-inline: auto; width: 100%;
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  .card {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-3) var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-2);
  }
  .card h3 {
    margin: 0;
    font-size: var(--fs-md);
    font-weight: 600;
    color: var(--accent);
    letter-spacing: 0.02em;
  }

  .theme-row { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
  .theme-row button {
    flex: 1 1 0;
    min-height: var(--tap);
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--fg-dim);
    border-radius: var(--radius-sm);
    cursor: pointer;
    display: inline-flex; align-items: center; justify-content: center;
    gap: 6px;
    font-size: var(--fs-sm);
  }
  .theme-row button.active {
    color: var(--accent); border-color: var(--accent);
    background: color-mix(in srgb, var(--accent) 10%, transparent);
  }

  .active {
    margin: 0;
    display: flex; flex-direction: column; gap: 4px;
  }
  .meta { font-size: var(--fs-xs); color: var(--fg-mute); }

  .models {
    display: flex; flex-direction: column; gap: var(--sp-2);
    margin-top: var(--sp-2);
  }
  details {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
  }
  summary {
    padding: 8px var(--sp-3);
    cursor: pointer;
    display: flex; justify-content: space-between; align-items: center;
    font-size: var(--fs-sm);
    color: var(--fg);
    list-style: none;
  }
  summary::-webkit-details-marker { display: none; }
  .count { font-size: var(--fs-xs); color: var(--fg-mute); }
  details ul { list-style: none; margin: 0; padding: 0 0 4px; }
  details li { border-top: 1px solid var(--border); }
  .model-row {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr max-content max-content;
    gap: var(--sp-2);
    padding: 6px var(--sp-3);
    background: transparent; border: none;
    text-align: left;
    color: var(--fg-dim); font-size: var(--fs-sm);
    cursor: pointer;
  }
  .model-row:hover { color: var(--accent); }
  .model-row.active {
    color: var(--accent);
    background: color-mix(in srgb, var(--accent) 8%, transparent);
  }
  .m-max, .m-res { font-size: var(--fs-xs); color: var(--fg-mute); }

  .kv { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
  .kv li { display: flex; justify-content: space-between; align-items: baseline; }
  .k { font-size: var(--fs-xs); color: var(--fg-mute); letter-spacing: 0.05em; text-transform: uppercase; }
  .v { font-size: var(--fs-sm); }

  .hint {
    margin: 0; font-size: var(--fs-xs); color: var(--fg-mute);
    line-height: 1.5;
  }

  .license-line {
    margin: 0;
    font-size: var(--fs-sm);
    color: var(--fg);
    line-height: 1.5;
  }
  .license-list {
    list-style: none; margin: 0; padding: 0;
    display: flex; flex-direction: column; gap: 4px;
    font-size: var(--fs-sm);
    color: var(--fg-dim);
  }
  .license-list li { display: flex; align-items: center; gap: 8px; }
  .license-list i { color: var(--green); width: 14px; text-align: center; }
  .license-list i.warn { color: var(--red); }

  .hint.warn {
    color: var(--orange);
    display: inline-flex; align-items: center; gap: 6px;
  }
  /* Connect-Karte (Messwert-Weiterleitung) */
  .connect-card h3 { display: inline-flex; align-items: center; gap: 8px; }
  .connect-toggle {
    display: inline-flex; align-items: center; gap: 8px;
    margin: var(--sp-2) 0;
    font-weight: 600;
    cursor: pointer;
  }
  .connect-field {
    display: flex; flex-direction: column; gap: 4px;
    margin-bottom: var(--sp-2);
  }
  .connect-label {
    font-size: var(--fs-sm);
    color: var(--fg-dim);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: inline-flex; align-items: center; gap: 8px;
  }
  .connect-token-hint { color: var(--fg-dim); text-transform: none; }
  .connect-field input {
    min-height: var(--tap);
    padding: 0 var(--sp-2);
    background: var(--bg-inset, transparent);
    border: 1px solid var(--line);
    border-radius: var(--radius-sm);
    color: var(--fg);
    font-family: var(--mono);
    font-size: var(--fs-sm);
  }
  .connect-field input:focus { outline: none; border-color: var(--accent); }
  .connect-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 110px;
    gap: var(--sp-2);
  }
  @media (max-width: 640px) {
    .connect-grid { grid-template-columns: 1fr; }
  }
  .connect-options {
    display: flex; gap: var(--sp-3); flex-wrap: wrap;
    margin-bottom: var(--sp-2);
  }
  .connect-options label {
    display: inline-flex; align-items: center; gap: 6px;
    cursor: pointer;
    font-size: var(--fs-sm);
  }
  .connect-actions { display: flex; gap: var(--sp-2); flex-wrap: wrap; }
  .connect-actions .btn {
    display: inline-flex; align-items: center; gap: 6px;
    min-height: var(--tap);
    padding: 0 var(--sp-3);
    background: transparent;
    border: 1px solid var(--line);
    border-radius: var(--radius-sm);
    color: var(--fg);
    font-family: var(--sans); font-size: var(--fs-sm); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em;
    cursor: pointer;
  }
  .connect-actions .btn:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
  .connect-actions .btn:disabled { opacity: 0.5; cursor: not-allowed; }

  .reset-card { border-color: var(--red); }
  .reset-card h3 { color: var(--red); }
  .reset-card .btn-warn.full {
    width: 100%;
    border-color: var(--red);
    color: var(--red);
    margin-top: var(--sp-2);
    display: inline-flex; align-items: center; justify-content: center;
    gap: 6px;
    min-height: var(--tap);
    padding: 0 var(--sp-3);
    background: transparent;
    border-radius: var(--radius-sm);
    font-family: var(--sans); font-size: var(--fs-sm); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em;
    cursor: pointer;
  }
  .reset-card .btn-warn.full:hover:not(:disabled) {
    background: color-mix(in srgb, var(--red) 14%, transparent);
  }

  .disclaimer-card { border-color: var(--orange); }
  .disclaimer-card h3 { color: var(--orange); }
  .disclaimer-short {
    margin: 0;
    font-size: var(--fs-sm);
    font-weight: 600;
    color: var(--orange);
    letter-spacing: 0.02em;
  }
  .disclaimer-body {
    margin: 0;
    font-size: 18px;       /* gut lesbar */
    line-height: 1.6;
    color: var(--fg);
  }
</style>
