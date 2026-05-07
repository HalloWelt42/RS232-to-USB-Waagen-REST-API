<script lang="ts">
  /**
   * Root-Komponente.
   *
   * - Routing initialisieren (Hash → mode/activeTool)
   * - WebSocket /scale/stream verbinden, in liveStore einspeisen
   * - Health-Polling alle 5 s für den Footer
   * - Messprotokoll initial vom Backend laden
   * - Layout: Topbar, Body (Dashboard | ToolView), Footer, ContactStrip
   * - HelpLayer und Toast als Overlay
   */
  import { onMount, onDestroy } from 'svelte';
  import { route } from './lib/routing.svelte';
  import { live } from './lib/liveStore.svelte';
  import { api } from './lib/api';
  import { WaageStream } from './lib/stream';
  import { theme } from './lib/theme';
  import type { ConnectionState, HealthInfo, MesslogEntry } from './lib/types';

  import Topbar from './components/Topbar.svelte';
  import Footer from './components/Footer.svelte';
  import ContactStrip from './components/ContactStrip.svelte';
  import Dashboard from './components/Dashboard.svelte';
  import ToolView from './components/ToolView.svelte';
  import HelpLayer from './components/HelpLayer.svelte';
  import Toast from './components/Toast.svelte';

  let health = $state<HealthInfo | null>(null);
  let messlog = $state<MesslogEntry[]>([]);
  let stream: WaageStream | null = null;
  let healthTimer: number | null = null;
  let messlogTimer: number | null = null;

  async function refreshHealth(): Promise<void> {
    try { health = await api.scale.health(); }
    catch { /* offline tolerieren */ }
  }

  async function refreshMesslog(): Promise<void> {
    try {
      const res = await api.app.messlog(200);
      messlog = res.items;
    } catch { /* tolerieren */ }
  }

  onMount(() => {
    // Theme initialisieren — Konstruktor setzt data-theme bereits
    theme.get();

    route.init();

    stream = new WaageStream(
      api.scale.streamUrl(),
      (r) => live.set(r),
      (s) => live.setConnection(s.status as ConnectionState),
    );
    stream.start();

    void refreshHealth();
    void refreshMesslog();
    healthTimer = window.setInterval(refreshHealth, 5000);
    messlogTimer = window.setInterval(refreshMesslog, 4000);
  });

  onDestroy(() => {
    stream?.stop();
    if (healthTimer !== null) clearInterval(healthTimer);
    if (messlogTimer !== null) clearInterval(messlogTimer);
  });

  let connection = $derived(live.connection);
</script>

<div class="layout">
  <Topbar />

  {#if route.mode === 'tool'}
    <ToolView />
  {:else}
    <Dashboard {messlog} />
  {/if}

  <Footer {health} {connection} />
  <ContactStrip />
</div>

<HelpLayer />
<Toast />

<style>
  .layout {
    flex: 1 1 auto;
    display: flex; flex-direction: column;
    width: 100%; height: 100%;
    min-height: 0;
    overflow: hidden;
  }
</style>
