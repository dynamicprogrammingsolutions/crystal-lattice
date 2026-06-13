import { readFileSync } from "node:fs";
import { dirname, isAbsolute, join, normalize } from "node:path";
import { load } from "js-yaml";
import { unified } from "unified";
import remarkParse from "remark-parse";
import { toHast } from "mdast-util-to-hast";
import { toHtml } from "hast-util-to-html";
import { toString } from "mdast-util-to-string";
import type {
  Heading,
  Html,
  List,
  ListItem,
  Paragraph,
  PhrasingContent,
  Root,
  RootContent,
} from "mdast";
import type { MarkdownDocument } from "./pageTypes";

const contentRoot = join(process.cwd(), "src", "content");
const pageContentRoot = join(contentRoot, "pages");
const markdownParser = unified().use(remarkParse);

export function loadMarkdown(source: string): MarkdownDocument {
  const sourcePath = resolveContentPath(source);
  const parsed = parseFrontmatter(readFileSync(sourcePath, "utf8"));
  return {
    sourcePath,
    frontmatter: parsed.frontmatter,
    ast: markdownParser.parse(parsed.body) as Root,
  };
}

export function headingText(node: Heading): string {
  return toString(node);
}

export function isHeading(node: RootContent, depth?: number): node is Heading {
  return node.type === "heading" && (depth === undefined || node.depth === depth);
}

export function isHtmlComment(node: RootContent): node is Html {
  return node.type === "html" && node.value.trim().startsWith("<!--");
}

export function isParagraph(node: RootContent): node is Paragraph {
  return node.type === "paragraph";
}

export function isList(node: RootContent): node is List {
  return node.type === "list";
}

export function renderInlineHtml(children: PhrasingContent[]): string {
  return renderNodesAsHtml(children);
}

export function renderListItemHtml(item: ListItem): string {
  if (item.children.length === 1 && item.children[0]?.type === "paragraph") {
    return renderInlineHtml(item.children[0].children);
  }
  return renderNodesAsHtml(item.children);
}

function renderNodesAsHtml(children: RootContent[] | PhrasingContent[]): string {
  const hast = toHast(
    { type: "root", children } as Root,
    { allowDangerousHtml: true },
  );
  return toHtml(hast, { allowDangerousHtml: true });
}

function parseFrontmatter(source: string): {
  frontmatter: Record<string, unknown>;
  body: string;
} {
  if (!source.startsWith("---\n")) {
    return { frontmatter: {}, body: source };
  }

  const closingMarker = source.indexOf("\n---", 4);
  if (closingMarker === -1) {
    return { frontmatter: {}, body: source };
  }

  const frontmatterSource = source.slice(4, closingMarker);
  const bodyStart = source.indexOf("\n", closingMarker + 4);
  const body = bodyStart === -1 ? "" : source.slice(bodyStart + 1);
  const parsed = load(frontmatterSource);

  return {
    frontmatter:
      parsed && typeof parsed === "object"
        ? (parsed as Record<string, unknown>)
        : {},
    body,
  };
}

function resolveContentPath(source: string): string {
  if (source.startsWith("/")) {
    return normalize(join(contentRoot, source.slice(1)));
  }
  if (isAbsolute(source)) {
    return source;
  }
  return normalize(join(dirname(join(pageContentRoot, "page.yaml")), source));
}
