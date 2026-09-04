/// <reference types="detox" />

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
}

describe("portable rich session UI", () => {
  it("selects, enters, and resets models and executes placed session actions", async () => {
    await launchHarness();

    await element(by.id("composer-rich-config-model")).tap();
    await waitFor(element(by.id("options-picker-option-claude-b")))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id("options-picker-option-claude-b")).tap();
    await waitFor(element(by.label("Model: Claude B")))
      .toBeVisible()
      .withTimeout(10000);

    await element(by.id("composer-rich-config-model")).tap();
    const customInput = element(by.id("options-picker-custom-input"));
    await customInput.tap();
    await customInput.replaceText("vendor/custom-model");
    await customInput.tapReturnKey();
    await waitFor(element(by.label("Model: vendor/custom-model")))
      .toBeVisible()
      .withTimeout(10000);

    await element(by.id("composer-rich-config-model")).tap();
    await element(by.id("options-picker-reset")).tap();
    await waitFor(element(by.label("Model: Claude A")))
      .toBeVisible()
      .withTimeout(10000);

    await waitFor(
      element(by.id("session-rich-action-toggle_feature-session-header")),
    )
      .toBeVisible()
      .withTimeout(10000);
    await element(
      by.id("session-rich-action-toggle_feature-session-header"),
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
  });
});
