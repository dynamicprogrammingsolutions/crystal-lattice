import { readFileSync } from "node:fs";
import { join } from "node:path";
import { load } from "js-yaml";
import type { PageDocument } from "./pageTypes";

const pagesDir = join(process.cwd(), "src", "content", "pages");

export function loadPage(name: string): PageDocument {
  const path = join(pagesDir, `${name}.yaml`);
  const parsed = load(readFileSync(path, "utf8"));
  if (!isPageDocument(parsed)) {
    throw new Error(`Invalid page content document: ${path}`);
  }
  return parsed;
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
