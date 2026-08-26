export function validateVisualAssets(configuration) {
  if (!Array.isArray(configuration.assets) || configuration.assets.length === 0) {
    throw new Error("Visual asset configuration has no assets");
  }

  const ids = new Set();
  for (const asset of configuration.assets) {
    if (!asset.id || ids.has(asset.id)) {
      throw new Error(`Invalid or duplicate visual asset id: ${asset.id}`);
    }
    ids.add(asset.id);
    if (!asset.variants || Object.keys(asset.variants).length === 0) {
      throw new Error(`${asset.id}: no variants are defined`);
    }
    for (const [variantName, variant] of Object.entries(asset.variants)) {
      if (!variant.source?.reviewedPath) {
        throw new Error(`${asset.id}/${variantName}: missing reviewed source`);
      }
      if (!variant.output?.startsWith("public/")) {
        throw new Error(
          `${asset.id}/${variantName}: output must be under public/`,
        );
      }
      if (typeof variant.pipeline?.run !== "function") {
        throw new Error(`${asset.id}/${variantName}: missing pipeline`);
      }
      if (!variant.expected) {
        throw new Error(`${asset.id}/${variantName}: missing expectations`);
      }
    }
  }
}

export function selectAssetVariants(
  configuration,
  {
    assetIds = [],
    variantName,
    all = false,
    defaultAll = false,
  } = {},
) {
  validateVisualAssets(configuration);
  if (all && assetIds.length > 0) {
    throw new Error("Use asset ids or --all, not both");
  }
  if (!all && !defaultAll && assetIds.length === 0) {
    throw new Error("Select at least one asset or pass --all");
  }

  const requestedIds =
    all || (defaultAll && assetIds.length === 0)
      ? configuration.assets.map((asset) => asset.id)
      : assetIds;
  const assetMap = new Map(
    configuration.assets.map((asset) => [asset.id, asset]),
  );
  const selected = [];

  for (const assetId of requestedIds) {
    const asset = assetMap.get(assetId);
    if (!asset) {
      throw new Error(`Unknown visual asset: ${assetId}`);
    }
    const variants = variantName
      ? [[variantName, asset.variants[variantName]]]
      : Object.entries(asset.variants);
    for (const [selectedVariantName, variant] of variants) {
      if (!variant) {
        throw new Error(
          `${assetId}: unknown variant ${selectedVariantName}`,
        );
      }
      selected.push({
        asset,
        variantName: selectedVariantName,
        variant,
      });
    }
  }

  return selected;
}