<script lang="ts">
  import { formatGrams } from '../lib/format';
  import HelpButton from './HelpButton.svelte';
  import type { Reading } from '../lib/types';

  interface Props {
    history: Reading[];
    windowSeconds?: number;
  }

  let { history = [], windowSeconds = 60 }: Props = $props();

  const W = 320;
  const H = 64;
  const PAD_X = 4;
  const PAD_Y = 4;

  let points = $derived.by<Reading[]>(() => {
    if (!history || history.length === 0) return [];
    const cutoff = Date.now() - windowSeconds * 1000;
    return history.filter(r => new Date(r.timestamp).getTime() >= cutoff);
  });

  let stats = $derived.by(() => {
    if (points.length === 0) return null;
    const weights = points.map(p => p.weight_g);
    return {
      min: Math.min(...weights),
      max: Math.max(...weights),
      last: points[points.length - 1].weight_g,
    };
  });

  let path = $derived.by<string>(() => {
    if (!stats || points.length < 2) return '';
    const tStart = new Date(points[0].timestamp).getTime();
    const tEnd   = new Date(points[points.length - 1].timestamp).getTime();
    const tSpan  = Math.max(1, tEnd - tStart);
    let yMin = stats.min;
    let yMax = stats.max;
    if (yMax - yMin < 0.001) {
      yMin -= 0.5;
      yMax += 0.5;
    }
    const ySpan = yMax - yMin;
    const innerW = W - 2 * PAD_X;
    const innerH = H - 2 * PAD_Y;
    return points.map((p, i) => {
      const t = new Date(p.timestamp).getTime();
      const x = PAD_X + ((t - tStart) / tSpan) * innerW;
      const y = PAD_Y + (1 - (p.weight_g - yMin) / ySpan) * innerH;
      return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1);
    }).join(' ');
  });

  let area = $derived.by<string>(() => {
    if (!path) return '';
    return path + ` L${(W - PAD_X).toFixed(1)},${(H - PAD_Y).toFixed(1)}` +
           ` L${PAD_X.toFixed(1)},${(H - PAD_Y).toFixed(1)} Z`;
  });
</script>

<section class="spark">
  <header>
    <h3>Verlauf {windowSeconds}s</h3>
    <div class="meta">
      {#if stats}
        <span class="num">min {formatGrams(stats.min)}</span>
        <span class="num">max {formatGrams(stats.max)}</span>
      {/if}
      <HelpButton id="sparkline" label="Hilfe zum Verlauf" />
    </div>
  </header>
  {#if path}
    <svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" role="img"
         aria-label="Live-Verlauf der letzten {windowSeconds} Sekunden">
      <path d={area} fill="color-mix(in srgb, var(--accent) 18%, transparent)" stroke="none" />
      <path d={path} fill="none" stroke="var(--accent)" stroke-width="1.5"
            stroke-linejoin="round" stroke-linecap="round" />
    </svg>
  {:else}
    <div class="placeholder">noch zu wenig Daten</div>
  {/if}
</section>

<style>
  .spark {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-2) var(--sp-3);
    box-shadow: var(--shadow);
    flex: 0 0 auto;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--sp-1);
    gap: var(--sp-2);
  }
  h3 { margin: 0; font-size: var(--fs-sm); color: var(--fg-dim); font-weight: 500; }
  .meta {
    display: flex;
    align-items: center;
    gap: var(--sp-3);
    font-size: var(--fs-xs);
    color: var(--fg-dim);
  }
  svg {
    width: 100%;
    height: 64px;
    display: block;
  }
  .placeholder {
    color: var(--fg-dim);
    font-size: var(--fs-sm);
    text-align: center;
    padding: var(--sp-3) 0;
  }
</style>
