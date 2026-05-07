<script lang="ts">
  /**
   * Spenden-Tab nach Vorlage RadioHub-SetupSpende, im Industrial-Look:
   *  - Großes Herz-Icon im Kreis als Eyecatcher
   *  - Intro-Text
   *  - Ko-fi-Button als zentrale Aktion
   *  - Trennlinie „oder per Kryptowährung"
   *  - Drei Krypto-Karten (BTC, DOGE, ETH) als Auswahl
   *  - Klick auf Karte zeigt QR-Code, Adresse und Kopier-Knopf
   *  - Lizenz-Fußzeile (CC BY-NC-ND 4.0 + Zusatzbestimmungen)
   */
  import { copyText } from '../../lib/clipboard';
  import { toast } from '../../lib/toast.svelte';
  import { t } from '../../lib/i18n';
  import HelpButton from '../HelpButton.svelte';

  interface CryptoAddr {
    id: 'btc' | 'doge' | 'eth';
    label: string;
    symbol: string;
    iconClass: string;
    color: string;
    address: string;
    qr: string;
  }

  // Adressen und QR-Codes übernommen aus RadioHub.
  const cryptos: readonly CryptoAddr[] = [
    {
      id: 'btc', label: 'Bitcoin', symbol: 'BTC',
      iconClass: 'fa-brands fa-bitcoin', color: '#f7931a',
      address: 'bc1qnd599khdkv3v3npmj9ufxzf6h4fzanny2acwqr',
      qr: '/images/btc-qr.svg',
    },
    {
      id: 'doge', label: 'Dogecoin', symbol: 'DOGE',
      iconClass: 'fa-solid fa-dog', color: '#c3a634',
      address: 'DL7tuiYCqm3xQjMDXChdxeQxqUGMACn1ZV',
      qr: '/images/doge-qr.svg',
    },
    {
      id: 'eth', label: 'Ethereum', symbol: 'ETH',
      iconClass: 'fa-brands fa-ethereum', color: '#627eea',
      address: '0x8A28fc47bFFFA03C8f685fa0836E2dBe1CA14F27',
      qr: '/images/eth-qr.svg',
    },
  ] as const;

  let active = $state<CryptoAddr['id'] | null>(null);
  let copied = $state<string | null>(null);

  function pick(id: CryptoAddr['id']): void {
    active = active === id ? null : id;
  }

  async function copy(addr: string): Promise<void> {
    const ok = await copyText(addr);
    if (ok) {
      copied = addr;
      toast.show(t('donate.addressCopied'), 'ok');
      window.setTimeout(() => { if (copied === addr) copied = null; }, 2000);
    } else {
      toast.show(t('donate.addressCopyError'), 'error');
    }
  }

  let activeData = $derived(cryptos.find(c => c.id === active) ?? null);
</script>

