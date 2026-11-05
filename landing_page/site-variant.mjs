import path from "node:path";

const supportedVariants = new Set(["production", "staging"]);

export function resolveSiteVariant(
  value = process.env.CRYSTAL_LATTICE_SITE_VARIANT,
) {
  const variant = value?.trim() || "production";
  if (!supportedVariants.has(variant)) {
    throw new Error(
      `CRYSTAL_LATTICE_SITE_VARIANT must be production or staging, got ${JSON.stringify(variant)}`,
    );
  }
  return variant;
}

export const siteVariant = resolveSiteVariant();
export const isProductionSite = siteVariant === "production";
export const isStagingSite = siteVariant === "staging";

export function siteRoot(root = process.cwd()) {
  return path.join(root, "sites", siteVariant);
}

export function siteOutputDirectory(root = process.cwd()) {
  return path.join(root, "dist", siteVariant);
}