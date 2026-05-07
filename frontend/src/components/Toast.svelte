<script lang="ts">
  import { toast } from '../lib/toast.svelte';
  let entry = $derived(toast.current);
</script>

{#if entry}
  <div class="toast {entry.kind}" role="status" aria-live="polite">{entry.message}</div>
{/if}

<style>
  .toast {
    position: fixed;
    left: 50%;
    bottom: calc(var(--footer-h) + var(--contact-h) + var(--sp-3));
    transform: translateX(-50%);
    background: var(--bg-elev);
    color: var(--fg);
    border: 1px solid var(--border-strong);
    border-radius: 999px;
    padding: 8px 16px;
    font-size: var(--fs-sm);
    box-shadow: var(--shadow-lg);
    z-index: 250;
    animation: pop 0.2s ease-out;
    pointer-events: none;
  }
  .toast.ok    { border-color: var(--green); color: var(--green); }
  .toast.error { border-color: var(--red);   color: var(--red); }
  @keyframes pop {
    from { transform: translateX(-50%) translateY(8px); opacity: 0; }
    to   { transform: translateX(-50%) translateY(0); opacity: 1; }
  }
</style>