<section class="panel">
  <header>
    <h2>{t('tools.donate')}</h2>
    <HelpButton id="donate" />
  </header>

  <div class="content">
    <div class="intro">
      <div class="intro-icon" aria-hidden="true">
        <i class="fa-solid fa-heart"></i>
      </div>
      <h3 class="intro-title">{t('donate.title')}</h3>
      <p class="intro-text">{t('donate.intro')}</p>
    </div>

    <a class="kofi-btn" href="https://ko-fi.com/HalloWelt42"
       target="_blank" rel="noopener">
      <i class="fa-solid fa-mug-hot"></i>
      <span>{t('donate.kofi')}</span>
    </a>

    <div class="divider">
      <span class="divider-line"></span>
      <span class="divider-label">{t('donate.orCrypto')}</span>
      <span class="divider-line"></span>
    </div>

    <div class="crypto-cards">
      {#each cryptos as c (c.id)}
        <button class="crypto-card" class:active={active === c.id}
                onclick={() => pick(c.id)}
                aria-pressed={active === c.id}>
          <span class="crypto-icon" style:--crypto-color={c.color}>
            <i class={c.iconClass} aria-hidden="true"></i>
          </span>
          <span class="crypto-name num">{c.symbol}</span>
          <span class="led" class:on={active === c.id}></span>
        </button>
      {/each}
    </div>

    {#if activeData}
      <div class="crypto-detail">
        <div class="qr" aria-label={t('donate.qrLabel')}>
          <img src={activeData.qr} alt="{activeData.symbol} QR-Code" />
        </div>
        <div class="info">
          <span class="lbl">{activeData.label}</span>
          <code class="addr num">{activeData.address}</code>
          <button class="copy-btn" onclick={() => copy(activeData.address)}>
            <i class="fa-solid {copied === activeData.address ? 'fa-check' : 'fa-copy'}"></i>
            <span>
              {copied === activeData.address
                ? t('donate.addressCopied')
                : t('donate.addressCopy')}
            </span>
          </button>
        </div>
      </div>
    {:else}
      <p class="hint">{t('donate.selectCrypto')}</p>
    {/if}

    <p class="thanks"><i class="fa-solid fa-heart"></i> {t('donate.thanks')}</p>
    <p class="license">{t('contact.license')}</p>
  </div>
</section>

<style>
  .panel {
    flex: 1 1 auto; min-height: 0; overflow-y: auto;
    padding: var(--sp-4);
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  header { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3); }
  header h2 {
    margin: 0; font-size: var(--fs-xl); font-weight: 600;
    color: var(--donate);
  }

  .content {
    max-width: 540px; margin-inline: auto; width: 100%;
    display: flex; flex-direction: column; align-items: center;
    gap: var(--sp-4);
  }

  /* Intro mit großem Herz */
  .intro {
    display: flex; flex-direction: column; align-items: center;
    gap: var(--sp-2);
    text-align: center;
  }
  .intro-icon {
    width: 64px; height: 64px;
    border-radius: 50%;
    background: color-mix(in srgb, var(--donate) 15%, transparent);
    color: var(--donate);
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 28px;
    filter: drop-shadow(0 0 12px var(--donate-glow));
  }
  .intro-title {
    margin: 0;
    font-family: var(--sans);
    font-size: var(--fs-lg);
    font-weight: 700;
    letter-spacing: 0.02em;
    color: var(--fg);
  }
  .intro-text {
    margin: 0;
    font-size: 18px;       /* Hilfe/Donate-Texte mind. 18 px */
    line-height: 1.6;
    color: var(--fg-dim);
    max-width: 460px;
  }

  /* Ko-fi-Button — pillförmig, Spende-Rot */
  .kofi-btn {
    display: inline-flex; align-items: center; gap: 10px;
    padding: 14px 32px;
    background: var(--donate);
    border: 1px solid var(--donate);
    border-radius: 999px;
    color: #ffffff;
    font-family: var(--sans);
    font-size: var(--fs-sm);
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    text-decoration: none;
    cursor: pointer;
    box-shadow: 0 4px 14px var(--donate-glow);
    transition: transform 0.15s, filter 0.15s, box-shadow 0.15s;
  }
  .kofi-btn:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
    box-shadow: 0 6px 22px var(--donate-glow);
    text-decoration: none;
  }
  .kofi-btn i { font-size: 16px; }

  /* Trenner */
  .divider {
    display: flex; align-items: center; gap: var(--sp-3);
    width: 100%;
    color: var(--fg-mute);
    font-size: var(--fs-xs);
    letter-spacing: 0.15em;
    text-transform: uppercase;
  }
  .divider-line { flex: 1; height: 1px; background: var(--border); }
  .divider-label { white-space: nowrap; }

  /* Krypto-Karten */
  .crypto-cards {
    display: flex; gap: var(--sp-3);
    flex-wrap: wrap; justify-content: center;
  }
  .crypto-card {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: var(--sp-3) var(--sp-5);
    display: flex; flex-direction: column; align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s, transform 0.15s;
    box-shadow: var(--shadow);
  }
  .crypto-card:hover {
    border-color: color-mix(in srgb, var(--accent) 60%, var(--border));
    transform: translateY(-2px);
  }
  .crypto-card.active {
    border-color: var(--accent);
    background: color-mix(in srgb, var(--accent) 8%, var(--bg-card-2));
    transform: none;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.3);
  }
  .crypto-icon {
    width: 56px; height: 56px;
    border-radius: 50%;
    background: var(--bg-card);
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 28px;
    color: var(--crypto-color);
  }
  .crypto-name {
    font-size: var(--fs-sm);
    color: var(--fg-dim);
    letter-spacing: 0.1em;
  }
  .crypto-card.active .crypto-name { color: var(--fg); }
  .led {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--fg-mute);
    transition: background 0.15s, box-shadow 0.15s;
  }
  .led.on { background: var(--green); box-shadow: 0 0 6px var(--green); }

  /* Detail-Bereich mit QR und Adresse */
  .crypto-detail {
    display: flex;
    gap: var(--sp-4);
    align-items: center;
    padding: var(--sp-4);
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    width: 100%;
    box-shadow: var(--shadow);
  }
  .qr {
    flex: 0 0 auto;
    width: 144px; height: 144px;
    background: #ffffff;
    border-radius: var(--radius-sm);
    padding: 8px;
    display: flex; align-items: center; justify-content: center;
  }
  .qr img { width: 100%; height: 100%; display: block; }
  .info {
    flex: 1; min-width: 0;
    display: flex; flex-direction: column; gap: var(--sp-2);
  }
  .info .lbl {
    font-family: var(--sans);
    font-size: var(--fs-md);
    font-weight: 700;
    letter-spacing: 0.02em;
    color: var(--fg);
  }
  .addr {
    font-size: 11px;
    color: var(--fg-dim);
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 8px 10px;
    border-radius: var(--radius-sm);
    word-break: break-all;
    line-height: 1.5;
  }
  .copy-btn {
    align-self: flex-start;
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 999px;
    color: var(--fg-dim);
    font-family: var(--sans);
    font-size: var(--fs-xs);
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s;
  }
  .copy-btn:hover { color: var(--accent); border-color: var(--accent); }

  .hint {
    margin: 0;
    font-size: var(--fs-sm);
    color: var(--fg-mute);
    text-align: center;
    font-style: italic;
  }

  .thanks {
    margin: 0;
    display: inline-flex; align-items: center; gap: 6px;
    color: var(--fg-dim);
    font-size: var(--fs-md);
    font-style: italic;
  }
  .thanks i { color: var(--donate); }

  .license {
    margin: 0;
    text-align: center;
    font-size: var(--fs-xs);
    color: var(--fg-mute);
    line-height: 1.5;
  }

  @media (max-width: 600px) {
    .crypto-detail { flex-direction: column; align-items: stretch; }
    .qr { align-self: center; }
  }
</style>
