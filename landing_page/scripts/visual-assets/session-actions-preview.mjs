import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export function readSessionActionsRecipe(landingRoot = fileURLToPath(new URL("../../", import.meta.url))) {
  return JSON.parse(fs.readFileSync(
    path.join(landingRoot, "visual_assets/session-actions-composition.json"), "utf8",
  ));
}
export const sessionActionsPreviewEnabled =
  process.env.CRYSTAL_SESSION_ACTIONS_PREVIEW === "1";

export function sessionActionsPreviewAsset(recipe) {
  const prefix = recipe.previewPrefix;
  return {
    src: `${prefix}/wide.webp`,
    srcDark: `${prefix}/wide-dark.webp`,
    srcCompact: `${prefix}/compact.webp`,
    srcCompactDark: `${prefix}/compact-dark.webp`,
    width: recipe.layouts.wide.width,
    height: recipe.layouts.wide.height,
    widthCompact: recipe.layouts.compact.width,
    heightCompact: recipe.layouts.compact.height,
    alt: "In the Desktop session menu, session-title-app adds Edit title, generate-title-app adds Generate title, and summarize-range-app adds Summarize range.",
  };
}

export function sessionActionsPreviewIntegration() {
  const sessionActionsRecipe = readSessionActionsRecipe();
  return {
    name: "session-actions-local-preview",
    hooks: {
      "astro:build:done": ({ dir }) => {
        const root = fileURLToPath(new URL("../../", import.meta.url));
        const destination = path.join(fileURLToPath(dir), sessionActionsRecipe.previewPrefix);
        fs.mkdirSync(destination, { recursive: true });
        for (const shape of Object.keys(sessionActionsRecipe.layouts)) {
          for (const suffix of ["", "-dark"]) {
            const name = `${shape}${suffix}.webp`;
            fs.copyFileSync(
              path.join(root, sessionActionsRecipe.candidateDirectory, name),
              path.join(destination, name),
            );
          }
        }
      },
    },
  };
}