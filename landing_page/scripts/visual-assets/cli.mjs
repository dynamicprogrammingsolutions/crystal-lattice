import path from "node:path";
import { fileURLToPath } from "node:url";

import configuration from "../../visual_assets/config.mjs";
import {
  executeVisualAssets,
  listVisualAssets,
} from "./runner.mjs";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const landingRoot = path.resolve(scriptDirectory, "..", "..");
const repositoryRoot = path.resolve(landingRoot, "..");
const supportedCommands = new Set([
  "capture",
  "check",
  "inspect",
  "list",
  "promote-source",
  "update",
]);

function usage() {
  return `Usage:
  node scripts/visual-assets/cli.mjs list
  node scripts/visual-assets/cli.mjs <capture|check|inspect|promote-source|update> [asset-id ...] [--variant name] [--all]`;
}

function parseArguments(args) {
  const options = {
    assetIds: [],
    all: false,
    variantName: undefined,
  };
  for (let index = 0; index < args.length; index += 1) {
    const current = args[index];
    if (current === "--all") {
      options.all = true;
    } else if (current === "--variant") {
      const value = args[index + 1];
      if (!value) {
        throw new Error("--variant requires a value");
      }
      options.variantName = value;
      index += 1;
    } else if (current.startsWith("--")) {
      throw new Error(`Unknown option: ${current}`);
    } else {
      options.assetIds.push(current);
    }
  }
  return options;
}

async function main() {
  const [command, ...args] = process.argv.slice(2);
  if (!supportedCommands.has(command)) {
    throw new Error(usage());
  }

  if (command === "list") {
    for (const asset of listVisualAssets(configuration)) {
      console.log(asset.id);
      for (const variant of asset.variants) {
        console.log(
          `  ${variant.name}: ${variant.source_kind} -> ${variant.output} (${variant.pipeline})`,
        );
      }
    }
    return;
  }

  const options = parseArguments(args);
  const report = await executeVisualAssets({
    configuration,
    command,
    ...options,
    repositoryRoot,
    landingRoot,
  });
  const byteTotal = report.results.reduce(
    (sum, result) => sum + (result.bytes ?? 0),
    0,
  );
  console.log(
    `${command} processed ${report.results.length} variants (${byteTotal} bytes)`,
  );
  console.log(`report: ${path.relative(landingRoot, report.reportPath)}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});