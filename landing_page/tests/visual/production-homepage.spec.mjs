import fs from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

test.skip(
  process.env.CRYSTAL_LATTICE_SITE_VARIANT !== "production",
  "production-only website contract",
);

const captureDirectory = path.resolve(
  "artifacts",
  "site-variants",
  "production",
  "captures",
);
fs.mkdirSync(captureDirectory, { recursive: true });

for (const scenario of [
  { name: "desktop", viewport: { width: 1440, height: 1000 } },
  { name: "phone", viewport: { width: 390, height: 844 } },
]) {
  for (const theme of ["light", "dark"]) {
    test(`production ${scenario.name} ${theme}`, async ({ page }) => {
      await page.setViewportSize(scenario.viewport);
      await page.addInitScript((selectedTheme) => {
        localStorage.setItem("cl-theme", selectedTheme);
      }, theme);
      await page.goto("/", { waitUntil: "networkidle" });

      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
      await expect(page.locator("[data-staging-banner]")).toHaveCount(0);
      await expect(page.locator('meta[name="robots"]')).toHaveCount(0);

      await expect(page.locator("#hero")).toBeVisible();
      await expect(page.locator("#getting-started")).toBeVisible();
      await expect(page.locator("#computer-to-phone")).toBeVisible();
      await expect(page.locator("#model-native-harnesses")).toBeVisible();
      await expect(page.locator("#native-provider-features")).toBeVisible();
      await expect(page.locator("#everything-replaceable")).toBeVisible();
      await expect(page.locator("#session-workbench")).toBeVisible();
      await expect(page.locator("#product-highlights")).toHaveCount(0);
      const hero = page.locator("#hero");
      await expect(
        hero.getByRole("link", { name: "Get started" }),
      ).toHaveAttribute("href", "#getting-started");
      await expect(
        hero.locator("[data-installation-chooser]"),
      ).toHaveCount(0);

      await expect(
        page.locator("#getting-started [data-getting-started-step]"),
      ).toHaveCount(6);
      await expect(
        page.locator("#getting-started [data-proof-placeholder]"),
      ).toHaveCount(0);
      await expect(page.getByText("Planned visual")).toHaveCount(0);
      await expect(page.locator("[data-installation-chooser]")).toHaveCount(1);
      await expect(
        page.locator('[data-desktop-platform="macos"]'),
      ).toHaveAttribute(
        "href",
        "https://download.crystallattice.dev/crystal-lattice-desktop/Crystal-Lattice-Desktop-v0.9.0-universal.dmg",
      );

      await page.locator('img[loading="lazy"]').evaluateAll((images) => {
        for (const image of images) image.loading = "eager";
      });
      await page.waitForFunction(() =>
        Array.from(document.images).every(
          (image) => image.complete && image.naturalWidth > 0,
        ),
      );
      const brokenImages = await page.locator("img").evaluateAll((images) =>
        images
          .filter((image) => !image.complete || image.naturalWidth === 0)
          .map((image) => image.getAttribute("src")),
      );
      expect(brokenImages).toEqual([]);

      const pageWidth = await page.evaluate(() => ({
        clientWidth: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
      }));
      expect(pageWidth.scrollWidth).toBeLessThanOrEqual(
        pageWidth.clientWidth + 1,
      );

      await page.screenshot({
        path: path.join(
          captureDirectory,
          `production-${scenario.name}-${theme}.png`,
        ),
        fullPage: true,
      });
    });
  }
}

test("production robots allow crawling", async ({ request }) => {
  const response = await request.get("/robots.txt");
  expect(response.ok()).toBe(true);
  expect(await response.text()).toBe("User-agent: *\nAllow: /\n");
});