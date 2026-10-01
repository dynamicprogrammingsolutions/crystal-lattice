import fs from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const captureDirectory = path.resolve(
  "artifacts",
  "visual-assets",
  "playwright",
  "captures",
);
fs.mkdirSync(captureDirectory, { recursive: true });

const scenarios = [
  {
    name: "home-desktop",
    route: "/",
    viewport: { width: 1440, height: 1000 },
    sections: [
      ["hero", "#hero"],
      ["highlights", "#product-highlights"],
      ["getting-started", "#getting-started"],
      ["bridge", "#bridge"],
      ["provider-features", "#native-provider-features"],
      ["session-workbench", "#session-workbench"],
    ],
  },
  {
    name: "home-phone",
    route: "/",
    viewport: { width: 390, height: 844 },
    sections: [
      ["hero", "#hero"],
      ["highlights", "#product-highlights"],
      ["getting-started", "#getting-started"],
      ["bridge", "#bridge"],
      ["provider-features", "#native-provider-features"],
      ["session-workbench", "#session-workbench"],
    ],
  },
  {
    name: "mobile-page-desktop",
    route: "/mobile",
    viewport: { width: 1440, height: 1000 },
    sections: [
      ["hero", "main > section:first-of-type"],
      ["features", "#features"],
      ["connect", "#connect"],
    ],
  },
  {
    name: "mobile-page-phone",
    route: "/mobile",
    viewport: { width: 390, height: 844 },
    sections: [
      ["hero", "main > section:first-of-type"],
      ["features", "#features"],
      ["connect", "#connect"],
    ],
  },
];

async function loadLazyImages(page) {
  await page.locator('img[loading="lazy"]').evaluateAll((images) => {
    for (const image of images) {
      image.loading = "eager";
    }
  });
  await page.waitForFunction(() =>
    Array.from(document.images).every(
      (image) => image.complete && image.naturalWidth > 0,
    ),
  );
}

for (const scenario of scenarios) {
  for (const theme of ["light", "dark"]) {
    test(`${scenario.name}-${theme}`, async ({ page }) => {
      await page.setViewportSize(scenario.viewport);
      await page.addInitScript((selectedTheme) => {
        localStorage.setItem("cl-theme", selectedTheme);
      }, theme);
      await page.goto(scenario.route, { waitUntil: "networkidle" });

      await expect(page.locator("body")).toBeVisible();
      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);

      const themedSources = await page
        .locator("img[data-theme-light-src][data-theme-dark-src]")
        .evaluateAll((images) =>
          images.map((image) => image.getAttribute("src") ?? ""),
        );
      for (const source of themedSources) {
        if (theme === "dark") {
          expect(source).toContain("-dark.webp");
        } else {
          expect(source).toMatch(/\.webp$/);
          expect(source).not.toContain("-dark.webp");
        }
      }

      await loadLazyImages(page);

      const brokenImages = await page.locator("img").evaluateAll((images) =>
        images
          .filter((image) => !image.complete || image.naturalWidth === 0)
          .map((image) => image.getAttribute("src")),
      );
      expect(brokenImages).toEqual([]);

      const invalidProofImages = await page
        .locator("main img[data-theme-light-src]")
        .evaluateAll((images) =>
          images
            .filter(
              (image) =>
                !image.alt.trim() ||
                !image.hasAttribute("width") ||
                !image.hasAttribute("height"),
            )
            .map((image) => image.getAttribute("data-theme-light-src")),
        );
      expect(invalidProofImages).toEqual([]);

      await page.screenshot({
        path: path.join(
          captureDirectory,
          `${scenario.name}-${theme}-full.png`,
        ),
        fullPage: true,
      });

      for (const [label, selector] of scenario.sections) {
        const section = page.locator(selector);
        await expect(section).toBeVisible();
        await section.scrollIntoViewIfNeeded();
        await page.waitForTimeout(150);
        await section.screenshot({
          path: path.join(
            captureDirectory,
            `${scenario.name}-${theme}-${label}.png`,
          ),
        });
      }
    });
  }
}