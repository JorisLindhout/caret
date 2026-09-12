import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 4731,
    host: true,
  },
  preview: {
    port: 4732,
    host: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
