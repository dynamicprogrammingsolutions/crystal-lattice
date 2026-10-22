import fs from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

import {
  walkthroughFinalChapters,
} from "../../scripts/visual-assets/walkthrough-final-preview.mjs";

test.skip(
  process.env.CRYSTAL_WALKTHROUGH_FINAL_PREVIEW !== "1",
  "Requires the explicitly enabled final walkthrough preview.",
);

const directory = path.resolve("artifacts/walkthrough-final-review/page");
const frames = walkthroughFinalChapters.flatMap((chapter, chapterIndex) =>
  chapter.frames.map((frame, frameIndex) => ({
    ...frame,
    chapterId: chapter.id,
    chapterLabel: chapter.label,
    chapterIndex,
    frameIndex,
  })),
);
const viewports = [
  { id: "1440", width: 1440, height: 1000 },
  { id: "1024", width: 1024, height: 1000 },
  { id: "768", width: 768, height: 1000 },
  { id: "390", width: 390, height: 844 },
  { id: "320-short", width: 320, height: 568 },
];

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

for (const viewport of viewports) {
  for (const theme of ["light", "dark"]) {
    test(`responsive walkthrough ${viewport.id} ${theme}`, async ({ page }) => {
      fs.mkdirSync(directory, { recursive: true });
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

      const walkthrough = page.locator("#product-walkthrough");
      const panels = walkthrough.locator("[data-walkthrough-panel]");
      const frameLocators = walkthrough.locator("[data-walkthrough-frame]");
      const wide = viewport.width >= 900;

      await expect(walkthrough).toBeVisible();
      await expect(panels).toHaveCount(6);
      await expect(frameLocators).toHaveCount(13);
      await expect(walkthrough).not.toContainText(/C0[1-9]|C1[0-4]/);
      await expect(walkthrough).not.toContainText(
        /candidate review|fixture|what it proves|source responsibility/i,
      );
      await expect(page.locator("#feature-model-families")).toHaveCount(0);
      await expect(page.locator("#session-workbench")).toHaveCount(0);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth + 1,
        ),
      ).toBe(true);

      if (wide) {
        const tabs = walkthrough.getByRole("tab");
        const tabpanels = walkthrough.locator('[role="tabpanel"]');
        await expect(tabs).toHaveCount(6);
        await expect(tabpanels).toHaveCount(6);
        await expect(tabs.nth(0)).toHaveAttribute("aria-selected", "true");
        await expect(frameLocators.nth(0)).toBeVisible();
        for (let index = 1; index < frames.length; index += 1) {
          await expect(frameLocators.nth(index)).toBeHidden();
        }

        for (const chapter of walkthroughFinalChapters) {
          await walkthrough.getByRole("tab", { name: chapter.label }).click();
          for (const [frameIndex, frame] of chapter.frames.entries()) {
            if (frameIndex > 0) {
              await walkthrough
                .getByRole("button", { name: `Show ${frame.title}` })
                .click();
            }
            const figure = walkthrough.locator(`#walkthrough-frame-${frame.id}`);
            const image = figure.locator("img");
            await expect(figure).toBeVisible();
            await expect(figure).toContainText(frame.caption);
            const imageState = await image.evaluate(element => ({
              currentSrc: element.currentSrc,
              naturalWidth: element.naturalWidth,
              naturalHeight: element.naturalHeight,
            }));
            expect(imageState.currentSrc).toContain(`${frame.id}-wide`);
            expect(imageState.naturalWidth).toBe(1600);
            expect(imageState.naturalHeight).toBe(1000);

            if (viewport.id === "1440") {
              await figure.screenshot({
                path: path.join(
                  directory,
                  `${frame.id}-${viewport.id}-${theme}.png`,
                ),
              });
            }
          }
        }
      } else {
        await expect(walkthrough.getByRole("tab")).toHaveCount(0);
        await expect(walkthrough.getByRole("tabpanel")).toHaveCount(0);
        await expect(walkthrough.locator("[data-walkthrough-tabs]")).toBeHidden();

        for (const panel of await panels.all()) {
          await expect(panel).toBeVisible();
        }
        for (const [index, frame] of frames.entries()) {
          const figure = frameLocators.nth(index);
          const image = figure.locator("img");
          await expect(figure).toBeVisible();
          await expect(
            figure.locator("[data-walkthrough-image-controls]"),
          ).toBeHidden();
          await expect(
            figure.locator("[data-walkthrough-frame-progress]"),
          ).toBeHidden();
          const imageState = await image.evaluate(element => ({
            currentSrc: element.currentSrc,
            naturalWidth: element.naturalWidth,
            naturalHeight: element.naturalHeight,
          }));
          expect(imageState.currentSrc).toContain(`${frame.id}-compact`);
          expect(imageState.naturalWidth).toBe(frame.image.widthCompact);
          expect(imageState.naturalHeight).toBe(frame.image.heightCompact);

          if (viewport.id === "390") {
            await figure.screenshot({
              path: path.join(
                directory,
                `${frame.id}-${viewport.id}-${theme}.png`,
              ),
            });
          }
        }

        expect(
          await walkthrough
            .locator(".walkthrough-frame-title")
            .allTextContents(),
        ).toEqual(frames.map(frame => frame.title));
      }

      await walkthrough.screenshot({
        path: path.join(
          directory,
          `walkthrough-${viewport.id}-${theme}.png`,
        ),
      });
    });
  }
}

