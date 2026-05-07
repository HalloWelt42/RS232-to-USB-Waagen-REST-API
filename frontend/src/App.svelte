<script>
  import { onMount } from 'svelte';
  import { api, subscribe } from './lib/api.js';
  import WeightDisplay from './components/WeightDisplay.svelte';
  import HistoryList from './components/HistoryList.svelte';
  import HealthPanel from './components/HealthPanel.svelte';
  import CountPanel from './components/CountPanel.svelte';
  import ActionButtons from './components/ActionButtons.svelte';

  let reading       = $state(null);
  let history       = $state([]);
  let health        = $state(null);
  let connection    = $state('connecting');
  let healthError   = $state(null);
  let stableTarget  = $state(null);     // {weight_g, ts} – nach explizitem Klick
  let stableLoading = $state(false);

  const HISTORY_MAX = 200;

  onMount(() => {
    loadInitial();
    pollHealth();
    const healthTimer = setInterval(pollHealth, 5000);

    const unsubscribe = subscribe(
      (r) => {
        reading = r;
        history = [...history, r].slice(-HISTORY_MAX);
      },
      (state) => {
        connection = state.status;
      },
    );

    return () => {
      clearInterval(healthTimer);
      unsubscribe();
    };
  });

  async function loadInitial() {
    // Beim Mount sofort den letzten Wert und die History via REST holen,
    // damit das UI nicht erst auf den ersten WebSocket-Frame warten muss.
    try {
      const [hist, current] = await Promise.allSettled([
        api.history(50),
        api.weight(),
      ]);
      if (hist.status === 'fulfilled') {
        history = hist.value.items;
      }
      if (current.status === 'fulfilled') {
        reading = current.value;
      }
    } catch (e) {
      console.warn('Initial-Laden gescheitert:', e);
    }
  }

  async function pollHealth() {
    try {
      health = await api.health();
      healthError = null;
    } catch (e) {
      healthError = e.message;
    }
  }

  async function fetchStable() {
    stableLoading = true;
    stableTarget = null;
    try {
      const r = await api.stable(10);
      stableTarget = r;
    } catch (e) {
      stableTarget = { error: e.message };
    } finally {
      stableLoading = false;
    }
  }
</script>

<main>
  <header class="topbar">
    <h1>
      Waage <span class="model">G&amp;G PLC 6000g/0,1g</span>
    </h1>
    <a class="docs-link" href="/docs" target="_blank" rel="noopener">
      API-Dokumentation
    </a>
  </header>

  <div class="grid">
    <div class="primary">
      <WeightDisplay {reading} {connection} />

      <ActionButtons />

      <div class="actions">
        <button onclick={fetchStable} disabled={stableLoading}>
          {stableLoading ? 'Warte auf Stable...' : 'Stable-Wert abrufen'}
        </button>
        {#if stableTarget && !stableTarget.error}
          <span class="stable-result">
            Letzter Stable: <code>{stableTarget.weight_g} g</code>
          </span>
        {:else if stableTarget?.error}
          <span class="stable-error">{stableTarget.error}</span>
        {/if}
      </div>
    </div>

    <aside>
      <CountPanel {reading} />
      <HealthPanel {health} />
      <HistoryList {history} />
    </aside>
  </div>

  <footer>
    <span>v{__APP_VERSION__}</span>
    <span>
      <a href="https://github.com/HalloWelt42/RS232-to-USB-Waagen-REST-API"
         target="_blank" rel="noopener">GitHub</a>
    </span>
  </footer>
</main>

<style>
  main {
    min-height: 100vh;
    padding: 1.5rem clamp(1rem, 4vw, 3rem);
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  .topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
  }
  h1 {
    margin: 0;
    font-size: clamp(1.1rem, 3vw, 1.5rem);
    font-weight: 500;
    letter-spacing: 0.02em;
  }
  .model {
    color: var(--fg-dim);
    font-weight: 400;
    font-size: 0.85em;
    margin-left: 0.4rem;
  }
  .docs-link {
    font-family: var(--mono);
    font-size: 0.9rem;
  }

  .grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1.5rem;
    align-items: start;
    justify-items: center;
  }
  @media (min-width: 900px) {
    .grid {
      grid-template-columns: 1fr 1fr;
      justify-items: stretch;
    }
  }
  .primary {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
  aside {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: center;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
    justify-content: center;
  }
  .stable-result {
    font-family: var(--mono);
    color: var(--fg-dim);
  }
  .stable-error {
    color: var(--red);
    font-size: 0.9rem;
  }

  footer {
    margin-top: auto;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    color: var(--fg-dim);
    font-size: 0.85rem;
  }
</style>
