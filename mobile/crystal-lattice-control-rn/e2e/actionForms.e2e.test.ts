/// <reference types="detox" />

import * as detox from 'detox';
import { expect as jestExpect } from '@jest/globals';
import { MANY_FIELD_DIALOG } from '../../../test/fixture/actionFormLayouts';

const detoxExpect = detox.expect;
const landscapeTest = process.env.CLC_TEST_ACTION_FORM_LANDSCAPE === '1' ? it : it.skip;
type Frame = { x: number; y: number; width: number; height: number };

async function frame(id: string, ancestorId?: string): Promise<Frame> {
  const matcher = ancestorId ? by.id(id).withAncestor(by.id(ancestorId)) : by.id(id);
  const attributes: any = await element(matcher).getAttributes();
  const result = attributes.frame ?? attributes.elementBounds;
  if (!result || typeof result.y !== 'number' || typeof result.height !== 'number') {
    throw new Error(`Missing native frame for ${id}: ${JSON.stringify(attributes)}`);
  }
  return result;
}

async function expectContained(
  childId: string,
  viewportId: string,
  ancestorId?: string,
): Promise<void> {
  const child = await frame(childId, ancestorId);
  const viewport = await frame(viewportId);
  const roundingTolerance = device.getPlatform() === 'android' ? 2 : 1;
  jestExpect(child.x).toBeGreaterThanOrEqual(viewport.x - roundingTolerance);
  jestExpect(child.y).toBeGreaterThanOrEqual(viewport.y - roundingTolerance);
  jestExpect(child.x + child.width).toBeLessThanOrEqual(
    viewport.x + viewport.width + roundingTolerance,
  );
  jestExpect(child.y + child.height).toBeLessThanOrEqual(
    viewport.y + viewport.height + roundingTolerance,
  );
}

async function open(scenario: string): Promise<void> {
  await element(by.id(`action-forms-open-${scenario}`)).tap();
}

async function editLastField(): Promise<void> {
  const input = element(
    by.id('action-form-input-last').withAncestor(by.id('application-action-dialog-body')),
  );
  await waitFor(input)
    .toBeVisible()
    .whileElement(by.id('application-action-dialog-body'))
    .scroll(200, 'down');
  await input.tap();
  await input.typeText(' changed');
  await detoxExpect(input).toBeVisible();
  await detoxExpect(element(by.id('application-action-dialog-primary'))).toBeVisible();
  await expectContained(
    'action-form-input-last',
    'application-action-dialog-body',
    'application-action-dialog-body',
  );
  await expectContained('application-action-dialog-controls', 'application-action-dialog-viewport');
}

function expectedManyValues(): Record<string, string | number> {
  const values: Record<string, string | number> = {};
  for (const input of MANY_FIELD_DIALOG.inputs) {
    values[input.name] = input.default as string | number;
  }
  return { ...values, last: 'last value changed' };
}

