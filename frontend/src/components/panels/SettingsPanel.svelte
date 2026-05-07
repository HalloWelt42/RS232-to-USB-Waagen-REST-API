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
  import type { ScaleConfig, ScaleModel, HealthInfo } from '../../lib/types';

  let models = $state<ScaleModel[]>([]);
  let cfg = $state<ScaleConfig | null>(null);
  let health = $state<HealthInfo | null>(null);
  let busy = $state(false);
  let currentTheme = $state<Theme>(themeManager.get());

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

  onMount(refresh);
</script>

<section class="panel">
  <header>
    <h2>{t('tools.settings')}</h2>
    <HelpButton id="settings" />
  </header>

  <div class="form">
    <div class="card">
      <h3>Anzeigemodus</h3>
      <div class="theme-row">
        <button class:active={currentTheme==='auto'}  onclick={() => setTheme('auto')}>
          <i class="fa-solid fa-circle-half-stroke"></i> Automatisch
        </button>
        <button class:active={currentTheme==='light'} onclick={() => setTheme('light')}>
          <i class="fa-solid fa-sun"></i> Hell
        </button>
        <button class:active={currentTheme==='dark'}  onclick={() => setTheme('dark')}>
          <i class="fa-solid fa-moon"></i> Dunkel
        </button>
      </div>
    </div>

    <div class="card">
      <h3>Aktives Modell</h3>
      {#if cfg}
        <p class="active">
          <span class="num">{cfg.active_model.manufacturer} {cfg.active_model.series}-{cfg.active_model.name}</span>
          <span class="meta">
            max {cfg.active_model.max_g} g · Auflösung {cfg.active_model.resolution_g} g
          </span>
        </p>
      {:else}
        <p>Wird geladen …</p>
      {/if}

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
                    <span class="num m-max">max {m.max_g} g</span>
                    <span class="num m-res">±{m.resolution_g} g</span>
                  </button>
                </li>
              {/each}
            </ul>
          </details>
        {/each}
      </div>
    </div>

    <div class="card">
      <h3>Anschluss</h3>
      {#if health}
        <ul class="kv">
          <li><span class="k">Port</span>          <span class="num v">{health.port}</span></li>
          <li><span class="k">Baudrate</span>      <span class="num v">{health.baudrate}</span></li>
          <li><span class="k">Reader</span>        <span class="num v">{health.reader_alive ? 'aktiv' : 'aus'}</span></li>
          <li><span class="k">Backend-Version</span><span class="num v">{health.version}</span></li>
        </ul>
      {/if}
      <p class="hint">
        Anschluss und Baudrate sind aktuell server-seitig konfiguriert. Das
        Backend findet den FTDI-Adapter automatisch.
      </p>
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
      <h3>Lizenz</h3>
      <p class="license-line">{t('contact.license')}</p>
      <ul class="license-list">
        <li><i class="fa-solid fa-check"></i> Private, nicht-kommerzielle Nutzung</li>
        <li><i class="fa-solid fa-check"></i> Private Modifikation für eigenen Gebrauch</li>
        <li><i class="fa-solid fa-check"></i> Pull Requests willkommen</li>
        <li><i class="fa-solid fa-xmark warn"></i> Keine kommerzielle Nutzung</li>
        <li><i class="fa-solid fa-xmark warn"></i> Keine Veröffentlichung modifizierter Versionen</li>
      </ul>
      <p class="hint">
        Volltext im Repository: <a href="https://github.com/HalloWelt42/RS232-to-USB-Waagen-REST-API/blob/main/LICENSE"
                                    target="_blank" rel="noopener">LICENSE</a>
        · Quellcode: <a href="https://github.com/HalloWelt42/RS232-to-USB-Waagen-REST-API"
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
