import { readFileSync } from "node:fs";
import { join } from "node:path";
import { load } from "js-yaml";
import type { PageDocument } from "./pageTypes";
import {
  sessionActionsPreviewAsset,
  sessionActionsPreviewEnabled,
  readSessionActionsRecipe,
} from "../../scripts/visual-assets/session-actions-preview.mjs";

const pagesDir = join(process.cwd(), "src", "content", "pages");

export function loadPage(name: string): PageDocument {
  const path = join(pagesDir, `${name}.yaml`);
  const parsed = load(readFileSync(path, "utf8"));
  if (!isPageDocument(parsed)) {
    throw new Error(`Invalid page content document: ${path}`);
  }
  if (!sessionActionsPreviewEnabled || name !== "home") return parsed;
  const previewAsset = sessionActionsPreviewAsset(readSessionActionsRecipe(process.cwd()));
  return {
    ...parsed,
    sections: parsed.sections.map(section => section.type !== "featureShowcase" ? section : ({
      ...section,
      items: section.items?.map(item => item.id !== "feature-plugins" ? item : ({
        ...item,
        media: {
          ...item.media,
          assets: item.media?.assets?.map((asset, index) =>
            index === 0 ? { ...asset, ...previewAsset } : asset),
        },
      })),
    })),
  };
}

function isPageDocument(value: unknown): value is PageDocument {
  if (!value || typeof value !== "object") {
    return false;
  }
  const sections = (value as { sections?: unknown }).sections;
  return (
    Array.isArray(sections) &&
    sections.every(
      (section) =>
        section &&
        typeof section === "object" &&
        typeof (section as { type?: unknown }).type === "string",
    )
  );
}
