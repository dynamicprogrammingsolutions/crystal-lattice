import type { Event } from '../types/events';
import type { ApiMessage, IndexedMessage } from '../types/messages';

export type ReduceResult =
  | { kind: 'ok'; messages: IndexedMessage[]; needsBackfill?: boolean }
  | { kind: 'noop'; messages: IndexedMessage[]; needsBackfill?: boolean }
  | { kind: 'dirty'; messages: IndexedMessage[]; reason: string };

export interface MessageHistoryReducerOptions {
  /**
   * When set, keeps only the last `maxMessages` items after appends.
   *
   * This is intended for true windowed history (e.g. "last 50 messages").
   */
  maxMessages?: number | null;

  /**
   * Whether the local history is expected to extend to the end of the session.
   *
   * When false, some operations (notably deletes) may not be safely applicable
   * without a full reload.
   */
  followTail?: boolean;
}

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

function getExpectedNextIndex(messages: IndexedMessage[]): number {
  if (!messages || messages.length === 0) {
    return 0;
  }
  return messages[messages.length - 1].index + 1;
}

function trimTail(messages: IndexedMessage[], maxMessages: number | null): IndexedMessage[] {
  if (maxMessages == null) {
    return messages;
  }
  if (!Number.isFinite(maxMessages) || maxMessages <= 0) {
    return [];
  }
  if (messages.length <= maxMessages) {
    return messages;
  }
  return messages.slice(messages.length - maxMessages);
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
  return reduceMessageHistoryWithOptions(messages, event, {});
}

/**
 * Window-aware variant of `reduceMessageHistory`.
 *
 * This reducer operates on session-global indices (`IndexedMessage.index` matches
 * server indices). It supports keeping only a bounded tail window via
 * `options.maxMessages`.
 */
export function reduceMessageHistoryWithOptions(
  messages: IndexedMessage[],
  event: Event,
  options: MessageHistoryReducerOptions,
): ReduceResult {
  const type = (event as any).type;
  const followTail = options.followTail ?? true;
  const maxMessages = options.maxMessages ?? null;

  if (type === 'final' || type === 'tool_results') {
    const startIndex = (event as any).start_index;
    if (!isFiniteInteger(startIndex) || startIndex < 0) {
      return { kind: 'dirty', messages, reason: `${type}: missing/invalid start_index` };
    }

    const expected = getExpectedNextIndex(messages);
    if (startIndex !== expected) {
      return {
        kind: 'dirty',
        messages,
        reason: `${type}: start_index ${startIndex} does not match expected ${expected}`,
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
    const next = trimTail([...messages, ...appended], maxMessages);
    return { kind: 'ok', messages: next };
  }

  if (type === 'message_appended') {
    const index = (event as any).index;
    if (!isFiniteInteger(index) || index < 0) {
      return { kind: 'dirty', messages, reason: 'message_appended: missing/invalid index' };
    }

    const expected = getExpectedNextIndex(messages);
    if (index !== expected) {
      return {
        kind: 'dirty',
        messages,
        reason: `message_appended: index ${index} does not match expected ${expected}`,
      };
    }

    const rawMessage = (event as any).message;
    if (!isApiMessage(rawMessage)) {
      return { kind: 'dirty', messages, reason: 'message_appended: missing/invalid message' };
    }

    const next = trimTail([...messages, { index, message: rawMessage }], maxMessages);
    return { kind: 'ok', messages: next };
  }

  if (type === 'message_modified') {
    const index = (event as any).index;
    if (!isFiniteInteger(index) || index < 0) {
      return { kind: 'dirty', messages, reason: 'message_modified: missing/invalid index' };
    }

    if (messages.length > 0) {
      const firstIndex = messages[0].index;
      const lastIndex = messages[messages.length - 1].index;
      if (index < firstIndex) {
        return { kind: 'noop', messages };
      }
      if (index > lastIndex) {
        return {
          kind: 'dirty',
          messages,
          reason: `message_modified: index ${index} is newer than window end ${lastIndex}`,
        };
      }
    }

    const rawMessage = (event as any).message;
    if (!isApiMessage(rawMessage)) {
      return { kind: 'dirty', messages, reason: 'message_modified: missing/invalid message' };
    }

    const next = messages.slice();
    const pos = next.findIndex((item) => item.index === index);
    if (pos === -1) {
      if (messages.length === 0) {
        return { kind: 'dirty', messages, reason: 'message_modified: no local messages' };
      }
      return {
        kind: 'dirty',
        messages,
        reason: `message_modified: index ${index} missing from current window`,
      };
    }
    next[pos] = { index, message: rawMessage };
    return { kind: 'ok', messages: next };
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

    if (messages.length === 0) {
      return {
        kind: 'dirty',
        messages,
        reason: 'messages_deleted: cannot apply to empty local history',
      };
    }

    const lastLocalIndex = messages[messages.length - 1].index;
    if (followTail && uniqueIndices[uniqueIndices.length - 1] > lastLocalIndex) {
      return {
        kind: 'dirty',
        messages,
        reason: `messages_deleted: delete index beyond window end ${lastLocalIndex}`,
      };
    }

    const remove = new Set(uniqueIndices);
    const survivors = messages.filter((item) => !remove.has(item.index));

    // Shift remaining indices down by the count of deleted indices < current index.
    let deletedBefore = 0;
    let deletePtr = 0;
    const shifted: IndexedMessage[] = [];
    for (const item of survivors) {
      while (deletePtr < uniqueIndices.length && uniqueIndices[deletePtr] < item.index) {
        deletedBefore += 1;
        deletePtr += 1;
      }
      shifted.push({ index: item.index - deletedBefore, message: item.message });
    }

    const trimmed = trimTail(shifted, maxMessages);
    const needsBackfill = followTail && maxMessages != null && trimmed.length < maxMessages;
    return { kind: 'ok', messages: trimmed, needsBackfill };
  }

  return { kind: 'noop', messages };
}
