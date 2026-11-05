import { expect, test } from "@playwright/test";

test.skip(
  process.env.CRYSTAL_LATTICE_SITE_VARIANT !== "staging",
  "staging-only website contract",
);

test("staging is visibly identified and excluded from indexing", async ({
  page,
  request,
}) => {
  await page.goto("/", { waitUntil: "networkidle" });

  await expect(page.locator("[data-staging-banner]")).toContainText(
    "Staging preview",
  );
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
    "content",
    "noindex, nofollow, noarchive, nosnippet",
  );
  await expect(page.locator('meta[name="googlebot"]')).toHaveAttribute(
    "content",
    "noindex, nofollow, noarchive, nosnippet",
  );
  await expect(page.locator("script[data-website-id]")).toHaveCount(0);

  const robots = await request.get("/robots.txt");
  expect(robots.ok()).toBe(true);
  expect(await robots.text()).toBe("User-agent: *\nDisallow: /\n");
});