import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/ui/',
  root: '.',
  publicDir: 'public',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
      },
    },
  },
  server: {
    port: 3000,
    open: '/ui/',
    cors: true,
    proxy: {
      // Proxy API requests to FastAPI backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // Proxy specific backend endpoints
      '/configure': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/graph': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/class_diagram': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/mermaid_classes': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/chroma': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/migrate': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/openapi.json': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/docs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // WebSocket for logs
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@hooks': resolve(__dirname, 'src/hooks'),
      '@store': resolve(__dirname, 'src/store'),
      '@types': resolve(__dirname, 'src/types'),
      '@utils': resolve(__dirname, 'src/utils'),
    },
  },
  define: {
    // Only expose specific environment variables, not the entire process.env
    'import.meta.env.MODE': JSON.stringify(process.env.NODE_ENV || 'development'),
    'import.meta.env.DEV': process.env.NODE_ENV !== 'production',
    'import.meta.env.PROD': process.env.NODE_ENV === 'production',
  },
});
