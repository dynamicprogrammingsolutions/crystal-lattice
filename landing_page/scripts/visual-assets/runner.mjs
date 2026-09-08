import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

import { selectAssets } from "./selection.mjs";

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

function flatten(values) {
  return values.flatMap((value) =>
    Array.isArray(value) ? flatten(value) : [value],
  );
}

function writeReport(artifactRoot, command, selection, details) {
  const reportDirectory = path.join(artifactRoot, "reports");
  fs.mkdirSync(reportDirectory, { recursive: true });
  const reportPath = path.join(reportDirectory, `${command}.json`);
  const report = {
    schema_version: 1,
    generated_at: new Date().toISOString(),
    command,
    selected_assets: selection
      ? selection.assets.map((asset) => asset.id)
      : [],
    selected_variant: selection?.variantName,
    all: selection?.all ?? false,
    ...details,
  };
  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  return {
    ...report,
    reportPath,
  };
}

function createAssetContext({
  asset,
  selection,
  repositoryRoot,
  landingRoot,
  artifactRoot,
  commandCache,
}) {
  const base = {
    repositoryRoot,
    landingRoot,
    artifactRoot,
    commandCache,
    variantName: selection.variantName,
    selectionIsAll: selection.all,
    selectionExplicit: selection.explicit,

    async run(command, args, options = {}) {
      return runProcess(command, args, {
        cwd: options.cwd ?? repositoryRoot,
        env: options.env,
        stdio: options.stdio,
      });
    },

    artifactPath(...segments) {
      return path.join(artifactRoot, ...segments);
    },
  };

  return {
    ...base,
    asset,
    config: asset.config,
    metadata: asset.metadata,

    hasCommand(name) {
      return asset.hasCommand(name);
    },

    hasLifecycle(name) {
      return asset.hasLifecycle(name);
    },

    hasLifecycles(names) {
      return names.every((name) => asset.hasLifecycle(name));
    },

    runCommand(name, input) {
      return asset.runCommand(name, base, input);
    },

    runLifecycle(name, input) {
      return asset.runLifecycle(name, base, input);
    },

    requireLifecycles(names) {
      const missing = names.filter((name) => !asset.hasLifecycle(name));
      if (missing.length > 0) {
        throw new Error(
          `${asset.id} is missing lifecycle callbacks: ${missing.join(", ")}`,
        );
      }
    },

    unsupported(name) {
      if (selection.all) {
        return {
          asset_id: asset.id,
          skipped: true,
          reason: `unsupported command ${name}`,
        };
      }
      throw new Error(`${asset.id} does not support command ${name}`);
    },
  };
}

function createCommandContext({
  catalog,
  args,
  repositoryRoot,
  landingRoot,
}) {
  const artifactRoot = path.join(landingRoot, "artifacts", "visual-assets");
  fs.mkdirSync(artifactRoot, { recursive: true });
  const commandCache = new Map();
  let lastSelection;

  const context = {
    arguments: args,
    repositoryRoot,
    landingRoot,
    artifactRoot,
    commandCache,

    select(options = {}) {
      lastSelection = selectAssets(catalog, args, options);
      return {
        ...lastSelection,
        assetContexts: lastSelection.assets.map((asset) =>
          createAssetContext({
            asset,
            selection: lastSelection,
            repositoryRoot,
            landingRoot,
            artifactRoot,
            commandCache,
          }),
        ),
      };
    },

    async forEachSelected(callback, options = {}) {
      const selection = context.select(options);
      const results = [];
      for (const assetContext of selection.assetContexts) {
        results.push(await callback(assetContext, selection));
      }
      return flatten(results).filter((result) => result !== undefined);
    },

    async describeAssets() {
      const selection = {
        assets: catalog.assets,
        all: true,
        explicit: false,
        variantName: undefined,
      };
      const descriptions = [];
      for (const asset of catalog.assets) {
        const assetContext = createAssetContext({
          asset,
          selection,
          repositoryRoot,
          landingRoot,
          artifactRoot,
          commandCache,
        });
        if (assetContext.hasCommand("list")) {
          descriptions.push(await assetContext.runCommand("list"));
        } else if (assetContext.hasLifecycle("describe")) {
          descriptions.push(await assetContext.runLifecycle("describe"));
        } else {
          descriptions.push({
            id: asset.id,
            metadata: asset.metadata,
            commands: Object.keys(asset.commands),
            lifecycle: Object.keys(asset.lifecycle),
          });
        }
      }
      return descriptions;
    },

    async applyAll(prepared) {
      const effects = flatten(prepared).filter(
        (item) => item && typeof item.apply === "function",
      );
      for (const effect of effects) {
        await effect.apply();
      }
      return effects.map((effect) => effect.report).filter(Boolean);
    },

    writeReport(command, details) {
      return writeReport(
        artifactRoot,
        command,
        lastSelection,
        details,
      );
    },

    flatten,
  };

  return context;
}

export async function executeVisualAssets({
  catalog,
  command,
  args,
  repositoryRoot,
  landingRoot,
}) {
  const commandContext = createCommandContext({
    catalog,
    args,
    repositoryRoot,
    landingRoot,
  });
  return catalog.execute(command, commandContext);
}