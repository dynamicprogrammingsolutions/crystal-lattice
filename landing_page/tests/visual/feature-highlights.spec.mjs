import fs from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

const captures = path.resolve("artifacts/homepage-image-cards");
fs.mkdirSync(captures, { recursive: true });

const scrollFraction = (element) => element.scrollLeft / element.clientWidth;

async function loadImages(page) {
  await page.locator('img[loading="lazy"]').evaluateAll((images) => {
    images.forEach((image) => { image.loading = "eager"; });
  });
  await page.waitForFunction(() => Array.from(document.images).every(
    (image) => image.complete && image.naturalWidth > 0,
  ));
}

for (const theme of ["light", "dark"]) {
  test(`option B uses aligned reference cards and responsive frames in ${theme}`, async ({ page }) => {
    await page.addInitScript((value) => localStorage.setItem("cl-theme", value), theme);
    for (const width of [1440, 1024, 768, 390, 320]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto("/", { waitUntil: "networkidle" });
      await loadImages(page);
      const highlights = page.locator("#product-highlights [data-feature-highlight]");
      await expect(highlights).toHaveCount(6);
      expect(await highlights.evaluateAll((items) => items.map((item) => item.id))).toEqual([
        "feature-model-families", "feature-work-anywhere", "feature-vibe-anything",
        "session-workbench", "feature-plugins", "feature-transparency",
      ]);
      await expect(page.locator("#transparency-details, #plugin-action-examples")).toHaveCount(0);
      await expect(page.locator("#product-highlights")).not.toContainText(
        /Scroll for more images|Inspect and restore session snapshots|illustrative fixture data/,
      );
      await expect(highlights.locator(".feature-proof > a")).toHaveCount(0);

      const appearance = (element) => {
        const style = getComputedStyle(element);
        return {
          background: style.backgroundColor, border: style.border,
          radius: style.borderRadius, padding: style.padding,
        };
      };
      const referenceCard = await page.locator("#native-provider-features article").first().evaluate(appearance);
      for (const item of await highlights.all()) {
        await expect(item).toHaveCSS("border-top-width", "0px");
        await expect(item).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
      }
      for (const card of await highlights.locator("[data-image-card]").all()) {
        expect(await card.evaluate(appearance)).toEqual(referenceCard);
      }
      const imageHeadings = await highlights.locator("[data-image-card]").evaluateAll((items) =>
        items.map((item) => {
          const caption = item.querySelector("figcaption").getBoundingClientRect();
          const image = item.querySelector("[data-proof-frame]").getBoundingClientRect();
          return { captionBottom: caption.bottom, imageTop: image.top };
        }),
      );
      imageHeadings.forEach(({ captionBottom, imageTop }) => {
        expect(imageTop).toBeGreaterThan(captionBottom);
      });
      await expect(page.locator("#feature-transparency .image-caption").nth(0))
        .toContainText("See the beginning of the Codex default.");
      const frames = await page.locator("[data-proof-frame]").evaluateAll((elements) => elements.map((element) => {
        const bounds = element.getBoundingClientRect();
        return {
          ratio: bounds.width / bounds.height,
          wide: element.closest("[data-feature-layout]")?.getAttribute("data-feature-layout") === "full-width",
        };
      }));
      for (const frame of frames) {
        expect(frame.ratio).toBeCloseTo(frame.wide && width > 760 ? 16 / 9 : 3 / 4, 2);
      }
      const boxes = await highlights.evaluateAll((items) => items.map((item) => {
        const card = item.getBoundingClientRect();
        const imageCard = item.querySelector("[data-image-card]").getBoundingClientRect();
        const frame = item.querySelector("[data-proof-frame]").getBoundingClientRect();
        const copy = item.querySelector(".feature-copy").getBoundingClientRect();
        return { width: card.width, top: frame.top, bottom: frame.bottom, gap: imageCard.top - copy.bottom };
      }));
      if (width > 760) {
        for (const index of [0, 2]) {
          expect(Math.abs(boxes[index].top - boxes[index + 1].top)).toBeLessThan(1);
          expect(Math.abs(boxes[index].bottom - boxes[index + 1].bottom)).toBeLessThan(1);
        }
        expect(boxes[4].width).toBeGreaterThan(boxes[0].width * 1.9);
        expect(boxes[5].width).toBe(boxes[4].width);
      } else {
        boxes.forEach((box) => expect(box.gap).toBeLessThanOrEqual(17));
      }
      const clipping = await page.locator(".proof-placeholder").evaluateAll((elements) =>
        elements.filter((element) => element.scrollHeight > element.clientHeight + 1)
          .map((element) => element.textContent.trim()),
      );
      expect(clipping, `placeholder clipping at ${width}px`).toEqual([]);
      const overflow = await page.evaluate(() =>
        document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      expect(overflow).toBeLessThanOrEqual(1);

      await page.locator("#product-highlights").evaluate((element) => {
        window.scrollTo(0, window.scrollY + element.getBoundingClientRect().top - 72);
      });
      await page.screenshot({ path: path.join(captures, `${width}-${theme}-viewport.png`) });
      await page.screenshot({ path: path.join(captures, `${width}-${theme}-full.png`), fullPage: true });
    }
  });
}

test("chevrons and dots follow native scrolling, resizing, and navigation", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  const plugins = page.locator("#feature-plugins feature-image-strip");
  const track = plugins.locator("[data-image-strip]");
  const dots = plugins.locator("[data-image-index]");
  const previous = plugins.getByRole("button", { name: "Previous image", exact: true });
  const next = plugins.getByRole("button", { name: "Next image", exact: true });
  await expect(previous).toBeDisabled();
  await expect(next).toBeEnabled();
  await expect(dots).toHaveCount(2);
  await expect(dots.nth(0)).toHaveAttribute("aria-current", "true");
  await next.click();
  await expect(dots.nth(1)).toHaveAttribute("aria-current", "true");
  await expect(next).toBeDisabled();
  await expect(page.locator("#feature-transparency [data-image-index]").first())
    .toHaveAttribute("aria-current", "true");

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(dots.nth(1)).toHaveAttribute("aria-current", "true");
  await expect.poll(() => track.evaluate(scrollFraction)).toBeGreaterThan(0.9);
  await track.focus();
  await track.press("ArrowLeft");
  await expect(dots.nth(0)).toHaveAttribute("aria-current", "true");
  await dots.nth(0).focus();
  await dots.nth(0).press("Enter");
  await expect(previous).toBeDisabled();
  await track.hover();
  await page.mouse.wheel(700, 0);
  await expect(dots.nth(1)).toHaveAttribute("aria-current", "true");

  const controlPositions = await plugins.evaluate((element) => {
    const selected = Number(element.querySelector('[data-image-index][aria-current="true"]').dataset.imageIndex);
    const card = element.querySelectorAll("[data-image-card]")[selected].getBoundingClientRect();
    const frame = element.querySelectorAll("[data-proof-frame]")[selected].getBoundingClientRect();
    const arrows = element.querySelector(".image-arrows").getBoundingClientRect();
    const dots = element.querySelector("[data-image-pagination]").getBoundingClientRect();
    return {
      centerError: Math.abs(arrows.top + arrows.height / 2 - (frame.top + frame.height / 2)),
      arrowsInsideCard: arrows.left >= card.left && arrows.right <= card.right,
      dotsBelowCard: dots.top >= card.bottom,
    };
  });
  expect(controlPositions.centerError).toBeLessThan(1);
  expect(controlPositions.arrowsInsideCard).toBe(true);
  expect(controlPositions.dotsBelowCard).toBe(true);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator('nav a[href="/mobile"]').click();
  await expect(page).toHaveURL(/\/mobile\/?$/);
  await page.locator('header a[href="/"]').click();
  await expect(previous).toBeDisabled();
  await next.click();
  await expect(dots.nth(1)).toHaveAttribute("aria-current", "true");
  await page.reload({ waitUntil: "networkidle" });
  await expect(previous).toBeDisabled();
});

