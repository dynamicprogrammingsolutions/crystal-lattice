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

  it("falls back to the ordinary form and submits resolved prefill", async () => {
    await launchHarness();

    await waitFor(element(by.id("session-actions-menu-server-first")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("session-actions-menu-server-first")).tap();
    await waitFor(element(by.id("actions-menu-action-set_session_status_fallback")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("actions-menu-action-set_session_status_fallback")).tap();

    await waitFor(element(by.id("action-dialog-select-status-done")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("application-action-dialog-primary")).tap();

    await waitFor(element(by.id("session-list-harness-submission")))
      .toHaveText("server-first:set_session_status:done")
      .withTimeout(30000);
  });

  it("uses the rich status list without an OK or Cancel confirmation", async () => {
    await launchHarness();

    await element(by.id("session-actions-menu-server-first")).tap();
    await waitFor(element(by.id("actions-menu-action-set_session_status")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("actions-menu-action-set_session_status")).tap();

    await waitFor(
      element(by.id("session-rich-list-server-first-set_session_status")),
    )
      .toBeVisible()
      .withTimeout(30000);
    await detoxExpect(
      element(by.id("application-action-dialog-primary")),
    ).not.toExist();
    await element(
      by.id("session-rich-list-server-first-set_session_status-option-todo"),
    ).tap();
    await waitFor(element(by.id("session-list-harness-submission")))
      .toHaveText("server-first:set_session_status:todo")
      .withTimeout(30000);
  });

  it("shows default-pinned rich pin and archive controls", async () => {
    await launchHarness();

    await waitFor(
      element(
        by.id(
          "session-rich-header-server-first-header_trailing-toggle_session_pinned",
        ),
      ),
    )
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(
      element(by.id("session-rich-action-server-first-toggle_session_pinned")),
    )
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(
      element(by.id("session-rich-action-server-first-toggle_session_archived")),
    )
      .toBeVisible()
      .withTimeout(30000);
  });

  it("uses the plugin-declared main search", async () => {
    await launchHarness();

    await waitFor(element(by.id("session-main-search")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("session-main-search")).replaceText("server-first");
    await waitFor(element(by.id("session-row-server-first")))
      .toBeVisible()
      .withTimeout(30000);
    await detoxExpect(element(by.id("session-row-server-second"))).not.toExist();
  });

  it("applies non-main filters and supports Show all and Reset", async () => {
    await launchHarness();

    await waitFor(element(by.id("session-filters-open")))
      .toBeVisible()
      .withTimeout(30000);
    await detoxExpect(
      element(by.id("session-filters-active-count")),
    ).toHaveText("1");
    await element(by.id("session-filters-open")).tap();
    await waitFor(element(by.id("session-filter-pinned_state-option-true")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("session-filter-pinned_state-option-true")).tap();
    await element(by.id("session-filters-close")).tap();
    await waitFor(element(by.id("session-row-server-first")))
      .toBeVisible()
      .withTimeout(30000);
    await detoxExpect(element(by.id("session-row-server-second"))).not.toExist();

    await element(by.id("session-filters-open")).tap();
    await element(by.id("session-filters-show-all")).tap();
    await waitFor(element(by.id("session-filter-session_status-option-0")))
      .toBeVisible()
      .withTimeout(30000);
    await element(by.id("session-filter-session_status-option-0")).tap();
    await element(by.id("session-filters-close")).tap();
    await waitFor(element(by.id("session-row-server-second")))
      .toBeVisible()
      .withTimeout(30000);
    await detoxExpect(element(by.id("session-row-server-first"))).not.toExist();

    await element(by.id("session-filters-open")).tap();
    await element(by.id("session-filters-show-all")).tap();
    await element(by.id("session-filters-close")).tap();
    await waitFor(element(by.id("session-row-server-first")))
      .toBeVisible()
      .withTimeout(30000);
    await waitFor(element(by.id("session-row-server-second")))
      .toBeVisible()
      .withTimeout(30000);

    await element(by.id("session-filters-open")).tap();
    await element(by.id("session-filters-reset")).tap();
    await element(by.id("session-filters-close")).tap();
    await detoxExpect(
      element(by.id("session-filters-active-count")),
    ).toHaveText("1");
  });
});
