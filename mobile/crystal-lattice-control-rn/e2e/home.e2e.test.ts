/// <reference types="detox" />

import * as detox from 'detox';
import { expect as jestExpect } from '@jest/globals';

const detoxExpect = detox.expect;

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

async function launchHome(deleteData: boolean): Promise<void> {
  await device.launchApp({
    newInstance: true,
    delete: deleteData,
    launchArgs: { clcHomeHarness: '1' },
  });
  await dismissAndroidImmersiveModeConfirmation();
  await waitFor(element(by.id('home-harness-ready')))
    .toExist()
    .withTimeout(30000);
  await waitFor(element(by.id('home-screen-header')))
    .toBeVisible()
    .withTimeout(30000);
}

describe('mobile Home Watchlist and recent sessions', () => {
  it('uses two-column reorderable tiles, permanent shared notes, settings, and closed navigation', async () => {
    await launchHome(true);

    await detoxExpect(element(by.id('home-tab'))).toBeVisible();
    await detoxExpect(element(by.id('connections-tab'))).toBeVisible();
    await detoxExpect(element(by.id('sessions-tab'))).toBeVisible();
    await detoxExpect(element(by.id('messages-tab'))).toBeVisible();
    await detoxExpect(element(by.id('home-recent-timeline'))).toBeVisible();
    await detoxExpect(element(by.text('Recent Sessions'))).toBeVisible();
    await detoxExpect(element(by.text('Last 3 days'))).toBeVisible();
    await detoxExpect(element(by.text('Older laptop session'))).toBeVisible();

    await element(by.id('home-recent-open-laptop-older')).tap();
    await waitFor(element(by.id('home-harness-last-action')))
      .toHaveText('opened:laptop')
      .withTimeout(10000);
    await detoxExpect(element(by.id('messages-tab-content'))).toBeVisible();
    await element(by.id('home-tab')).tap();

    await element(by.id('home-recent-watch-office-shared')).tap();
    await element(by.id('home-recent-watch-laptop-shared')).tap();
    await waitFor(element(by.id('home-watchlist-tile-office-shared')))
      .toBeVisible()
      .withTimeout(10000);

    const firstBefore = frameFrom(
      await element(by.id('home-watchlist-tile-office-shared')).getAttributes(),
    );
    const secondBefore = frameFrom(
      await element(by.id('home-watchlist-tile-laptop-shared')).getAttributes(),
    );
    jestExpect(Math.abs(firstBefore.y - secondBefore.y)).toBeLessThanOrEqual(2);
    jestExpect(firstBefore.x).toBeLessThan(secondBefore.x);
    jestExpect(Math.abs(firstBefore.width - secondBefore.width)).toBeLessThanOrEqual(2);

    await element(by.id('home-watchlist-note-office-shared')).tap();
    await element(by.id('session-note-input')).replaceText('Permanent shared note');
    await element(by.id('session-note-save')).tap();
    await detoxExpect(
      element(by.id('home-watchlist-note-preview-office-shared')),
    ).toHaveText('Permanent shared note');
    await detoxExpect(
      element(by.id('home-watchlist-note-preview-laptop-shared')),
    ).toHaveText('Permanent shared note');

    await element(by.id('home-watchlist-drag-office-shared')).swipe(
      'right',
      'fast',
      0.8,
    );
    const firstAfter = frameFrom(
      await element(by.id('home-watchlist-tile-office-shared')).getAttributes(),
    );
    const secondAfter = frameFrom(
      await element(by.id('home-watchlist-tile-laptop-shared')).getAttributes(),
    );
    jestExpect(firstAfter.x).toBeGreaterThan(secondAfter.x);

    await element(by.id('home-menu')).tap();
    await element(by.id('home-menu-global-settings')).tap();
    await waitFor(element(by.id('global-settings-modal')))
      .toBeVisible()
      .withTimeout(10000);
    await element(by.id('global-settings-recent-sessions')).tap();
    await element(by.id('options-picker-option-24h')).tap();
    await detoxExpect(
      element(by.id('global-settings-recent-sessions-value')),
    ).toHaveText('Last 24 hours');
    await element(by.id('global-settings-modal-close')).tap();
    await detoxExpect(element(by.text('Older laptop session'))).not.toExist();

    await launchHome(false);
    await detoxExpect(
      element(by.id('home-watchlist-note-preview-office-shared')),
    ).toHaveText('Permanent shared note');
    const persistedFirst = frameFrom(
      await element(by.id('home-watchlist-tile-laptop-shared')).getAttributes(),
    );
    const persistedSecond = frameFrom(
      await element(by.id('home-watchlist-tile-office-shared')).getAttributes(),
    );
    jestExpect(persistedFirst.x).toBeLessThan(persistedSecond.x);
    await detoxExpect(element(by.text('Last 24 hours'))).toBeVisible();
  });
});