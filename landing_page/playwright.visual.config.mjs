import { defineConfig } from "@playwright/test";

const channel = process.env.PLAYWRIGHT_CHANNEL;
const port = Number(process.env.PLAYWRIGHT_PORT ?? "4321");

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error("PLAYWRIGHT_PORT must be a valid TCP port");
}

const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: "./tests/visual",
  outputDir:
    "./artifacts/visual-assets/playwright/test-results",
  timeout: 60_000,
  workers: 1,
  reporter: "list",
  use: {
    baseURL,
    locale: "en-US",
    reducedMotion: "reduce",
    trace: "off",
    video: "off",
    ...(channel ? { channel } : {}),
  },
  webServer: {
    command: `yarn build && yarn preview --host 127.0.0.1 --port ${port}`,
    url: baseURL,
    reuseExistingServer:
      process.env.PLAYWRIGHT_REUSE_EXISTING_SERVER !== "false",
    timeout: 120_000,
  },
});