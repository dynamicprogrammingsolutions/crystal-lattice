/// <reference types="detox" />

import fs from 'node:fs';
import { expect as jestExpect } from '@jest/globals';

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

type InkBand = {
  firstY: number;
  lastY: number;
  inkPixels: number;
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

function markerInkBands(
  image: PngImage,
  rootFrame: Frame,
  rendererFrame: Frame,
): InkBand[] {
  const scaleX = image.width / rootFrame.width;
  const scaleY = image.height / rootFrame.height;
  const minX = Math.max(0, Math.floor(rendererFrame.x * scaleX));
  const maxX = Math.min(image.width, Math.ceil((rendererFrame.x + 30) * scaleX));
  const minY = Math.max(0, Math.floor(rendererFrame.y * scaleY));
  const maxY = Math.min(image.height, Math.ceil((rendererFrame.y + rendererFrame.height) * scaleY));
  const rowInk = new Map<number, number>();

  for (let y = minY; y < maxY; y += 1) {
    let inkPixels = 0;
    for (let x = minX; x < maxX; x += 1) {
      const offset = (image.width * y + x) * 4;
      const red = image.data[offset];
      const green = image.data[offset + 1];
      const blue = image.data[offset + 2];
      const alpha = image.data[offset + 3];

      if (alpha < 16) {
        continue;
      }

      const luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
      if (luminance < 150) {
        inkPixels += 1;
      }
    }
    if (inkPixels >= 2) {
      rowInk.set(y, inkPixels);
    }
  }

  const bands: InkBand[] = [];
  for (const [y, inkPixels] of rowInk) {
    const previous = bands[bands.length - 1];
    if (previous && y - previous.lastY <= 5) {
      previous.lastY = y;
      previous.inkPixels += inkPixels;
    } else {
      bands.push({ firstY: y, lastY: y, inkPixels });
    }
  }
  return bands;
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
      clcOrderedListMarkdownHarness: '1',
    },
  });
  await dismissAndroidImmersiveModeConfirmation();
  await waitFor(element(by.id('ordered-list-markdown-harness-ready')))
    .toExist()
    .withTimeout(30000);
}

describe('enriched markdown ordered-list rendering', () => {
  beforeEach(async () => {
    await launchHarness();
  });

  it('preserves the ordered-list start number from markdown', async () => {
    const rootFrame = frameFrom(
      await element(by.id('ordered-list-markdown-harness-ready')).getAttributes(),
    );
    const enrichedFrame = frameFrom(
      await element(by.id('ordered-list-enriched-renderer')).getAttributes(),
    );
    const legacyFrame = frameFrom(
      await element(by.id('ordered-list-legacy-renderer')).getAttributes(),
    );
    const screenshotPath = await device.takeScreenshot('ordered-list-start-number');
    const screenshot = PNG.sync.read(fs.readFileSync(screenshotPath)) as PngImage;
    const enrichedBands = markerInkBands(screenshot, rootFrame, enrichedFrame);
    const legacyBands = markerInkBands(screenshot, rootFrame, legacyFrame);
    const enrichedFirstMarker = enrichedBands[0];
    const legacyFirstMarker = legacyBands[0];

    if (!enrichedFirstMarker || !legacyFirstMarker) {
      throw new Error(
        `Missing first marker band: enriched=${JSON.stringify(enrichedBands)}, legacy=${JSON.stringify(legacyBands)}`,
      );
    }

    const inkRatio = enrichedFirstMarker.inkPixels / legacyFirstMarker.inkPixels;
    jestExpect(inkRatio).toBeGreaterThanOrEqual(0.85);
  });

  it('draws an ordered marker only beside the first paragraph of an item', async () => {
    const rootFrame = frameFrom(
      await element(by.id('ordered-list-markdown-harness-ready')).getAttributes(),
    );
    const enrichedFrame = frameFrom(
      await element(by.id('ordered-list-enriched-renderer')).getAttributes(),
    );
    const legacyFrame = frameFrom(
      await element(by.id('ordered-list-legacy-renderer')).getAttributes(),
    );
    const screenshotPath = await device.takeScreenshot('ordered-list-marker-repetition');
    const screenshot = PNG.sync.read(fs.readFileSync(screenshotPath)) as PngImage;
    const enrichedBands = markerInkBands(screenshot, rootFrame, enrichedFrame);
    const legacyBands = markerInkBands(screenshot, rootFrame, legacyFrame);

    jestExpect(enrichedBands).toHaveLength(legacyBands.length);
  });
});