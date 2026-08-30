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

type VisualKind = "actions" | "snapshots" | "settings" | "usage" | "hero";

async function captureTheme(
  kind: VisualKind,
  theme: "light" | "dark"
): Promise<void> {
  await device.launchApp({
    newInstance: true,
    launchArgs: {
      clcWebsiteVisualHarness: "1",
      clcWebsiteVisualTheme: theme,
      clcWebsiteVisualKind: kind,
      detoxEnableSynchronization: "0",
    },
  });
  await dismissAndroidImmersiveModeConfirmation();
  await device.disableSynchronization();
  await waitFor(element(by.id(`website-visual-open-${kind}`)))
    .toExist()
    .withTimeout(30000);
  await element(by.id(`website-visual-open-${kind}`)).tap();
  if (kind === "actions") {
    await waitFor(element(by.id("session-actions-menu")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("session-actions-menu")).tap();
  }
  const readinessText: string | null =
    kind === "actions"
      ? "Copy session"
      : kind === "snapshots"
        ? "Snapshots"
        : kind === "settings"
          ? "Reasoning Effort"
          : null;
  if (readinessText) {
    await waitFor(element(by.text(readinessText)))
      .toBeVisible()
      .withTimeout(30000);
  } else if (kind === "usage") {
    await waitFor(element(by.id("message-footer-4")))
      .toBeVisible()
      .withTimeout(30000);
  } else {
    await waitFor(element(by.id("message-bubble-6")))
      .toExist()
      .withTimeout(30000);
    await waitFor(element(by.text("Plan a Starlette compatibility fix")))
      .toBeVisible()
      .withTimeout(30000);
  }
  await new Promise((resolve) => setTimeout(resolve, 600));

  const source = await device.takeScreenshot(
    `website-${kind}-${theme}`
  );
  const directory = path.resolve(process.cwd(), "artifacts", "website-visual");
  fs.mkdirSync(directory, { recursive: true });
  fs.copyFileSync(
    source,
    path.join(directory, `${kind}-${theme}.png`)
  );
}

describe("website visual source capture", () => {
  it("captures deterministic light and dark production workbench states", async () => {
    for (const kind of ["actions", "snapshots", "settings", "usage", "hero"] as const) {
      await captureTheme(kind, "light");
      await captureTheme(kind, "dark");
    }
  }, 300000);
});
