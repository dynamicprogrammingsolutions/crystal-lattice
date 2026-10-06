/// <reference types="detox" />

import * as detox from "detox";
import { expect as jestExpect } from "@jest/globals";
import fs from "node:fs";
import path from "node:path";

const detoxExpect = detox.expect;

async function dismissAndroidImmersiveModeConfirmation(): Promise<void> {
  if (device.getPlatform() !== "android") {
    return;
  }
  try {
    await system.element(by.system.label("Got it")).tap();
  } catch {
    // Fresh E2E images do not show this one-time Android confirmation.
  }
}

async function launchHarness(): Promise<void> {
  await device.launchApp({
    newInstance: true,
    resetAppState: true,
    launchArgs: {
      clcRichSessionUiHarness: "1",
      detoxEnableSynchronization: "0",
    },
  });
  await device.disableSynchronization();
  await dismissAndroidImmersiveModeConfirmation();
  await waitFor(element(by.id("rich-session-ui-harness-ready")))
    .toExist()
    .withTimeout(30000);
  await waitFor(element(by.id("composer-rich-config-model")))
    .toBeVisible()
    .withTimeout(30000);
  await waitFor(element(by.id("rich-session-ui-watchlist-state")))
    .toHaveText("not-watched")
    .withTimeout(10000);
}

async function openPicker(
  controlId: string,
  expectedElementId: string
): Promise<void> {
  let opened = false;
  for (let attempt = 0; attempt < 2 && !opened; attempt += 1) {
    await element(by.id(controlId)).tap();
    try {
      await waitFor(element(by.id("options-picker-input")))
        .toExist()
        .withTimeout(5000);
      opened = true;
    } catch {
      // The Android API 36.1 emulator occasionally drops the first tap.
    }
  }
  if (!opened) {
    await waitFor(element(by.id("options-picker-input")))
      .toExist()
      .withTimeout(10000);
  }
  await waitFor(element(by.id(expectedElementId)))
    .toBeVisible()
    .withTimeout(10000);
}

async function collapseExpandedComposer(): Promise<void> {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    await element(by.id("expanded-composer-collapse")).tap();
    try {
      await waitFor(element(by.id("expanded-composer-input")))
        .not.toExist()
        .withTimeout(5000);
      return;
    } catch {
      // iOS text-editing overlays may consume the first tap after replaceText.
    }
  }
  await waitFor(element(by.id("expanded-composer-input")))
    .not.toExist()
    .withTimeout(10000);
}

async function tapAfterModalDismissal(testID: string): Promise<void> {
  // With synchronization disabled, React content disappears before UIKit's
  // fading transition view stops intercepting taps. Retry the real tap only
  // for that temporary hit-test failure.
  for (let attempt = 0; attempt < 5; attempt += 1) {
    try {
      await element(by.id(testID)).tap();
      return;
    } catch (error) {
      if (attempt === 4 || !String(error).includes("View is not hittable")) {
        throw error;
      }
      await new Promise((resolve) => setTimeout(resolve, 200));
    }
  }
}

