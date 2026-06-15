import type { PageDocument } from "../content/pageTypes";
import { loadMarkdown } from "../content/markdown";
import { resolvePublicUrlPlaceholders } from "../config/publicUrls";
import { sectionDefinitionByType } from "./registry";

export function preparePage(page: PageDocument): PageDocument {
  const prepared = {
    ...page,
    sections: page.sections.flatMap((section) => {
      const definition = sectionDefinitionByType.get(section.type);
      if (!definition) {
        return [section];
      }
      return [definition.prepare?.(section, { loadMarkdown }) ?? section];
    }),
  };
  return resolvePublicUrlValues(prepared) as PageDocument;
}

function resolvePublicUrlValues(value: unknown): unknown {
  if (typeof value === "string") {
    return resolvePublicUrlPlaceholders(value);
  }
  if (Array.isArray(value)) {
    return value.map((item) => resolvePublicUrlValues(item));
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [
        key,
        resolvePublicUrlValues(item),
      ]),
    );
  }
  return value;
}
