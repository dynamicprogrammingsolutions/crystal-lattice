import { defineConfig } from "@playwright/test";

const channel = process.env.PLAYWRIGHT_CHANNEL;
const port = Number(process.env.PLAYWRIGHT_PORT ?? "4321");
const variant = process.env.CRYSTAL_LATTICE_SITE_VARIANT ?? "production";

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error("PLAYWRIGHT_PORT must be a valid TCP port");
}
if (!["production", "staging"].includes(variant)) {
  throw new Error("CRYSTAL_LATTICE_SITE_VARIANT must be production or staging");
}

const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: "./tests/visual",
  outputDir:
    `./artifacts/site-variants/${variant}/test-results`,
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
    command: `yarn build:${variant} && node scripts/run-site-variant.mjs ${variant} astro preview --host 127.0.0.1 --port ${port}`,
    url: baseURL,
    reuseExistingServer:
      process.env.PLAYWRIGHT_REUSE_EXISTING_SERVER !== "false",
    timeout: 120_000,
  },
});