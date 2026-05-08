/**
 * Reaktiver Versions-Store mit drei Quellen, klarer Priorität:
 *
 *   1. `/version.json` — statische Datei, die `bump.sh` bei jedem
 *      Bump aktualisiert. Wird mit Cache-Buster gefetcht, ist also
 *      auch ohne Frontend-Rebuild oder Service-Worker-Invalidation
 *      immer aktuell. Das ist die robusteste Quelle.
 *
 *   2. `health.version` — kommt vom Backend (/scale/health) und
 *      spiegelt die VERSION-Datei via `_load_version()`. Sicherer
 *      Fallback, falls `/version.json` (z.B. wegen statischer
 *      Hosting-Konfig ohne Cache-Header) nicht zuverlässig ist.
 *
 *   3. `__APP_VERSION__` — Vite-Build-Zeit-Konstante. Letzte
 *      Sicherheit für komplett isolierte Builds.
 *
 * Footer und überall, wo „Version" angezeigt wird, sollten
 * `versionStore.value` lesen statt direkt `health.version` oder
 * `__APP_VERSION__`.
 */

class VersionStore {
  /** Frontend-Version aus `/version.json` (gefetcht). null = noch
   *  nicht geladen oder Fetch fehlgeschlagen. */
  fromFile = $state<string | null>(null);

  /** Backend-Version aus `/scale/health`. Wird vom App-Root gesetzt. */
  fromBackend = $state<string | null>(null);

  /** Vite-Build-Zeit-Konstante — Fallback wenn beides oben fehlt. */
  readonly fromBuild: string = __APP_VERSION__;

  setBackend(v: string | undefined | null): void {
    this.fromBackend = v ?? null;
  }

  /**
   * Holt `/version.json` einmalig beim Start. Cache-Buster im
   * Query-String stellt sicher, dass Browser-Cache ignoriert wird.
   */
  async loadFromFile(): Promise<void> {
    try {
      const ts = Date.now();
      const res = await fetch(`/version.json?t=${ts}`, { cache: 'no-store' });
      if (!res.ok) return;
      const data = (await res.json()) as { version?: string };
      if (typeof data.version === 'string' && data.version) {
        this.fromFile = data.version;
      }
    } catch {
      // Datei fehlt im Setup oder Fetch fehlgeschlagen — Fallback
      // greift automatisch.
    }
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
}

export const versionStore = new VersionStore();
