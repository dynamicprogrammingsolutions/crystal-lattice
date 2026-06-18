import Features from "../components/Features.astro";
import {
  headingText,
  isHeading,
  isHtmlComment,
  isParagraph,
  renderInlineHtml,
} from "../content/markdown";
import type { SectionPrepareContext } from "../content/pageTypes";

type FeatureItem = {
  icon?: string;
  title: string;
  descHtml: string;
};

export const featuresSection = {
  type: "features",
  Component: Features,
  prepare(section: Record<string, unknown> & { type: string }, context: SectionPrepareContext) {
    if (typeof section.source !== "string") {
      return section;
    }

    const markdown = context.loadMarkdown(section.source);
    const items: FeatureItem[] = [];
    let current: FeatureItem | undefined;

    for (const node of markdown.ast.children) {
      if (isHeading(node, 2)) {
        current = {
          title: headingText(node),
          descHtml: "",
        };
        items.push(current);
        continue;
      }

      if (!current) {
        continue;
      }

      if (isHtmlComment(node)) {
        const icon = parseIconComment(node.value);
        if (icon) {
          current.icon = icon;
        }
        continue;
      }

      if (isParagraph(node)) {
        const paragraph = renderInlineHtml(node.children);
        current.descHtml = current.descHtml
          ? `${current.descHtml} ${paragraph}`
          : paragraph;
      }
    }

    return {
      ...section,
      eyebrow: textValue(markdown.frontmatter.eyebrow, section.eyebrow),
      title: textValue(markdown.frontmatter.title, section.title),
      body: textValue(markdown.frontmatter.body, section.body),
      items,
    };
  },
} as const;

function parseIconComment(value: string): string | undefined {
  const match = value.match(/<!--\s*icon:\s*([a-zA-Z0-9_-]+)\s*-->/);
  return match?.[1];
}

function textValue(value: unknown, fallback: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  return typeof fallback === "string" ? fallback : "";
}
