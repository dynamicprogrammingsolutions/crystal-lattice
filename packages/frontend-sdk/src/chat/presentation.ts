import type { ApiMessage, IndexedMessage } from '../types/messages';
import type { UiSchemaElement } from '../types/uiSchema';
import { extractByPath, renderTemplate, formatValueForElement, evaluateCondition } from '../utils/uiSchema';
import type { StreamingRow } from './chatController';

export function selectLastAssistantMessage(options: {
  messages: IndexedMessage[];
  streamingRow: StreamingRow | null;
}): ApiMessage | null {
  const { messages, streamingRow } = options;

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

  parts.push(`Session: ${sessionId}`);
  if (!lastAssistantMessage || !statusBarElements.length) {
    return parts;
  }

  statusBarElements.forEach((el) => {
    if (!el || el.ui_type !== 'status_bar') return;
    const condition = (el as any).condition;
    if (condition != null && !evaluateCondition(condition, lastAssistantMessage)) return;
    const rawValue = extractByPath(lastAssistantMessage, el.data);
    const valueForTemplate = formatValueForElement(el, rawValue);
    if (valueForTemplate === undefined || valueForTemplate === null || valueForTemplate === '') return;
    const text = renderTemplate(el.template ?? '{{data}}', valueForTemplate);
    if (text) parts.push(text);
  });

  return parts;
}
