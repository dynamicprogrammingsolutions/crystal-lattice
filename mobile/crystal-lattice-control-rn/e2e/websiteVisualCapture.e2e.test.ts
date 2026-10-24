/// <reference types="detox" />

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { expect as jestExpect } from "@jest/globals";

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
  | "message-actions"
  | "snapshots"
  | "settings"
  | "usage"
  | "cost"
  | "hero"
  | "provider-settings"
  | "plugins"
  | "compiled"
  | "vibe"
  | "workspaces"
  | "composer-active"
  | "system-template"
  | "home"
  | "connections";

async function persistWebsiteScreenshot(
  screenshotName: string,
  filename: string
): Promise<void> {
  const source = await device.takeScreenshot(screenshotName);
  const directory = path.resolve(process.cwd(), "artifacts", "website-visual");
  fs.mkdirSync(directory, { recursive: true });
  fs.copyFileSync(source, path.join(directory, filename));
}

async function captureVibeGeometry(theme: "light" | "dark"): Promise<void> {
  const targets = [
    "website-visual-harness-ready",
    "messages-screen-header",
    "transcript-scroll-list",
    "message-bubble-0",
    "message-bubble-1",
    "assistant-reasoning-content-2",
  ];
  const attributes: Record<string, unknown> = {};
  for (const id of targets) {
    attributes[id] = await element(by.id(id)).getAttributes();
  }
  const viewport = (
    attributes["transcript-scroll-list"] as Detox.IosElementAttributes
  ).frame;
  for (const id of [
    "message-bubble-0",
    "message-bubble-1",
    "assistant-reasoning-content-2",
  ]) {
    const frame = (attributes[id] as Detox.IosElementAttributes).frame;
    jestExpect(frame.y).toBeGreaterThanOrEqual(viewport.y);
    jestExpect(frame.y + frame.height).toBeLessThanOrEqual(
      viewport.y + viewport.height + 1
    );
    jestExpect(frame.x).toBeGreaterThanOrEqual(viewport.x);
    jestExpect(frame.x + frame.width).toBeLessThanOrEqual(
      viewport.x + viewport.width + 1
    );
  }
  const directory = path.resolve("artifacts/website-visual");
  fs.mkdirSync(directory, { recursive: true });
  fs.writeFileSync(
    path.join(directory, `vibe-${theme}-geometry.json`),
    JSON.stringify(attributes, null, 2)
  );
}

async function captureTheme(
  kind: VisualKind,
  theme: "light" | "dark"
): Promise<void> {
  if (kind === "connections") {
    if (device.getPlatform() === "ios") {
      execFileSync("xcrun", ["simctl", "ui", device.id, "appearance", theme]);
    }
    await device.launchApp({
      newInstance: true,
      delete: true,
      launchArgs: {
        detoxEnableSynchronization: "0",
      },
    });
    await device.disableSynchronization();
    await waitFor(element(by.id("home-menu")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("home-menu")).tap();
    await waitFor(element(by.id("home-menu-new-connection")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("home-menu-new-connection")).performAccessibilityAction(
      "activate"
    );
    await waitFor(element(by.id("connection-method-manual")))
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(element(by.id("connection-method-discovery")))
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(element(by.id("connection-method-bridge")))
      .toBeVisible()
      .withTimeout(30000);
    await persistWebsiteScreenshot(
      `website-${kind}-${theme}`,
      `${kind}-${theme}.png`
    );
    return;
  }
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
  } else if (kind === "home") {
    await waitFor(element(by.id("website-home-ready")))
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
  if (kind === "message-actions") {
    try {
      await element(by.id("transcript-scroll-to-bottom")).tap();
    } catch {
      // The terminal message may already be fully visible.
    }
    // Detox does not preserve the React ancestor relationship in the native
    // accessibility hierarchy. The seven loaded messages expose seven
    // generic triggers in chronological accessibility order, so the terminal
    // assistant response is the last one.
    const terminalMessageActions = element(
      by.id("message-actions-menu")
    ).atIndex(6);
    await waitFor(terminalMessageActions).toBeVisible().withTimeout(30000);
    await terminalMessageActions.tap();
    await waitFor(element(by.text("Fork here")))
      .toBeVisible()
      .withTimeout(30000);
  }
  if (kind === "composer-active") {
    await waitFor(element(by.id("composer-rich-config-model")))
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(element(by.id("composer-rich-config-reasoning_effort")))
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(element(by.id("composer-rich-config-enable_web_search")))
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(element(by.label("Open Composer actions")))
      .toBeVisible()
      .withTimeout(30000);
    await persistWebsiteScreenshot(
      `website-composer-overview-${theme}`,
      `composer-overview-${theme}.png`
    );
    await element(by.label("Open Composer actions")).tap();
    await waitFor(element(by.text("Soft cancel request")))
      .toBeVisible()
      .withTimeout(30000);
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
    try {
      await element(by.id("transcript-scroll-to-top")).tap();
    } catch {
      // Short capture transcripts may already fit without an edge control.
    }
    await captureVibeGeometry(theme);
    await waitFor(element(by.id("message-bubble-0")))
      .toBeVisible()
      .withTimeout(10000);
    await waitFor(element(by.text("[1] User")))
      .toBeVisible()
      .withTimeout(10000);
    await waitFor(element(by.id("assistant-reasoning-content-2")))
      .toBeVisible()
      .withTimeout(10000);
  } else if (kind === "system-template") {
    try {
      await element(by.id("transcript-scroll-to-top")).tap();
    } catch {
      // The full short transcript may already fit without an edge control.
    }
    await waitFor(element(by.id("message-bubble-0")))
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(element(by.text("[0] System")))
      .toBeVisible()
      .withTimeout(30000);
  } else if (kind === "workspaces") {
    await waitFor(element(by.text("Plan a Starlette compatibility fix")))
      .toBeVisible()
      .withTimeout(30000);
    await persistWebsiteScreenshot(
      `website-workspaces-list-${theme}`,
      `workspaces-list-${theme}.png`
    );
    await waitFor(
      element(
        by.id("session-rich-action-starlette-compatibility-set_session_status")
      )
    )
      .toBeVisible()
      .withTimeout(30000);
    await element(
      by.id("session-rich-action-starlette-compatibility-set_session_status")
    ).tap();
    await waitFor(
      element(
        by.id("session-rich-list-starlette-compatibility-set_session_status")
      )
    )
      .toBeVisible()
      .withTimeout(30000);
  } else if (kind === "home") {
    await waitFor(
      element(
        by.id("home-watchlist-tile-local-workspace-starlette-compatibility")
      )
    )
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(element(by.text("Recent Sessions")))
      .toBeVisible()
      .withTimeout(30000);
    await persistWebsiteScreenshot(
      `website-workspaces-list-${theme}`,
      `workspaces-list-${theme}.png`
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
    `${kind}-${theme}.png`
  );
}

describe("website visual source capture", () => {
  it("captures deterministic light and dark production workbench states", async () => {
    const allKinds = [
      "actions",
      "message-actions",
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
      "composer-active",
      "system-template",
      "home",
      "connections",
    ] as const;
    const requested = (process.env.CLC_WEBSITE_VISUAL_KINDS ?? "")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean);
    const selected =
      requested.length > 0
        ? allKinds.filter((kind) => requested.includes(kind))
        : allKinds;
    for (const kind of selected) {
      await captureTheme(kind, "light");
      await captureTheme(kind, "dark");
    }
  }, 300000);
});
