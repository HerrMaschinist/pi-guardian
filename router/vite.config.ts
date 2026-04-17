import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const routerHost = env.VITE_ROUTER_HOST || '127.0.0.1';
  const routerPort = env.VITE_ROUTER_PORT || '8071';

  return {
    plugins: [react()],
    base: '/',
    server: {
      host: '0.0.0.0',
      port: 3000,
      proxy: {
        '/api': {
          target: `http://${routerHost}:${routerPort}`,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  };
});
