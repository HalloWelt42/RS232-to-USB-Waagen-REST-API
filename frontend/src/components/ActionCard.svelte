<script lang="ts">
  import { route, type ToolKey } from '../lib/routing.svelte';
  import { t } from '../lib/i18n';

  interface Props {
    tool: ToolKey;
    icon: string;            // FA-Klasse, z.B. 'fa-solid fa-scale-balanced'
    iconColor?: 'accent' | 'donate' | 'info';
  }
  let { tool, icon, iconColor = 'accent' }: Props = $props();

  function open(): void { route.go(tool); }
</script>

<button class="card" data-color={iconColor} onclick={open}>
  <span class="original num">{t(`toolsOriginal.${tool}`)}</span>
  <span class="icon">
    <i class={icon} aria-hidden="true"></i>
  </span>
  <h3>{t(`tools.${tool}`)}</h3>
  <p>{t(`toolsDescription.${tool}`)}</p>
</button>

<style>
  .card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-4);
    cursor: pointer;
    transition: border-color 0.15s, transform 0.15s;
    display: flex; flex-direction: column;
    gap: var(--sp-2);
    min-height: 144px;
    box-shadow: var(--shadow);
    position: relative;
    text-align: left;
    color: var(--fg);
    width: 100%;
    font-family: var(--sans);
  }
  .card:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
  }
  .card .icon {
    width: 48px; height: 48px;
    border-radius: var(--radius-sm);
    background: var(--bg-card-2);
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 22px;
  }
  .card[data-color="accent"] .icon { color: var(--accent); }
  .card[data-color="donate"] .icon { color: var(--donate); }
  .card[data-color="info"]   .icon { color: var(--info-blue); }
  .card h3 {
    margin: 0; font-size: var(--fs-lg); font-weight: 600;
    letter-spacing: 0.01em;
  }
  .card .original {
    position: absolute; top: var(--sp-2); right: var(--sp-2);
    font-size: 10px;
    color: var(--fg-mute);
    opacity: 0;
    transition: opacity 0.15s;
    letter-spacing: 0.04em;
  }
  .card:hover .original { opacity: 1; }
  .card p {
    margin: 0; font-size: var(--fs-sm); color: var(--fg-dim);
    line-height: 1.5;
  }
</style>
