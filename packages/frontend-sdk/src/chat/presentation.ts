import type { ApiMessage, IndexedMessage } from '../types/messages';
import type { UiSchemaElement } from '../types/uiSchema';
import { extractByPath, renderTemplate } from '../utils/uiSchema';
import type { StreamingRow } from './chatController';

export function selectLastAssistantMessage(options: {
  messages: IndexedMessage[];
  streamingRow: StreamingRow | null;
}): ApiMessage | null {
  const { messages, streamingRow } = options;

  if (streamingRow && (streamingRow.content || streamingRow.reasoning)) {
    return {
      role: 'assistant',
      content: streamingRow.content,
      metadata: streamingRow.metadata || {},
    };
  }

  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const message = messages[i].message;
    if ((message.role || 'unknown') === 'assistant') {
      return message;
    }
  }

  return null;
}

export function deriveChatStatusBarParts(options: {
  sessionId: string;
  sessionAgentId?: string | null;
  availableAgents?: string[];
  lastAssistantMessage: ApiMessage | null;
  statusBarElements: UiSchemaElement[];
}): string[] {
  const { sessionId, sessionAgentId, availableAgents, lastAssistantMessage, statusBarElements } =
    options;
  const parts: string[] = [];

  const agentLabel =
    sessionAgentId &&
    sessionAgentId !== 'default' &&
    Array.isArray(availableAgents) &&
    availableAgents.includes(sessionAgentId)
      ? sessionAgentId
      : null;
  if (agentLabel) {
    parts.push(`Agent: ${agentLabel}`);
  }

  parts.push(`Session: ${sessionId.slice(0, 8)}`);
  if (!lastAssistantMessage || !statusBarElements.length) {
    return parts;
  }

  statusBarElements.forEach((el) => {
    if (!el || el.ui_type !== 'status_bar') return;
    const value = extractByPath(lastAssistantMessage, el.data);
    if (value === undefined || value === null || value === '') return;
    const text = renderTemplate(el.template ?? '{{data}}', value);
    if (text) parts.push(text);
  });

  return parts;
}
