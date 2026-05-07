import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { readFileSync } from 'fs';

const pkg = JSON.parse(readFileSync('./package.json', 'utf-8'));

// Backend-Target — im Compose-Setup heißt der Service `waage-backend`,
// im lokalen Dev-Modus läuft er auf localhost:8200.
const BACKEND = process.env.VITE_BACKEND || 'http://localhost:8200';

export default defineConfig({
  plugins: [svelte()],
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
  server: {
    host: '0.0.0.0',
    port: 5184,
    strictPort: false,
    cors: true,
    proxy: {
      // REST-Endpoints
      '/api': {
        target: BACKEND,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // WebSocket
      '/stream': {
        target: BACKEND.replace(/^http/, 'ws'),
        changeOrigin: true,
        ws: true,
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
    include: ['tests/**/*.test.js', 'src/**/*.test.js'],
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
  },
});
