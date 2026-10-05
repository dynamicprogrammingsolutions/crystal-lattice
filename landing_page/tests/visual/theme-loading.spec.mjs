import { expect, test } from "@playwright/test";

function sortedUnique(values) {
  return [...new Set(values)].sort();
}

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
  await page.waitForLoadState("networkidle");
}

test("uses the approved desktop screenshot-card columns", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.addInitScript(() => {
    localStorage.setItem("cl-theme", "light");
  });
  await page.goto("/", { waitUntil: "networkidle" });

  const providerGrid = page.locator("#native-provider-features .grid").last();
  await expect(providerGrid).toBeVisible();

  const providerColumns = await providerGrid.evaluate(
    (element) =>
      getComputedStyle(element).gridTemplateColumns.split(" ").length,
  );
  expect(providerColumns).toBe(2);
  await expect(page.locator('#product-highlights [data-feature-layout="compact"]')).toHaveCount(4);
  await expect(page.locator('#product-highlights [data-feature-layout="full-width"]')).toHaveCount(2);
});

test("loads only the active theme and swaps the same image elements", async ({
  page,
}) => {
  await page.addInitScript(() => {
    localStorage.setItem("cl-theme", "light");
  });

  const imageResponses = [];
  const responseJobs = [];
  page.on("response", (response) => {
    if (response.request().resourceType() !== "image") {
      return;
    }
    responseJobs.push(response.headerValue("content-length").then((length) => {
      imageResponses.push({
        url: new URL(response.url()).pathname,
        contentLength: Number(length ?? "0"),
      });
    }));
  });

  await page.goto("/", { waitUntil: "networkidle" });
  await Promise.all(responseJobs);
  expect(
    imageResponses.filter((response) => response.url.includes("-dark.webp")),
  ).toEqual([]);

  await loadLazyImages(page);
  await Promise.all(responseJobs);
  const lightImages = imageResponses.filter((response) =>
    response.url.endsWith(".webp"),
  );
  expect(lightImages.length).toBeGreaterThan(0);
  expect(lightImages.every((response) => !response.url.includes("-dark.webp"))).toBe(
    true,
  );
  expect(
    lightImages.every((response) => response.contentLength > 0),
  ).toBe(true);

  const themedImages = page.locator(
    "img[data-theme-light-src][data-theme-dark-src]",
  );
  const lightSources = await themedImages.evaluateAll(
    (images) => images.map((image) => image.getAttribute("src")),
  );
  expect(sortedUnique(lightImages.map(({ url }) => url))).toEqual(sortedUnique(lightSources));

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
  await Promise.all(responseJobs);

  const darkImages = imageResponses.filter((response) =>
    response.url.includes("-dark.webp"),
  );
  expect(darkImages.length).toBeGreaterThan(0);
  expect(
    darkImages.every((response) => response.contentLength > 0),
  ).toBe(true);
  const darkSources = await themedImages.evaluateAll(
    (images) => images.map((image) => image.getAttribute("src")),
  );
  expect(sortedUnique(darkImages.map(({ url }) => url))).toEqual(sortedUnique(darkSources));
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
  expect(webpPaths.length).toBeGreaterThan(0);
  expect(webpPaths.every((path) => path.includes("-dark.webp"))).toBe(true);
  const initialSources = await page.locator("img[data-theme-light-src][data-theme-dark-src]")
    .evaluateAll((images) => images.map((image) => image.getAttribute("src")));
  expect(sortedUnique(webpPaths)).toEqual(sortedUnique(initialSources));

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
  expect(restoredSources.length).toBeGreaterThan(0);
  expect(
    restoredSources.every((source) => source.includes("-dark.webp")),
  ).toBe(true);
});

test("loads the active mobile hero theme inside the CSS phone frame", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.addInitScript(() => {
    localStorage.setItem("cl-theme", "light");
  });
  await page.goto("/mobile", { waitUntil: "networkidle" });

  const heroImage = page.locator("[data-phone-frame] img").first();
  const phoneFrame = page.locator("[data-phone-frame]").first();
  await expect(heroImage).toBeVisible();
  await expect(heroImage).toHaveAttribute(
    "src",
    "/mobile-active-session.webp",
  );
  await expect(heroImage).toHaveAttribute("loading", "eager");
  await expect(heroImage).toHaveAttribute("width", "1000");
  await expect(heroImage).toHaveAttribute("height", "2025");

  const frameStyle = await phoneFrame.evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      borderRadius: Number.parseFloat(style.borderRadius),
      borderWidth: Number.parseFloat(style.borderTopWidth),
      overflow: style.overflow,
    };
  });
  expect(frameStyle.borderRadius).toBeGreaterThan(30);
  expect(frameStyle.borderWidth).toBe(8);
  expect(frameStyle.overflow).toBe("hidden");

  await page.locator("#themeToggle").click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(heroImage).toHaveAttribute(
    "src",
    "/mobile-active-session-dark.webp",
  );
});