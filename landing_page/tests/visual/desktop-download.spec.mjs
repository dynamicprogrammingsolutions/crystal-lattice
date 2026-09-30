import { expect, test } from "@playwright/test";

const downloadUrl =
  "https://download.crystallattice.dev/crystal-lattice-desktop/Crystal-Lattice-Desktop-v0.9.0-universal.dmg";
const accessibleName =
  "Download Crystal Lattice Desktop for macOS";

for (const viewport of [
  { name: "desktop", width: 1440, height: 1000 },
  { name: "phone", width: 390, height: 844 },
]) {
  test(`desktop download is visible and keyboard reachable on ${viewport.name}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await page.goto("/", { waitUntil: "networkidle" });

    const download = page.getByRole("link", { name: accessibleName });
    await expect(download).toBeVisible();
    await expect(download).toHaveAttribute("href", downloadUrl);

    const box = await download.boundingBox();
    expect(box).not.toBeNull();
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(viewport.width);

    for (let index = 0; index < 12; index += 1) {
      await page.keyboard.press("Tab");
      if (
        await page.evaluate(
          (name) => document.activeElement?.getAttribute("aria-label") === name,
          accessibleName,
        )
      ) {
        break;
      }
    }

    await expect(download).toBeFocused();
  });
}