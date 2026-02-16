import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
    fileParallelism:
      !(process.env.RUN_BACKEND_INTEGRATION === '1' || process.env.RUN_BRIDGE_E2E_INTEGRATION === '1'),
  },
});
