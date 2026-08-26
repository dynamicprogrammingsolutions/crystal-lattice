import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

import {
  capturedSource,
  captureOutput,
  defineAsset,
  definePipeline,
  defineVisualAssets,
} from "../../scripts/visual-assets/api.mjs";
import { detoxCapture } from "../../scripts/visual-assets/producers/detox.mjs";
import { executeVisualAssets } from "../../scripts/visual-assets/runner.mjs";
import {
  inspectImage,
  sha256,
} from "../../scripts/visual-assets/validation.mjs";

test("capture and source promotion are separate explicit operations", async () => {
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
  const configuration = defineVisualAssets({
    assets: [
      defineAsset({
        id: "mobile-hero",
        variants: {
          default: {
            source,
            output: "public/mobile-hero.webp",
            pipeline: definePipeline({
              id: "unused-in-capture-test",
              async run() {},
            }),
            expected: {
              width: 1,
              height: 1,
              maxBytes: 100,
              sha256: "not-used",
            },
          },
        },
      }),
    ],
  });

  await executeVisualAssets({
    configuration,
    command: "capture",
    assetIds: ["mobile-hero"],
    all: false,
    repositoryRoot,
    landingRoot,
  });

  assert.equal(fs.readFileSync(candidateAbsolute, "utf8"), "captured");
  assert.equal(fs.existsSync(reviewedAbsolute), false);

  await executeVisualAssets({
    configuration,
    command: "promote-source",
    assetIds: ["mobile-hero"],
    all: false,
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

test("a failed selected candidate does not partially update public files", async () => {
  const repositoryRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), "visual-assets-update-"),
  );
  const landingRoot = path.join(repositoryRoot, "landing_page");
  const sourceRelative = "visual_assets/sources/source.png";
  const sourceAbsolute = path.join(landingRoot, sourceRelative);
  const publicOne = path.join(landingRoot, "public/one.png");
  fs.mkdirSync(path.dirname(sourceAbsolute), { recursive: true });
  fs.mkdirSync(path.dirname(publicOne), { recursive: true });
  const generated = spawnSync(
    "magick",
    ["-size", "1x1", "xc:red", sourceAbsolute],
    { encoding: "utf8" },
  );
  assert.equal(generated.status, 0, generated.stderr);
  fs.writeFileSync(publicOne, "unchanged");

  const metrics = inspectImage(sourceAbsolute);
  const copyingPipeline = definePipeline({
    id: "copy",
    async run(context) {
      fs.copyFileSync(context.sourcePath, context.candidatePath);
    },
  });
  const validExpected = {
    width: metrics.width,
    height: metrics.height,
    maxBytes: metrics.bytes,
    sha256: metrics.sha256,
  };
  const configuration = defineVisualAssets({
    assets: [
      defineAsset({
        id: "one",
        variants: {
          default: {
            source: {
              kind: "reviewed-file",
              reviewedPath: sourceRelative,
            },
            output: "public/one.png",
            pipeline: copyingPipeline,
            expected: validExpected,
          },
        },
      }),
      defineAsset({
        id: "two",
        variants: {
          default: {
            source: {
              kind: "reviewed-file",
              reviewedPath: sourceRelative,
            },
            output: "public/two.png",
            pipeline: copyingPipeline,
            expected: {
              ...validExpected,
              sha256: "does-not-match",
            },
          },
        },
      }),
    ],
  });
  const before = sha256(publicOne);

  await assert.rejects(
    executeVisualAssets({
      configuration,
      command: "update",
      assetIds: [],
      all: true,
      repositoryRoot,
      landingRoot,
    }),
    /generated sha256/,
  );

  assert.equal(sha256(publicOne), before);
  fs.rmSync(repositoryRoot, { recursive: true, force: true });
});