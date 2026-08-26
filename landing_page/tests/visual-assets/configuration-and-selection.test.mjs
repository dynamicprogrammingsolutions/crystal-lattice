import assert from "node:assert/strict";
import test from "node:test";

import catalog from "../../visual_assets/config.mjs";
import { defineAsset } from "../../scripts/visual-assets/api.mjs";
import { selectAssets } from "../../scripts/visual-assets/selection.mjs";

test("the current catalog defines commands and source-local lifecycle assets", () => {
  assert.equal(catalog.assets.length, 5);
  assert.deepEqual(catalog.commandNames, [
    "list",
    "inspect",
    "check",
    "update",
    "capture",
    "promote-source",
  ]);

  for (const asset of catalog.assets) {
    assert.equal(asset.hasCommand("check"), false);
    assert.equal(asset.hasLifecycle("buildCandidate"), true);
    assert.equal(asset.hasLifecycle("comparePublished"), true);
    for (const variant of Object.values(asset.config.variants)) {
      assert.match(
        variant.source.reviewedPath,
        /^visual_assets\/sources\//,
      );
      assert.equal(
        variant.provenance.revision,
        "e88aa46ee8d6bd0969c63c78f8e152f1fd938974",
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

  assert.equal(selected.assets.length, 5);
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