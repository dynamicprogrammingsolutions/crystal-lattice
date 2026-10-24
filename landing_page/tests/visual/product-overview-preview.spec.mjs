import fs from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

import {
  productOverviewStories,
} from "../../scripts/visual-assets/product-overview-preview.mjs";

test.skip(
  process.env.CRYSTAL_PRODUCT_OVERVIEW_PREVIEW !== "1",
  "Requires the explicitly enabled product overview preview.",
);

const captureDirectory = path.resolve(
  "artifacts/product-overview-review",
);

async function loadImages(page) {
  await page.locator('img[loading="lazy"]').evaluateAll(images => {
    images.forEach(image => {
      image.loading = "eager";
    });
  });
  await page.waitForFunction(() =>
    Array.from(document.images).every(
      image => image.complete && image.naturalWidth > 0,
    ),
  );
}

test("renders the concise product overview before Getting Started", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/", { waitUntil: "networkidle" });
  await loadImages(page);

  const primaryOrder = await page
    .locator("#hero, #product-overview, #getting-started")
    .evaluateAll(sections => sections.map(section => section.id));
  expect(primaryOrder).toEqual([
    "hero",
    "product-overview",
    "getting-started",
  ]);

  await expect(page.locator("#product-highlights")).toHaveCount(0);
  await expect(page.locator("#product-overview")).toBeVisible();
  await expect(
    page.locator("[data-product-overview-story]"),
  ).toHaveCount(4);
  await expect(
    page.locator("[data-product-overview-image]"),
  ).toHaveCount(5);
  await expect(
    page.locator("#product-overview button"),
  ).toHaveCount(0);
  await expect(page.locator("#product-overview")).not.toContainText(
    /Planned visual|candidate|fixture|review|what it proves/i,
  );

  const storyIds = await page
    .locator("[data-product-overview-story]")
    .evaluateAll(stories =>
      stories.map(story =>
        story.getAttribute("data-product-overview-story"),
      ),
    );
  expect(storyIds).toEqual(productOverviewStories.map(story => story.id));

  const gettingStartedTop = await page.locator("#getting-started").evaluate(
    element => element.getBoundingClientRect().top + window.scrollY,
  );
  const secondaryProofTop = await page
    .locator("#secondary-product-proof")
    .evaluate(element => element.getBoundingClientRect().top + window.scrollY);
  expect(secondaryProofTop).toBeGreaterThan(gettingStartedTop);
});

for (const viewport of [
  { id: "1440", width: 1440, height: 1000 },
  { id: "768", width: 768, height: 1000 },
  { id: "390", width: 390, height: 844 },
  { id: "320", width: 320, height: 568 },
]) {
  for (const theme of ["light", "dark"]) {
    test(`product overview ${viewport.id} ${theme}`, async ({ page }) => {
      fs.mkdirSync(captureDirectory, { recursive: true });
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height,
      });
      await page.addInitScript(
        value => localStorage.setItem("cl-theme", value),
        theme,
      );
      await page.goto("/", { waitUntil: "networkidle" });
      await loadImages(page);

      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth + 1,
        ),
      ).toBe(true);

      const overview = page.locator("#product-overview");
      await expect(overview).toBeVisible();
      for (const story of productOverviewStories) {
        const article = overview.locator(`#${story.id}`);
        await article.scrollIntoViewIfNeeded();
        await expect(article).toBeVisible();
        await expect(article).toContainText(story.title);
        for (const image of story.images) {
          const figure = article.locator(
            `[data-product-overview-image="${image.id}"]`,
          );
          const state = await figure.locator("img").evaluate(element => ({
            currentSrc: element.currentSrc,
            naturalWidth: element.naturalWidth,
            naturalHeight: element.naturalHeight,
          }));
          const compact = viewport.width <= 760;
          expect(state.currentSrc).toContain(
            `${image.id}-${compact ? "compact" : "wide"}`,
          );
          expect(state.naturalWidth).toBe(
            compact ? image.widthCompact : image.width,
          );
          expect(state.naturalHeight).toBe(
            compact ? image.heightCompact : image.height,
          );
        }
      }

      if (viewport.id === "1440" || viewport.id === "390") {
        await overview.screenshot({
          path: path.join(
            captureDirectory,
            `overview-${viewport.id}-${theme}.png`,
          ),
        });
        await page.screenshot({
          fullPage: true,
          path: path.join(
            captureDirectory,
            `full-${viewport.id}-${theme}.png`,
          ),
        });
      }
    });
  }
}