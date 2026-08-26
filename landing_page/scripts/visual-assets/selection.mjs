export function parseSelectionArguments(args) {
  const selection = {
    assetIds: [],
    all: false,
    variantName: undefined,
    extraArgs: [],
  };

  for (let index = 0; index < args.length; index += 1) {
    const current = args[index];
    if (current === "--all") {
      selection.all = true;
    } else if (current === "--variant") {
      const value = args[index + 1];
      if (!value) {
        throw new Error("--variant requires a value");
      }
      selection.variantName = value;
      index += 1;
    } else if (current.startsWith("--")) {
      selection.extraArgs.push(current);
    } else {
      selection.assetIds.push(current);
    }
  }

  return selection;
}

export function selectAssets(
  catalog,
  args,
  {
    defaultAll = false,
    requireSelection = false,
    allowExtraArgs = false,
  } = {},
) {
  const parsed = parseSelectionArguments(args);
  if (!allowExtraArgs && parsed.extraArgs.length > 0) {
    throw new Error(`Unknown options: ${parsed.extraArgs.join(", ")}`);
  }
  if (parsed.all && parsed.assetIds.length > 0) {
    throw new Error("Use asset ids or --all, not both");
  }
  if (
    requireSelection &&
    !parsed.all &&
    parsed.assetIds.length === 0
  ) {
    throw new Error("Select at least one asset or pass --all");
  }

  const selectedIds =
    parsed.all || (defaultAll && parsed.assetIds.length === 0)
      ? catalog.assets.map((asset) => asset.id)
      : parsed.assetIds;
  const assets = selectedIds.map((assetId) => {
    const asset = catalog.assetMap.get(assetId);
    if (!asset) {
      throw new Error(`Unknown visual asset: ${assetId}`);
    }
    return asset;
  });

  return {
    ...parsed,
    assets,
    explicit: !parsed.all,
  };
}