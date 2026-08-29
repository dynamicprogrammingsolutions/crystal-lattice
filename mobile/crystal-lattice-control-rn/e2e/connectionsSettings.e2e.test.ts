/// <reference types="detox" />

import * as detox from 'detox';
import { expect as jestExpect } from '@jest/globals';

const detoxExpect = detox.expect;
const HARNESS_LAUNCH_ARGS = { clcConnectionsSettingsHarness: '1' };

type Frame = { x: number; y: number; width: number; height: number };
function frameFrom(attributes: any): Frame {
  const frame = attributes?.frame || attributes?.elementBounds;
  if (
    !frame ||
    typeof frame.x !== 'number' ||
    typeof frame.y !== 'number' ||
    typeof frame.width !== 'number' ||
    typeof frame.height !== 'number'
  ) {
    throw new Error(`Missing native frame: ${JSON.stringify(attributes)}`);
  }
  return frame;
}

async function dismissAndroidImmersiveModeConfirmation(): Promise<void> {
  if (device.getPlatform() !== 'android') return;
  try {
    await system.element(by.system.label('Wait')).tap();
  } catch {
    // Some emulator images surface a transient system-process ANR dialog.
  }
  try {
    await system.element(by.system.label('Got it')).tap();
  } catch {
    // Fresh E2E images do not show this one-time Android system confirmation.
  }
}

async function launchHarness(deleteData: boolean): Promise<void> {
  await device.launchApp({
    newInstance: true,
    delete: deleteData,
    launchArgs: HARNESS_LAUNCH_ARGS,
  });
  await dismissAndroidImmersiveModeConfirmation();
  await waitFor(element(by.id('connections-settings-harness-ready')))
    .toExist()
    .withTimeout(30000);
}

