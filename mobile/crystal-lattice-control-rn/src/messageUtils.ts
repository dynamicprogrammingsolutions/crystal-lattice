import type { ApiMessage } from './api';

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
