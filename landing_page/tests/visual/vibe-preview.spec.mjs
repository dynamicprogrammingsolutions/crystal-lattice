import fs from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

test.skip(process.env.CRYSTAL_PROOF_BATCH_PREVIEW !== "1", "Requires the explicit candidate homepage.");
for (const width of [1440, 390]) for (const theme of ["light", "dark"]) {
  test(`Vibe System/User/reasoning ${width} ${theme}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1100 });
    await page.addInitScript(value => localStorage.setItem("cl-theme", value), theme);
    await page.goto("/", { waitUntil: "networkidle" });
    const section = page.locator("#feature-vibe-anything");
    const image = section.locator("img");
    await section.scrollIntoViewIfNeeded();
    await expect.poll(() => image.evaluate(node => node.currentSrc))
      .toContain(`/__preview/vibe/portrait${theme === "dark" ? "-dark" : ""}.webp`);
    await expect.poll(() => image.evaluate(node => node.complete && node.naturalWidth > 0)).toBe(true);
    await expect(section.locator("figcaption")).toContainText(/plugin-driven/i);
    await expect(section.locator("figcaption")).toContainText(/easily/i);
    await expect(page.locator("#feature-transparency [data-image-card]")).toHaveCount(2);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const directory = path.resolve("artifacts/illustrative-review");
    fs.mkdirSync(directory, { recursive: true });
    await section.evaluate(element => {
      const header = document.querySelector("header").getBoundingClientRect();
      window.scrollTo(0, scrollY + element.getBoundingClientRect().top - header.height - 12);
    });
    await expect.poll(() => section.evaluate(element =>
      element.getBoundingClientRect().top - document.querySelector("header").getBoundingClientRect().bottom))
      .toBeGreaterThanOrEqual(0);
    await section.screenshot({ path: path.join(directory, `vibe-${width}-${theme}.png`) });
  });
}