test("pointer and keyboard can scroll each image strip independently", async ({ page }) => {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/", { waitUntil: "networkidle" });
    const agents = page.locator("#feature-model-families [data-image-strip]");
    const workspaces = page.locator("#session-workbench [data-image-strip]");
    await agents.focus();
    await agents.press("ArrowRight");
    await expect.poll(() => agents.evaluate(scrollFraction)).toBeGreaterThan(0.9);
    expect(await workspaces.evaluate(scrollFraction)).toBe(0);
    await agents.press("ArrowLeft");
    await expect.poll(() => agents.evaluate(scrollFraction)).toBeLessThan(0.1);
    await workspaces.hover();
    await page.mouse.wheel(1000, 0);
    await expect.poll(() => workspaces.evaluate(scrollFraction)).toBeGreaterThan(0.9);
    expect(await agents.evaluate(scrollFraction)).toBeLessThan(0.1);
  }
});

test("mobile touch swipe updates the active dot", async ({ browser, baseURL }) => {
  const context = await browser.newContext({
    baseURL, viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
  });
  try {
    const page = await context.newPage();
    await page.goto("/", { waitUntil: "networkidle" });
    const strip = page.locator("#feature-model-families [data-image-strip]");
    await strip.scrollIntoViewIfNeeded();
    const box = await strip.boundingBox();
    const x = box.x + box.width - 30;
    const y = box.y + 80;
    const input = await context.newCDPSession(page);
    await input.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x, y, id: 1 }] });
    for (let step = 1; step <= 10; step += 1) {
      await input.send("Input.dispatchTouchEvent", {
        type: "touchMove", touchPoints: [{ x: x - step * 18, y, id: 1 }],
      });
      await page.waitForTimeout(16);
    }
    await input.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    await expect.poll(() => strip.evaluate(scrollFraction)).toBeGreaterThan(0.9);
    await expect(page.locator("#feature-model-families [data-image-index]").nth(1))
      .toHaveAttribute("aria-current", "true");
  } finally {
    await context.close();
  }
});