import path from "node:path";
import { fileURLToPath } from "node:url";

import catalog from "../../visual_assets/config.mjs";
import { executeVisualAssets } from "./runner.mjs";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const landingRoot = path.resolve(scriptDirectory, "..", "..");
const repositoryRoot = path.resolve(landingRoot, "..");
function usage() {
  return `Usage:
  node scripts/visual-assets/cli.mjs <${catalog.commandNames.join("|")}> [arguments]`;
}

async function main() {
  const [command, ...args] = process.argv.slice(2);
  if (!catalog.hasCommand(command)) {
    throw new Error(usage());
  }

  const result = await executeVisualAssets({
    catalog,
    command,
    args,
    repositoryRoot,
    landingRoot,
  });
  if (result?.kind === "list") {
    for (const asset of result.assets) {
      console.log(asset.id);
      for (const variant of asset.variants ?? []) {
        console.log(
          `  ${variant.name}: ${variant.source_kind} -> ${variant.output} (${variant.build})`,
        );
      }
      if (!asset.variants) {
        console.log(
          `  commands: ${(asset.commands ?? []).join(", ") || "-"}`,
        );
        console.log(
          `  lifecycle: ${(asset.lifecycle ?? []).join(", ") || "-"}`,
        );
      }
    }
    return;
  }

  const byteTotal = (result.results ?? []).reduce(
    (sum, result) => sum + (result.bytes ?? 0),
    0,
  );
  console.log(
    `${command} processed ${result.results?.length ?? 0} results (${byteTotal} bytes)`,
  );
  if (result.reportPath) {
    console.log(
      `report: ${path.relative(landingRoot, result.reportPath)}`,
    );
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});