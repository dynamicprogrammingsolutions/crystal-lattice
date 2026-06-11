import type { Root } from "mdast";

export type MarkdownDocument = {
  sourcePath: string;
  frontmatter: Record<string, unknown>;
  ast: Root;
};

export type SectionPrepareContext = {
  loadMarkdown: (source: string) => MarkdownDocument;
};

export type SectionDefinition = {
  type: string;
  Component: unknown;
  prepare?: (
    section: Record<string, unknown> & { type: string },
    context: SectionPrepareContext,
  ) => Record<string, unknown> & { type: string };
};

export type PageDocument = {
  seo?: {
    title?: string;
    description?: string;
  };
  nav?: Array<{
    label: string;
    href: string;
  }>;
  sections: Array<Record<string, unknown> & { type: string }>;
};
