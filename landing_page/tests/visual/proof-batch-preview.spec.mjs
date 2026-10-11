import fs from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";
import {
  proofBatchPreviewRecipes,
  readSessionActionsRecipe,
} from "../../scripts/visual-assets/session-actions-preview.mjs";

test.skip(process.env.CRYSTAL_PROOF_BATCH_PREVIEW !== "1",
  "Requires the explicitly enabled plugin/transparency homepage preview.");
const first = readSessionActionsRecipe();
const recipes = [
  { ...first, feature: "feature-plugins", slot: 0 },
  ...proofBatchPreviewRecipes,
];
const directory = path.resolve("artifacts/proof-batch-review/page");

const overlaps = (a, b) => a.x < b.x + b.width && a.x + a.width > b.x
  && a.y < b.y + b.height && a.y + a.height > b.y;

for (const width of [1440, 1024, 768, 390, 320]) {
  for (const theme of ["light", "dark"]) {
    test(`both proof sections ${width} ${theme}`, async ({ page }) => {
      fs.mkdirSync(directory, { recursive: true });
      await page.setViewportSize({ width, height: 1100 });
      await page.addInitScript(value => localStorage.setItem("cl-theme", value), theme);
      await page.goto("/", { waitUntil: "networkidle" });
      const shape = width > 760 ? "wide" : "compact";
      const suffix = theme === "dark" ? "-dark" : "";
      for (const featureId of ["feature-plugins", "feature-transparency"]) {
        const feature = page.locator(`#${featureId}`);
        const selectedRecipes = recipes.filter(item => item.feature === featureId);
        await expect(feature.locator("[data-image-card]")).toHaveCount(selectedRecipes.length);
        await expect(feature.locator("[data-proof-placeholder]")).toHaveCount(0);
        for (const recipe of selectedRecipes) {
          await feature.locator(`[data-image-index="${recipe.slot}"]`).click();
          await expect(feature.locator(`[data-image-index="${recipe.slot}"]`))
            .toHaveAttribute("aria-current", "true");
          const card = feature.locator("[data-image-card]").nth(recipe.slot);
          const image = card.locator("img");
          await card.scrollIntoViewIfNeeded();
          await expect.poll(() => image.evaluate(node => node.currentSrc))
            .toContain(`${recipe.previewPrefix}/${shape}${suffix}.webp`);
          await expect.poll(() => image.evaluate(node => node.complete && node.naturalWidth > 0)).toBe(true);
          const frame = await card.locator("[data-proof-frame]").boundingBox();
          expect(frame.width / frame.height).toBeCloseTo(width > 760 ? 16 / 9 : 3 / 4, 2);
          const manifest = JSON.parse(fs.readFileSync(`${recipe.candidateDirectory}/manifest.json`, "utf8"));
          const composition = manifest.results.find(item => item.variant === `${shape}-${theme}`);
          if (recipe.type === "report" && shape === "wide") {
            if (recipe.reportOnly) expect(composition.reportContext).toBeUndefined();
            else expect(composition.reportContext.source).toMatch(/-(conversation)\.png$/);
            expect(composition.excerpts.filter(excerpt => excerpt.kind === "report")).toHaveLength(1);
            const report = composition.excerpts.find(excerpt => excerpt.kind === "report");
            expect(report.source.height).toBe(recipe.wideReportHeight);
            expect(report.source.height).toBeLessThan(composition.nativeGeometry.report.height);
            if (recipe.metadataExcerpt) expect(composition.metadataCorrespondence).toBeDefined();
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
          for (const mapping of composition.correspondences ?? composition.endpoints ?? []) {
            for (const source of [mapping.configLabel, mapping.actionRow].filter(Boolean)) {
              const target = {
                x: origin.x + source.x * scale, y: origin.y + source.y * scale,
                width: source.width * scale, height: source.height * scale,
              };
              for (const arrow of arrows) {
                expect(overlaps(target, arrow), `${recipe.id}: ${mapping.package} obscured by navigation`).toBe(false);
              }
            }
          }
          if (shape === "compact" && recipe.type !== "report") {
            expect(composition.endpoints).toEqual([]);
            const rows = composition.correspondences;
            expect(Math.max(...rows.map(row => row.configLabel.y + row.configLabel.height)))
              .toBeLessThan(Math.min(...rows.map(row => row.actionRow.y)));
            if (recipe.scene === "message-actions") {
              expect(rows.filter(row => row.package === "message-export-actions").map(row => row.color))
                .toEqual(["#a879ed", "#a879ed"]);
              expect(composition.popupExcerpt.segments).toHaveLength(2);
            }
          }
          await expect(card.locator("figcaption")).toContainText(/plugin-driven/i);
          await expect(card.locator("figcaption")).toContainText(/easy to|easily/i);
          if (recipe.sampleData) await expect(card.locator("figcaption")).toContainText("Sample data");
          if (recipe.id === "homepage-usage-overview") {
            expect(manifest.actualReport.metrics).toMatchObject({
              estimated_total_usd: "220.00", percentage_point_change: 40, days_since_reset: 3,
            });
            await expect(card.locator("figcaption")).toContainText("$550");
          }
          expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
          // Keep the section heading clear of the sticky navigation in review
          // screenshots rather than letting element capture align it behind it.
          await feature.evaluate(element => {
            const header = document.querySelector("header").getBoundingClientRect();
            window.scrollTo(0, scrollY + element.getBoundingClientRect().top - header.height - 12);
          });
          await expect.poll(() => feature.evaluate(element =>
            element.getBoundingClientRect().top - document.querySelector("header").getBoundingClientRect().bottom))
            .toBeGreaterThanOrEqual(0);
          await feature.screenshot({
            path: path.join(directory, `${featureId.replace("feature-", "")}-${recipe.slot}-${width}-${theme}.png`),
          });
        }
        const lastSlot = selectedRecipes.at(-1).slot;
        await feature.getByRole("button", { name: "Previous image", exact: true }).click();
        await expect(feature.locator(`[data-image-index="${lastSlot - 1}"]`)).toHaveAttribute("aria-current", "true");
        await feature.getByRole("button", { name: "Next image", exact: true }).click();
        await expect(feature.locator(`[data-image-index="${lastSlot}"]`)).toHaveAttribute("aria-current", "true");
      }
      // The strips have independent state; theme changes update their current
      // genuine captures without reloading or moving the visitor's selection.
      await page.getByRole("button", { name: "Toggle theme", exact: true }).click();
      for (const featureId of ["feature-plugins", "feature-transparency"]) {
        const recipe = recipes.filter(item => item.feature === featureId).at(-1);
        const image = page.locator(`#${featureId} [data-image-card]`).nth(recipe.slot).locator("img");
        await expect.poll(() => image.evaluate(node => node.currentSrc))
          .toContain(`${recipe.previewPrefix}/${shape}${theme === "light" ? "-dark" : ""}.webp`);
      }
      await expect(page.locator("#feature-model-families")).toBeVisible();
      await expect(page.locator("#getting-started")).toBeVisible();
      await expect(page.locator("#everything-replaceable")).toHaveCount(0);
      await expect(page.locator("#feature-plugins")).not.toContainText("A session list that fits your work");
      await expect(page.locator("nav a[data-section='feature-plugins']")).toHaveAttribute("href", "/#feature-plugins");
    });
  }
}

test("both groups switch shape on resize and retain separate selections", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/");
  for (const [feature, slot] of [["feature-plugins", 1], ["feature-transparency", 1]]) {
    const dot = page.locator(`#${feature} [data-image-index="${slot}"]`);
    await dot.click();
    await expect(dot).toHaveAttribute("aria-current", "true");
  }
  for (const width of [390, 1024]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const [feature, slot] of [["feature-plugins", 1], ["feature-transparency", 1]]) {
      const recipe = recipes.find(item => item.feature === feature && item.slot === slot);
      const image = page.locator(`#${feature} [data-image-card]`).nth(slot).locator("img");
      await expect.poll(() => image.evaluate(node => node.currentSrc))
        .toMatch(new RegExp(`${recipe.previewPrefix}/${width > 760 ? "wide" : "compact"}(-dark)?\\.webp$`));
      await expect(page.locator(`#${feature} [data-image-index="${slot}"]`)).toHaveAttribute("aria-current", "true");
    }
  }
});