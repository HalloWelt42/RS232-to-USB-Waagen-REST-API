<script lang="ts">
  import { onMount } from 'svelte';
  import { theme, type Theme } from '../lib/theme';
  import { t } from '../lib/i18n';

  let current = $state<Theme>('auto');
  onMount(() => theme.subscribe((tt) => { current = tt; }));

  const titles: Record<Theme, string> = {
    auto:  'topbar.themeAuto',
    light: 'topbar.themeLight',
    dark:  'topbar.themeDark',
  };
  const icons: Record<Theme, string> = {
    auto:  'fa-circle-half-stroke',
    light: 'fa-sun',
    dark:  'fa-moon',
  };

  function toggle(): void { current = theme.cycle(); }
</script>

<button class="hdr-btn icon-only" onclick={toggle}
        title={t(titles[current])} aria-label={t(titles[current])}>
  <i class="fa-solid {icons[current]}" aria-hidden="true"></i>
</button>
