import fs from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

test.skip(
  process.env.CRYSTAL_WALKTHROUGH_FINAL_PREVIEW !== "1",
  "Requires the explicitly enabled final walkthrough preview.",
);

const directory = path.resolve("artifacts/walkthrough-final-review/page");
const chapters = [
  { id: "compose", label: "Compose", compactHeight: 1500 },
  { id: "messages", label: "Messages", compactHeight: 1570 },
  { id: "session-actions", label: "Session actions", compactHeight: 1450 },
  { id: "session-settings", label: "Session settings", compactHeight: 1450 },
  { id: "workspace", label: "Workspace", compactHeight: 1370 },
];
const viewports = [
  { id: "1440", width: 1440, height: 1000 },
  { id: "1024", width: 1024, height: 1000 },
  { id: "768", width: 768, height: 1000 },
  { id: "390", width: 390, height: 844 },
  { id: "375", width: 375, height: 812 },
  { id: "375-short", width: 375, height: 667 },
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
    test(`final walkthrough ${viewport.id} ${theme}`, async ({ page }) => {
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
      const tabs = walkthrough.getByRole("tab");
      const panels = walkthrough.locator('[role="tabpanel"]');
      await expect(walkthrough).toBeVisible();
      await expect(tabs).toHaveCount(5);
      await expect(panels).toHaveCount(5);
      await expect(tabs.nth(0)).toHaveAttribute("aria-selected", "true");
      await expect(panels.nth(0)).toBeVisible();
      const panelCount = await panels.count();
      for (let index = 1; index < panelCount; index += 1) {
        await expect(panels.nth(index)).toBeHidden();
      }
      await expect(walkthrough).not.toContainText(/C0[1-9]|C1[0-4]/);
      await expect(walkthrough).not.toContainText(/candidate review/i);
      await expect(page.locator("#feature-model-families")).toHaveCount(0);
      await expect(page.locator("#session-workbench")).toHaveCount(0);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth + 1,
        ),
      ).toBe(true);

      const firstImage = panels.nth(0).locator("img");
      const currentSource = await firstImage.evaluate(image => image.currentSrc);
      if (viewport.width <= 760) {
        expect(currentSource).toContain("compose-compact");
      } else {
        expect(currentSource).toContain("compose-wide");
      }

      await walkthrough.scrollIntoViewIfNeeded();
      await walkthrough.screenshot({
        path: path.join(
          directory,
          `walkthrough-${viewport.id}-${theme}.png`,
        ),
      });

      for (let index = 0; index < chapters.length; index += 1) {
        await tabs.nth(index).click();
        await expect(tabs.nth(index)).toHaveAttribute("aria-selected", "true");
        await expect(panels.nth(index)).toBeVisible();
        const image = panels.nth(index).locator("img");
        const imageState = await image.evaluate(element => ({
          currentSrc: element.currentSrc,
          naturalWidth: element.naturalWidth,
          naturalHeight: element.naturalHeight,
          renderedWidth: element.getBoundingClientRect().width,
          renderedHeight: element.getBoundingClientRect().height,
        }));
        if (viewport.width <= 760) {
          expect(imageState.currentSrc).toContain(
            `${chapters[index].id}-compact`,
          );
          expect(imageState.naturalWidth).toBe(1000);
          expect(imageState.naturalHeight).toBe(chapters[index].compactHeight);
          expect(
            imageState.renderedHeight / imageState.renderedWidth,
          ).toBeCloseTo(chapters[index].compactHeight / 1000, 2);
          const imageStage = panels
            .nth(index)
            .locator("[data-walkthrough-image-stage]");
          await imageStage.evaluate(element => {
            const bounds = element.getBoundingClientRect();
            window.scrollTo({
              top:
                window.scrollY
                + bounds.top
                - (window.innerHeight - bounds.height) / 2,
              behavior: "instant",
            });
          });
          const stageBounds = await imageStage.boundingBox();
          const imageBounds = await image.boundingBox();
          expect(stageBounds).not.toBeNull();
          expect(imageBounds).not.toBeNull();
          expect(imageBounds.width).toBeGreaterThanOrEqual(
            stageBounds.width - 1,
          );
          expect(imageBounds.y).toBeGreaterThanOrEqual(0);
          expect(imageBounds.y + imageBounds.height).toBeLessThanOrEqual(
            viewport.height,
          );

          const previous = panels.nth(index).getByRole("button", {
            name: /^Previous chapter/,
          });
          const next = panels.nth(index).getByRole("button", {
            name: /^Next chapter/,
          });
          await expect(previous).toBeVisible();
          await expect(next).toBeVisible();
          const previousBounds = await previous.boundingBox();
          const nextBounds = await next.boundingBox();
          const imageCenter = imageBounds.y + imageBounds.height / 2;
          expect(
            Math.abs(
              previousBounds.y + previousBounds.height / 2 - imageCenter,
            ),
          ).toBeLessThanOrEqual(2);
          expect(
            Math.abs(nextBounds.y + nextBounds.height / 2 - imageCenter),
          ).toBeLessThanOrEqual(2);
        } else {
          expect(imageState.currentSrc).toContain(`${chapters[index].id}-wide`);
          expect(imageState.naturalWidth).toBe(1800);
          expect(imageState.naturalHeight).toBe(1013);
        }
        await walkthrough.screenshot({
          path: path.join(
            directory,
            `${chapters[index].id}-${viewport.id}-${theme}.png`,
          ),
        });
      }

      await page.screenshot({
        path: path.join(directory, `full-${viewport.id}-${theme}.png`),
        fullPage: true,
      });
    });
  }
}

