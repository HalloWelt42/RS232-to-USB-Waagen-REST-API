<script lang="ts">
  /**
   * Einmaliger Begrüßungs-Hinweis — sieht der Anwender beim allerersten
   * Aufruf. Lässt sich für immer wegklicken (Speicher in localStorage)
   * und ist absichtlich klein, damit er nicht bevormundet.
   */
  import { dismissWelcome } from '../lib/welcome';
  import { helpStore } from '../lib/helpStore.svelte';

  interface Props {
    onClose: () => void;
  }
  let { onClose }: Props = $props();

  function dismiss(): void {
    dismissWelcome();
    onClose();
  }

  function showOverview(): void {
    helpStore.open('overview');
    dismissWelcome();
    onClose();
  }
</script>

<aside class="hint" role="dialog" aria-labelledby="welcome-title">
  <div class="content">
    <h2 id="welcome-title">Willkommen</h2>
    <p>
      Das ist die Live-Anzeige Ihrer Waage. Links sehen Sie das Gewicht,
      rechts finden Sie Werkzeuge für Toleranz, Netto, Stückzählung und
      Werte-Erfassung.
    </p>
    <p class="small">
      In jedem Bereich gibt es einen Fragezeichen-Knopf — der öffnet ein
      Hilfe-Fenster, das Sie frei verschieben können.
    </p>
    <div class="actions">
      <button class="primary" onclick={showOverview}>Kurze Einführung</button>
      <button onclick={dismiss}>Schon klar, los geht's</button>
    </div>
  </div>
</aside>

<style>
  .hint {
    position: fixed;
    bottom: calc(var(--footer-h) + var(--sp-3));
    right: var(--sp-3);
    z-index: 200;
    max-width: 380px;
    background: var(--bg-elev);
    border: 1px solid var(--accent);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    animation: slide-in 0.3s ease-out;
  }
  .content {
    padding: var(--sp-4);
    display: flex;
    flex-direction: column;
    gap: var(--sp-3);
  }
  h2 {
    margin: 0;
    font-size: var(--fs-lg);
    font-weight: 600;
  }
  p {
    margin: 0;
    font-size: var(--fs-sm);
    line-height: 1.55;
    color: var(--fg);
  }
  p.small {
    color: var(--fg-dim);
    font-size: var(--fs-xs);
  }
  .actions {
    display: flex;
    gap: var(--sp-2);
    margin-top: var(--sp-1);
  }
  .actions button { flex: 1; }
  .primary {
    background: var(--bg-card-2);
    border-color: var(--accent);
    color: var(--accent);
  }
  @keyframes slide-in {
    from { transform: translateY(20px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
  }
</style>
