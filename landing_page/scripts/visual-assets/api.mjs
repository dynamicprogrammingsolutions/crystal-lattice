export function defineVisualAssets(configuration) {
  return configuration;
}

export function defineAsset(asset) {
  return asset;
}

export function definePipeline({ id, run }) {
  if (typeof run !== "function") {
    throw new Error(`Pipeline ${id ?? "<anonymous>"} must define run(context)`);
  }
  return { id, run };
}

export function reviewedFile(reviewedPath) {
  return {
    kind: "reviewed-file",
    reviewedPath,
  };
}

export function captureOutput({ candidatePath, capture }) {
  if (!candidatePath || typeof capture !== "function") {
    throw new Error(
      "captureOutput requires candidatePath and capture(context)",
    );
  }
  return {
    kind: "capture-output",
    candidatePath,
    capture,
  };
}

export function capturedSource({ reviewed, candidate }) {
  if (!reviewed || candidate?.kind !== "capture-output") {
    throw new Error(
      "capturedSource requires a reviewed path and captureOutput candidate",
    );
  }
  return {
    kind: "captured-source",
    reviewedPath: reviewed,
    candidate,
  };
}

export function yamlMediaBinding({
  file,
  sectionId,
  collection,
  title,
  mediaField,
  variantFields,
}) {
  return {
    kind: "yaml-media",
    file,
    sectionId,
    collection,
    title,
    mediaField,
    variantFields,
  };
}