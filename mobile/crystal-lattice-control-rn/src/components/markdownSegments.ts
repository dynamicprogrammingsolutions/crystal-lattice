import MarkdownIt from 'markdown-it';

export type MarkdownSegment =
  | {
      type: 'markdown';
      markdown: string;
    }
  | {
      type: 'code';
      language: string;
      content: string;
    };

const markdownParser = new MarkdownIt({
  html: false,
  linkify: false,
  typographer: false,
});

function lineStartOffsets(text: string): number[] {
  const offsets = [0];
  for (let index = 0; index < text.length; index += 1) {
    if (text[index] === '\n') {
      offsets.push(index + 1);
    }
  }
  return offsets;
}

function offsetForLine(offsets: number[], line: number, textLength: number): number {
  if (line < 0) return 0;
  return offsets[line] ?? textLength;
}

function languageFromInfo(info: unknown): string {
  if (typeof info !== 'string') return 'plaintext';
  const language = info.trim().split(/\s+/, 1)[0];
  return language || 'plaintext';
}

export function splitMarkdownIntoSegments(text: string): MarkdownSegment[] {
  if (!text) return [];

  const tokens = markdownParser.parse(text, {});
  const offsets = lineStartOffsets(text);
  const codeTokens = tokens
    .filter((token) => {
      return (
        (token.type === 'fence' || token.type === 'code_block') &&
        Array.isArray(token.map) &&
        token.map.length === 2
      );
    })
    .map((token) => {
      const [startLine, endLine] = token.map as [number, number];
      return {
        token,
        startOffset: offsetForLine(offsets, startLine, text.length),
        endOffset: offsetForLine(offsets, endLine, text.length),
      };
    })
    .filter((entry) => entry.endOffset > entry.startOffset)
    .sort((a, b) => a.startOffset - b.startOffset);

  if (codeTokens.length === 0) {
    return [{ type: 'markdown', markdown: text }];
  }

  const segments: MarkdownSegment[] = [];
  let cursor = 0;

  for (const entry of codeTokens) {
    if (entry.startOffset < cursor) continue;

    const markdown = text.slice(cursor, entry.startOffset);
    if (markdown.trim().length > 0) {
      segments.push({ type: 'markdown', markdown });
    }

    segments.push({
      type: 'code',
      language: entry.token.type === 'fence' ? languageFromInfo(entry.token.info) : 'plaintext',
      content: entry.token.content,
    });
    cursor = entry.endOffset;
  }

  const trailingMarkdown = text.slice(cursor);
  if (trailingMarkdown.trim().length > 0) {
    segments.push({ type: 'markdown', markdown: trailingMarkdown });
  }

  return segments;
}