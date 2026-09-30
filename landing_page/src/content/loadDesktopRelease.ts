import { readFileSync } from "node:fs";
import { join } from "node:path";
import { load } from "js-yaml";

export type DesktopRelease = {
  product: string;
  version: string;
  buildNumber: number;
  minimumMacos: string;
  architectures: string[];
  dmg: {
    filename: string;
    url: string;
    sha256: string;
  };
};

const desktopReleasePath = join(
  process.cwd(),
  "src",
  "content",
  "releases",
  "desktop.yaml",
);

export function loadDesktopRelease(): DesktopRelease {
  const parsed = load(readFileSync(desktopReleasePath, "utf8"));
  if (!isDesktopRelease(parsed)) {
    throw new Error(`Invalid desktop release metadata: ${desktopReleasePath}`);
  }
  return parsed;
}

function isDesktopRelease(value: unknown): value is DesktopRelease {
  if (!value || typeof value !== "object") {
    return false;
  }

  const release = value as Partial<DesktopRelease>;
  return (
    typeof release.product === "string" &&
    typeof release.version === "string" &&
    Number.isInteger(release.buildNumber) &&
    typeof release.minimumMacos === "string" &&
    Array.isArray(release.architectures) &&
    release.architectures.every((architecture) => typeof architecture === "string") &&
    !!release.dmg &&
    typeof release.dmg.filename === "string" &&
    typeof release.dmg.url === "string" &&
    typeof release.dmg.sha256 === "string"
  );
}