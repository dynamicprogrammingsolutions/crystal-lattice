import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { defineAsset } from "./api.mjs";

const hash = file => createHash("sha256").update(fs.readFileSync(file)).digest("hex");
export const vibePreviewAsset = {
  src: "/__preview/vibe/portrait.webp",
  srcDark: "/__preview/vibe/portrait-dark.webp",
  width: 1200, height: 1600,
  alt: "A plugin-driven research agent shows a first System message, a user request with two file attachments, and its initial reasoning.",
};

async function compose(context) {
  const directory = path.join(context.landingRoot, "artifacts/visual-assets/homepage-vibe-workflow");
  const source = path.join(context.repositoryRoot, "mobile/crystal-lattice-control-rn/artifacts/website-visual");
  const fixtureFiles = [
    "mobile/crystal-lattice-control-rn/src/testing/MobileWebsiteVisualHarness.tsx",
    "mobile/crystal-lattice-control-rn/src/testing/fixtures/websiteVibeMessages.json",
    "mobile/crystal-lattice-control-rn/e2e/websiteVisualCapture.e2e.test.ts",
    "mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx",
  ];
  const sources = Object.fromEntries(fixtureFiles.map(file => [file, hash(path.join(context.repositoryRoot, file))]));
  fs.mkdirSync(directory, { recursive: true });
  const results = [];
  for (const theme of ["light", "dark"]) {
    const image = path.join(source, `vibe-${theme}.png`);
    const geometryFile = path.join(source, `vibe-${theme}-geometry.json`);
    const geometry = JSON.parse(fs.readFileSync(geometryFile, "utf8"));
    const header = geometry["messages-screen-header"].frame;
    const root = geometry["website-visual-harness-ready"].frame;
    const rows = ["message-bubble-0", "message-bubble-1", "assistant-reasoning-content-2"]
      .map(id => geometry[id].frame);
    assert.ok(rows.every(row => row.width > 0 && row.height > 0));
    assert.ok(rows[0].y < rows[1].y && rows[1].y < rows[2].y);
    const { stdout } = await context.run("magick", ["identify", "-format", "%w %h", image], { stdio: "pipe" });
    const [width, height] = stdout.trim().split(/\s+/).map(Number);
    const scale = width / root.width;
    const y = Math.max(0, Math.round((header.y - 8) * scale));
    const bottom = Math.round((Math.max(...rows.map(row => row.y + row.height)) + 10) * scale);
    assert.ok(bottom <= height);
    const crop = `${width}x${bottom - y}+0+${y}`;
    const file = `portrait${theme === "dark" ? "-dark" : ""}.webp`;
    const output = path.join(directory, file);
    await context.run("magick", [image, "-crop", crop, "+repage", "-resize", "1120x1520>",
      "-background", theme === "dark" ? "#0b0d10" : "#f3f4f7",
      "-gravity", "center", "-extent", "1200x1600", "-strip", "-quality", "88",
      "-define", "webp:method=6", output], { stdio: "pipe" });
    for (const sourceFile of [image, geometryFile]) sources[path.relative(context.repositoryRoot, sourceFile)] = hash(sourceFile);
    assert.ok(fs.statSync(output).size <= 240000);
    results.push({ variant: theme, file, crop, width: 1200, height: 1600, bytes: fs.statSync(output).size, sha256: hash(output) });
  }
  fs.writeFileSync(path.join(directory, "manifest.json"), JSON.stringify({ reviewState: "candidate", sourceHashes: sources, results }, null, 2));
  return results;
}

export const vibeComposition = defineAsset({
  id: "homepage-vibe-workflow",
  metadata: { reviewState: "candidate", claim: vibePreviewAsset.alt },
  commands: {
    inspect: context => context.input?.explicitAsset ? compose(context) : { skipped: true },
    check: context => {
      if (!context.input?.explicitAsset) return { skipped: true };
      const directory = path.join(context.landingRoot, "artifacts/visual-assets/homepage-vibe-workflow");
      const manifest = JSON.parse(fs.readFileSync(path.join(directory, "manifest.json"), "utf8"));
      for (const [file, expected] of Object.entries(manifest.sourceHashes)) {
        assert.equal(hash(path.join(context.repositoryRoot, file)), expected);
      }
      for (const result of manifest.results) assert.equal(hash(path.join(directory, result.file)), result.sha256);
      return manifest.results;
    },
  },
});