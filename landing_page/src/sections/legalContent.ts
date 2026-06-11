import LegalContent from "../components/LegalContent.astro";
import {
  headingText,
  isHeading,
  isList,
  isParagraph,
  renderInlineHtml,
  renderListItemHtml,
} from "../content/markdown";
import type { SectionPrepareContext } from "../content/pageTypes";

type LegalBlock =
  | { type: "paragraph"; html: string }
  | { type: "list"; items: string[] };

type LegalSection = {
  title: string;
  blocks: LegalBlock[];
};

export const legalContentSection = {
  type: "legalContent",
  Component: LegalContent,
  prepare(section: Record<string, unknown> & { type: string }, context: SectionPrepareContext) {
    if (typeof section.source !== "string") {
      return section;
    }

    const markdown = context.loadMarkdown(section.source);
    const legalSections: LegalSection[] = [];
    let current: LegalSection | undefined;

    for (const node of markdown.ast.children) {
      if (isHeading(node, 2)) {
        current = { title: headingText(node), blocks: [] };
        legalSections.push(current);
        continue;
      }

      if (!current) {
        continue;
      }

      if (isParagraph(node)) {
        current.blocks.push({
          type: "paragraph",
          html: renderInlineHtml(node.children),
        });
        continue;
      }

      if (isList(node)) {
        current.blocks.push({
          type: "list",
          items: node.children.map((item) => renderListItemHtml(item)),
        });
      }
    }

    return {
      ...section,
      label: textValue(markdown.frontmatter.label, section.label),
      title: textValue(markdown.frontmatter.title, section.title),
      meta: textValue(markdown.frontmatter.meta, section.meta),
      sections: legalSections,
    };
  },
} as const;

function textValue(value: unknown, fallback: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  return typeof fallback === "string" ? fallback : "";
}
