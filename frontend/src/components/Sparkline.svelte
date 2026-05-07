<script>
  import { formatGrams, formatTime } from '../lib/format.js';

  let { history = [], windowSeconds = 60 } = $props();

  // Punkte aus den letzten N Sekunden filtern und auf SVG-Koordinaten mappen
  let points = $derived.by(() => {
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
      first: points[0].weight_g,
      last:  points[points.length - 1].weight_g,
      count: points.length,
    };
  });

  const W = 320;
  const H = 80;
  const PAD_X = 6;
  const PAD_Y = 6;

  let path = $derived.by(() => {
    if (!stats || points.length < 2) return '';
    const tStart = new Date(points[0].timestamp).getTime();
    const tEnd   = new Date(points[points.length - 1].timestamp).getTime();
    const tSpan  = Math.max(1, tEnd - tStart);
    let yMin = stats.min;
    let yMax = stats.max;
    if (yMax - yMin < 0.001) {
      // konstante Linie: künstlich etwas Range, damit nicht kollabiert
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

  let area = $derived.by(() => {
    if (!path) return '';
    return path + ` L${(W - PAD_X).toFixed(1)},${(H - PAD_Y).toFixed(1)} L${PAD_X.toFixed(1)},${(H - PAD_Y).toFixed(1)} Z`;
  });
</script>

<section class="spark">
  <header>
    <h3>Verlauf {windowSeconds}s</h3>
    {#if stats}
      <span class="meta">
        Min {formatGrams(stats.min)} · Max {formatGrams(stats.max)}
      </span>
    {/if}
  </header>
  {#if path}
    <svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" role="img"
         aria-label="Live-Verlauf der letzten {windowSeconds} Sekunden">
      <path d={area} fill="rgba(88, 166, 255, 0.18)" stroke="none" />
      <path d={path} fill="none" stroke="var(--accent)" stroke-width="1.5"
            stroke-linejoin="round" stroke-linecap="round" />
    </svg>
  {:else}
    <div class="placeholder">noch zu wenig Daten</div>
  {/if}
</section>

<style>
  .spark {
    background:    var(--bg-card);
    border:        1px solid var(--border);
    border-radius: var(--radius);
    padding:       1rem 1.25rem;
    box-shadow:    var(--shadow);
    width:         min(28rem, 90vw);
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 0.5rem;
  }
  h3 { margin: 0; font-size: 1rem; }
  .meta {
    font-family: var(--mono);
    font-size: 0.8rem;
    color: var(--fg-dim);
  }
  svg {
    width: 100%;
    height: 80px;
    display: block;
  }
  .placeholder {
    color: var(--fg-dim);
    font-size: 0.85rem;
    text-align: center;
    padding: 1.5rem 0;
  }
</style>
