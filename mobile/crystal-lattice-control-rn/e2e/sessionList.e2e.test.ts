/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;

function verticalPosition(attributes: any): number {
  const bounds = attributes?.frame || attributes?.elementBounds;
  const value = bounds?.y ?? bounds?.top;
  if (typeof value !== "number") {
    throw new Error(
      `Element attributes do not contain vertical bounds: ${JSON.stringify(
        attributes
      )}`
    );
  }
  return value;
}

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

async function launchHarness(): Promise<void> {
  await device.launchApp({
    newInstance: true,
    launchArgs: {
      clcSessionListHarness: "1",
    },
  });
  await dismissAndroidImmersiveModeConfirmation();
  await waitFor(element(by.id("session-list-harness-ready")))
    .toExist()
    .withTimeout(30000);
}

describe("mobile session-list contracts", () => {
  it("renders server presentation and preserves server order", async () => {
    await launchHarness();

    await waitFor(element(by.id("session-title-server-first")))
      .toBeVisible()
      .withTimeout(30000);
    await detoxExpect(
      element(by.id("session-title-server-first")),
    ).toHaveText("Server first title");
    await detoxExpect(
      element(by.id("session-subtitle-server-first")),
    ).toHaveText("Server first subtitle");
    await detoxExpect(
      element(by.id("session-meta-server-first")),
    ).toHaveText("Server first meta");

    const firstAttributes = await element(
      by.id("session-row-server-first"),
    ).getAttributes();
    const secondAttributes = await element(
      by.id("session-row-server-second"),
    ).getAttributes();
    const firstY = verticalPosition(firstAttributes);
    const secondY = verticalPosition(secondAttributes);
    if (firstY >= secondY) {
      throw new Error(
        `Expected server-first above server-second, got ${firstY} >= ${secondY}`
      );
    }
  });

  it("falls back to the ordinary action and submits resolved prefill", async () => {
    await launchHarness();

    await waitFor(element(by.id("session-actions-menu-server-first")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("session-actions-menu-server-first")).tap();
    await waitFor(element(by.id("actions-menu-action-edit-status")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("actions-menu-action-edit-status")).tap();

    await waitFor(element(by.id("action-dialog-select-status-done")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("application-action-dialog-primary")).tap();

    await waitFor(element(by.id("session-list-harness-submission")))
      .toHaveText("server-first:done")
      .withTimeout(30000);
  });
});
