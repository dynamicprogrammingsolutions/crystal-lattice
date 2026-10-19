import fs from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

test.skip(
  process.env.CRYSTAL_WALKTHROUGH_FINAL_PREVIEW !== "1",
  "Requires the explicitly enabled final walkthrough preview.",
);

const directory = path.resolve("artifacts/walkthrough-final-review/page");
const chapters = [
  { id: "compose", label: "Compose", compactHeight: 1920 },
  { id: "messages", label: "Messages", compactHeight: 2490 },
  { id: "session-actions", label: "Session actions", compactHeight: 1920 },
  { id: "session-settings", label: "Session settings", compactHeight: 3280 },
  { id: "workspace", label: "Workspace", compactHeight: 1370 },
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

for (const width of [1440, 1024, 768, 390, 375, 320]) {
  for (const theme of ["light", "dark"]) {
    test(`final walkthrough ${width} ${theme}`, async ({ page }) => {
      fs.mkdirSync(directory, { recursive: true });
      await page.setViewportSize({ width, height: 1000 });
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
      if (width <= 760) {
        expect(currentSource).toContain("compose-compact");
      } else {
        expect(currentSource).toContain("compose-wide");
      }

      await walkthrough.scrollIntoViewIfNeeded();
      await walkthrough.screenshot({
        path: path.join(directory, `walkthrough-${width}-${theme}.png`),
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
        if (width <= 760) {
          expect(imageState.currentSrc).toContain(
            `${chapters[index].id}-compact`,
          );
          expect(imageState.naturalWidth).toBe(1000);
          expect(imageState.naturalHeight).toBe(chapters[index].compactHeight);
          expect(
            imageState.renderedHeight / imageState.renderedWidth,
          ).toBeCloseTo(chapters[index].compactHeight / 1000, 2);
        } else {
          expect(imageState.currentSrc).toContain(`${chapters[index].id}-wide`);
          expect(imageState.naturalWidth).toBe(1800);
          expect(imageState.naturalHeight).toBe(1013);
        }
        await walkthrough.screenshot({
          path: path.join(
            directory,
            `${chapters[index].id}-${width}-${theme}.png`,
          ),
        });
      }

      await page.screenshot({
        path: path.join(directory, `full-${width}-${theme}.png`),
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
  const next = walkthrough.getByRole("button", { name: /^Next:/ });
  const previous = walkthrough.getByRole("button", { name: /^Previous/ });

  await expect(next).toContainText("Messages");
  await next.click();
  await expect(tabs.nth(1)).toHaveAttribute("aria-selected", "true");
  await expect(previous).toContainText("Compose");

  await tabs.nth(1).focus();
  await page.keyboard.press("ArrowRight");
  await expect(tabs.nth(2)).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("End");
  await expect(tabs.nth(4)).toHaveAttribute("aria-selected", "true");

  await page.waitForTimeout(1200);
  await expect(tabs.nth(4)).toHaveAttribute("aria-selected", "true");

  await tabs.nth(2).click();
  const visual = panels.nth(2).locator("[data-walkthrough-visual]");
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
  await context.close();
});