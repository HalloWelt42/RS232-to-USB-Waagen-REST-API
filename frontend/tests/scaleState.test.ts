import { describe, it, expect, afterEach } from 'vitest';
import { healthStore, SCALE_LABEL_KEY } from '../src/lib/healthStore.svelte';
import { HELP_IDS, helpEntriesByLang } from '../src/lib/help';
import { i18n, t } from '../src/lib/i18n';
import type { HealthInfo } from '../src/lib/types';

function health(over: Partial<HealthInfo>): HealthInfo {
  return {
    ok: false,
    reader_alive: false,
    scale_alive: false,
    adapter_present: false,
    stale_for_s: null,
    last_seen: null,
    port: 'auto',
    baudrate: 9600,
    uptime_seconds: 10,
    version: '0.7.0',
    source_mode: 'live',
    simulated: false,
    ...over,
  };
}

describe('healthStore.scaleState', () => {
  afterEach(() => healthStore.set(null));

  it('meldet fehlenden Adapter getrennt von "Waage aus"', () => {
    healthStore.set(health({ adapter_present: false }));
    expect(healthStore.scaleState).toBe('noAdapter');
    healthStore.set(health({ adapter_present: true, reader_alive: true }));
    expect(healthStore.scaleState).toBe('offline');
  });

  it('live, sobald die Waage antwortet', () => {
    healthStore.set(health({ adapter_present: true, reader_alive: true, scale_alive: true }));
    expect(healthStore.scaleState).toBe('live');
  });

  it('Simulator hat Vorrang, auch ohne Adapter', () => {
    healthStore.set(health({ simulated: true, source_mode: 'simulate', adapter_present: false }));
    expect(healthStore.scaleState).toBe('simulated');
  });

  it('älteres Backend ohne adapter_present bleibt bei "Waage aus"', () => {
    const old = health({});
    delete old.adapter_present;
    healthStore.set(old);
    expect(healthStore.scaleState).toBe('offline');
  });

  it('hat für jeden Zustand eine Beschriftung in beiden Sprachen', () => {
    for (const lang of ['de', 'en'] as const) {
      i18n.set(lang);
      for (const key of Object.values(SCALE_LABEL_KEY)) {
        expect(t(key)).not.toBe(key);
      }
    }
    i18n.set('de');
    expect(t(SCALE_LABEL_KEY.noAdapter)).toBe('KEIN ADAPTER');
  });
});

describe('Hilfe-Themen', () => {
  it('HELP_IDS deckt sich mit den Hilfe-Bäumen beider Sprachen', () => {
    const ids = [...HELP_IDS].sort();
    expect(Object.keys(helpEntriesByLang.de).sort()).toEqual(ids);
    expect(Object.keys(helpEntriesByLang.en).sort()).toEqual(ids);
  });

  it('enthält das Thema Anschluss', () => {
    expect(helpEntriesByLang.de.connection.title).toBe('Anschluss');
    expect(helpEntriesByLang.en.connection.title).toBe('Connection');
  });
});