describe('mobile Connections and markdown settings', () => {
  it('uses production actions, modals, persistence, and native geometry', async () => {
    await launchHarness(true);

    await detoxExpect(element(by.id('connections-global-settings'))).toBeVisible();
    await detoxExpect(element(by.id('connections-new-connection'))).toBeVisible();
    await detoxExpect(element(by.id('connection-status-active'))).toHaveText('Open');
    await detoxExpect(element(by.id('connection-status-closed'))).toHaveText('Closed');
    await detoxExpect(element(by.text('Connected to'))).not.toExist();
    await detoxExpect(element(by.text('Last used:'))).not.toExist();

    const connectionsTitleFrame = frameFrom(
      await element(by.id('connections-screen-title')).getAttributes(),
    );
    const connectionCardTitleFrame = frameFrom(
      await element(by.id('connection-title-active')).getAttributes(),
    );
    jestExpect(
      Math.abs(connectionsTitleFrame.x - connectionCardTitleFrame.x),
    ).toBeLessThanOrEqual(1);

    await element(by.id('connection-open')).tap();
    await detoxExpect(element(by.id('connection-status-closed'))).toHaveText('Open');
    await detoxExpect(element(by.id('connections-harness-last-action'))).toHaveText('opened:closed');

    await element(by.id('connection-card-closed')).tap();
    await detoxExpect(
      element(by.text('No sessions loaded yet. Open the Connections tab to connect to a server.')),
    ).toBeVisible();
    await detoxExpect(element(by.id('connections-harness-last-action'))).toHaveText('opened:closed');
    await element(by.id('connections-tab')).tap();

    await element(by.id('connection-disconnect')).tap();
    await detoxExpect(element(by.id('connections-harness-last-action'))).toHaveText('disconnected');
    await element(by.id('connection-card-active')).tap();
    await detoxExpect(
      element(by.text('No sessions loaded yet. Open the Connections tab to connect to a server.')),
    ).toBeVisible();
    await detoxExpect(element(by.id('connections-harness-last-action'))).toHaveText('opened:active');
    await element(by.id('connections-tab')).tap();

    const rootFrame = frameFrom(
      await element(by.id('connections-settings-harness-ready')).getAttributes(),
    );
    const previewFrame = frameFrom(
      await element(by.id('markdown-preview')).getAttributes(),
    );
    const initialHeadingFrame = frameFrom(
      await element(by.id('markdown-preview-h1')).getAttributes(),
    );
    const initialBodyFrame = frameFrom(
      await element(by.id('markdown-preview-body')).getAttributes(),
    );
    const initialFooterFrame = frameFrom(
      await element(by.id('footer-geometry-probe')).getAttributes(),
    );
    jestExpect(previewFrame.width).toBeLessThanOrEqual(rootFrame.width);
    jestExpect(initialHeadingFrame.height).toBeGreaterThan(initialBodyFrame.height);

    await element(by.id('connections-global-settings')).tap();
    await waitFor(element(by.id('global-settings-modal'))).toBeVisible().withTimeout(10000);
    await element(by.id('global-settings-base-font-size')).tap();
    await element(by.id('options-picker-option-16')).tap();
    await detoxExpect(element(by.id('global-settings-base-font-size-value'))).toHaveText('16');
    await element(by.id('global-settings-modal-close')).tap();

    const footerAt16Frame = frameFrom(
      await element(by.id('footer-geometry-probe')).getAttributes(),
    );
    jestExpect(footerAt16Frame.height).toBeGreaterThan(initialFooterFrame.height);

    await element(by.id('connections-global-settings')).tap();
    await element(by.id('global-settings-base-font-size')).tap();
    await element(by.id('options-picker-option-17')).tap();
    await element(by.id('global-settings-markdown-headers')).tap();
    await element(by.id('options-picker-option-small')).tap();
    await detoxExpect(element(by.id('global-settings-base-font-size-value'))).toHaveText('17');
    await detoxExpect(element(by.id('global-settings-markdown-headers-value'))).toHaveText('Small');
    await element(by.id('global-settings-modal-close')).tap();

    const smallHeadingFrame = frameFrom(
      await element(by.id('markdown-preview-h1')).getAttributes(),
    );
    const largeBodyFrame = frameFrom(
      await element(by.id('markdown-preview-body')).getAttributes(),
    );
    jestExpect(smallHeadingFrame.height).toBeLessThan(initialHeadingFrame.height);
    jestExpect(largeBodyFrame.height).toBeGreaterThan(initialBodyFrame.height);
    jestExpect(smallHeadingFrame.width).toBeLessThanOrEqual(previewFrame.width);
    jestExpect(largeBodyFrame.width).toBeLessThanOrEqual(previewFrame.width);

    await element(by.id('connection-health-check')).tap();
    await waitFor(element(by.id('health-check-modal'))).toBeVisible().withTimeout(10000);
    await detoxExpect(element(by.id('health-check-result'))).toHaveText(
      'OK: {\n  "message": "healthy"\n}',
    );
    await element(by.id('health-check-modal-close')).tap();

    await element(by.id('connection-server-settings')).tap();
    await waitFor(element(by.id('server-settings-modal'))).toBeVisible().withTimeout(10000);
    await element(by.id('server-settings-modal-close')).tap();

    await element(by.id('connection-actions-menu-active')).tap();
    await waitFor(element(by.id('actions-menu-pin-delete'))).toBeVisible().withTimeout(10000);
    const actionsPanelFrame = frameFrom(
      await element(by.id('actions-menu-panel')).getAttributes(),
    );
    const actionsTitleFrame = frameFrom(
      await element(by.id('actions-menu-title')).getAttributes(),
    );
    const actionsCloseFrame = frameFrom(
      await element(by.id('actions-menu-close')).getAttributes(),
    );
    jestExpect(
      actionsTitleFrame.x + actionsTitleFrame.width,
    ).toBeLessThanOrEqual(actionsCloseFrame.x);
    jestExpect(actionsCloseFrame.x + actionsCloseFrame.width).toBeLessThanOrEqual(
      actionsPanelFrame.x + actionsPanelFrame.width,
    );
    await element(by.id('actions-menu-pin-delete')).tap();
    await element(by.id('actions-menu-close')).tap();
    await detoxExpect(element(by.label('Delete')).atIndex(0)).toBeVisible();

    await launchHarness(false);
    await detoxExpect(element(by.label('Delete')).atIndex(0)).toBeVisible();
    await element(by.id('connections-global-settings')).tap();
    await detoxExpect(element(by.id('global-settings-base-font-size-value'))).toHaveText('17');
    await detoxExpect(element(by.id('global-settings-markdown-headers-value'))).toHaveText('Small');
    await element(by.id('global-settings-modal-close')).tap();

    await element(by.id('connections-new-connection')).tap();
    await detoxExpect(element(by.id('connections-harness-last-action'))).toHaveText('newConnection');
  });
});