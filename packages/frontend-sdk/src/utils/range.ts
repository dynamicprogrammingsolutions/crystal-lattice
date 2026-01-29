export function parseOptionalInt(text: string): number | undefined {
  const trimmed = text.trim();
  if (!trimmed) return undefined;
  const parsed = parseInt(trimmed, 10);
  return Number.isNaN(parsed) ? undefined : parsed;
}

export function parseIndexRangeText(options: {
  startText: string;
  endText: string;
}): { start?: number; end?: number } {
  const start = parseOptionalInt(options.startText);
  const end = parseOptionalInt(options.endText);
  return { start, end };
}
