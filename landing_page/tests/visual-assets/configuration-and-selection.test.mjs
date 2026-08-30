import assert from "node:assert/strict";
import test from "node:test";

import catalog from "../../visual_assets/config.mjs";
import { defineAsset } from "../../scripts/visual-assets/api.mjs";
import { selectAssets } from "../../scripts/visual-assets/selection.mjs";

function valuesAfter(args, option) {
  return args.flatMap((value, index) =>
    value === option ? [args[index + 1]] : [],
  );
}

function parseCrop(value) {
  const match = /^(\d+)x(\d+)\+(\d+)\+(\d+)$/.exec(value);
  assert.ok(match, `invalid crop geometry: ${value}`);
  return {
    width: Number(match[1]),
    height: Number(match[2]),
    x: Number(match[3]),
    y: Number(match[4]),
  };
}

function parseResize(value) {
  const match = /^(\d+)x(\d+)!$/.exec(value);
  assert.ok(match, `invalid resize geometry: ${value}`);
  return {
    width: Number(match[1]),
    height: Number(match[2]),
  };
}

function parsePlacement(value) {
  const match = /^\+(-?\d+)\+(-?\d+)$/.exec(value);
  assert.ok(match, `invalid placement geometry: ${value}`);
  return {
    x: Number(match[1]),
    y: Number(match[2]),
  };
}

async function capturePipelineArguments(pipeline) {
  const calls = [];
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
  return calls[0].args;
}

test("the current catalog defines commands and source-local lifecycle assets", () => {
  assert.equal(catalog.assets.length, 8);
  assert.deepEqual(catalog.commandNames, [
    "list",
    "inspect",
    "check",
    "update",
    "capture",
    "promote-source",
    "refresh-session",
    "promote-session",
    "refresh-runtime-ui",
    "promote-runtime-ui",
  ]);

  const sessionAsset = catalog.assetMap.get("coding-plan");
  assert.equal(sessionAsset.hasCommand("refresh-session"), true);
  assert.equal(sessionAsset.hasCommand("promote-session"), true);
  assert.equal(sessionAsset.hasCommand("check"), true);

  const runtimeUiAsset = catalog.assetMap.get("mobile-workbench");
  assert.equal(runtimeUiAsset.hasCommand("refresh-runtime-ui"), true);
  assert.equal(runtimeUiAsset.hasCommand("promote-runtime-ui"), true);
  assert.equal(runtimeUiAsset.hasCommand("check"), true);

  for (const asset of catalog.assets.filter(
    (item) => !["coding-plan", "mobile-workbench"].includes(item.id),
  )) {
    assert.equal(asset.hasCommand("check"), false);
    assert.equal(asset.hasLifecycle("buildCandidate"), true);
    assert.equal(asset.hasLifecycle("comparePublished"), true);
    for (const variant of Object.values(asset.config.variants)) {
      assert.match(
        variant.source.reviewedPath,
        /^visual_assets\/sources\//,
      );
      if (asset.id === "mobile-active-session") {
        assert.equal(variant.provenance.kind, "detox-capture");
        assert.equal(variant.provenance.fixture, "coding-plan");
      } else {
        assert.equal(
          variant.provenance.revision,
          "e88aa46ee8d6bd0969c63c78f8e152f1fd938974",
        );
      }
    }
  }
});

test("provider focus callouts vertically cover the source regions they enlarge", async () => {
  for (const assetId of ["provider-reasoning", "provider-usage-cost"]) {
    const asset = catalog.assetMap.get(assetId);
    for (const [variantName, variant] of Object.entries(asset.config.variants)) {
      const args = await capturePipelineArguments(variant.build);
      const crops = valuesAfter(args, "-crop").map(parseCrop);
      const resizes = valuesAfter(args, "-resize").map(parseResize);
      const placements = valuesAfter(args, "-geometry").map(parsePlacement);
      assert.equal(crops.length, 2);
      assert.equal(resizes.length, 2);
      assert.equal(placements.length, 2);

      const [originalCrop, calloutCrop] = crops;
      const [originalResize, calloutResize] = resizes;
      const [originalPlacement, calloutPlacement] = placements;
      const scaleY = originalResize.height / originalCrop.height;
      const targetTop =
        originalPlacement.y + (calloutCrop.y - originalCrop.y) * scaleY;
      const targetBottom = targetTop + calloutCrop.height * scaleY;
      const calloutTop = calloutPlacement.y;
      const calloutBottom = calloutTop + calloutResize.height;

      assert.ok(
        calloutTop <= targetTop,
        `${assetId}/${variantName}: callout starts below its source region`,
      );
      assert.ok(
        calloutBottom >= targetBottom,
        `${assetId}/${variantName}: callout does not cover its source region`,
      );
    }
  }
});

test("selection addresses assets while leaving variant interpretation to callbacks", () => {
  const selected = selectAssets(
    catalog,
    ["provider-reasoning", "--variant", "dark"],
    {
      requireSelection: true,
    },
  );

  assert.equal(selected.assets.length, 1);
  assert.equal(selected.assets[0].id, "provider-reasoning");
  assert.equal(selected.variantName, "dark");
});

test("check-style default selection includes the complete catalog", () => {
  const selected = selectAssets(catalog, [], {
    defaultAll: true,
  });

  assert.equal(selected.assets.length, 8);
});

test("mutating commands require an explicit selection or --all", () => {
  assert.throws(
    () =>
      selectAssets(catalog, [], {
        requireSelection: true,
      }),
    /Select at least one asset or pass --all/,
  );
});

test("an asset can define commands, lifecycle callbacks, or both", async () => {
  const direct = defineAsset({
    id: "direct",
    config: { value: 1 },
    commands: {
      check: ({ config }) => config.value,
    },
  });
  const lifecycle = defineAsset({
    id: "lifecycle",
    config: { value: 2 },
    lifecycle: {
      validate: ({ config }) => config.value,
    },
  });
  const mixed = defineAsset({
    id: "mixed",
    config: { value: 3 },
    commands: {
      capture: ({ config }) => config.value,
    },
    lifecycle: {
      validate: ({ config }) => config.value,
    },
  });

  assert.equal(direct.hasCommand("check"), true);
  assert.equal(direct.hasLifecycle("validate"), false);
  assert.equal(await direct.runCommand("check", {}), 1);
  assert.equal(lifecycle.hasLifecycle("validate"), true);
  assert.equal(await lifecycle.runLifecycle("validate", {}), 2);
  assert.equal(mixed.hasCommand("capture"), true);
  assert.equal(mixed.hasLifecycle("validate"), true);
});

test("defineAsset rejects unknown common keys", () => {
  assert.throws(
    () =>
      defineAsset({
        id: "invalid",
        config: {},
        commands: {
          check() {},
        },
        unexpected: true,
      }),
    /unknown keys: unexpected/,
  );
});