test("desktop navigation advances frames and chapters without autoplay", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/", { waitUntil: "networkidle" });
  await loadImages(page);

  const walkthrough = page.locator("#product-walkthrough");
  const tabs = walkthrough.getByRole("tab");
  const firstFrame = walkthrough.locator("#walkthrough-frame-compose-controls");
  const secondFrame = walkthrough.locator("#walkthrough-frame-compose-running");

  await expect(firstFrame).toBeVisible();
  await expect(
    firstFrame.getByRole("button", { name: "Previous image" }),
  ).toBeDisabled();
  await firstFrame
    .getByRole("button", { name: "Next: Control work that is already running" })
    .click();
  await expect(secondFrame).toBeVisible();
  await expect(tabs.nth(0)).toHaveAttribute("aria-selected", "true");

  await secondFrame
    .getByRole("button", { name: "Next: Inspect the response in context" })
    .click();
  await expect(
    walkthrough.locator("#walkthrough-frame-message-metadata"),
  ).toBeVisible();
  await expect(tabs.nth(1)).toHaveAttribute("aria-selected", "true");

  await walkthrough.getByRole("tab", { name: "Session settings" }).click();
  await expect(
    walkthrough.locator("#walkthrough-frame-agent-profile"),
  ).toBeVisible();
  await walkthrough
    .getByRole("button", { name: "Show Change plugins for this session" })
    .click();
  await expect(
    walkthrough.locator("#walkthrough-frame-session-plugins"),
  ).toBeVisible();

  await walkthrough.getByRole("tab", { name: "Session settings" }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(tabs.nth(4)).toHaveAttribute("aria-selected", "true");
  await expect(
    walkthrough.locator("#walkthrough-frame-workspace-sessions"),
  ).toBeVisible();
  await page.keyboard.press("End");
  await expect(tabs.nth(5)).toHaveAttribute("aria-selected", "true");

  await walkthrough
    .getByRole("button", { name: "Show Reach a workspace from mobile" })
    .click();
  const lastFrame = walkthrough.locator("#walkthrough-frame-mobile-connection");
  await expect(lastFrame).toBeVisible();
  await expect(
    lastFrame.getByRole("button", { name: "Next image" }),
  ).toBeDisabled();

  await page.waitForTimeout(1200);
  await expect(lastFrame).toBeVisible();
});

test("resizing to mobile reveals the complete reading order", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/", { waitUntil: "networkidle" });
  await loadImages(page);

  const walkthrough = page.locator("#product-walkthrough");
  await walkthrough.getByRole("tab", { name: "Session settings" }).click();
  await walkthrough
    .getByRole("button", { name: "Show Adjust provider-specific settings" })
    .click();
  await expect(
    walkthrough.locator("#walkthrough-frame-provider-settings"),
  ).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(walkthrough.getByRole("tab")).toHaveCount(0);
  await expect(walkthrough.getByRole("tabpanel")).toHaveCount(0);
  for (const frame of await walkthrough.locator("[data-walkthrough-frame]").all()) {
    await expect(frame).toBeVisible();
  }
  for (const controls of await walkthrough
    .locator("[data-walkthrough-image-controls], [data-walkthrough-frame-progress]")
    .all()) {
    await expect(controls).toBeHidden();
  }
});

test("walkthrough remains a complete vertical document without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: { width: 1440, height: 1000 },
  });
  const page = await context.newPage();
  await page.goto("/");

  const walkthrough = page.locator("#product-walkthrough");
  await expect(walkthrough.getByRole("tab")).toHaveCount(0);
  await expect(walkthrough.getByRole("tabpanel")).toHaveCount(0);
  await expect(walkthrough.locator("[data-walkthrough-panel]")).toHaveCount(6);
  await expect(walkthrough.locator("[data-walkthrough-frame]")).toHaveCount(13);
  for (const panel of await walkthrough.locator("[data-walkthrough-panel]").all()) {
    await expect(panel).toBeVisible();
  }
  for (const frame of await walkthrough.locator("[data-walkthrough-frame]").all()) {
    await expect(frame).toBeVisible();
  }
  for (const controls of await walkthrough
    .locator("[data-walkthrough-tabs], [data-walkthrough-image-controls], [data-walkthrough-frame-progress]")
    .all()) {
    await expect(controls).toBeHidden();
  }

  await context.close();
});