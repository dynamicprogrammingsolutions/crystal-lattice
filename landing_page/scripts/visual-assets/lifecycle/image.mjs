import fs from "node:fs";
import path from "node:path";

import {
  ensureArtifactPath,
  inspectImage,
  resolveLandingPath,
  resolveRepositoryPath,
  sha256,
  validateContentBindings,
} from "../validation.mjs";

function selectedVariants(config, variantName) {
  if (!config?.variants || Object.keys(config.variants).length === 0) {
    throw new Error("Image asset requires config.variants");
  }
  if (variantName) {
    const variant = config.variants[variantName];
    if (!variant) {
      throw new Error(`Unknown image variant: ${variantName}`);
    }
    return [[variantName, variant]];
  }
  return Object.entries(config.variants);
}

function expectedMatches(metrics, expected) {
  return {
    width: metrics.width === expected.width,
    height: metrics.height === expected.height,
    max_bytes: metrics.bytes <= expected.maxBytes,
    sha256: metrics.sha256 === expected.sha256,
  };
}

function assertExpected(assetId, variantName, metrics, expected, matches) {
  if (!matches.width || !matches.height) {
    throw new Error(
      `${assetId}/${variantName}: generated ${metrics.width}x${metrics.height}, expected ${expected.width}x${expected.height}`,
    );
  }
  if (!matches.max_bytes) {
    throw new Error(
      `${assetId}/${variantName}: ${metrics.bytes} bytes exceeds ${expected.maxBytes}`,
    );
  }
  if (!matches.sha256) {
    throw new Error(
      `${assetId}/${variantName}: generated sha256 ${metrics.sha256}, expected ${expected.sha256}`,
    );
  }
}

function captureCandidatePath(source, repositoryRoot) {
  const candidatePath = resolveRepositoryPath(
    repositoryRoot,
    source.candidate.candidatePath,
    "Capture candidate",
  );
  ensureArtifactPath(repositoryRoot, candidatePath);
  return candidatePath;
}

export async function describeImageAsset({
  asset,
  config,
}) {
  return {
    id: asset.id,
    metadata: asset.metadata,
    variants: Object.entries(config.variants).map(
      ([variantName, variant]) => ({
        name: variantName,
        source_kind: variant.source.kind,
        output: variant.output,
        build: variant.build.id ?? "<anonymous>",
      }),
    ),
    commands: Object.keys(asset.commands),
    lifecycle: Object.keys(asset.lifecycle),
  };
}

export async function validateImageAssetDefinition({
  asset,
  config,
  landingRoot,
  commandCache,
}) {
  for (const [variantName, variant] of Object.entries(config.variants ?? {})) {
    if (!variant.source?.reviewedPath) {
      throw new Error(`${asset.id}/${variantName}: missing reviewed source`);
    }
    if (!variant.output?.startsWith("public/")) {
      throw new Error(
        `${asset.id}/${variantName}: output must be under public/`,
      );
    }
    if (typeof variant.build?.run !== "function") {
      throw new Error(`${asset.id}/${variantName}: missing build`);
    }
    if (!variant.expected) {
      throw new Error(`${asset.id}/${variantName}: missing expectations`);
    }
  }

  let documentCache = commandCache.get("yaml-documents");
  if (!documentCache) {
    documentCache = new Map();
    commandCache.set("yaml-documents", documentCache);
  }
  validateContentBindings(
    {
      id: asset.id,
      presentation: config.presentation,
      contentBindings: config.contentBindings,
      variants: config.variants,
    },
    landingRoot,
    documentCache,
  );
}

export async function buildImageCandidates({
  asset,
  config,
  variantName,
  landingRoot,
  artifactPath,
  run,
}) {
  const candidates = [];
  for (const [selectedVariantName, variant] of selectedVariants(
    config,
    variantName,
  )) {
    const sourcePath = resolveLandingPath(
      landingRoot,
      variant.source.reviewedPath,
      "Reviewed source",
    );
    if (!fs.existsSync(sourcePath)) {
      throw new Error(
        `${asset.id}/${selectedVariantName}: missing reviewed source ${variant.source.reviewedPath}`,
      );
    }
    const candidatePath = artifactPath(
      "generated",
      asset.id,
      selectedVariantName,
      path.basename(variant.output),
    );
    fs.rmSync(path.dirname(candidatePath), {
      recursive: true,
      force: true,
    });
    fs.mkdirSync(path.dirname(candidatePath), { recursive: true });

    await variant.build.run({
      asset,
      variant,
      variantName: selectedVariantName,
      sourcePath,
      candidatePath,
      landingRoot,
      run,
    });
    if (!fs.existsSync(candidatePath)) {
      throw new Error(
        `${asset.id}/${selectedVariantName}: build ${variant.build.id ?? "<anonymous>"} did not create ${candidatePath}`,
      );
    }

    candidates.push({
      assetId: asset.id,
      variantName: selectedVariantName,
      variant,
      sourcePath,
      candidatePath,
      publicPath: resolveLandingPath(
        landingRoot,
        variant.output,
        "Public output",
      ),
    });
  }
  return candidates;
}

