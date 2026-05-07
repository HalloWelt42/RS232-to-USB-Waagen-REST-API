<script lang="ts">
  /**
   * Spenden-Tab — Ko-fi-Link plus mehrere Krypto-Adressen mit
   * Klick-zum-Kopieren-Button.
   */
  import { copyText } from '../../lib/clipboard';
  import { toast } from '../../lib/toast.svelte';
  import { t } from '../../lib/i18n';
  import HelpButton from '../HelpButton.svelte';

  interface CryptoAddr {
    code: string;
    label: string;
    iconClass: string;
    address: string;
  }

  // Adressen aus dem RadioHub-Schema übernommen.
  const addresses: CryptoAddr[] = [
    { code: 'BTC',  label: 'Bitcoin',
      iconClass: 'fa-brands fa-bitcoin',
      address: 'bc1qhalloWELT42btcaddressplaceholder' },
    { code: 'DOGE', label: 'Dogecoin',
      iconClass: 'fa-solid fa-dog',
      address: 'DhalloWELT42dogeaddressplaceholder' },
    { code: 'ETH',  label: 'Ethereum',
      iconClass: 'fa-brands fa-ethereum',
      address: '0xhalloWELT42ethaddressplaceholder' },
  ];

  async function copy(addr: string): Promise<void> {
    const ok = await copyText(addr);
    toast.show(ok ? t('toast.addressCopied') : t('toast.copyError'),
      ok ? 'ok' : 'error');
  }
</script>

<section class="panel">
  <header>
    <h2>{t('tools.donate')}</h2>
    <HelpButton id="donate" />
  </header>

  <div class="content">
    <p class="intro">{t('donate.intro')}</p>

    <a class="kofi" href="https://ko-fi.com/HalloWelt42" target="_blank" rel="noopener">
      <i class="fa-solid fa-mug-hot"></i>
      {t('donate.kofi')}
    </a>

    <div class="divider"><span>{t('donate.orCrypto')}</span></div>

    <ul class="cryptos">
      {#each addresses as a (a.code)}
        <li class="crypto">
          <span class="left">
            <i class={a.iconClass} aria-hidden="true"></i>
            <span class="lbl">{a.label}</span>
            <span class="num code">{a.code}</span>
          </span>
          <button class="addr" onclick={() => copy(a.address)}
                  title={t('donate.addressCopy')} aria-label={t('donate.addressCopy')}>
            <span class="num">{a.address}</span>
            <i class="fa-regular fa-copy"></i>
          </button>
        </li>
      {/each}
    </ul>

    <p class="thanks">{t('donate.thanks')}</p>
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
    max-width: 720px; margin-inline: auto; width: 100%;
    display: flex; flex-direction: column; gap: var(--sp-3);
  }
  .intro {
    margin: 0;
    font-size: 18px;       /* Anwender-Vorgabe */
    line-height: 1.6;
    color: var(--fg);
  }
  .kofi {
    background: var(--donate);
    color: white;
    border: 1px solid var(--donate);
    border-radius: var(--radius-sm);
    padding: 12px var(--sp-4);
    text-decoration: none;
    text-align: center;
    font-size: var(--fs-md);
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    display: inline-flex; align-items: center; justify-content: center;
    gap: 8px;
    min-height: var(--tap);
    box-shadow: 0 4px 14px var(--donate-glow);
    transition: transform 0.15s, box-shadow 0.15s;
  }
  .kofi:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px var(--donate-glow);
    text-decoration: none;
  }

  .divider {
    display: flex; align-items: center; gap: var(--sp-3);
    color: var(--fg-mute);
    font-size: var(--fs-xs);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: var(--sp-2) 0;
  }
  .divider::before, .divider::after {
    content: ''; flex: 1; height: 1px; background: var(--border);
  }

  .cryptos {
    list-style: none; margin: 0; padding: 0;
    display: flex; flex-direction: column; gap: var(--sp-2);
  }
  .crypto {
    background: var(--bg-card-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: var(--sp-2) var(--sp-3);
    display: flex; align-items: center; justify-content: space-between;
    gap: var(--sp-2);
  }
  .left { display: flex; align-items: center; gap: 10px; }
  .left i { font-size: 18px; color: var(--accent); width: 24px; text-align: center; }
  .lbl { font-size: var(--fs-sm); color: var(--fg); }
  .code { font-size: var(--fs-xs); color: var(--fg-mute); }

  .addr {
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--fg-dim);
    border-radius: var(--radius-sm);
    padding: 6px var(--sp-2);
    display: inline-flex; align-items: center; gap: 8px;
    font-size: var(--fs-xs);
    cursor: pointer;
    max-width: 60%;
    overflow: hidden;
  }
  .addr:hover { color: var(--accent); border-color: var(--accent); }
  .addr .num {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .thanks {
    text-align: center;
    font-size: var(--fs-md);
    color: var(--accent);
    margin: var(--sp-3) 0 0;
  }
  .license {
    text-align: center;
    font-size: var(--fs-xs);
    color: var(--fg-mute);
    margin: 0;
  }

  @media (max-width: 600px) {
    .crypto { flex-direction: column; align-items: stretch; gap: 6px; }
    .addr { max-width: 100%; }
  }
</style>
