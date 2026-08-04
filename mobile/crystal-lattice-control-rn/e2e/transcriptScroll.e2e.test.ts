/// <reference types="detox" />

import * as detox from "detox";

const detoxExpect = detox.expect;

const HARNESS_LAUNCH_ARGS = {
  clcTranscriptScrollHarness: "1",
};

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
    launchArgs: HARNESS_LAUNCH_ARGS,
  });
  await dismissAndroidImmersiveModeConfirmation();
  await waitFor(element(by.id("transcript-harness-ready")))
    .toExist()
    .withTimeout(30000);
}

async function expectBottomState(): Promise<void> {
  await waitFor(element(by.id("transcript-message-299")))
    .toBeVisible()
    .withTimeout(30000);
  await waitFor(element(by.id("transcript-scroll-to-top")))
    .toBeVisible()
    .withTimeout(30000);
  await detoxExpect(
    element(by.id("transcript-scroll-to-bottom"))
  ).not.toExist();
}

async function expectTopState(): Promise<void> {
  await waitFor(element(by.id("transcript-message-0")))
    .toBeVisible()
    .withTimeout(60000);
  await waitFor(element(by.id("transcript-scroll-to-bottom")))
    .toBeVisible()
    .withTimeout(30000);
  await detoxExpect(element(by.id("transcript-scroll-to-top"))).not.toExist();
}

async function scrollToTop(): Promise<void> {
  await element(by.id("transcript-scroll-to-top")).tap();
  await expectTopState();
}

async function scrollToBottom(): Promise<void> {
  await element(by.id("transcript-scroll-to-bottom")).tap();
  await expectBottomState();
}

describe("mobile transcript edge navigation", () => {
  it("supports initial, edge, middle, and repeated navigation states", async () => {
    await launchHarness();
    await expectBottomState();
    await detoxExpect(element(by.id("transcript-message-0"))).not.toBeVisible();

    await scrollToTop();
    await scrollToBottom();

    if (device.getPlatform() === "android") {
      await element(by.id("transcript-message-295")).swipe(
        "down",
        "fast",
        0.75
      );
    } else {
      await element(by.id("transcript-scroll-list")).swipe("down", "fast", 0.5);
    }
    await waitFor(element(by.id("transcript-scroll-to-bottom")))
      .toExist()
      .withTimeout(30000);
    await detoxExpect(element(by.id("transcript-scroll-to-top"))).toExist();
    await scrollToBottom();

    await scrollToTop();
    await scrollToBottom();
    await scrollToTop();
    await scrollToBottom();
  });
});
