<script lang="ts">
  /**
   * Karten-Grid als Eingangs-Ansicht im rechten Bereich.
   * LiveWaage und MessLog leben separat in der Sidebar — hier
   * gibt es nur die Werkzeug-Karten.
   */
  import ActionCard from './ActionCard.svelte';
</script>

<div class="grid">
  <ActionCard tool="wiegen"    icon="fa-solid fa-scale-balanced" />
  <ActionCard tool="netto"     icon="fa-solid fa-flask" />
  <ActionCard tool="count"     icon="fa-solid fa-hashtag" />
  <ActionCard tool="tolerance" icon="fa-solid fa-bullseye" />
  <ActionCard tool="samples"   icon="fa-solid fa-clipboard-list" />
  <ActionCard tool="differenz" icon="fa-solid fa-arrow-right-arrow-left" />
  <ActionCard tool="help"      icon="fa-solid fa-book" iconColor="info" />
  <ActionCard tool="settings"  icon="fa-solid fa-gear" />
  <ActionCard tool="donate"    icon="fa-solid fa-heart" iconColor="donate" />
</div>

<style>
  .grid {
    flex: 1 1 auto;
    min-height: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(220px, 100%), 1fr));
    gap: var(--sp-3);
    align-content: start;
    overflow-y: auto;
    padding: var(--sp-3);
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
  }

  @media (max-width: 800px) {
    .grid {
      padding: var(--sp-2);
      gap: var(--sp-2);
    }
  }
</style>
