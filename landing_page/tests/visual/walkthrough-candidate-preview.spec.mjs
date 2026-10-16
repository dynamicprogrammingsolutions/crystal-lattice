import fs from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

test.skip(
  process.env.CRYSTAL_WALKTHROUGH_CANDIDATE_PREVIEW !== "1",
  "Requires the explicitly enabled walkthrough candidate homepage.",
);

const directory = path.resolve("artifacts/walkthrough-candidate-review/page");

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

for (const width of [1440, 1024, 768, 390, 320]) {
  for (const theme of ["light", "dark"]) {
    test(`walkthrough candidates ${width} ${theme}`, async ({ page }) => {
      fs.mkdirSync(directory, { recursive: true });
      await page.setViewportSize({ width, height: 1000 });
      await page.addInitScript(
        value => localStorage.setItem("cl-theme", value),
        theme,
      );
      await page.goto("/", { waitUntil: "networkidle" });
      await loadImages(page);

      const walkthrough = page.locator("#product-walkthrough-candidates");
      await expect(walkthrough).toBeVisible();
      await expect(walkthrough.locator("[data-feature-highlight]")).toHaveCount(5);
      await expect(walkthrough.locator("[data-image-card]")).toHaveCount(10);
      await expect(walkthrough.locator("[data-proof-placeholder]")).toHaveCount(0);
      await expect(walkthrough).toContainText(
        "Familiar chat. More control at every level.",
      );
      await expect(walkthrough).toContainText("Steer the next request.");
      await expect(walkthrough).toContainText("Act from any message.");
      await expect(walkthrough).toContainText("Control the whole session.");
      await expect(walkthrough).toContainText("Configure this session.");
      await expect(walkthrough).toContainText("Keep many sessions moving.");

      await expect(page.locator("#feature-model-families")).toHaveCount(0);
      await expect(page.locator("#session-workbench")).toHaveCount(0);
      await expect(page.locator("#feature-work-anywhere [data-proof-placeholder]"))
        .toHaveCount(0);
      await expect(page.locator("#feature-transparency [data-image-card]"))
        .toHaveCount(3);
      await expect(page.locator("#feature-transparency [data-proof-placeholder]"))
        .toHaveCount(0);
      await expect(page.locator("#connect-mobile [data-proof-placeholder]"))
        .toHaveCount(0);
      await expect(page.locator("#connect-mobile [data-proof-media]"))
        .toHaveCount(1);

      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth + 1,
        ),
      ).toBe(true);

      await walkthrough.evaluate(element => {
        const header = document.querySelector("header").getBoundingClientRect();
        window.scrollTo(
          0,
          window.scrollY + element.getBoundingClientRect().top - header.height - 12,
        );
      });
      await page.screenshot({
        path: path.join(directory, `walkthrough-${width}-${theme}.png`),
      });
      await page.screenshot({
        path: path.join(directory, `full-${width}-${theme}.png`),
        fullPage: true,
      });

      for (const id of [
        "walkthrough-compose",
        "walkthrough-messages",
        "walkthrough-session-actions",
        "walkthrough-session-configuration",
        "walkthrough-workspace",
        "feature-work-anywhere",
        "feature-transparency",
        "connect-mobile",
      ]) {
        const section = page.locator(`#${id}`);
        await section.scrollIntoViewIfNeeded();
        await section.screenshot({
          path: path.join(directory, `${id}-${width}-${theme}.png`),
        });
      }
    });
  }
}

test("candidate strips remain independently navigable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/", { waitUntil: "networkidle" });
  const configuration = page.locator(
    "#walkthrough-session-configuration feature-image-strip",
  );
  const workspace = page.locator("#walkthrough-workspace feature-image-strip");
  const configurationDots = configuration.locator("[data-image-index]");
  const workspaceDots = workspace.locator("[data-image-index]");
  await expect(configurationDots).toHaveCount(3);
  await expect(workspaceDots).toHaveCount(3);

  await configuration.getByRole("button", { name: "Next image" }).click();
  await expect(configurationDots.nth(1)).toHaveAttribute("aria-current", "true");
  await expect(workspaceDots.nth(0)).toHaveAttribute("aria-current", "true");

  await workspaceDots.nth(2).click();
  await expect(workspaceDots.nth(2)).toHaveAttribute("aria-current", "true");
  await expect(configurationDots.nth(1)).toHaveAttribute("aria-current", "true");
});

const candidateStrips = [
  { id: "walkthrough-messages", count: 2 },
  { id: "walkthrough-session-configuration", count: 3 },
  { id: "walkthrough-workspace", count: 3 },
  { id: "feature-transparency", count: 3 },
];

for (const width of [1440, 390]) {
  for (const theme of ["light", "dark"]) {
    test(`every candidate slide ${width} ${theme}`, async ({ page }) => {
      fs.mkdirSync(directory, { recursive: true });
      await page.setViewportSize({ width, height: 1000 });
      await page.addInitScript(
        value => localStorage.setItem("cl-theme", value),
        theme,
      );
      await page.goto("/", { waitUntil: "networkidle" });
      await loadImages(page);

      for (const { id, count } of candidateStrips) {
        const section = page.locator(`#${id}`);
        const dots = section.locator("[data-image-index]");
        await expect(dots).toHaveCount(count);

        for (let index = 0; index < count; index += 1) {
          await dots.nth(index).click();
          await expect(dots.nth(index)).toHaveAttribute(
            "aria-current",
            "true",
          );
          await section.screenshot({
            path: path.join(
              directory,
              `candidate-${id}-${index}-${width}-${theme}.png`,
            ),
          });
        }
      }
    });
  }
}