export async function inspectImageCandidates({
  asset,
  metadata,
  input,
}) {
  return input.candidates.map((candidate) => {
    const metrics = inspectImage(candidate.candidatePath);
    const expected = candidate.variant.expected;
    const matches = expectedMatches(metrics, expected);
    const publicExists = fs.existsSync(candidate.publicPath);
    const publicMatches =
      publicExists && sha256(candidate.publicPath) === metrics.sha256;

    return {
      ...candidate,
      metrics,
      matches,
      result: {
        asset_id: asset.id,
        variant: candidate.variantName,
        build: candidate.variant.build.id ?? "<anonymous>",
        source: candidate.variant.source.reviewedPath,
        output: candidate.variant.output,
        metadata,
        width: metrics.width,
        height: metrics.height,
        bytes: metrics.bytes,
        sha256: metrics.sha256,
        expected: {
          width: expected.width,
          height: expected.height,
          max_bytes: expected.maxBytes,
          sha256: expected.sha256,
        },
        matches_expected: matches,
        public_exists: publicExists,
        public_matches_candidate: publicMatches,
      },
    };
  });
}

export async function validateImageCandidates({
  asset,
  input,
}) {
  const strict = input.strict ?? true;
  for (const candidate of input.candidates) {
    if (strict) {
      assertExpected(
        asset.id,
        candidate.variantName,
        candidate.metrics,
        candidate.variant.expected,
        candidate.matches,
      );
    }
  }
  return input.candidates;
}

export async function comparePublishedImages({
  asset,
  input,
}) {
  for (const candidate of input.candidates) {
    if (!candidate.result.public_matches_candidate) {
      throw new Error(
        `${asset.id}/${candidate.variantName}: ${candidate.variant.output} differs; run yarn visual-assets:update ${asset.id}`,
      );
    }
  }
  return input.candidates;
}

export async function prepareImagePublication({
  asset,
  input,
}) {
  return input.candidates.map((candidate) => ({
    report: candidate.result,
    async apply() {
      fs.mkdirSync(path.dirname(candidate.publicPath), {
        recursive: true,
      });
      fs.copyFileSync(candidate.candidatePath, candidate.publicPath);
      if (
        sha256(candidate.publicPath) !== candidate.result.sha256
      ) {
        throw new Error(
          `${asset.id}/${candidate.variantName}: failed to update ${candidate.variant.output}`,
        );
      }
      candidate.result.public_exists = true;
      candidate.result.public_matches_candidate = true;
    },
  }));
}

export async function captureImageSources({
  asset,
  config,
  variantName,
  selectionIsAll,
  repositoryRoot,
  run,
}) {
  const results = [];
  for (const [selectedVariantName, variant] of selectedVariants(
    config,
    variantName,
  )) {
    if (variant.source.kind !== "captured-source") {
      if (selectionIsAll) {
        continue;
      }
      throw new Error(
        `${asset.id}/${selectedVariantName}: source has no capture producer`,
      );
    }
    const candidatePath = captureCandidatePath(
      variant.source,
      repositoryRoot,
    );
    const producedPath = await variant.source.candidate.capture({
      asset,
      variant,
      variantName: selectedVariantName,
      repositoryRoot,
      run,
    });
    if (
      path.resolve(producedPath) !== candidatePath ||
      !fs.existsSync(candidatePath)
    ) {
      throw new Error(
        `${asset.id}/${selectedVariantName}: capture producer did not create ${candidatePath}`,
      );
    }
    results.push({
      asset_id: asset.id,
      variant: selectedVariantName,
      candidate: path.relative(repositoryRoot, candidatePath),
      bytes: fs.statSync(candidatePath).size,
    });
  }
  return results;
}

export async function prepareImageSourcePromotion({
  asset,
  config,
  variantName,
  selectionIsAll,
  repositoryRoot,
  landingRoot,
}) {
  const prepared = [];
  for (const [selectedVariantName, variant] of selectedVariants(
    config,
    variantName,
  )) {
    if (variant.source.kind !== "captured-source") {
      if (selectionIsAll) {
        continue;
      }
      throw new Error(
        `${asset.id}/${selectedVariantName}: source has no captured candidate`,
      );
    }
    const candidatePath = captureCandidatePath(
      variant.source,
      repositoryRoot,
    );
    if (!fs.existsSync(candidatePath)) {
      throw new Error(
        `${asset.id}/${selectedVariantName}: missing captured candidate ${candidatePath}; run capture first`,
      );
    }
    const reviewedPath = resolveLandingPath(
      landingRoot,
      variant.source.reviewedPath,
      "Reviewed source",
    );
    const report = {
      asset_id: asset.id,
      variant: selectedVariantName,
      candidate: path.relative(repositoryRoot, candidatePath),
      reviewed_source: variant.source.reviewedPath,
      bytes: fs.statSync(candidatePath).size,
      sha256: sha256(candidatePath),
    };
    prepared.push({
      report,
      async apply() {
        fs.mkdirSync(path.dirname(reviewedPath), { recursive: true });
        fs.copyFileSync(candidatePath, reviewedPath);
      },
    });
  }
  return prepared;
}