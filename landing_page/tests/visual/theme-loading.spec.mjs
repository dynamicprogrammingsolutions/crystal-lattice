import { expect, test } from "@playwright/test";

async function loadLazyImages(page) {
  const lazyImages = page.locator('img[loading="lazy"]');
  for (let index = 0; index < (await lazyImages.count()); index += 1) {
    await lazyImages.nth(index).scrollIntoViewIfNeeded();
  }
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
  await page.waitForLoadState("networkidle");
}

test("uses the approved desktop screenshot-card columns", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.addInitScript(() => {
    localStorage.setItem("cl-theme", "light");
  });
  await page.goto("/", { waitUntil: "networkidle" });

  const providerGrid = page.locator("#native-provider-features .grid").last();
  const workbenchGrid = page.locator("#session-workbench .grid").last();
  await expect(providerGrid).toBeVisible();
  await expect(workbenchGrid).toBeVisible();

  const providerColumns = await providerGrid.evaluate(
    (element) =>
      getComputedStyle(element).gridTemplateColumns.split(" ").length,
  );
  const workbenchColumns = await workbenchGrid.evaluate(
    (element) =>
      getComputedStyle(element).gridTemplateColumns.split(" ").length,
  );
  expect(providerColumns).toBe(2);
  expect(workbenchColumns).toBe(3);
});

test("loads only the active theme and swaps the same image elements", async ({
  page,
}) => {
  await page.addInitScript(() => {
    localStorage.setItem("cl-theme", "light");
  });

  const imageResponses = [];
  page.on("response", async (response) => {
    if (response.request().resourceType() !== "image") {
      return;
    }
    imageResponses.push({
      url: new URL(response.url()).pathname,
      contentLength: Number(
        (await response.headerValue("content-length")) ?? "0",
      ),
    });
  });

  await page.goto("/", { waitUntil: "networkidle" });
  expect(
    imageResponses.filter((response) => response.url.endsWith(".webp")),
  ).toEqual([]);

  await loadLazyImages(page);
  const lightImages = imageResponses.filter((response) =>
    response.url.endsWith(".webp"),
  );
  expect(lightImages).toHaveLength(5);
  expect(lightImages.every((response) => !response.url.includes("-dark.webp"))).toBe(
    true,
  );
  expect(
    lightImages.reduce((sum, response) => sum + response.contentLength, 0),
  ).toBe(221532);

  const themedImages = page.locator(
    "img[data-theme-light-src][data-theme-dark-src]",
  );
  expect(await themedImages.count()).toBe(5);

  await page.locator("#themeToggle").click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.waitForFunction(() =>
    Array.from(
      document.querySelectorAll(
        "img[data-theme-light-src][data-theme-dark-src]",
      ),
    ).every(
      (image) =>
        image.getAttribute("src")?.includes("-dark.webp") &&
        image.complete &&
        image.naturalWidth > 0,
    ),
  );
  await page.waitForLoadState("networkidle");

  const darkImages = imageResponses.filter((response) =>
    response.url.includes("-dark.webp"),
  );
  expect(darkImages).toHaveLength(5);
  expect(
    darkImages.reduce((sum, response) => sum + response.contentLength, 0),
  ).toBe(230356);
  expect(await themedImages.count()).toBe(5);
});

test("loads saved dark variants and preserves them across navigation", async ({
  page,
}) => {
  await page.addInitScript(() => {
    localStorage.setItem("cl-theme", "dark");
  });

  const imagePaths = [];
  page.on("response", (response) => {
    if (response.request().resourceType() === "image") {
      imagePaths.push(new URL(response.url()).pathname);
    }
  });

  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await loadLazyImages(page);

  const webpPaths = imagePaths.filter((path) => path.endsWith(".webp"));
  expect(webpPaths).toHaveLength(5);
  expect(webpPaths.every((path) => path.includes("-dark.webp"))).toBe(true);

  await page.locator('nav a[href="/mobile"]').click();
  await expect(page).toHaveURL(/\/mobile\/?$/);
  await page.locator('header a[href="/"]').click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

  const restoredSources = await page
    .locator("img[data-theme-light-src][data-theme-dark-src]")
    .evaluateAll((images) =>
      images.map((image) => image.getAttribute("src") ?? ""),
    );
  expect(restoredSources).toHaveLength(5);
  expect(
    restoredSources.every((source) => source.includes("-dark.webp")),
  ).toBe(true);
});