/// <reference types="detox" />

import fs from "node:fs";
import path from "node:path";

async function dismissAndroidImmersiveModeConfirmation(): Promise<void> {
  if (device.getPlatform() !== "android") {
    return;
  }
  try {
    await system.element(by.system.label("Got it")).tap();
  } catch {
    // Fresh E2E images do not show this one-time Android system confirmation.
  }
}

async function captureTheme(theme: "light" | "dark"): Promise<void> {
  await device.launchApp({
    newInstance: true,
    launchArgs: {
      clcWebsiteVisualHarness: "1",
      clcWebsiteVisualTheme: theme,
      detoxEnableSynchronization: "0",
    },
  });
  await dismissAndroidImmersiveModeConfirmation();
  await device.disableSynchronization();
  await waitFor(element(by.id("website-visual-open-session-settings")))
    .toExist()
    .withTimeout(30000);
  await element(by.id("website-visual-open-session-settings")).tap();
  await waitFor(element(by.text("Model")))
    .toBeVisible()
    .withTimeout(30000);
  await waitFor(element(by.text("Reasoning effort")))
    .toBeVisible()
    .withTimeout(30000);

  const source = await device.takeScreenshot(
    `website-session-settings-${theme}`
  );
  const directory = path.resolve(process.cwd(), "artifacts", "website-visual");
  fs.mkdirSync(directory, { recursive: true });
  fs.copyFileSync(
    source,
    path.join(directory, `session-settings-${theme}.png`)
  );
  await device.enableSynchronization();
}

describe("website visual source capture", () => {
  afterEach(async () => {
    await device.enableSynchronization();
  });

  it("captures deterministic light and dark production session settings", async () => {
    await captureTheme("light");
    await captureTheme("dark");
  });
});
