import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

import { selectAssetVariants, validateVisualAssets } from "./selection.mjs";
import {
  ensureArtifactPath,
  inspectImage,
  resolveLandingPath,
  resolveRepositoryPath,
  sha256,
  validateContentBindings,
} from "./validation.mjs";

function runProcess(
  command,
  args,
  {
    cwd,
    env = {},
    stdio = "inherit",
  } = {},
) {
  const result = spawnSync(command, args, {
    cwd,
    env: { ...process.env, ...env },
    encoding: stdio === "pipe" ? "utf8" : undefined,
    maxBuffer: 64 * 1024 * 1024,
    stdio,
  });
  if (result.status !== 0) {
    const stderr =
      typeof result.stderr === "string"
        ? result.stderr
        : result.stderr?.toString("utf8");
    throw new Error(
      `${command} ${args.join(" ")} failed: ${stderr || "unknown error"}`,
    );
  }
  return {
    stdout:
      typeof result.stdout === "string"
        ? result.stdout
        : result.stdout?.toString("utf8"),
  };
}

function candidatePathFor(artifactRoot, asset, variantName, outputPath) {
  return path.join(
    artifactRoot,
    "generated",
    asset.id,
    variantName,
    path.basename(outputPath),
  );
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

function writeReport(artifactRoot, command, report) {
  const reportDirectory = path.join(artifactRoot, "reports");
  fs.mkdirSync(reportDirectory, { recursive: true });
  const reportPath = path.join(reportDirectory, `${command}.json`);
  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  return reportPath;
}

function uniqueAssets(selected) {
  const assets = new Map();
  for (const item of selected) {
    assets.set(item.asset.id, item.asset);
  }
  return [...assets.values()];
}

function applyBudgets(configuration, results, strict) {
  const budgets = [];
  for (const budget of configuration.budgets ?? []) {
    const applicable = results.filter((result) =>
      budget.select({
        assetId: result.asset_id,
        variantName: result.variant,
      }),
    );
    const bytes = applicable.reduce((sum, result) => sum + result.bytes, 0);
    const withinBudget = bytes <= budget.maxBytes;
    if (strict && !withinBudget) {
      throw new Error(
        `${budget.id}: ${bytes} bytes exceeds ${budget.maxBytes}`,
      );
    }
    budgets.push({
      id: budget.id,
      max_bytes: budget.maxBytes,
      selected_assets: applicable.length,
      bytes,
      within_budget: withinBudget,
    });
  }
  return budgets;
}

function generationContext({
  asset,
  variant,
  variantName,
  sourcePath,
  candidatePath,
  repositoryRoot,
  landingRoot,
  artifactRoot,
}) {
  return {
    asset,
    variant,
    variantName,
    sourcePath,
    candidatePath,
    repositoryRoot,
    landingRoot,
    artifactRoot,
    run: async (command, args, options = {}) =>
      runProcess(command, args, {
        cwd: options.cwd ?? repositoryRoot,
        env: options.env,
        stdio: options.stdio,
      }),
    artifactPath(...segments) {
      return path.join(artifactRoot, ...segments);
    },
  };
}

async function generateVariants({
  configuration,
  selected,
  command,
  repositoryRoot,
  landingRoot,
  artifactRoot,
}) {
  const strict = command !== "inspect";
  const documentCache = new Map();
  const results = [];
  const generated = [];

  for (const asset of uniqueAssets(selected)) {
    validateContentBindings(asset, landingRoot, documentCache);
  }

  for (const { asset, variantName, variant } of selected) {
    const sourcePath = resolveLandingPath(
      landingRoot,
      variant.source.reviewedPath,
      "Reviewed source",
    );
    if (!fs.existsSync(sourcePath)) {
      throw new Error(
        `${asset.id}/${variantName}: missing reviewed source ${variant.source.reviewedPath}`,
      );
    }

    const candidatePath = candidatePathFor(
      artifactRoot,
      asset,
      variantName,
      variant.output,
    );
    fs.rmSync(path.dirname(candidatePath), {
      recursive: true,
      force: true,
    });
    fs.mkdirSync(path.dirname(candidatePath), { recursive: true });

    const context = generationContext({
      asset,
      variant,
      variantName,
      sourcePath,
      candidatePath,
      repositoryRoot,
      landingRoot,
      artifactRoot,
    });
    await variant.pipeline.run(context);
    if (!fs.existsSync(candidatePath)) {
      throw new Error(
        `${asset.id}/${variantName}: pipeline ${variant.pipeline.id ?? "<anonymous>"} did not create ${candidatePath}`,
      );
    }

    const metrics = inspectImage(candidatePath);
    const matches = expectedMatches(metrics, variant.expected);
    if (strict) {
      assertExpected(
        asset.id,
        variantName,
        metrics,
        variant.expected,
        matches,
      );
    }

    const publicPath = resolveLandingPath(
      landingRoot,
      variant.output,
      "Public output",
    );
    const publicExists = fs.existsSync(publicPath);
    const publicMatches =
      publicExists && sha256(publicPath) === metrics.sha256;
    if (command === "check" && !publicMatches) {
      throw new Error(
        `${asset.id}/${variantName}: ${variant.output} differs; run yarn visual-assets:update ${asset.id}`,
      );
    }

    const result = {
      asset_id: asset.id,
      variant: variantName,
      pipeline: variant.pipeline.id ?? "<anonymous>",
      source: variant.source.reviewedPath,
      output: variant.output,
      width: metrics.width,
      height: metrics.height,
      bytes: metrics.bytes,
      sha256: metrics.sha256,
      expected: {
        width: variant.expected.width,
        height: variant.expected.height,
        max_bytes: variant.expected.maxBytes,
        sha256: variant.expected.sha256,
      },
      matches_expected: matches,
      public_exists: publicExists,
      public_matches_candidate: publicMatches,
    };
    results.push(result);
    generated.push({
      assetId: asset.id,
      variantName,
      candidatePath,
      publicPath,
      output: variant.output,
      result,
    });
  }

  const budgets = applyBudgets(configuration, results, strict);

  if (command === "update") {
    for (const current of generated) {
      fs.mkdirSync(path.dirname(current.publicPath), { recursive: true });
      fs.copyFileSync(current.candidatePath, current.publicPath);
      if (sha256(current.publicPath) !== current.result.sha256) {
        throw new Error(
          `${current.assetId}/${current.variantName}: failed to update ${current.output}`,
        );
      }
      current.result.public_exists = true;
      current.result.public_matches_candidate = true;
    }
  }

  return {
    results,
    budgets,
  };
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

async function captureVariants({
  selected,
  all,
  repositoryRoot,
  landingRoot,
  artifactRoot,
}) {
  const results = [];
  for (const { asset, variantName, variant } of selected) {
    if (variant.source.kind !== "captured-source") {
      if (all) {
        continue;
      }
      throw new Error(
        `${asset.id}/${variantName}: source has no capture producer`,
      );
    }
    const candidatePath = captureCandidatePath(
      variant.source,
      repositoryRoot,
    );
    const context = generationContext({
      asset,
      variant,
      variantName,
      sourcePath: undefined,
      candidatePath,
      repositoryRoot,
      landingRoot,
      artifactRoot,
    });
    const producedPath = await variant.source.candidate.capture(context);
    if (
      path.resolve(producedPath) !== candidatePath ||
      !fs.existsSync(candidatePath)
    ) {
      throw new Error(
        `${asset.id}/${variantName}: capture producer did not create ${candidatePath}`,
      );
    }
    results.push({
      asset_id: asset.id,
      variant: variantName,
      candidate: path.relative(repositoryRoot, candidatePath),
      bytes: fs.statSync(candidatePath).size,
    });
  }
  return results;
}

function promoteSources({
  selected,
  all,
  repositoryRoot,
  landingRoot,
}) {
  const results = [];
  for (const { asset, variantName, variant } of selected) {
    if (variant.source.kind !== "captured-source") {
      if (all) {
        continue;
      }
      throw new Error(
        `${asset.id}/${variantName}: source has no captured candidate`,
      );
    }
    const candidatePath = captureCandidatePath(
      variant.source,
      repositoryRoot,
    );
    if (!fs.existsSync(candidatePath)) {
      throw new Error(
        `${asset.id}/${variantName}: missing captured candidate ${candidatePath}; run capture first`,
      );
    }
    const reviewedPath = resolveLandingPath(
      landingRoot,
      variant.source.reviewedPath,
      "Reviewed source",
    );
    fs.mkdirSync(path.dirname(reviewedPath), { recursive: true });
    fs.copyFileSync(candidatePath, reviewedPath);
    results.push({
      asset_id: asset.id,
      variant: variantName,
      candidate: path.relative(repositoryRoot, candidatePath),
      reviewed_source: variant.source.reviewedPath,
      bytes: fs.statSync(reviewedPath).size,
      sha256: sha256(reviewedPath),
    });
  }
  return results;
}

export function listVisualAssets(configuration) {
  validateVisualAssets(configuration);
  return configuration.assets.map((asset) => ({
    id: asset.id,
    variants: Object.entries(asset.variants).map(([variantName, variant]) => ({
      name: variantName,
      source_kind: variant.source.kind,
      output: variant.output,
      pipeline: variant.pipeline.id ?? "<anonymous>",
    })),
  }));
}

export async function executeVisualAssets({
  configuration,
  command,
  assetIds,
  variantName,
  all,
  repositoryRoot,
  landingRoot,
}) {
  const defaultAll = command === "check" || command === "inspect";
  const selected = selectAssetVariants(configuration, {
    assetIds,
    variantName,
    all,
    defaultAll,
  });
  const artifactRoot = path.join(landingRoot, "artifacts", "visual-assets");
  fs.mkdirSync(artifactRoot, { recursive: true });

  let details;
  if (["check", "inspect", "update"].includes(command)) {
    details = await generateVariants({
      configuration,
      selected,
      command,
      repositoryRoot,
      landingRoot,
      artifactRoot,
    });
  } else if (command === "capture") {
    details = {
      results: await captureVariants({
        selected,
        all,
        repositoryRoot,
        landingRoot,
        artifactRoot,
      }),
    };
  } else if (command === "promote-source") {
    details = {
      results: promoteSources({
        selected,
        all,
        repositoryRoot,
        landingRoot,
      }),
    };
  } else {
    throw new Error(`Unknown visual-assets command: ${command}`);
  }

  const report = {
    schema_version: 1,
    generated_at: new Date().toISOString(),
    command,
    selected_assets: [...new Set(selected.map((item) => item.asset.id))],
    selected_variant: variantName,
    all,
    ...details,
  };
  const reportPath = writeReport(artifactRoot, command, report);
  return {
    ...report,
    reportPath,
  };
}