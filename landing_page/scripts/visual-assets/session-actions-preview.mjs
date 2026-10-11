import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { proofBatchRecipes } from "../../visual_assets/proof-batch-recipes.mjs";
import { vibePreviewAsset } from "./vibe-composition.mjs";
import { createHash } from "node:crypto";
export { vibePreviewAsset };

// Retain the list candidate for possible workspace proof, but the user selected
// only Session actions and Message actions for the plugin highlight.
export const proofBatchPreviewRecipes = proofBatchRecipes.filter(
  recipe => !["homepage-session-list", "homepage-cost-report", "homepage-chatgpt-usage"].includes(recipe.id),
);
export const proofBatchPreviewEnabled = process.env.CRYSTAL_PROOF_BATCH_PREVIEW === "1";
export function proofRecipeReady(recipe, landingRoot = fileURLToPath(new URL("../../", import.meta.url))) {
  const directory = path.join(landingRoot, recipe.candidateDirectory);
  const manifestFile = path.join(directory, "manifest.json");
  if (!fs.existsSync(manifestFile)) return false;
  const manifest = JSON.parse(fs.readFileSync(manifestFile, "utf8"));
  const config = recipe.configFile ?? "landing_page/visual_assets/runtime/proof-batch/config.json";
  const repositoryRoot = path.resolve(landingRoot, "..");
  const actual = createHash("sha256").update(fs.readFileSync(path.join(repositoryRoot, config))).digest("hex");
  return manifest.sourceHashes[config] === actual
    && ["wide.webp", "wide-dark.webp", "compact.webp", "compact-dark.webp"]
      .every(file => fs.existsSync(path.join(directory, file)));
}
export function readSessionActionsRecipe(landingRoot = fileURLToPath(new URL("../../", import.meta.url))) {
  return JSON.parse(fs.readFileSync(
    path.join(landingRoot, "visual_assets/session-actions-composition.json"), "utf8",
  ));
}
export const sessionActionsPreviewEnabled =
  process.env.CRYSTAL_SESSION_ACTIONS_PREVIEW === "1" || proofBatchPreviewEnabled;

export function proofBatchPreviewAsset(recipe) {
  return {
    src: `${recipe.previewPrefix}/wide.webp`,
    srcDark: `${recipe.previewPrefix}/wide-dark.webp`,
    srcCompact: `${recipe.previewPrefix}/compact.webp`,
    srcCompactDark: `${recipe.previewPrefix}/compact-dark.webp`,
    width: 2400, height: 1350, widthCompact: 1200, heightCompact: 1600,
    alt: recipe.alt,
  };
}

export function proofBatchPreviewFor(feature, slot, landingRoot) {
  const recipe = proofBatchPreviewRecipes.find(item => item.feature === feature && item.slot === slot);
  return recipe && proofRecipeReady(recipe, landingRoot) ? {
    asset: proofBatchPreviewAsset(recipe),
    sampleData: recipe.sampleData,
    sampleNotice: recipe.sampleNotice ?? "Sample data.",
  } : undefined;
}

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
        if (proofBatchPreviewEnabled) {
          const vibeDestination = path.join(fileURLToPath(dir), "__preview/vibe");
          fs.mkdirSync(vibeDestination, { recursive: true });
          for (const filename of ["portrait.webp", "portrait-dark.webp"]) {
            fs.copyFileSync(path.join(root, "artifacts/visual-assets/homepage-vibe-workflow", filename),
              path.join(vibeDestination, filename));
          }
          for (const recipe of proofBatchPreviewRecipes) {
            if (!proofRecipeReady(recipe, root)) continue;
            const destination = path.join(fileURLToPath(dir), recipe.previewPrefix);
            fs.mkdirSync(destination, { recursive: true });
            for (const shape of ["wide", "compact"]) for (const suffix of ["", "-dark"]) {
              const name = `${shape}${suffix}.webp`;
              fs.copyFileSync(path.join(root, recipe.candidateDirectory, name), path.join(destination, name));
            }
          }
        }
      },
    },
  };
}