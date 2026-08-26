import assert from "node:assert/strict";
import test from "node:test";

import configuration from "../../visual_assets/config.mjs";
import {
  selectAssetVariants,
  validateVisualAssets,
} from "../../scripts/visual-assets/selection.mjs";

test("the current programmatic configuration is valid and source-local", () => {
  validateVisualAssets(configuration);

  assert.equal(configuration.assets.length, 5);
  for (const asset of configuration.assets) {
    for (const variant of Object.values(asset.variants)) {
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

test("selection can address one asset and one arbitrary variant", () => {
  const selected = selectAssetVariants(configuration, {
    assetIds: ["provider-reasoning"],
    variantName: "dark",
  });

  assert.equal(selected.length, 1);
  assert.equal(selected[0].asset.id, "provider-reasoning");
  assert.equal(selected[0].variantName, "dark");
});

test("check-style default selection includes the complete catalog", () => {
  const selected = selectAssetVariants(configuration, {
    defaultAll: true,
  });

  assert.equal(selected.length, 10);
});

test("mutating commands require an explicit selection or --all", () => {
  assert.throws(
    () => selectAssetVariants(configuration),
    /Select at least one asset or pass --all/,
  );
});