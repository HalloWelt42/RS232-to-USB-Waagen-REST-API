<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from './lib/api';
  import { WaageStream } from './lib/stream';
  import { HistoryTracker } from './lib/historyTracker';
  import type {
    ConnectionState,
    HealthInfo,
    Reading,
  } from './lib/types';

  import WeightDisplay from './components/WeightDisplay.svelte';
  import Sparkline from './components/Sparkline.svelte';
  import HistoryList from './components/HistoryList.svelte';
  import ActionButtons from './components/ActionButtons.svelte';
  import TolerancePanel from './components/TolerancePanel.svelte';
  import NettoPanel from './components/NettoPanel.svelte';
  import CountPanel from './components/CountPanel.svelte';
  import SamplesPanel from './components/SamplesPanel.svelte';
  import StatusFooter from './components/StatusFooter.svelte';

  type TabKey = 'tolerance' | 'netto' | 'count' | 'samples';

  interface TabDef {
    key: TabKey;
    label: string;
  }

  const tabs: TabDef[] = [
    { key: 'tolerance', label: 'Toleranz' },
    { key: 'netto',     label: 'Netto' },
    { key: 'count',     label: 'Zählen' },
    { key: 'samples',   label: 'Erfassen' },
  ];

  let activeTab = $state<TabKey>('tolerance');

  // ---- State ----
  let reading    = $state<Reading | null>(null);
  let history    = $state<Reading[]>([]);
  let health     = $state<HealthInfo | null>(null);
  let connection = $state<ConnectionState>('connecting');

  const tracker = new HistoryTracker(200, 0.05);

  onMount(() => {
    void loadInitial();
    void pollHealth();
    const healthTimer = window.setInterval(() => void pollHealth(), 5000);

    const stream = new WaageStream(
      '/stream',
      (r: Reading) => {
        reading = r;
        if (tracker.push(r)) {
          history = tracker.get();
        }
      },
      (state) => { connection = state.status; },
    );
    stream.start();

    return () => {
      clearInterval(healthTimer);
      stream.stop();
    };
  });

  async function loadInitial(): Promise<void> {
    try {
      const [hist, current] = await Promise.allSettled([
        api.history(200),
        api.weight(),
      ]);
      if (hist.status === 'fulfilled') {
        tracker.hydrate(hist.value.items);
        history = tracker.get();
      }
      if (current.status === 'fulfilled') {
        reading = current.value;
      }
    } catch (e) {
      console.warn('Initial-Laden gescheitert:', e);
    }
  }

  async function pollHealth(): Promise<void> {
    try { health = await api.health(); }
    catch (e) { console.warn('Health-Poll Fehler:', e); }
  }
</script>

<div class="app">
  <header class="topbar">
    <h1>
      <span class="title">Waage</span>
      <span class="model">G&amp;G PLC 6000g/0,1g</span>
    </h1>
    <div class="header-actions">
      <ActionButtons />
      <a class="docs-link" href="/docs" target="_blank" rel="noopener">API-Doku</a>
    </div>
  </header>

  <main class="content">
    <section class="left">
      <WeightDisplay {reading} {connection} />
      <Sparkline {history} windowSeconds={60} />
      <HistoryList {history} />
    </section>

    <section class="right">
      <nav class="tabs">
        {#each tabs as t (t.key)}
          <button
            class:active={activeTab === t.key}
            onclick={() => (activeTab = t.key)}
          >{t.label}</button>
        {/each}
      </nav>
      <div class="tab-body">
        {#if activeTab === 'tolerance'}
          <TolerancePanel {reading} />
        {:else if activeTab === 'netto'}
          <NettoPanel {reading} />
        {:else if activeTab === 'count'}
          <CountPanel {reading} />
        {:else if activeTab === 'samples'}
          <SamplesPanel {reading} />
        {/if}
      </div>
    </section>
  </main>

  <StatusFooter {health} {connection} />
</div>

<style>
  .app {
    display: flex;
    flex-direction: column;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
  }

  .topbar {
    height: var(--header-h);
    background: var(--bg-card);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.25rem;
    flex: 0 0 auto;
  }
  h1 {
    margin: 0;
    font-size: 1rem;
    font-weight: 500;
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
  }
  .title { font-weight: 600; letter-spacing: 0.04em; }
  .model { color: var(--fg-dim); font-size: 0.85rem; }
  .header-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .docs-link {
    font-family: var(--mono);
    font-size: 0.8rem;
    color: var(--fg-dim);
    padding: 0.35rem 0.7rem;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
  }
  .docs-link:hover {
    color: var(--accent);
    border-color: var(--accent);
    text-decoration: none;
  }

  .content {
    flex: 1 1 auto;
    min-height: 0;
    display: grid;
    grid-template-columns: minmax(360px, 1fr) minmax(420px, 1.2fr);
    gap: 1rem;
    padding: 1rem;
    overflow: hidden;
  }

  .left {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    min-height: 0;
  }

  .right {
    display: flex;
    flex-direction: column;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
    min-height: 0;
  }

  .tabs {
    display: flex;
    border-bottom: 1px solid var(--border);
    background: var(--bg);
    flex: 0 0 auto;
  }
  .tabs button {
    flex: 1 1 0;
    background: transparent;
    border: none;
    border-radius: 0;
    border-bottom: 2px solid transparent;
    padding: 0.7rem 0.5rem;
    font-size: 0.85rem;
    color: var(--fg-dim);
    cursor: pointer;
  }
  .tabs button:hover {
    background: var(--bg-card-2);
    color: var(--fg);
  }
  .tabs button.active {
    color: var(--fg);
    border-bottom-color: var(--accent);
    background: var(--bg-card);
  }

  .tab-body {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    padding: 1.25rem;
  }

  @media (max-width: 800px) {
    .content {
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr;
      overflow-y: auto;
    }
    .left { min-height: 0; }
  }
</style>
