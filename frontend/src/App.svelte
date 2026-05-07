<script lang="ts">
  /**
   * Root-Komponente.
   *
   * Layout:
   *   ┌──────────────────────────────────────────────┐
   *   │  Topbar                                      │
   *   ├──────────────┬───────────────────────────────┤
   *   │ Sidebar      │ Right: Karten oder ToolView   │
   *   │ (persistent) │                               │
   *   ├──────────────┴───────────────────────────────┤
   *   │  Footer + ContactStrip                       │
   *   └──────────────────────────────────────────────┘
   *
   * Im Tool-Modus wird die Sidebar nicht ausgeblendet — der Anwender
   * sieht das Live-Gewicht ständig, auch während er Toleranz oder
   * Netto bedient.
   *
   * Mobile (≤ 800 px): Sidebar wird zum kompakten Header oben.
   */
  import { onMount, onDestroy } from 'svelte';
  import { route } from './lib/routing.svelte';
  import { live } from './lib/liveStore.svelte';
  import { api } from './lib/api';
  import { WaageStream } from './lib/stream';
  import { theme } from './lib/theme';
  import { helpStore } from './lib/helpStore.svelte';
  import { healthStore } from './lib/healthStore.svelte';
  import { modelStore } from './lib/modelStore.svelte';
  import { setDefaultResolution } from './lib/format';
  import type { ConnectionState, HealthInfo, MesslogEntry } from './lib/types';

  import Topbar from './components/Topbar.svelte';
  import Footer from './components/Footer.svelte';
  import ContactStrip from './components/ContactStrip.svelte';
  import Sidebar from './components/Sidebar.svelte';
  import CardGrid from './components/CardGrid.svelte';
  import ToolView from './components/ToolView.svelte';
  import HelpLayer from './components/HelpLayer.svelte';
  import Toast from './components/Toast.svelte';
  import SearchPalette from './components/SearchPalette.svelte';
  import SimulatorBanner from './components/SimulatorBanner.svelte';

  let health = $state<HealthInfo | null>(null);
  let messlog = $state<MesslogEntry[]>([]);
  let stream: WaageStream | null = null;
  let healthTimer: number | null = null;
  let messlogTimer: number | null = null;

  async function refreshHealth(): Promise<void> {
    try {
      health = await api.scale.health();
      healthStore.set(health);
    } catch {
      // offline tolerieren — bestehender Status bleibt sichtbar
    }
  }

  async function refreshMesslog(): Promise<void> {
    try {
      const res = await api.app.messlog(200);
      messlog = res.items;
    } catch { /* tolerieren */ }
  }

  onMount(() => {
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
    void modelStore.refresh();
    healthTimer = window.setInterval(refreshHealth, 5000);
    messlogTimer = window.setInterval(refreshMesslog, 4000);

    window.addEventListener('resize', () => helpStore.reflow());
  });

  onDestroy(() => {
    stream?.stop();
    if (healthTimer !== null) clearInterval(healthTimer);
    if (messlogTimer !== null) clearInterval(messlogTimer);
  });

  // Hilfe-Stack ist URL-getrieben: route.helpOpen ist die Wahrheit,
  // helpStore folgt; das macht Deeplinks wie ?help=count,glossary möglich.
  $effect(() => { helpStore.syncOpenIds(route.helpOpen); });

  // Bei Modell-Wechsel die Default-Auflösung der Format-Funktionen
  // anpassen — alle Anzeigen rendern sofort mit passender Präzision neu.
  $effect(() => { setDefaultResolution(modelStore.active.resolution_g); });

  let connection = $derived(live.connection);
</script>

<div class="layout">
  <Topbar />
  <SimulatorBanner {health} />

  <main class="body" data-mode={route.mode}>
    <div class="sidebar-wrap"><Sidebar {messlog} onMesslogChanged={refreshMesslog} /></div>
    <section class="right">
      {#if route.mode === 'tool'}
        <ToolView />
      {:else}
        <CardGrid />
      {/if}
    </section>
  </main>

  <Footer {health} {connection} />
  <ContactStrip />
</div>

<HelpLayer />
<Toast />
<SearchPalette />

<style>
  .layout {
    flex: 1 1 auto;
    display: flex; flex-direction: column;
    width: 100%; height: 100%;
    min-height: 0;
    overflow: hidden;
  }
  .body {
    flex: 1 1 auto;
    min-height: 0;
    display: flex;
    gap: var(--sp-3);
    /* Mehr Luft oben, damit aktive Tab-Indikatoren und Box-Schatten
       der Karten nicht in den Bereich der Topbar reinrutschen. */
    padding: var(--sp-4) var(--sp-3) var(--sp-3);
    overflow: hidden;
  }
  .right {
    flex: 1 1 auto;
    min-width: 0;
    min-height: 0;
    display: flex; flex-direction: column;
    overflow: hidden;
  }
  .sidebar-wrap {
    display: contents;       /* Sidebar bleibt direktes Flex-Kind */
  }

  /* Mobile-Switch früher: in der 800–900-px-Übergangsphase wurde die
     Sidebar zu schmal, um Live-Display und Messprotokoll lesbar zu
     halten — und gleichzeitig blieb für die Tool-Karten zu wenig
     Platz. Wir wechseln deshalb ab 900 px ins Single-Column-Layout. */
  @media (max-width: 900px) {
    .body {
      flex-direction: column;
      gap: var(--sp-2);
      padding: var(--sp-2);
      overflow-y: auto;
    }
    .right { flex: 1 1 auto; }
    /* Im Tool-Modus die Sidebar ausblenden — Werkzeug-Panels zeigen
       den Live-Wert eh prominent, doppelte Anzeige unnötig. Im
       Dashboard-Modus bleibt die Sidebar sichtbar, die LiveWaage
       klebt sticky am oberen Rand und nur die Messprotokoll-Liste
       scrollt intern (siehe LiveWaage.svelte / MessLog.svelte). */
    .body[data-mode="tool"] .sidebar-wrap { display: none; }
  }
</style>
