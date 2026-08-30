import assert from "node:assert/strict";
import test from "node:test";

import {
  centerExtent,
  crop,
  encodeWebp,
  focusCalloutPipeline,
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
      crop("1200x1600+10+20"),
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
        "-crop",
        "1200x1600+10+20",
        "+repage",
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

test("focus callout exposes square original and callout geometry per asset", async () => {
  const calls = [];
  const pipeline = focusCalloutPipeline({
    id: "focus",
    canvas: {
      width: 1000,
      height: 1315,
      background: "#F3F4F7",
    },
    original: {
      crop: "1200x1600+0+100",
      width: 720,
      height: 960,
      gravity: "center",
      geometry: "+0+180",
      dimPercent: 22,
      borderColor: "#D9DDE5",
      borderWidth: 1,
    },
    callout: {
      crop: "900x500+100+700",
      width: 920,
      height: 510,
      gravity: "north",
      geometry: "+0+92",
      borderColor: "#FFFFFF",
      borderWidth: 3,
      shadow: {
        color: "rgba(0,0,0,0.55)",
        geometry: "45x14+0+10",
      },
    },
    quality: 78,
  });

  await pipeline.run({
    sourcePath: "/tmp/source.png",
    candidatePath: "/tmp/candidate.webp",
    landingRoot: "/tmp/landing",
    async run(command, args, options) {
      calls.push({ command, args, options });
    },
  });

  assert.equal(calls.length, 1);
  assert.equal(calls[0].command, "magick");
  assert.deepEqual(calls[0].options, {
    cwd: "/tmp/landing",
    stdio: "pipe",
  });
  assert.deepEqual(calls[0].args.slice(0, 23), [
    "(",
    "-size",
    "1000x1315",
    "xc:#F3F4F7",
    ")",
    "(",
    "/tmp/source.png",
    "-gravity",
    "northwest",
    "-crop",
    "1200x1600+0+100",
    "+repage",
    "-resize",
    "720x960!",
    "-fill",
    "#000000",
    "-colorize",
    "22%",
    "-bordercolor",
    "#D9DDE5",
    "-border",
    "1x1",
    ")",
  ]);
  assert.ok(calls[0].args.includes("900x500+100+700"));
  assert.ok(calls[0].args.includes("920x510!"));
  assert.ok(calls[0].args.includes("45x14+0+10"));
  assert.ok(!calls[0].args.includes("-draw"));
  assert.deepEqual(
    calls[0].args.filter((value) => value === "+0+180"),
    ["+0+180"],
  );
  assert.deepEqual(
    calls[0].args.filter((value) => value === "+0+92"),
    ["+0+92"],
  );
  assert.deepEqual(calls[0].args.slice(-8), [
    "-colorspace",
    "sRGB",
    "-strip",
    "-quality",
    "78",
    "-define",
    "webp:method=6",
    "/tmp/candidate.webp",
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