describe("portable rich session UI", () => {
  it("wraps the compaction name and keeps its pin independent", async () => {
    await launchHarness();
    await element(by.id("message-actions-menu")).tap();
    const action = element(by.id("actions-menu-action-compact_native_history_through_message"));
    await waitFor(action).toBeVisible().withTimeout(10000);
    await detoxExpect(action).toHaveLabel("OpenAI compaction up to here");
    const compactionAttributes: any = await action.getAttributes();
    const copyAttributes: any = await element(by.id("actions-menu-action-copy")).getAttributes();
    const compactionFrame = compactionAttributes.frame ?? compactionAttributes.elementBounds;
    const copyFrame = copyAttributes.frame ?? copyAttributes.elementBounds;
    jestExpect(compactionFrame.height).toBeGreaterThanOrEqual(copyFrame.height - 0.5);
    const longAttributes: any = await element(by.id("actions-menu-action-long_plugin_action")).getAttributes();
    const longFrame = longAttributes.frame ?? longAttributes.elementBounds;
    jestExpect(longFrame.height).toBeGreaterThan(copyFrame.height + 5);
    await element(by.id("actions-menu-pin-compact_native_history_through_message")).tap();
    await waitFor(element(by.id("actions-menu-pin-compact_native_history_through_message")))
      .toHaveLabel("Unpin OpenAI compaction up to here").withTimeout(10000);
    await detoxExpect(element(by.id("rich-session-ui-last-action"))).toHaveText("none");
    const screenshot = await device.takeScreenshot("message-action-two-line-labels");
    const reviewDirectory = path.join(process.cwd(), "artifacts", "detox", "action-popup-review");
    fs.mkdirSync(reviewDirectory, { recursive: true });
    fs.copyFileSync(screenshot, path.join(reviewDirectory, "ios-message-actions.png"));
    await element(by.id("actions-menu-close")).tap();
    await detoxExpect(action).not.toExist();

    await tapAfterModalDismissal("message-menu-long-list");
    await element(by.id("message-actions-menu")).tap();
    await waitFor(action).toBeVisible().withTimeout(10000);
    const panelAttributes: any = await element(by.id("actions-menu-panel")).getAttributes();
    const rootAttributes: any = await element(by.id("rich-session-ui-harness-ready")).getAttributes();
    const panelFrame = panelAttributes.frame ?? panelAttributes.elementBounds;
    const rootFrame = rootAttributes.frame ?? rootAttributes.elementBounds;
    jestExpect(panelFrame.height).toBeLessThan(rootFrame.height);
    const lastPin = element(by.id("actions-menu-pin-long-17"));
    await waitFor(lastPin).toBeVisible()
      .whileElement(by.id("actions-menu-scroll")).scroll(350, "down");
    await lastPin.tap();
    await waitFor(lastPin).toHaveLabel(
      "Unpin Summarize this conversation and preserve every decision"
    ).withTimeout(10000);
    await element(by.id("actions-menu-close")).tap();
  });

  it("places Resend, hard cancel, and soft cancel in Session actions", async () => {
    await launchHarness();

    await element(by.id("session-actions-menu")).tap();
    await waitFor(element(by.id("actions-menu-action-resend")))
      .toBeVisible()
      .withTimeout(10000);
    await detoxExpect(element(by.id("actions-menu-action-cancel"))).toExist();
    await detoxExpect(
      element(by.id("actions-menu-action-softCancel"))
    ).toHaveLabel("Soft cancel request");
    await detoxExpect(
      element(by.id("actions-menu-action-localWatchlist"))
    ).toHaveLabel("Add to Watchlist");
    await element(
      by.id("actions-menu-action-localWatchlist")
    ).performAccessibilityAction("activate");
    await waitFor(element(by.id("rich-session-ui-watchlist-state")))
      .toHaveText("watched")
      .withTimeout(10000);
  });

  it("selects, enters, and resets models and executes placed session actions", async () => {
    await launchHarness();

    await openPicker(
      "composer-rich-config-model",
      "options-picker-declared-claude-b"
    );
    await element(by.id("options-picker-declared-claude-b")).tap();
    await waitFor(element(by.label("Model: Claude B")))
      .toBeVisible()
      .withTimeout(10000);

    await openPicker("composer-rich-config-model", "options-picker-input");
    const customInput = element(by.id("options-picker-input"));
    await customInput.tap();
    await customInput.replaceText("vendor/custom-model");
    await waitFor(element(by.id("options-picker-custom-vendor/custom-model")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("options-picker-custom-vendor/custom-model")).tap();
    await waitFor(element(by.label("Model: vendor/custom-model")))
      .toBeVisible()
      .withTimeout(10000);

    await openPicker("composer-rich-config-model", "options-picker-reset");
    await element(by.id("options-picker-reset")).tap();
    await waitFor(element(by.label("Model: Claude A")))
      .toBeVisible()
      .withTimeout(10000);

    await openPicker(
      "composer-rich-config-reasoning_effort",
      "options-picker-declared-high"
    );
    await element(by.id("options-picker-declared-high")).tap();
    await waitFor(element(by.label("Reasoning effort: High")))
      .toBeVisible()
      .withTimeout(10000);

    await element(by.id("composer-rich-config-web_search_enabled")).tap();
    await waitFor(element(by.label("Web search: On")))
      .toBeVisible()
      .withTimeout(10000);

    await waitFor(element(by.id("composer-action-append")))
      .toBeVisible()
      .withTimeout(10000);
    await waitFor(element(by.id("composer-primary-action-resend")))
      .toBeVisible()
      .withTimeout(10000);

    await element(by.label("Open Composer actions")).tap();
    await waitFor(element(by.id("actions-menu-action-cancel")))
      .toBeVisible()
      .withTimeout(10000);
    await detoxExpect(
      element(by.id("actions-menu-action-softCancel"))
    ).toExist();
    await detoxExpect(element(by.id("actions-menu-action-resend"))).toExist();
    await element(by.id("actions-menu-close")).tap();

    const resendAttributes: any = await element(
      by.id("composer-primary-action-resend")
    ).getAttributes();
    const sendAttributes: any = await element(
      by.id("composer-send")
    ).getAttributes();
    if (!(resendAttributes.frame.y < sendAttributes.frame.y)) {
      throw new Error(
        `Expected Resend above Send, got resendY=${resendAttributes.frame.y} sendY=${sendAttributes.frame.y}`
      );
    }

    await element(by.id("message-composer-input")).replaceText(
      "Expanded draft"
    );
    await element(by.id("composer-maximize")).tap();
    await waitFor(element(by.id("expanded-composer-input")))
      .toHaveText("Expanded draft")
      .withTimeout(10000);
    await element(by.id("expanded-composer-input")).replaceText(
      "Expanded draft updated"
    );
    await collapseExpandedComposer();
    await waitFor(element(by.id("message-composer-input")))
      .toHaveText("Expanded draft updated")
      .withTimeout(10000);

    await waitFor(
      element(by.id("session-rich-action-toggle_feature-session-header"))
    )
      .toBeVisible()
      .withTimeout(10000);
    await element(
      by.id("session-rich-action-toggle_feature-session-header")
    ).tap();
    await waitFor(element(by.id("rich-session-ui-last-action")))
      .toHaveText("toggle_feature:true")
      .withTimeout(10000);

    await waitFor(element(by.id("session-rich-action-set_status-composer")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("session-rich-action-set_status-composer")).tap();
    await waitFor(element(by.id("session-rich-list-set_status-option-done")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("session-rich-list-set_status-option-done")).tap();
    await waitFor(element(by.id("rich-session-ui-last-action")))
      .toHaveText("set_status:done")
      .withTimeout(10000);

    await element(by.label("Open Composer actions")).tap();
    await waitFor(element(by.id("actions-menu-action-resend")))
      .toBeVisible()
      .withTimeout(10000);
    await detoxExpect(element(by.id("actions-menu-action-append"))).toExist();
    await detoxExpect(element(by.id("actions-menu-action-appendAs"))).toExist();
    await detoxExpect(
      element(by.id("actions-menu-action-cancel"))
    ).not.toExist();
  });
});
