import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => {
  // Load environment variables based on current mode
  const env = loadEnv(mode, process.cwd(), '');

  // Get backend URL from environment or use default
  const backendUrl = env.VITE_BACKEND_URL || env.VITE_API_URL || 'http://localhost:8000';

  console.log(`[Vite] Mode: ${mode}`);
  console.log(`[Vite] Backend URL: ${backendUrl}`);
  console.log(`[Vite] Dev server will proxy API requests to: ${backendUrl}`);

  return {
    plugins: [react()],
    base: mode === 'production' ? '/app/' : '/',  // Use /app/ only in production
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    build: {
      outDir: 'dist',  // Build to dist directory (copied to static/app by build script)
      emptyOutDir: true,
      sourcemap: false,
      minify: 'esbuild',  // Use esbuild for faster builds (terser not required)
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom'],
            'ui-vendor': ['@radix-ui/react-slot', '@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
            'chart-vendor': ['recharts'],
          },
        },
      },
      chunkSizeWarningLimit: 1000,
    },
    server: {
      port: 5173,
      proxy: {
        // Proxy all API routes to backend
        '/v1': {
          target: backendUrl,
          changeOrigin: true,
          ws: true,  // Enable WebSocket proxying
        },
        '/metrics': {
          target: backendUrl,
          changeOrigin: true,
          ws: true,
        },
        '/dynamo': {
          target: backendUrl,
          changeOrigin: true,
          ws: true,
        },
        '/dcgm': {
          target: backendUrl,
          changeOrigin: true,
          ws: true,
        },
        '/kv-cache': {
          target: backendUrl,
          changeOrigin: true,
          ws: true,
        },
        '/ai-dynamo': {
          target: backendUrl,
          changeOrigin: true,
          ws: true,
        },
        '/admin': {
          target: backendUrl,
          changeOrigin: true,
        },
        '/api': {
          target: backendUrl,
          changeOrigin: true,
        },
      },
    },
  };
});
