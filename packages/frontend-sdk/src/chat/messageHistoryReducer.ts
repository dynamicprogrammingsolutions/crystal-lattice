import type { Event } from '../types/events';
import type { ApiMessage, IndexedMessage } from '../types/messages';

export type ReduceResult =
  | { kind: 'ok'; messages: IndexedMessage[] }
  | { kind: 'noop'; messages: IndexedMessage[] }
  | { kind: 'dirty'; messages: IndexedMessage[]; reason: string };

function isApiMessage(value: unknown): value is ApiMessage {
  if (!value || typeof value !== 'object') return false;
  const role = (value as any).role;
  const content = (value as any).content;
  if (typeof role !== 'string' || typeof content !== 'string') return false;

  const metadata = (value as any).metadata;
  if (metadata != null && typeof metadata !== 'object') return false;

  return true;
}

function isFiniteInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && Number.isInteger(value);
}

function reindexMessages(messages: IndexedMessage[]): IndexedMessage[] {
  return messages.map((item, idx) => ({ index: idx, message: item.message }));
}

function validateNewMessages(raw: unknown): ApiMessage[] | null {
  if (!Array.isArray(raw)) {
    return null;
  }
  if (raw.length === 0) {
    return [];
  }
  if (!raw.every(isApiMessage)) {
    return null;
  }
  return raw;
}

/**
 * Index-based reducer for session message history.
 *
 * If the event cannot be applied safely (missing required fields, index
 * mismatch, out-of-bounds mutation), returns `dirty` and leaves the existing
 * history unchanged.
 */
export function reduceMessageHistory(messages: IndexedMessage[], event: Event): ReduceResult {
  const type = (event as any).type;

  if (type === 'final' || type === 'tool_results') {
    const startIndex = (event as any).start_index;
    if (!isFiniteInteger(startIndex) || startIndex < 0) {
      return { kind: 'dirty', messages, reason: `${type}: missing/invalid start_index` };
    }
    if (startIndex !== messages.length) {
      return {
        kind: 'dirty',
        messages,
        reason: `${type}: start_index ${startIndex} does not match local length ${messages.length}`,
      };
    }

    const newMessages = validateNewMessages((event as any).messages);
    if (newMessages == null) {
      return { kind: 'dirty', messages, reason: `${type}: missing/invalid messages payload` };
    }
    if (newMessages.length === 0) {
      return { kind: 'noop', messages };
    }

    const appended = newMessages.map((message, offset) => ({
      index: startIndex + offset,
      message,
    }));
    return { kind: 'ok', messages: reindexMessages([...messages, ...appended]) };
  }

  if (type === 'message_appended') {
    const index = (event as any).index;
    if (!isFiniteInteger(index) || index < 0) {
      return { kind: 'dirty', messages, reason: 'message_appended: missing/invalid index' };
    }
    if (index !== messages.length) {
      return {
        kind: 'dirty',
        messages,
        reason: `message_appended: index ${index} does not match local length ${messages.length}`,
      };
    }

    const rawMessage = (event as any).message;
    if (!isApiMessage(rawMessage)) {
      return { kind: 'dirty', messages, reason: 'message_appended: missing/invalid message' };
    }

    return {
      kind: 'ok',
      messages: reindexMessages([...messages, { index, message: rawMessage }]),
    };
  }

  if (type === 'message_modified') {
    const index = (event as any).index;
    if (!isFiniteInteger(index) || index < 0) {
      return { kind: 'dirty', messages, reason: 'message_modified: missing/invalid index' };
    }
    if (index >= messages.length) {
      return {
        kind: 'dirty',
        messages,
        reason: `message_modified: index ${index} out of bounds for length ${messages.length}`,
      };
    }

    const rawMessage = (event as any).message;
    if (!isApiMessage(rawMessage)) {
      return { kind: 'dirty', messages, reason: 'message_modified: missing/invalid message' };
    }

    const next = messages.slice();
    next[index] = { index, message: rawMessage };
    return { kind: 'ok', messages: reindexMessages(next) };
  }

  if (type === 'messages_deleted') {
    const rawIndices = (event as any).indices;
    if (!Array.isArray(rawIndices)) {
      return { kind: 'dirty', messages, reason: 'messages_deleted: missing/invalid indices' };
    }

    const indices: number[] = [];
    for (const raw of rawIndices) {
      if (!isFiniteInteger(raw) || raw < 0) {
        return { kind: 'dirty', messages, reason: 'messages_deleted: indices must be non-negative integers' };
      }
      indices.push(raw);
    }

    const uniqueIndices = [...new Set(indices)].sort((a, b) => a - b);
    if (uniqueIndices.length === 0) {
      return { kind: 'noop', messages };
    }
    if (uniqueIndices[uniqueIndices.length - 1] >= messages.length) {
      return {
        kind: 'dirty',
        messages,
        reason: `messages_deleted: index out of bounds for length ${messages.length}`,
      };
    }

    const remove = new Set(uniqueIndices);
    const next = messages.filter((item, idx) => !remove.has(idx));
    return { kind: 'ok', messages: reindexMessages(next) };
  }

  return { kind: 'noop', messages };
}
