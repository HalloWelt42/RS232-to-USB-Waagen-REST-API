<script lang="ts">
  /**
   * Entwickler-Kontakt im Footer als SVG-Grafik.
   * Email steht nur im SVG <text>, nicht als Plain-Text im DOM —
   * Spam-Schutz gegen Crawler. Klick öffnet mailto: per JS.
   */
  import { copyText } from '../lib/clipboard';
  import { toast } from '../lib/toast.svelte';
  import { t } from '../lib/i18n';

  // Email-Adresse stückweise zusammengesetzt — kein Plain-Text im
  // produzierten Bundle als zusammenhängender String.
  const _user = 'dev-pilot';
  const _domain = '2y4.de';
  const _email = `${_user}@${_domain}`;

  function handleClick(): void {
    void copyText(_email).then((ok) => {
      toast.show(ok ? t('toast.addressCopied') : t('toast.copyError'), ok ? 'ok' : 'error');
    });
    // Mailto erst nach Toast — Browser öffnet ggf. Mail-Client
    window.setTimeout(() => {
      window.location.href = `mailto:${_email}`;
    }, 200);
  }
</script>

<div class="contact">
  <span class="label">{t('contact.label')}:</span>
  <button class="email-btn" onclick={handleClick}
          title={t('commands.contactMailTitle')}
          aria-label={t('commands.contactMailAria')}>
    <svg width="220" height="20" viewBox="0 0 220 20"
         xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M2 4 L13 12 L24 4 M2 4 L2 17 L24 17 L24 4 Z"
            stroke="currentColor" stroke-width="1.4" fill="none"
            stroke-linejoin="round" stroke-linecap="round" />
      <text x="32" y="14" font-family="'Chakra Petch','Barlow',monospace"
            font-size="12" font-weight="600" fill="currentColor"
            letter-spacing="0.02em">{_user}@{_domain}</text>
    </svg>
  </button>
  <span class="intro">{t('contact.intro')}</span>
  <span class="license">{t('contact.license')}</span>
</div>

<style>
  .contact {
    height: var(--contact-h);
    flex: 0 0 auto;
    display: flex; align-items: center; gap: var(--sp-3);
    padding: 0 var(--sp-3);
    background: var(--bg-card);
    border-top: 1px solid var(--border);
    font-size: var(--fs-xs);
    color: var(--fg-dim);
    overflow: hidden;
  }
  .label {
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-size: 10px;
  }
  .email-btn {
    background: transparent;
    border: none;
    padding: 0;
    color: var(--fg);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    height: 22px;
  }
  .email-btn:hover { color: var(--accent); }
  .email-btn svg { display: block; }
  .intro {
    font-style: italic;
    color: var(--fg-mute);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
  }
  .license {
    color: var(--fg-mute);
    font-size: 10px;
    white-space: nowrap;
  }
  @media (max-width: 900px) {
    /* Auf Mobile reduzieren wir auf den Email-Knopf — Intro-Text,
       Label und Lizenz-Zeile sind doppelt vorhanden (Settings,
       Hilfe „Disclaimer") und kosten am Handy nur Platz. */
    .intro, .label, .license { display: none; }
    .contact { justify-content: center; padding: 0 var(--sp-2); }
  }
</style>
