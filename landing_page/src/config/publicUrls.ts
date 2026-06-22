export const DEFAULT_SITE_URL = "https://crystallattice.dev";
export const DEFAULT_DOCS_URL = "https://docs.crystallattice.dev";

function trimTrailingSlash(url: string): string {
  return url.replace(/\/+$/, "");
}

export const siteUrl = trimTrailingSlash(
  import.meta.env.PUBLIC_CRYSTAL_LATTICE_SITE_URL ?? DEFAULT_SITE_URL,
);

export const docsUrl = trimTrailingSlash(
  import.meta.env.PUBLIC_CRYSTAL_LATTICE_DOCS_URL ?? DEFAULT_DOCS_URL,
);

export function resolvePublicUrlPlaceholders(value: string): string {
  return value
    .replaceAll("$siteUrl", siteUrl)
    .replaceAll("$docsUrl", docsUrl);
}