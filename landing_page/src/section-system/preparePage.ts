import type { PageDocument } from "../content/pageTypes";
import { loadMarkdown } from "../content/markdown";
import { sectionDefinitionByType } from "./registry";

export function preparePage(page: PageDocument): PageDocument {
  return {
    ...page,
    sections: page.sections.flatMap((section) => {
      const definition = sectionDefinitionByType.get(section.type);
      if (!definition) {
        return [section];
      }
      const prepared = definition.prepare?.(section, { loadMarkdown }) ?? section;
      return [prepared as PageDocument["sections"][number]];
    }),
  };
}
