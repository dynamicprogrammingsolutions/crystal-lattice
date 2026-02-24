import { describe, expect, it } from 'vitest';

import { reduceMessageHistory, reduceMessageHistoryWithOptions } from '../messageHistoryReducer';
import type { ApiMessage, IndexedMessage } from '../../types/messages';

function msg(role: ApiMessage['role'], content: string, metadata?: ApiMessage['metadata']): ApiMessage {
  return { role, content, metadata: metadata ?? null };
}

function freezeMessages(messages: IndexedMessage[]): IndexedMessage[] {
  return Object.freeze(messages) as unknown as IndexedMessage[];
}

describe('reduceMessageHistory', () => {
  it('appends final messages when start_index matches local length', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 0, message: Object.freeze(msg('user', 'hello')) },
    ]);

    const event = {
      type: 'final',
      start_index: 1,
      messages: [msg('assistant', 'a'), msg('assistant', 'b')],
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result.kind).toBe('ok');
    expect(result.messages).toHaveLength(3);
    expect(result.messages.slice(1).map((item) => item.message.content)).toEqual(['a', 'b']);
    expect(result.messages.map((item) => item.index)).toEqual([0, 1, 2]);
  });

  it('marks dirty when start_index does not match local length', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 0, message: Object.freeze(msg('user', 'hello')) },
    ]);

    const event = {
      type: 'final',
      start_index: 0,
      messages: [msg('assistant', 'a')],
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result.kind).toBe('dirty');
    expect(result.messages).toEqual(initial);
  });

  it('marks dirty when a final/tool_results payload contains invalid messages', () => {
    const initial: IndexedMessage[] = freezeMessages([]);
    const event = {
      type: 'tool_results',
      start_index: 0,
      messages: [msg('tool', 'ok'), { nope: true }],
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result.kind).toBe('dirty');
    expect(result.messages).toEqual(initial);
  });

  it('appends message_appended when index matches local length', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 0, message: Object.freeze(msg('user', 'hi')) },
    ]);

    const event = {
      type: 'message_appended',
      index: 1,
      message: msg('assistant', 'reply'),
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result.kind).toBe('ok');
    expect(result.messages).toHaveLength(2);
    expect(result.messages[1].index).toBe(1);
    expect(result.messages[1].message.content).toBe('reply');
  });

  it('marks dirty when message_appended index does not match local length', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 0, message: Object.freeze(msg('user', 'hi')) },
    ]);

    const event = {
      type: 'message_appended',
      index: 5,
      message: msg('assistant', 'reply'),
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result.kind).toBe('dirty');
    expect(result.messages).toEqual(initial);
  });

  it('replaces a message_modified payload by index', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 0, message: Object.freeze(msg('user', 'hi')) },
      { index: 1, message: Object.freeze(msg('assistant', 'old')) },
    ]);

    const event = {
      type: 'message_modified',
      index: 1,
      message: msg('assistant', 'new'),
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result.kind).toBe('ok');
    expect(result.messages).toHaveLength(2);
    expect(result.messages[1].message.content).toBe('new');
  });

  it('removes messages_deleted indices and reindexes', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 0, message: Object.freeze(msg('user', '0')) },
      { index: 1, message: Object.freeze(msg('user', '1')) },
      { index: 2, message: Object.freeze(msg('user', '2')) },
    ]);

    const event = {
      type: 'messages_deleted',
      indices: [1],
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result.kind).toBe('ok');
    expect(result.messages.map((item) => item.message.content)).toEqual(['0', '2']);
    expect(result.messages.map((item) => item.index)).toEqual([0, 1]);
  });

  it('no-ops for unsupported event types', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 0, message: Object.freeze(msg('user', 'hi')) },
    ]);

    const event = { type: 'partial', message: msg('assistant', 'x') } as any;
    const result = reduceMessageHistory(initial, event);

    expect(result.kind).toBe('noop');
    expect(result.messages).toEqual(initial);
  });

  it('treats message indices as global (windowed history)', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 100, message: Object.freeze(msg('user', 'hi')) },
    ]);

    const event = {
      type: 'message_appended',
      index: 101,
      message: msg('assistant', 'reply'),
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result.kind).toBe('ok');
    expect(result.messages.map((item) => item.index)).toEqual([100, 101]);
  });

  it('trims to maxMessages when configured', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 2, message: Object.freeze(msg('user', '2')) },
      { index: 3, message: Object.freeze(msg('user', '3')) },
      { index: 4, message: Object.freeze(msg('user', '4')) },
    ]);

    const event = {
      type: 'message_appended',
      index: 5,
      message: msg('assistant', '5'),
    } as any;

    const result = reduceMessageHistoryWithOptions(initial, event, { maxMessages: 3 });
    expect(result.kind).toBe('ok');
    expect(result.messages.map((item) => item.index)).toEqual([3, 4, 5]);
  });

  it('shifts indices on delete even when deleted messages are outside the window', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 10, message: Object.freeze(msg('user', '10')) },
      { index: 11, message: Object.freeze(msg('user', '11')) },
      { index: 12, message: Object.freeze(msg('user', '12')) },
    ]);

    const event = {
      type: 'messages_deleted',
      indices: [0, 1, 2],
    } as any;

    const result = reduceMessageHistoryWithOptions(initial, event, { followTail: true, maxMessages: 3 });
    expect(result.kind).toBe('ok');
    expect(result.messages.map((item) => item.index)).toEqual([7, 8, 9]);
  });

  it('signals needsBackfill when delete reduces the window size below maxMessages', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 10, message: Object.freeze(msg('user', '10')) },
      { index: 11, message: Object.freeze(msg('user', '11')) },
      { index: 12, message: Object.freeze(msg('user', '12')) },
    ]);

    const event = {
      type: 'messages_deleted',
      indices: [11],
    } as any;

    const result = reduceMessageHistoryWithOptions(initial, event, { followTail: true, maxMessages: 3 });
    expect(result.kind).toBe('ok');
    expect(result.messages.map((item) => item.index)).toEqual([10, 11]);
    expect(result.kind === 'ok' && result.needsBackfill).toBe(true);
  });

  it('no-ops message_modified when the target index is older than the window', () => {
    const initial: IndexedMessage[] = freezeMessages([
      { index: 10, message: Object.freeze(msg('user', '10')) },
      { index: 11, message: Object.freeze(msg('user', '11')) },
    ]);

    const event = {
      type: 'message_modified',
      index: 1,
      message: msg('user', 'updated'),
    } as any;

    const result = reduceMessageHistoryWithOptions(initial, event, { followTail: true, maxMessages: 2 });
    expect(result.kind).toBe('noop');
    expect(result.messages).toEqual(initial);
  });
});
