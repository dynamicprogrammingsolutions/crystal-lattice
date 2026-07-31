/// <reference types="detox" />

import * as detox from 'detox';
import fs from 'node:fs';
import path from 'node:path';

const detoxExpect = detox.expect;

type Frame = {
  x: number;
  y: number;
  width: number;
  height: number;
};

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

function expectBefore(upper: Frame, lower: Frame, label: string): void {
  const upperBottom = upper.y + upper.height;
  if (upperBottom > lower.y + 1) {
    throw new Error(
      `${label}: expected ${upperBottom} <= ${lower.y}; upper=${JSON.stringify(
        upper,
      )} lower=${JSON.stringify(lower)}`,
    );
  }
}

async function captureScreenshot(name: string): Promise<void> {
  const source = await device.takeScreenshot(name);
  const directory = path.resolve(process.cwd(), 'artifacts', 'notification-visual');
  fs.mkdirSync(directory, { recursive: true });
  fs.copyFileSync(source, path.join(directory, `${name}.png`));
}

async function openScenario(
  scenario:
    | 'sessions-banner'
    | 'sessions-modal'
    | 'sessions-session-hidden'
    | 'messages-banner'
    | 'messages-application-hidden'
    | 'messages-inline'
    | 'messages-modal',
): Promise<void> {
  await device.launchApp({
    newInstance: true,
    launchArgs: { clcNotificationBannerHarness: '1' },
  });
  await waitFor(element(by.id('notification-banner-harness-ready')))
    .toExist()
    .withTimeout(30000);
  await element(by.id(`notification-scenario-${scenario}`)).tap();
  await device.disableSynchronization();
  await waitFor(element(by.id('notification-visual-ready')))
    .toExist()
    .withTimeout(30000);
}

describe('mobile notification visual placement', () => {
  afterEach(async () => {
    await device.enableSynchronization();
  });

  it('places the application banner below Sessions search/filter and above rows', async () => {
    await openScenario('sessions-banner');
    await waitFor(element(by.id('sessions-notification-banner-rail')))
      .toExist()
      .withTimeout(30000);

    const filter = frameFrom(
      await element(by.id('sessions-search-filter-row')).getAttributes(),
    );
    const banner = frameFrom(
      await element(by.id('sessions-notification-banner-rail')).getAttributes(),
    );
    const firstRow = frameFrom(
      await element(by.id('session-row-notification-visual-session')).getAttributes(),
    );
    expectBefore(filter, banner, 'Sessions filter row must precede banner');
    expectBefore(banner, firstRow, 'Sessions banner must push rows down');

    await captureScreenshot('notifications-sessions-application-banner');
  });

  it('shows the application modal over the production Sessions screen', async () => {
    await openScenario('sessions-modal');
    await waitFor(element(by.id('global-notification-modal')))
      .toExist()
      .withTimeout(30000);
    await detoxExpect(element(by.text('Notification visual modal'))).toBeVisible();

    await captureScreenshot('notifications-sessions-application-modal');
  });

  it('does not show a session notification on Sessions', async () => {
    await openScenario('sessions-session-hidden');
    await new Promise<void>((resolve) => setTimeout(resolve, 500));
    await detoxExpect(
      element(by.id('sessions-notification-banner-rail')),
    ).not.toExist();

    await captureScreenshot('notifications-sessions-session-hidden');
  });

  it('places the session banner below the Messages header and above transcript', async () => {
    await openScenario('messages-banner');
    await waitFor(element(by.id('messages-notification-banner-rail')))
      .toExist()
      .withTimeout(30000);

    const header = frameFrom(
      await element(by.id('messages-screen-header')).getAttributes(),
    );
    const banner = frameFrom(
      await element(by.id('messages-notification-banner-rail')).getAttributes(),
    );
    const transcript = frameFrom(
      await element(by.id('transcript-scroll-list')).getAttributes(),
    );
    expectBefore(header, banner, 'Messages header must precede banner');
    expectBefore(banner, transcript, 'Messages banner must push transcript down');

    await captureScreenshot('notifications-messages-session-banner');
  });

  it('captures inline session notification placement in Messages content', async () => {
    await openScenario('messages-inline');
    await waitFor(element(by.text('Inline session notification')))
      .toBeVisible()
      .withTimeout(30000);

    await captureScreenshot('notifications-messages-session-inline');
  });

  it('does not show an application notification on Messages', async () => {
    await openScenario('messages-application-hidden');
    await new Promise<void>((resolve) => setTimeout(resolve, 500));
    await detoxExpect(
      element(by.id('messages-notification-banner-rail')),
    ).not.toExist();

    await captureScreenshot('notifications-messages-application-hidden');
  });

  it('captures modal session notification presentation on Messages', async () => {
    await openScenario('messages-modal');
    await waitFor(element(by.id('global-notification-modal')))
      .toExist()
      .withTimeout(30000);

    await captureScreenshot('notifications-messages-session-modal');
  });
});