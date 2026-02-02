import type { ApiMessage } from '../types/messages';

export function selectDisplayContent(message: ApiMessage): string {
  const metadata = message.metadata || {};
  const display = (metadata as any).display;
  if (display && typeof display === 'object' && display.type === 'text') {
    const content = (display as any).content;
    if (typeof content === 'string' && content.trim()) {
      return content;
    }
  }

  if (typeof message.content === 'string' && message.content.trim()) {
    return message.content;
  }

  return '';
}

/**
 * Extract the single-line preview content from a tool message's display metadata.
 *
 * Returns the `metadata.display.single_line` field if available, otherwise `null`.
 * Intended for compact/collapsed tool-result views.
 */
export function selectSingleLineContent(message: ApiMessage): string | null {
  const metadata = message.metadata || {};
  const display = (metadata as any).display;
  if (display && typeof display === 'object') {
    const singleLine = (display as any).single_line;
    if (typeof singleLine === 'string' && singleLine.trim()) {
      return singleLine;
    }
  }
  return null;
}
