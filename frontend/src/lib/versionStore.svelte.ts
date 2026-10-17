/**
 * Reaktiver Versions-Store: Anzeige der Version und selbsttätiges
 * Neuladen, sobald eine neue Fassung ausgeliefert ist.
 *
 * Quellen, klare Priorität für die Anzeige:
 *
 *   1. `/version.json` — statische Datei, die `bump.sh` bei jedem
 *      Bump aktualisiert und die mit der Oberfläche ausgeliefert wird.
 *      Wird ohne Zwischenspeicher gefetcht, ist also die Fassung, die
 *      der Server gerade ausliefert.
 *
 *   2. `health.version` — kommt vom Backend (/scale/health) und
 *      spiegelt die VERSION-Datei via `_load_version()`.
 *
 *   3. `__APP_VERSION__` — Vite-Build-Zeit-Konstante: die Fassung,
 *      die in diesem Tab gerade läuft.
 *
 * Neue Fassung: nie ein hartes Neuladen verlangen. Die Startseite kommt
 * ohne Zwischenspeicher (nginx), die Skripte tragen Prüfsummen im Namen.
 * Weicht (1) von (3) ab, lädt die Seite von selbst neu: in den ersten
 * Sekunden nach dem Start sofort, später beim nächsten Ansichtswechsel
 * oder wenn das Fenster wieder nach vorn kommt; Letzteres nicht, solange
 * seit dem letzten Ansichtswechsel etwas eingegeben wurde. Dazwischen
 * steht ein Band mit Knopf. Je ausgelieferter Fassung nur ein
 * selbsttätiger Versuch (Merker in der Sitzung), damit ein hängender
 * Zwischenspeicher keine Schleife auslöst.
 *
 * Footer und überall, wo "Version" angezeigt wird, sollten
 * `versionStore.value` lesen statt direkt `health.version` oder
 * `__APP_VERSION__`.
 */

import { tick } from 'svelte';

const RELOAD_MARKER = 'waage.neu_geladen';
const START_WINDOW_MS = 10_000;
const CHECK_INTERVAL_MS = 60_000;

export type Trigger = 'start' | 'interval' | 'navigation' | 'visible';

class VersionStore {
  /** Ausgelieferte Version aus `/version.json` (gefetcht). null = noch
   *  nicht geladen oder Fetch fehlgeschlagen. */
  fromFile = $state<string | null>(null);

  /** Backend-Version aus `/scale/health`. Wird vom App-Root gesetzt. */
  fromBackend = $state<string | null>(null);

  /** Vite-Build-Zeit-Konstante: die Fassung, die in diesem Tab läuft. */
  readonly fromBuild: string = __APP_VERSION__;

  /** Seit dem letzten Ansichtswechsel wurde etwas eingegeben. */
  #inputSinceNavigation = $state(false);

  setBackend(v: string | undefined | null): void {
    this.fromBackend = v ?? null;
  }

  /** Anzuzeigender Wert nach Priorität. */
  get value(): string {
    return this.fromFile ?? this.fromBackend ?? this.fromBuild;
  }

  /** True, wenn Frontend- und Backend-Version voneinander abweichen.
   *  Hilft beim Debug von Deployment-Diskrepanzen. */
  get hasMismatch(): boolean {
    return (
      this.fromFile !== null &&
      this.fromBackend !== null &&
      this.fromFile !== this.fromBackend
    );
  }

  /** Neu ausgelieferte Fassung, oder null, wenn dieser Tab aktuell ist. */
  get available(): string | null {
    return this.fromFile !== null && this.fromFile !== this.fromBuild ? this.fromFile : null;
  }

  /** Nichts offen, was ein Neuladen abbrechen würde. */
  idle(): boolean {
    return !this.#inputSinceNavigation;
  }

  maybeReload(trigger: Trigger): void {
    const next = this.available;
    if (!next || trigger === 'interval' || !this.idle()) return;
    if (trigger === 'start' && performance.now() > START_WINDOW_MS) return;
    if (this.#allowed(next)) location.reload();
  }

  /** Beim Ansichtswechsel sind die alten Eingaben weg; erst nach dem
   *  Umbau der Ansicht prüfen. */
  afterNavigation(): void {
    this.#inputSinceNavigation = false;
    void tick().then(() => this.maybeReload('navigation'));
  }

  /** Holt `/version.json` ohne Zwischenspeicher und prüft auf eine neue Fassung. */
  async check(trigger: Trigger): Promise<void> {
    try {
      const res = await fetch(`/version.json?t=${Date.now()}`, { cache: 'no-store' });
      if (!res.ok) return;
      const data = (await res.json()) as { version?: string };
      if (typeof data.version === 'string' && data.version) {
        this.fromFile = data.version;
      }
    } catch {
      return; // Datei fehlt im Setup oder Fetch fehlgeschlagen: Fallback greift
    }
    this.maybeReload(trigger);
  }

  /** Beim Start, jede Minute und beim Zurückkehren ins Fenster prüfen. */
  watch(): () => void {
    void this.check('start');
    const timer = window.setInterval(() => void this.check('interval'), CHECK_INTERVAL_MS);
    const onVisible = (): void => {
      if (document.visibilityState === 'visible') void this.check('visible');
    };
    const onInput = (): void => { this.#inputSinceNavigation = true; };
    document.addEventListener('visibilitychange', onVisible);
    document.addEventListener('input', onInput, true);
    return () => {
      clearInterval(timer);
      document.removeEventListener('visibilitychange', onVisible);
      document.removeEventListener('input', onInput, true);
    };
  }

  #allowed(next: string): boolean {
    try {
      if (sessionStorage.getItem(RELOAD_MARKER) === next) return false;
      sessionStorage.setItem(RELOAD_MARKER, next);
    } catch {
      // ohne Sitzungsspeicher kein Merker: dann lieber einmal laden als nie
    }
    return true;
  }
}

export const versionStore = new VersionStore();
