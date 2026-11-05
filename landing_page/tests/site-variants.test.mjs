import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFile, readdir } from "node:fs/promises";
import test from "node:test";
import { load } from "js-yaml";

const productionHomeUrl = new URL(
  "../sites/production/content/pages/home.yaml",
  import.meta.url,
);
const stagingHomeUrl = new URL(
  "../sites/staging/content/pages/home.yaml",
  import.meta.url,
);
const productionGettingStartedUrl = new URL(
  "../sites/production/content/sections/getting-started.yaml",
  import.meta.url,
);

test("production homepage source exactly matches the approved historical baseline", async () => {
  const actual = await readFile(productionHomeUrl, "utf8");
  const expected = execFileSync(
    "git",
    [
      "show",
      "d3fe28a62ccdf82451e8273dc30245ca9075f0dd:landing_page/src/content/pages/home.yaml",
    ],
    {
      cwd: new URL("../..", import.meta.url),
      encoding: "utf8",
    },
  );
  assert.equal(actual, expected);
});

test("production Getting Started has six steps and no review or visual placeholders", async () => {
  const section = load(await readFile(productionGettingStartedUrl, "utf8"));
  assert.equal(section.type, "gettingStarted");
  assert.deepEqual(
    section.steps.map(({ id, kind }) => ({ id, kind })),
    [
      { id: "install-cli", kind: "install" },
      { id: "start-workspace", kind: "command" },
      { id: "download-desktop", kind: "desktop-download" },
      { id: "connect-desktop", kind: "desktop-connect" },
      { id: "get-mobile", kind: "mobile-download" },
      { id: "connect-mobile", kind: "mobile-connect" },
    ],
  );
  const serialized = JSON.stringify(section);
  assert.doesNotMatch(serialized, /reviewStatus|placeholder-needed|Planned visual/);
  for (const step of section.steps) {
    assert.equal(step.media, undefined);
  }
});

test("production records the approved hero-only duplicate cleanup", async () => {
  const adjustments = load(
    await readFile(
      new URL(
        "../sites/production/content/home-adjustments.yaml",
        import.meta.url,
      ),
      "utf8",
    ),
  );
  assert.deepEqual(adjustments, {
    hero: {
      removeInstall: true,
      primaryAction: {
        label: "Get started",
        href: "#getting-started",
      },
    },
  });
});

test("staging retains the in-progress homepage instead of the production baseline", async () => {
  const staging = load(await readFile(stagingHomeUrl, "utf8"));
  assert.ok(staging.sections.some(({ id }) => id === "product-highlights"));
  assert.ok(staging.sections.some(({ id }) => id === "getting-started"));
  assert.equal(
    staging.sections.some(({ id }) => id === "computer-to-phone"),
    false,
  );
});

test("draft homepage assets are owned by staging and unavailable to production public sources", async () => {
  const stagingAssets = await readdir(
    new URL("../sites/staging/public/homepage-draft/", import.meta.url),
  );
  assert.deepEqual(stagingAssets.sort(), [
    "agent-claude-dark.webp",
    "agent-claude-light.webp",
    "agent-codex-dark.webp",
    "agent-codex-light.webp",
    "vibe-dark.webp",
    "vibe-light.webp",
  ]);
  let sharedDraftAssets = [];
  try {
    sharedDraftAssets = await readdir(
      new URL("../public/homepage-draft/", import.meta.url),
    );
  } catch (error) {
    if (!error || typeof error !== "object" || error.code !== "ENOENT") {
      throw error;
    }
  }
  assert.deepEqual(sharedDraftAssets, []);
});