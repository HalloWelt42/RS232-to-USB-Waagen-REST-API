<script lang="ts">
  import { onMount } from 'svelte';
  import { theme, type Theme } from '../lib/theme';

  let current = $state<Theme>('auto');

  onMount(() => theme.subscribe((t) => { current = t; }));

  function toggle(): void {
    current = theme.cycle();
  }

  const labels: Record<Theme, string> = {
    auto:  'Automatisch',
    light: 'Hell',
    dark:  'Dunkel',
  };
</script>

<button
  class="theme-toggle"
  onclick={toggle}
  title="Anzeigemodus: {labels[current]} (klicken zum Umschalten)"
  aria-label="Anzeigemodus umschalten"
>
  {#if current === 'auto'}
    <!-- Halbmond/halb-Sonne als Auto-Symbol -->
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 4v0M12 20v0M4 12h0M20 12h0M6 6l0 0M18 6l0 0M6 18l0 0M18 18l0 0" />
      <path d="M12 4a8 8 0 0 1 0 16" fill="currentColor" stroke="none" opacity="0.4" />
    </svg>
  {:else if current === 'light'}
    <!-- Sonne -->
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  {:else}
    <!-- Mond -->
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  {/if}
  <span class="label">{labels[current]}</span>
</button>

<style>
  .theme-toggle {
    display: inline-flex;
    align-items: center;
    gap: var(--sp-2);
    padding: 6px 12px;
    color: var(--fg-dim);
  }
  .theme-toggle:hover {
    color: var(--fg);
  }
  .label {
    font-size: var(--fs-xs);
    font-family: var(--mono);
  }
</style>
