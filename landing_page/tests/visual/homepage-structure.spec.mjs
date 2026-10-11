import { expect, test } from "@playwright/test";

const desktopDownloadUrl =
  "https://download.crystallattice.dev/crystal-lattice-desktop/Crystal-Lattice-Desktop-v0.9.0-universal.dmg";

test("renders the approved homepage structure and disabled waitlist slot", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/", { waitUntil: "networkidle" });

  const primaryOrder = await page
    .locator("#hero, #product-highlights, #getting-started")
    .evaluateAll((sections) => sections.map((section) => section.id));
  expect(primaryOrder).toEqual([
    "hero",
    "product-highlights",
    "getting-started",
  ]);

  await expect(page.locator("#hero [data-installation-chooser]")).toHaveCount(
    0,
  );
  await expect(
    page.locator("#getting-started [data-installation-chooser]"),
  ).toHaveCount(1);
  await expect(
    page.locator("#product-highlights [data-feature-highlight]"),
  ).toHaveCount(6);
  await expect(
    page.locator("#product-highlights [data-proof-placeholder]"),
  ).toHaveCount(7);
  await expect(page.locator("#product-highlights [data-proof-media]")).toHaveCount(3);
  await expect(page.locator("#everything-replaceable")).toHaveCount(0);
  await expect(page.locator("nav a[data-section='feature-plugins']")).toHaveAttribute(
    "href", "/#feature-plugins",
  );
  await expect(
    page.locator("#getting-started [data-getting-started-step]"),
  ).toHaveCount(6);
  await expect(page.locator("#product-highlights")).not.toContainText(
    "Structural prototype",
  );
  await expect(page.locator("#getting-started")).not.toContainText(
    "Structural prototype",
  );

  const highlightsSection = page.locator("#product-highlights");
  await expect(highlightsSection).toHaveCSS("border-top-width", "0px");

  const firstHighlight = highlightsSection
    .locator("[data-feature-highlight]")
    .first();
  await expect(firstHighlight).toHaveCSS("border-top-width", "0px");
  const highlightTypeScale = await firstHighlight.evaluate((element) => {
    const title = element.querySelector("h3");
    const body = element.querySelector("p");
    return {
      title: Number.parseFloat(getComputedStyle(title).fontSize),
      body: Number.parseFloat(getComputedStyle(body).fontSize),
    };
  });
  expect(highlightTypeScale.title).toBeGreaterThan(
    highlightTypeScale.body * 1.4,
  );

  const stepKinds = await page
    .locator("#getting-started [data-getting-started-step]")
    .evaluateAll((steps) =>
      steps.map((step) => step.getAttribute("data-getting-started-step")),
    );
  expect(stepKinds).toEqual([
    "install",
    "command",
    "desktop-download",
    "desktop-connect",
    "mobile-download",
    "mobile-connect",
  ]);
  await expect(
    page.locator("#connect-desktop [data-connection-methods] article"),
  ).toHaveCount(1);
  await expect(page.locator("#connect-desktop")).toContainText(
    "The host defaults to 127.0.0.1",
  );
  await expect(page.locator("#connect-desktop code")).toHaveText("9000");

  await expect(
    page.locator('[data-desktop-platform="macos"]'),
  ).toHaveAttribute("href", desktopDownloadUrl);
  await expect(
    page.locator('[data-desktop-platform="macos"] svg'),
  ).toHaveCount(1);
  await expect(
    page.locator('#download-desktop [data-platform-logo="apple"]'),
  ).toHaveCount(1);
  await expect(
    page.locator('#download-desktop [data-platform-logo="windows"]'),
  ).toHaveCount(1);
  await expect(
    page.locator('#download-desktop [data-platform-logo="linux"]'),
  ).toHaveCount(1);
  await expect(page.locator("#download-desktop")).toContainText(
    "All platforms",
  );
  await expect(
    page.locator('[data-desktop-platform="windows"]'),
  ).toHaveAttribute("aria-disabled", "true");
  await expect(
    page.locator('[data-desktop-platform="linux"]'),
  ).toHaveAttribute("aria-disabled", "true");

  const waitlist = page.locator("[data-waitlist-slot]");
  await expect(waitlist).toBeVisible();
  await expect(waitlist).toHaveAttribute("aria-disabled", "true");
  await expect(waitlist.locator('input[type="email"]')).toHaveCount(0);
  await expect(waitlist.locator("form")).toHaveCount(0);
  await expect(page.locator("[data-mobile-platform] svg")).toHaveCount(2);
  await expect(
    page.locator('#get-mobile [data-platform-logo="apple"]'),
  ).toHaveCount(1);
  await expect(
    page.locator('#get-mobile [data-platform-logo="android"]'),
  ).toHaveCount(1);
});

test("uses a provisional responsive highlights baseline without overflow", async ({
  page,
}) => {
  for (const viewport of [
    { width: 1440, height: 1000, expectedColumns: 2 },
    { width: 1024, height: 900, expectedColumns: 2 },
    { width: 768, height: 900, expectedColumns: 2 },
    { width: 390, height: 844, expectedColumns: 1 },
    { width: 320, height: 700, expectedColumns: 1 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto("/", { waitUntil: "networkidle" });

    const grid = page.locator(
      "#product-highlights [data-feature-showcase-grid]",
    );
    const columns = await grid.evaluate(
      (element) =>
        getComputedStyle(element).gridTemplateColumns.split(" ").length,
    );
    expect(columns).toBe(viewport.expectedColumns);

    const pageWidth = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    expect(pageWidth.scrollWidth).toBeLessThanOrEqual(pageWidth.clientWidth + 1);
  }
});

test("keeps getting started keyboard reachable from the hero", async ({
  page,
}) => {
  await page.goto("/", { waitUntil: "networkidle" });

  const heroAction = page.locator("#hero").getByRole("link", {
    name: "Get started",
  });
  await heroAction.focus();
  await expect(heroAction).toBeFocused();
  await heroAction.press("Enter");

  await expect(page).toHaveURL(/#getting-started$/);
  await expect(page.locator("#getting-started")).toBeVisible();
  await expect(
    page.locator("#getting-started").getByRole("tab", {
      name: "macOS/Linux",
    }),
  ).toBeVisible();
});