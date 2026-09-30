import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { load } from "js-yaml";

const releasePath = new URL(
  "../src/content/releases/desktop.yaml",
  import.meta.url,
);
const navPath = new URL("../src/components/Nav.astro", import.meta.url);

const expectedFilename =
  "Crystal-Lattice-Desktop-v0.9.0-universal.dmg";
const expectedUrl =
  `https://download.crystallattice.dev/crystal-lattice-desktop/${expectedFilename}`;
const expectedChecksum =
  "8bbd119552de60eee53dd4d45fb8cd360faa1a7a788b780114e274ee46959bb5";
const accessibleName =
  "Download Crystal Lattice Desktop for macOS";

async function loadRelease() {
  return load(await readFile(releasePath, "utf8"));
}

test("desktop release metadata identifies the accepted public artifact", async () => {
  const release = await loadRelease();

  assert.equal(release.product, "Crystal Lattice Desktop");
  assert.equal(release.version, "0.9.0");
  assert.equal(release.buildNumber, 4);
  assert.equal(release.minimumMacos, "14.0");
  assert.deepEqual(release.architectures, ["arm64", "x86_64"]);
  assert.equal(release.dmg.filename, expectedFilename);
  assert.equal(release.dmg.url, expectedUrl);
  assert.match(release.dmg.url, /^https:\/\//);
  assert.ok(release.dmg.url.endsWith(`/${release.dmg.filename}`));
  assert.equal(release.dmg.sha256, expectedChecksum);
  assert.match(release.dmg.sha256, /^[0-9a-f]{64}$/);
});

test("shared header exposes an accessible ordinary download link", async () => {
  const nav = await readFile(navPath, "utf8");

  assert.match(nav, /const desktopRelease = loadDesktopRelease\(\)/);
  assert.match(nav, /href=\{desktopRelease\.dmg\.url\}/);
  assert.match(nav, new RegExp(`aria-label="${accessibleName}"`));
  assert.match(nav, /data-desktop-download/);
  assert.match(nav, /focus-visible:ring-2/);
  assert.doesNotMatch(nav, /navigator\.(?:platform|userAgent)/);
});