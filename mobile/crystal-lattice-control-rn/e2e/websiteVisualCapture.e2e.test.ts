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

type VisualKind =
  | "actions"
  | "snapshots"
  | "settings"
  | "usage"
  | "cost"
  | "hero"
  | "provider-settings"
  | "plugins"
  | "compiled"
  | "vibe"
  | "workspaces";

async function persistWebsiteScreenshot(
  screenshotName: string,
  filename: string,
): Promise<void> {
  const source = await device.takeScreenshot(screenshotName);
  const directory = path.resolve(process.cwd(), "artifacts", "website-visual");
  fs.mkdirSync(directory, { recursive: true });
  fs.copyFileSync(source, path.join(directory, filename));
}

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
  if (kind === "workspaces") {
    await waitFor(element(by.id("website-workspaces-ready")))
      .toExist()
      .withTimeout(30000);
  } else {
    await waitFor(element(by.id(`website-visual-open-${kind}`)))
      .toExist()
      .withTimeout(30000);
    await element(by.id(`website-visual-open-${kind}`)).tap();
  }
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
          : kind === "provider-settings"
            ? "Authentication mode"
            : kind === "plugins"
              ? "Reasoning controls"
          : null;
  if (readinessText) {
    await waitFor(element(by.text(readinessText)))
      .toBeVisible()
      .withTimeout(30000);
  } else if (kind === "usage") {
    await waitFor(element(by.id("message-footer-4")))
      .toExist()
      .withTimeout(30000);
  } else if (kind === "compiled") {
    await waitFor(element(by.id("website-compiled-action-display")))
      .toBeVisible()
      .withTimeout(30000);
  } else if (kind === "cost") {
    await waitFor(element(by.id("website-cost-action-display")))
      .toBeVisible()
      .withTimeout(30000);
  } else if (kind === "vibe") {
    await waitFor(element(by.id("message-bubble-2")))
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(element(by.id("assistant-reasoning-disclosure-2")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("assistant-reasoning-disclosure-2")).tap();
    await waitFor(element(by.id("assistant-reasoning-content-2")))
      .toExist()
      .withTimeout(30000);
  } else if (kind === "workspaces") {
    await waitFor(element(by.text("Launch strategy research")))
      .toBeVisible()
      .withTimeout(30000);
    await persistWebsiteScreenshot(
      `website-workspaces-list-${theme}`,
      `workspaces-list-${theme}.png`,
    );
    await waitFor(
      element(by.id("session-rich-action-launch-research-set_session_status"))
    )
      .toBeVisible()
      .withTimeout(30000);
    await element(
      by.id("session-rich-action-launch-research-set_session_status")
    ).tap();
    await waitFor(
      element(by.id("session-rich-list-launch-research-set_session_status"))
    )
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

  await persistWebsiteScreenshot(
    `website-${kind}-${theme}`,
    `${kind}-${theme}.png`,
  );
}

describe("website visual source capture", () => {
  it("captures deterministic light and dark production workbench states", async () => {
    const allKinds = [
      "actions",
      "snapshots",
      "settings",
      "usage",
      "cost",
      "hero",
      "provider-settings",
      "plugins",
      "compiled",
      "vibe",
      "workspaces",
    ] as const;
    const requested = (process.env.CLC_WEBSITE_VISUAL_KINDS ?? "")
      .split(",")
      .map(value => value.trim())
      .filter(Boolean);
    const selected = requested.length > 0
      ? allKinds.filter(kind => requested.includes(kind))
      : allKinds;
    for (const kind of selected) {
      await captureTheme(kind, "light");
      await captureTheme(kind, "dark");
    }
  }, 300000);
});
