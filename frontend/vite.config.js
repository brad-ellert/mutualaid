import { defineConfig } from 'vite';
import basicSsl from '@vitejs/plugin-basic-ssl';

export default defineConfig({
  plugins: [
    basicSsl()
  ],
  server: {
    port: 3000,
    https: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: '../backend/app/static',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: 'index.html',
      },
    },
  },
});
