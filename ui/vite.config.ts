import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const guardianTarget = env.VITE_GUARDIAN_API_TARGET || 'http://127.0.0.1:8000';
  const guardianPrefix = env.VITE_GUARDIAN_API_PREFIX || '/api/guardian';

  return {
    plugins: [vue()],
    test: {
      environment: 'jsdom',
      globals: true,
      restoreMocks: true,
    },
    server: {
      host: '0.0.0.0',
      port: 3000,
      proxy: {
        [guardianPrefix]: {
          target: guardianTarget,
          changeOrigin: true,
          rewrite: (path) => (path.startsWith(guardianPrefix) ? path.slice(guardianPrefix.length) || '/' : path),
        },
      },
    },
  };
});
