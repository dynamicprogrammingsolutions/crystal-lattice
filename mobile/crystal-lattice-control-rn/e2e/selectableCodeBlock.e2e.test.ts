/// <reference types="detox" />

import fs from 'node:fs';

const { PNG } = require('pngjs');

type Frame = {
  x: number;
  y: number;
  width: number;
  height: number;
};

type PngImage = {
  width: number;
  height: number;
  data: Buffer;
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

function expectMinimumFrame(frame: Frame, minimum: Pick<Frame, 'width' | 'height'>, label: string): void {
  if (frame.width < minimum.width || frame.height < minimum.height) {
    throw new Error(
      `${label}: expected at least ${JSON.stringify(minimum)}, got ${JSON.stringify(frame)}`,
    );
  }
}

function readPng(filePath: string): PngImage {
  return PNG.sync.read(fs.readFileSync(filePath));
}

function countInkPixels(
  image: PngImage,
  frame: Frame,
  scaleX: number,
  scaleY: number,
): { inkPixels: number; sampledPixels: number } {
  const minX = Math.max(0, Math.floor(frame.x * scaleX));
  const minY = Math.max(0, Math.floor(frame.y * scaleY));
  const maxX = Math.min(image.width, Math.ceil((frame.x + frame.width) * scaleX));
  const maxY = Math.min(image.height, Math.ceil((frame.y + frame.height) * scaleY));
  let inkPixels = 0;
  let sampledPixels = 0;

  for (let y = minY; y < maxY; y += 1) {
    for (let x = minX; x < maxX; x += 1) {
      const offset = (image.width * y + x) * 4;
      const red = image.data[offset];
      const green = image.data[offset + 1];
      const blue = image.data[offset + 2];
      const alpha = image.data[offset + 3];

      if (alpha < 16) {
        continue;
      }

      sampledPixels += 1;

      const luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
      const channelSpread = Math.max(red, green, blue) - Math.min(red, green, blue);
      if (luminance < 145 || channelSpread > 45) {
        inkPixels += 1;
      }
    }
  }

  return { inkPixels, sampledPixels };
}

function expectPaintedCodeText(
  image: PngImage,
  rootFrame: Frame,
  nativeFrame: Frame,
  label: string,
): void {
  const scaleX = image.width / rootFrame.width;
  const scaleY = image.height / rootFrame.height;
  const { inkPixels, sampledPixels } = countInkPixels(image, nativeFrame, scaleX, scaleY);
  const ratio = sampledPixels > 0 ? inkPixels / sampledPixels : 0;

  if (inkPixels < 120 || ratio < 0.008) {
    throw new Error(
      `${label}: expected visible code glyph pixels, got inkPixels=${inkPixels}, ratio=${ratio.toFixed(
        4,
      )}, frame=${JSON.stringify(nativeFrame)}, root=${JSON.stringify(rootFrame)}`,
    );
  }
}

async function dismissAndroidImmersiveModeConfirmation(): Promise<void> {
  if (device.getPlatform() !== 'android') {
    return;
  }
  try {
    await system.element(by.system.label('Got it')).tap();
  } catch {
    // Fresh E2E images do not show this one-time Android system confirmation.
  }
}

async function launchHarness(): Promise<void> {
  await device.launchApp({
    newInstance: true,
    launchArgs: {
      clcSelectableCodeBlockHarness: '1',
    },
  });
  await dismissAndroidImmersiveModeConfirmation();
  await waitFor(element(by.id('code-block-harness-ready')))
    .toExist()
    .withTimeout(30000);
}

async function expectCodeBlocksMeasured(label: string): Promise<void> {
  const screenshotPath = await device.takeScreenshot(`selectable-code-block-${label}`);
  const screenshot = readPng(screenshotPath);
  const rootFrame = frameFrom(await element(by.id('code-block-harness-ready')).getAttributes());

  for (let index = 0; index < 5; index += 1) {
    const outerId = `code-block-repro-${index}`;
    const nativeId = `${outerId}-native`;

    await waitFor(element(by.id(outerId)))
      .toExist()
      .withTimeout(30000);
    await waitFor(element(by.id(nativeId)))
      .toExist()
      .withTimeout(30000);

    const outerFrame = frameFrom(await element(by.id(outerId)).getAttributes());
    const nativeFrame = frameFrom(await element(by.id(nativeId)).getAttributes());

    expectMinimumFrame(outerFrame, { width: 250, height: 50 }, `${label}: ${outerId}`);
    expectMinimumFrame(nativeFrame, { width: 250, height: 16 }, `${label}: ${nativeId}`);
    expectPaintedCodeText(screenshot, rootFrame, nativeFrame, `${label}: ${nativeId}`);
  }
}

async function remountCodeBlocks(): Promise<void> {
  await element(by.id('code-block-harness-sessions-tab')).tap();
  await waitFor(element(by.id('code-block-harness-placeholder')))
    .toExist()
    .withTimeout(30000);
  await element(by.id('code-block-harness-messages-tab')).tap();
  await waitFor(element(by.id('code-block-repro-0')))
    .toExist()
    .withTimeout(30000);
}

describe('selectable code block layout', () => {
  it('keeps five unwrapped long code blocks measured after remounts', async () => {
    await launchHarness();
    await expectCodeBlocksMeasured('initial');

    for (let cycle = 0; cycle < 4; cycle += 1) {
      await remountCodeBlocks();
      await expectCodeBlocksMeasured(`remount ${cycle + 1}`);
    }
  });
});