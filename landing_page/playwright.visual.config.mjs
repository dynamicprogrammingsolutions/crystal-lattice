import { defineConfig } from "@playwright/test";

const channel = process.env.PLAYWRIGHT_CHANNEL;

export default defineConfig({
  testDir: "./tests/visual",
  outputDir:
    "./artifacts/research/025-current-visual-baseline-and-asset-pipeline/playwright/test-results",
  timeout: 60_000,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:4321",
    locale: "en-US",
    reducedMotion: "reduce",
    trace: "off",
    video: "off",
    ...(channel ? { channel } : {}),
  },
  webServer: {
    command: "yarn build && yarn preview --host 127.0.0.1",
    url: "http://127.0.0.1:4321",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});