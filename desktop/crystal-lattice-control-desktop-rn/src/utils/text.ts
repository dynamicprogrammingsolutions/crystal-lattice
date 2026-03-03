export function normalizeInlineText(text: string): string {
  return String(text ?? '').replace(/\s+/g, ' ').trim();
}

export function truncateByChars(text: string, maxChars: number): string {
  const normalized = normalizeInlineText(text);
  if (!normalized) return '';
  if (!Number.isFinite(maxChars) || maxChars <= 0) return '';
  if (normalized.length <= maxChars) return normalized;
  if (maxChars <= 3) return '.'.repeat(Math.max(1, Math.floor(maxChars)));
  return `${normalized.slice(0, Math.max(0, maxChars - 3))}...`;
}
