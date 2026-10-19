/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;

type ElementFrame = {
  y: number;
  height: number;
};

async function launchHarness(
  strategy: "simple-reload" | "mobile-anchor-v1" | "single-flight-anchor"
): Promise<void> {
  await device.launchApp({
    newInstance: true,
    launchArgs: {
      clcTranscriptRangeNavigationHarness: "1",
      clcTranscriptAnchorStrategy: strategy,
      detoxEnableSynchronization: "0",
    },
  });
  await device.disableSynchronization();
  await waitFor(element(by.id("transcript-range-navigation-harness-ready")))
    .toExist()
    .withTimeout(30000);
  await waitFor(element(by.id("transcript-range-navigation-loaded-range")))
    .toHaveText("100:199")
    .withTimeout(30000);
  await detoxExpect(
    element(by.id("transcript-range-navigation-anchor-strategy"))
  ).toHaveText(strategy);
}

async function frameFor(testID: string): Promise<ElementFrame> {
  const attributes = (await element(by.id(testID)).getAttributes()) as any;
  const frame =
    attributes.frame ??
    attributes.elementFrame ??
    attributes.visibleFrame ??
    attributes;
  const resolved = {
    y: Number(frame.y),
    height: Number(frame.height),
  };
  if (!Number.isFinite(resolved.y) || !Number.isFinite(resolved.height)) {
    throw new Error(
      `No usable frame for ${testID}: ${JSON.stringify(attributes)}`
    );
  }
  return resolved;
}

function expectApproximatelyEqual(actual: number, expected: number): void {
  if (Math.abs(actual - expected) > 16) {
    throw new Error(`Expected ${actual} to be within 16px of ${expected}`);
  }
}

async function isVisible(testID: string): Promise<boolean> {
  try {
    const attributes = (await element(by.id(testID)).getAttributes()) as {
      visible?: boolean;
      hittable?: boolean;
    };
    return attributes.visible !== false && attributes.hittable !== false;
  } catch {
    return false;
  }
}

async function scrollToLoadedTop(): Promise<void> {
  const list = element(by.id("transcript-scroll-list"));
  if (await isVisible("transcript-scroll-to-top")) {
    await element(by.id("transcript-scroll-to-top")).tap();
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (await isVisible("transcript-range-top-expandAbove")) {
      return;
    }
    await list.swipe("down", "fast", 0.75);
  }
  await waitFor(element(by.id("transcript-range-top-expandAbove")))
    .toBeVisible()
    .withTimeout(30000);
}

describe("mobile transcript range viewport preservation", () => {
  it("preserves visible overlap for older and newer range navigation", async () => {
    await launchHarness("single-flight-anchor");

    await scrollToLoadedTop();
    await waitFor(element(by.id("transcript-message-100")))
      .toBeVisible()
      .withTimeout(60000);
    const olderAnchorBefore = await frameFor("transcript-message-100");

    await element(by.id("transcript-range-top-expandAbove")).tap();
    await waitFor(element(by.id("transcript-range-navigation-loaded-range")))
      .toHaveText("50:149")
      .withTimeout(30000);
    await waitFor(element(by.id("transcript-message-100")))
      .toBeVisible()
      .withTimeout(30000);
    const olderAnchorAfter = await frameFor("transcript-message-100");
    expectApproximatelyEqual(olderAnchorAfter.y, olderAnchorBefore.y);

    await element(by.id("transcript-scroll-to-bottom")).tap();
    await waitFor(element(by.id("transcript-message-149")))
      .toBeVisible()
      .withTimeout(60000);
    const newerAnchor = await frameFor("transcript-message-149");

    await element(by.id("transcript-range-bottom-expandBelow")).tap();
    await waitFor(element(by.id("transcript-range-navigation-loaded-range")))
      .toHaveText("100:199")
      .withTimeout(30000);
    await waitFor(element(by.id("transcript-message-149")))
      .toBeVisible()
      .withTimeout(30000);
    const newerAnchorAfter = await frameFor("transcript-message-149");
    expectApproximatelyEqual(newerAnchorAfter.y, newerAnchor.y);

    await detoxExpect(
      element(by.id("transcript-range-navigation-loaded-range"))
    ).toHaveText("100:199");
  });

  it("loads ranges through the simple reload baseline", async () => {
    await launchHarness("simple-reload");
    await scrollToLoadedTop();
    await element(by.id("transcript-range-top-expandAbove")).tap();
    await waitFor(element(by.id("transcript-range-navigation-loaded-range")))
      .toHaveText("50:149")
      .withTimeout(30000);
  });

  it("keeps the original mobile anchor implementation selectable", async () => {
    await launchHarness("mobile-anchor-v1");
    await scrollToLoadedTop();
    await waitFor(element(by.id("transcript-message-100")))
      .toBeVisible()
      .withTimeout(60000);
    const before = await frameFor("transcript-message-100");
    await element(by.id("transcript-range-top-expandAbove")).tap();
    await waitFor(element(by.id("transcript-range-navigation-loaded-range")))
      .toHaveText("50:149")
      .withTimeout(30000);
    await waitFor(element(by.id("transcript-message-100")))
      .toBeVisible()
      .withTimeout(30000);
    const after = await frameFor("transcript-message-100");
    expectApproximatelyEqual(after.y, before.y);
  });
});