test("walkthrough supports labeled controls, keyboard navigation, swipe, and no autoplay", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/", { waitUntil: "networkidle" });
  await loadImages(page);

  const walkthrough = page.locator("#product-walkthrough");
  const tabs = walkthrough.getByRole("tab");
  const panels = walkthrough.locator('[role="tabpanel"]');
  await expect(walkthrough.locator(".walkthrough-controls")).toHaveCount(0);
  const firstStage = panels.nth(0).locator("[data-walkthrough-image-stage]");
  await firstStage.evaluate(element => {
    const bounds = element.getBoundingClientRect();
    window.scrollTo({
      top:
        window.scrollY
        + bounds.top
        - (window.innerHeight - bounds.height) / 2,
      behavior: "instant",
    });
  });
  const firstStageBounds = await firstStage.boundingBox();
  const previousAtStart = panels.nth(0).getByRole("button", {
    name: "Previous chapter",
  });
  const next = panels.nth(0).getByRole("button", {
    name: "Next chapter: Messages",
  });
  await expect(previousAtStart).toBeDisabled();
  await next.click();
  await expect(tabs.nth(1)).toHaveAttribute("aria-selected", "true");
  const secondStage = panels.nth(1).locator("[data-walkthrough-image-stage]");
  await expect(secondStage).toBeVisible();
  await page.waitForTimeout(50);
  const secondStageBounds = await secondStage.boundingBox();
  expect(Math.abs(secondStageBounds.y - firstStageBounds.y)).toBeLessThanOrEqual(
    2,
  );
  await expect(
    panels.nth(1).getByRole("button", {
      name: "Previous chapter: Compose",
    }),
  ).toBeVisible();

  await tabs.nth(1).focus();
  await page.keyboard.press("ArrowRight");
  await expect(tabs.nth(2)).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("End");
  await expect(tabs.nth(4)).toHaveAttribute("aria-selected", "true");
  await expect(
    panels.nth(4).getByRole("button", { name: "Next chapter" }),
  ).toBeDisabled();

  await page.waitForTimeout(1200);
  await expect(tabs.nth(4)).toHaveAttribute("aria-selected", "true");

  await tabs.nth(2).click();
  const visual = panels.nth(2).locator("[data-walkthrough-image-stage]");
  await visual.evaluate(element => {
    const start = new Event("touchstart", { bubbles: true });
    Object.defineProperty(start, "changedTouches", {
      value: [{ clientX: 300, clientY: 220 }],
    });
    element.dispatchEvent(start);
    const end = new Event("touchend", { bubbles: true });
    Object.defineProperty(end, "changedTouches", {
      value: [{ clientX: 120, clientY: 225 }],
    });
    element.dispatchEvent(end);
  });
  await expect(tabs.nth(3)).toHaveAttribute("aria-selected", "true");
});

test("walkthrough content remains sequential without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("/");
  const walkthrough = page.locator("#product-walkthrough");
  await expect(walkthrough.getByRole("tabpanel")).toHaveCount(5);
  for (const chapter of chapters) {
    await expect(
      walkthrough.locator(`#walkthrough-panel-${chapter.id}`),
    ).toBeVisible();
  }
  for (const controls of await walkthrough
    .locator("[data-walkthrough-image-controls]")
    .all()) {
    await expect(controls).toBeHidden();
  }
  await context.close();
});