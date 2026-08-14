/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;

const HARNESS_LAUNCH_ARGS = {
  clcTranscriptRangeNavigationHarness: "1",
};

type ElementFrame = {
  y: number;
  height: number;
};

async function launchHarness(): Promise<void> {
  await device.launchApp({
    newInstance: true,
    launchArgs: HARNESS_LAUNCH_ARGS,
  });
  await waitFor(element(by.id("transcript-range-navigation-harness-ready")))
    .toExist()
    .withTimeout(30000);
  await waitFor(element(by.id("transcript-range-navigation-loaded-range")))
    .toHaveText("100:199")
    .withTimeout(30000);
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
      `No usable frame for ${testID}: ${JSON.stringify(attributes)}`,
    );
  }
  return resolved;
}

function expectApproximatelyEqual(actual: number, expected: number): void {
  if (Math.abs(actual - expected) > 16) {
    throw new Error(`Expected ${actual} to be within 16px of ${expected}`);
  }
}

describe("mobile transcript range viewport preservation", () => {
  it("preserves visible overlap for older and newer range navigation", async () => {
    await launchHarness();

    await element(by.id("transcript-scroll-to-top")).tap();
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
      element(by.id("transcript-range-navigation-loaded-range")),
    ).toHaveText("100:199");
  });
});
