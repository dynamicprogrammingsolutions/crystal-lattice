import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  capturedSource,
  captureOutput,
  defineAsset,
  defineVisualAssets,
} from "../../scripts/visual-assets/api.mjs";
import {
  captureImageSources,
  prepareImageSourcePromotion,
} from "../../scripts/visual-assets/lifecycle/image.mjs";
import { detoxCapture } from "../../scripts/visual-assets/producers/detox.mjs";
import { executeVisualAssets } from "../../scripts/visual-assets/runner.mjs";
import { sha256 } from "../../scripts/visual-assets/validation.mjs";

test("capture and source promotion are separate catalog workflows", async () => {
  const repositoryRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), "visual-assets-capture-"),
  );
  const landingRoot = path.join(repositoryRoot, "landing_page");
  fs.mkdirSync(landingRoot, { recursive: true });

  const candidateRelative = "landing_page/artifacts/captures/mobile-hero.png";
  const candidateAbsolute = path.join(repositoryRoot, candidateRelative);
  const reviewedRelative = "visual_assets/sources/mobile-hero.png";
  const reviewedAbsolute = path.join(landingRoot, reviewedRelative);

  const source = capturedSource({
    reviewed: reviewedRelative,
    candidate: captureOutput({
      candidatePath: candidateRelative,
      async capture() {
        fs.mkdirSync(path.dirname(candidateAbsolute), { recursive: true });
        fs.writeFileSync(candidateAbsolute, "captured");
        return candidateAbsolute;
      },
    }),
  });
  const catalog = defineVisualAssets({
    commands: {
      async capture(context) {
        const results = await context.forEachSelected(
          (assetContext) =>
            assetContext.runLifecycle("capture"),
          { requireSelection: true },
        );
        return context.writeReport("capture", { results });
      },

      async "promote-source"(context) {
        const prepared = await context.forEachSelected(
          (assetContext) =>
            assetContext.runLifecycle(
              "prepareSourcePromotion",
            ),
          { requireSelection: true },
        );
        const results = prepared.map((effect) => effect.report);
        await context.applyAll(prepared);
        return context.writeReport("promote-source", {
          results,
        });
      },
    },

    assets: [
      defineAsset({
        id: "mobile-hero",
        config: {
          variants: {
            default: {
              source,
            },
          },
        },
        lifecycle: {
          capture: captureImageSources,
          prepareSourcePromotion:
            prepareImageSourcePromotion,
        },
      }),
    ],
  });

  await executeVisualAssets({
    catalog,
    command: "capture",
    args: ["mobile-hero"],
    repositoryRoot,
    landingRoot,
  });

  assert.equal(fs.readFileSync(candidateAbsolute, "utf8"), "captured");
  assert.equal(fs.existsSync(reviewedAbsolute), false);

  await executeVisualAssets({
    catalog,
    command: "promote-source",
    args: ["mobile-hero"],
    repositoryRoot,
    landingRoot,
  });

  assert.equal(fs.readFileSync(reviewedAbsolute, "utf8"), "captured");
  fs.rmSync(repositoryRoot, { recursive: true, force: true });
});

test("one Detox producer run can serve multiple named outputs", async () => {
  const repositoryRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), "visual-assets-detox-"),
  );
  const outputOne = "mobile/artifacts/visual/one.png";
  const outputTwo = "mobile/artifacts/visual/two.png";
  let runCount = 0;

  const producer = detoxCapture({
    id: "mobile-showcase",
    projectDirectory: "mobile",
    command: ["yarn", "detox", "test"],
    outputs: {
      one: outputOne,
      two: outputTwo,
    },
  });
  const context = {
    repositoryRoot,
    async run() {
      runCount += 1;
      for (const relativePath of [outputOne, outputTwo]) {
        const absolutePath = path.join(repositoryRoot, relativePath);
        fs.mkdirSync(path.dirname(absolutePath), { recursive: true });
        fs.writeFileSync(absolutePath, relativePath);
      }
    },
  };

  const [first, second] = await Promise.all([
    producer.output("one").capture(context),
    producer.output("two").capture(context),
  ]);

  assert.equal(runCount, 1);
  assert.equal(first, path.join(repositoryRoot, outputOne));
  assert.equal(second, path.join(repositoryRoot, outputTwo));
  fs.rmSync(repositoryRoot, { recursive: true, force: true });
});

test("catalog preparation failure prevents every durable apply callback", async () => {
  const repositoryRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), "visual-assets-update-"),
  );
  const landingRoot = path.join(repositoryRoot, "landing_page");
  const publicOne = path.join(landingRoot, "public/one.txt");
  fs.mkdirSync(path.dirname(publicOne), { recursive: true });
  fs.writeFileSync(publicOne, "unchanged");
  const before = sha256(publicOne);

  const catalog = defineVisualAssets({
    commands: {
      async update(context) {
        const prepared = await context.forEachSelected(
          (assetContext) =>
            assetContext.runCommand("update"),
          { requireSelection: true },
        );
        await context.applyAll(prepared);
        return { results: [] };
      },
    },

    assets: [
      defineAsset({
        id: "one",
        config: { publicOne },
        commands: {
          update: ({ config }) => ({
            report: { asset_id: "one" },
            async apply() {
              fs.writeFileSync(config.publicOne, "changed");
            },
          }),
        },
      }),
      defineAsset({
        id: "two",
        config: {},
        commands: {
          update() {
            throw new Error("second preparation failed");
          },
        },
      }),
    ],
  });

  await assert.rejects(
    executeVisualAssets({
      catalog,
      command: "update",
      args: ["--all"],
      repositoryRoot,
      landingRoot,
    }),
    /second preparation failed/,
  );

  assert.equal(sha256(publicOne), before);
  fs.rmSync(repositoryRoot, { recursive: true, force: true });
});

test("one catalog command can choose direct commands or lifecycle composition per asset", async () => {
  const repositoryRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), "visual-assets-resolution-"),
  );
  const landingRoot = path.join(repositoryRoot, "landing_page");
  fs.mkdirSync(landingRoot, { recursive: true });

  const catalog = defineVisualAssets({
    commands: {
      async check(context) {
        const results = await context.forEachSelected(
          async (assetContext) => {
            if (assetContext.hasCommand("check")) {
              return assetContext.runCommand("check");
            }
            return assetContext.runLifecycle("validate");
          },
          { defaultAll: true },
        );
        return context.writeReport("check", { results });
      },
    },

    assets: [
      defineAsset({
        id: "mixed",
        config: { value: "direct" },
        commands: {
          check: ({ config }) => ({
            asset_id: "mixed",
            result: config.value,
          }),
        },
        lifecycle: {
          validate: () => ({
            asset_id: "mixed",
            result: "lifecycle-should-not-run",
          }),
        },
      }),
      defineAsset({
        id: "lifecycle-only",
        config: { value: "lifecycle" },
        lifecycle: {
          validate: ({ config }) => ({
            asset_id: "lifecycle-only",
            result: config.value,
          }),
        },
      }),
    ],
  });

  const report = await executeVisualAssets({
    catalog,
    command: "check",
    args: [],
    repositoryRoot,
    landingRoot,
  });

  assert.deepEqual(report.results, [
    {
      asset_id: "mixed",
      result: "direct",
    },
    {
      asset_id: "lifecycle-only",
      result: "lifecycle",
    },
  ]);
  fs.rmSync(repositoryRoot, { recursive: true, force: true });
});