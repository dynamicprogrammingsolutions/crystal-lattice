import assert from "node:assert/strict";
import test from "node:test";

import {
  centerExtent,
  encodeWebp,
  imageMagickArguments,
  imageMagickPipeline,
  normalizeSrgb,
  resize,
  stripMetadata,
  trim,
} from "../../scripts/visual-assets/operations.mjs";

test("programmatic ImageMagick operations produce one replaceable pipeline", async () => {
  const calls = [];
  const pipeline = imageMagickPipeline({
    id: "test-pipeline",
    operations: [
      trim(),
      resize("1000x1315^"),
      centerExtent("1000x1315"),
      normalizeSrgb(),
      stripMetadata(),
      encodeWebp({ quality: 80, method: 6 }),
    ],
  });

  await pipeline.run({
    sourcePath: "/tmp/source.png",
    candidatePath: "/tmp/candidate.webp",
    landingRoot: "/tmp/landing",
    async run(command, args, options) {
      calls.push({ command, args, options });
    },
  });

  assert.deepEqual(calls, [
    {
      command: "magick",
      args: [
        "/tmp/source.png",
        "-trim",
        "+repage",
        "-resize",
        "1000x1315^",
        "-gravity",
        "center",
        "-extent",
        "1000x1315",
        "-colorspace",
        "sRGB",
        "-strip",
        "-quality",
        "80",
        "-define",
        "webp:method=6",
        "/tmp/candidate.webp",
      ],
      options: {
        cwd: "/tmp/landing",
        stdio: "pipe",
      },
    },
  ]);
});

test("an asset can add a one-off operation without changing the runner", async () => {
  const calls = [];
  const uniqueOperation = imageMagickArguments("unique-border-removal", () => [
    "-shave",
    "3x4",
  ]);
  const pipeline = imageMagickPipeline({
    id: "one-off",
    operations: [uniqueOperation, encodeWebp()],
  });

  await pipeline.run({
    sourcePath: "source.png",
    candidatePath: "candidate.webp",
    landingRoot: "/tmp/landing",
    async run(command, args) {
      calls.push({ command, args });
    },
  });

  assert.deepEqual(calls[0].args, [
    "source.png",
    "-shave",
    "3x4",
    "-quality",
    "80",
    "-define",
    "webp:method=6",
    "candidate.webp",
  ]);
});