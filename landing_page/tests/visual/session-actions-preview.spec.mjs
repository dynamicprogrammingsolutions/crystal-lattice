import fs from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

const previewEnabled = process.env.CRYSTAL_SESSION_ACTIONS_PREVIEW === "1";
const directory = path.resolve("artifacts/plugin-session-actions-review");
test.skip(!previewEnabled, "Requires the explicitly enabled native-capture preview.");

for (const width of [1440, 1024, 768, 390, 320]) {
  for (const theme of ["light", "dark"]) {
    test(`session actions ${width} ${theme}`, async ({ page }) => {
      fs.mkdirSync(directory, { recursive: true });
      await page.setViewportSize({ width, height: 1100 });
      await page.addInitScript(value => localStorage.setItem("cl-theme", value), theme);
      await page.goto("/", { waitUntil: "networkidle" });
      const feature = page.locator("#feature-plugins");
      const card = feature.locator("[data-image-card]").first();
      const image = card.locator("img");
      await card.scrollIntoViewIfNeeded();
      await expect(image).toBeVisible();
      const shape = width > 760 ? "wide" : "compact";
      const suffix = theme === "dark" ? "-dark" : "";
      await expect.poll(() => image.evaluate(node => node.currentSrc))
        .toContain(`/__preview/session-actions/${shape}${suffix}.webp`);
      await expect.poll(() => image.evaluate(node => node.complete && node.naturalWidth > 0)).toBe(true);
      await expect(image).toHaveAttribute("alt", /Edit title.*Generate title.*Summarize range/);
      await expect(feature.locator("[data-image-card]")).toHaveCount(3);
      await expect(feature.locator("[data-proof-placeholder]")).toHaveCount(2);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      const frame = await card.locator("[data-proof-frame]").boundingBox();
      expect(frame.width / frame.height).toBeCloseTo(width > 760 ? 16 / 9 : 3 / 4, 2);
      const manifest = JSON.parse(fs.readFileSync("artifacts/visual-assets/homepage-session-actions/manifest.json", "utf8"));
      const composition = manifest.results.find(result => result.variant === `${shape}-${theme}`);
      const correspondences = composition.correspondences ?? composition.endpoints;
      if (shape === "compact") {
        expect(composition.presentation).toBe("stacked-highlights");
        expect(composition.endpoints).toEqual([]);
        expect(correspondences).toHaveLength(3);
        expect(composition.popupExcerpt.headerHeight).toBeGreaterThan(0);
        expect(composition.popupExcerpt.omitted.height).toBeGreaterThan(0);
        expect(Math.max(...correspondences.map(row => row.configLabel.y + row.configLabel.height)))
          .toBeLessThan(Math.min(...correspondences.map(row => row.actionRow.y)));
      }
      const imageBounds = await image.boundingBox();
      const scale = Math.min(imageBounds.width / composition.width, imageBounds.height / composition.height);
      const origin = {
        x: imageBounds.x + (imageBounds.width - composition.width * scale) / 2,
        y: imageBounds.y + (imageBounds.height - composition.height * scale) / 2,
      };
      const arrows = await feature.locator("[data-image-step]").evaluateAll(elements =>
        elements.map(element => {
          const rect = element.getBoundingClientRect();
          return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
        }));
      for (const endpoint of correspondences) {
        const source = endpoint.configLabel;
        const label = {
          x: origin.x + source.x * scale, y: origin.y + source.y * scale,
          width: source.width * scale, height: source.height * scale,
        };
        for (const arrow of arrows) {
          const overlaps = label.x < arrow.x + arrow.width && label.x + label.width > arrow.x
            && label.y < arrow.y + arrow.height && label.y + label.height > arrow.y;
          expect(overlaps, `${endpoint.package} must remain clear of image navigation`).toBe(false);
        }
        if (endpoint.actionRow) {
          const source = endpoint.actionRow;
          const row = {
            x: origin.x + source.x * scale, y: origin.y + source.y * scale,
            width: source.width * scale, height: source.height * scale,
          };
          for (const arrow of arrows) {
            const overlaps = row.x < arrow.x + arrow.width && row.x + row.width > arrow.x
              && row.y < arrow.y + arrow.height && row.y + row.height > arrow.y;
            expect(overlaps, `${endpoint.package} action must remain clear of image navigation`).toBe(false);
          }
        }
      }
      await feature.screenshot({ path: path.join(directory, `${width}-${theme}.png`) });
      if ((width === 1440 || width === 390) && theme === "light") {
        await feature.screenshot({ path: path.join(directory, width === 1440 ? "desktop.png" : "mobile.png") });
      }
      await page.getByRole("button", { name: "Toggle theme", exact: true }).click();
      const nextSuffix = theme === "light" ? "-dark" : "";
      await expect.poll(() => image.evaluate(node => node.currentSrc))
        .toContain(`/${shape}${nextSuffix}.webp`);
      await expect.poll(() => image.evaluate(node => node.complete && node.naturalWidth > 0)).toBe(true);
      await feature.getByRole("button", { name: "Next image", exact: true }).click();
      await expect(feature.locator("[data-image-index='1']")).toHaveAttribute("aria-current", "true");
      await feature.getByRole("button", { name: "Previous image", exact: true }).click();
      await expect(feature.locator("[data-image-index='0']")).toHaveAttribute("aria-current", "true");
    });
  }
}

test("responsive sources follow viewport changes without reloading", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  const image = page.locator("#feature-plugins [data-image-card]").first().locator("img");
  await image.scrollIntoViewIfNeeded();
  await expect.poll(() => image.evaluate(node => node.currentSrc)).toMatch(/wide(-dark)?\.webp$/);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => image.evaluate(node => node.currentSrc)).toMatch(/compact(-dark)?\.webp$/);
  await page.setViewportSize({ width: 1024, height: 1000 });
  await expect.poll(() => image.evaluate(node => node.currentSrc)).toMatch(/wide(-dark)?\.webp$/);
});