describe('mobile action forms and report layout', () => {
  beforeEach(async () => {
    await device.launchApp({
      newInstance: true,
      launchArgs: { clcActionFormsHarness: '1' },
    });
    if (device.getPlatform() === 'android') {
      for (const label of ['Wait', 'Got it']) {
        try {
          await system.element(by.system.label(label)).tap();
        } catch {}
      }
    }
    await device.setOrientation('portrait');
    await waitFor(element(by.id('action-forms-harness-ready')))
      .toExist()
      .withTimeout(30000);
  });

  afterEach(async () => {
    await device.setOrientation('portrait');
  });

  it('keeps a short confirmation compact inside the safe viewport', async () => {
    await open('confirm');
    await expectContained('application-action-dialog-card', 'application-action-dialog-viewport');
    const card = await frame('application-action-dialog-card');
    const viewport = await frame('application-action-dialog-viewport');
    jestExpect(card.height).toBeLessThan(viewport.height / 2);
    await element(by.id('application-action-dialog-cancel')).tap();
    await detoxExpect(element(by.id('application-action-dialog-card'))).not.toExist();
  });

  it('edits a three-field form and submits while the software keyboard is open', async () => {
    await open('three');
    const initialViewport = await frame('application-action-dialog-viewport');
    await editLastField();
    const keyboardViewport = await frame('application-action-dialog-viewport');
    jestExpect(keyboardViewport.height).toBeLessThan(initialViewport.height);
    await element(by.id('application-action-dialog-primary')).tap();
    await detoxExpect(element(by.id('action-forms-submitted'))).toHaveText(
      JSON.stringify({
        first: 'first value',
        notes: 'fixture notes',
        last: 'last value changed',
      }),
    );
  });

  it('scrolls a many-field form with the keyboard open and retains all submitted values', async () => {
    await open('large-text');
    await open('many');
    await element(by.id('action-form-input-value_0')).tap();
    await editLastField();
    await element(by.id('application-action-dialog-primary')).tap();
    await detoxExpect(element(by.id('action-forms-submitted'))).toHaveText(
      JSON.stringify(expectedManyValues()),
    );
  });

  it.each(['react-native-markdown-display', 'react-native-enriched-markdown'])(
    'scrolls %s markdown independently of the result controls',
    async (renderer) => {
      if (renderer === 'react-native-enriched-markdown') await open('renderer');
      await open('report');
      const contentId = `action-forms-result-body-content-${renderer}`;
      const contentBefore = await frame(contentId);
      const controlsBefore = await frame('action-result-controls');
      await element(by.id('action-forms-result-body')).swipe('up', 'slow', 0.6);
      const contentAfter = await frame(contentId);
      const controlsAfter = await frame('action-result-controls');
      jestExpect(contentAfter.y).toBeLessThan(contentBefore.y - 30);
      jestExpect(Math.abs(controlsAfter.y - controlsBefore.y)).toBeLessThanOrEqual(1);
      await detoxExpect(element(by.id('action-display-action-edit'))).toBeVisible();
      await expectContained('action-result-card', 'action-result-viewport');
      await element(by.id('action-result-close')).tap();
    },
  );

  it('keeps small embedded fields and actions reachable above the keyboard', async () => {
    await open('small-form');
    const initialViewport = await frame('action-result-viewport');
    await waitFor(element(by.id('action-form-input-to')))
      .toBeVisible()
      .whileElement(by.id('action-forms-result-body-form'))
      .scroll(100, 'down');
    await element(by.id('action-form-input-to')).tap();
    await element(by.id('action-form-input-to')).typeText(' changed');
    await detoxExpect(element(by.id('action-form-input-to'))).toBeVisible();
    await expectContained('action-form-input-to', 'action-forms-result-body-form');
    await expectContained('action-result-controls', 'action-result-viewport');
    const keyboardViewport = await frame('action-result-viewport');
    jestExpect(keyboardViewport.height).toBeLessThan(initialViewport.height);
    await element(by.id('action-display-action-apply')).tap();
    await element(by.id('action-result-close')).tap();
    await detoxExpect(element(by.id('action-forms-submitted'))).toHaveText(
      JSON.stringify({
        from: 'first bound',
        to: 'last bound changed',
      }),
    );
  });

  it('contains oversized embedded fields and opens a scrollable follow-up dialog', async () => {
    await open('oversized-form');
    await expectContained('action-result-controls', 'action-result-viewport');
    await waitFor(element(by.id('action-form-input-last')))
      .toBeVisible()
      .whileElement(by.id('action-forms-result-body-form'))
      .scroll(120, 'down');
    await element(by.id('action-form-input-last')).tap();
    await element(by.id('action-form-input-last')).typeText(' embedded');
    await detoxExpect(element(by.id('action-display-action-edit'))).toBeVisible();
    await element(by.id('action-display-action-edit')).tap();
    await editLastField();
    await element(by.id('application-action-dialog-primary')).tap();
    await detoxExpect(element(by.id('action-display-action-edit'))).toBeVisible();
    await element(by.id('action-result-close')).tap();
    await detoxExpect(element(by.id('action-forms-submitted'))).toHaveText(
      JSON.stringify(expectedManyValues()),
    );
  });

  landscapeTest(
    'retains controls in a reduced-height viewport with larger typography',
    async () => {
      await open('large-text');
      await device.setOrientation('landscape');
      await waitFor(element(by.id('action-forms-orientation')))
        .toHaveText('landscape')
        .withTimeout(10000);
      await open('many');
      await editLastField();
      await element(by.id('application-action-dialog-cancel')).tap();
      await open('small-form');
      await waitFor(element(by.id('action-form-input-to')))
        .toBeVisible()
        .whileElement(by.id('action-forms-result-body-form'))
        .scroll(100, 'down');
      await element(by.id('action-form-input-to')).tap();
      await waitFor(element(by.id('action-form-input-to')))
        .toBeVisible()
        .withTimeout(5000);
      await element(by.id('action-form-input-to')).typeText(' landscape');
      await detoxExpect(element(by.id('action-form-input-to'))).toBeVisible();
      await expectContained('action-form-input-to', 'action-forms-result-body-form');
      await expectContained('action-result-controls', 'action-result-viewport');
      await detoxExpect(element(by.id('action-display-action-edit'))).toBeVisible();
      await element(by.id('action-display-action-apply')).tap();
      await element(by.id('action-result-close')).tap();
      await detoxExpect(element(by.id('action-forms-submitted'))).toHaveText(
        JSON.stringify({ from: 'first bound', to: 'last bound landscape' }),
      );
    },
  );
});
