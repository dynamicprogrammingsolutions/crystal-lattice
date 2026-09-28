/// <reference types="detox" />

import * as detox from "detox";

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

describe("portable rich session UI", () => {
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
    await waitFor(element(by.id("composer-action-resend")))
      .toBeVisible()
      .withTimeout(10000);

    const cancelAttributes: any = await element(
      by.id("composer-cancel-request")
    ).getAttributes();
    const sendAttributes: any = await element(
      by.id("composer-send")
    ).getAttributes();
    if (!(cancelAttributes.frame.y < sendAttributes.frame.y)) {
      throw new Error(
        `Expected Cancel above Send, got cancelY=${cancelAttributes.frame.y} sendY=${sendAttributes.frame.y}`
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
