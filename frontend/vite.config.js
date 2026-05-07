import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { readFileSync, existsSync } from 'fs';

const pkg = JSON.parse(readFileSync('./package.json', 'utf-8'));
// Single Source of Truth: VERSION-Datei im Repo-Wurzel.
// Falls vorhanden, hat sie Vorrang gegenüber package.json.
let APP_VERSION = pkg.version;
if (existsSync('../VERSION')) {
  APP_VERSION = readFileSync('../VERSION', 'utf-8').trim();
}

// Backend-Target — im Compose-Setup heißt der Service `waage-backend`,
// im lokalen Dev-Modus läuft er auf localhost:8200.
const BACKEND = process.env.VITE_BACKEND || 'http://localhost:8200';

export default defineConfig({
  plugins: [svelte()],
  define: {
    __APP_VERSION__: JSON.stringify(APP_VERSION),
  },
  server: {
    host: '0.0.0.0',
    port: 5184,
    strictPort: false,
    cors: true,
    proxy: {
      // REST-Endpoints + WebSocket (/api/scale/stream wird mit ws upgegradet)
      '/api': {
        target: BACKEND,
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // Swagger UI und OpenAPI-Schema direkt vom Backend
      '/docs': {
        target: BACKEND,
        changeOrigin: true,
      },
      '/redoc': {
        target: BACKEND,
        changeOrigin: true,
      },
      '/openapi.json': {
        target: BACKEND,
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['tests/**/*.test.{js,ts}', 'src/**/*.test.{js,ts}'],
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
  },
});
