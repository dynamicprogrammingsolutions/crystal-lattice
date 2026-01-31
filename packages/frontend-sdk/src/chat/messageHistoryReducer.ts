import type { Event } from '../types/events';
import type { ApiMessage, IndexedMessage } from '../types/messages';

function isApiMessage(value: unknown): value is ApiMessage {
  if (!value || typeof value !== 'object') return false;
  const role = (value as any).role;
  const content = (value as any).content;
  if (typeof role !== 'string' || typeof content !== 'string') return false;

  const metadata = (value as any).metadata;
  if (metadata != null && typeof metadata !== 'object') return false;

  return true;
}

function getLastIndex(messages: IndexedMessage[]): number {
  if (messages.length === 0) return -1;
  const lastIndex = messages[messages.length - 1]?.index;
  if (typeof lastIndex === 'number' && Number.isFinite(lastIndex)) {
    return lastIndex;
  }
  return messages.length - 1;
}

function appendMessages(messages: IndexedMessage[], newMessages: ApiMessage[]): IndexedMessage[] {
  if (newMessages.length === 0) return messages;

  const baseIndex = getLastIndex(messages);
  const appended: IndexedMessage[] = [];
  for (let offset = 0; offset < newMessages.length; offset += 1) {
    appended.push({ index: baseIndex + offset + 1, message: newMessages[offset] });
  }
  return [...messages, ...appended];
}

export function reduceMessageHistory(messages: IndexedMessage[], event: Event): IndexedMessage[] {
  const type = (event as any).type;

  if (type === 'final' || type === 'tool_results') {
    const raw = (event as any).messages;
    const newMessages = Array.isArray(raw) ? raw.filter(isApiMessage) : [];
    if (newMessages.length === 0) return messages;
    return appendMessages(messages, newMessages);
  }

  if (type === 'message_appended') {
    const rawMessage = (event as any).message;
    if (isApiMessage(rawMessage)) {
      return appendMessages(messages, [rawMessage]);
    }

    const role = (event as any).role;
    const content = (event as any).content;
    if (typeof role !== 'string' || typeof content !== 'string') {
      return messages;
    }

    const rawMetadata = (event as any).metadata;
    const metadata = rawMetadata == null || typeof rawMetadata === 'object' ? rawMetadata : null;
    return appendMessages(messages, [{ role, content, metadata }]);
  }

  return messages;
}
