import { describe, expect, it } from 'vitest';

import { reduceMessageHistory } from '../messageHistoryReducer';
import type { ApiMessage, IndexedMessage } from '../../types/messages';

function msg(role: ApiMessage['role'], content: string, metadata?: ApiMessage['metadata']): ApiMessage {
  return { role, content, metadata: metadata ?? null };
}

describe('reduceMessageHistory', () => {
  it('appends final messages when start_index matches local length', () => {
    const initial: IndexedMessage[] = Object.freeze([
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
    const initial: IndexedMessage[] = Object.freeze([
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
    const initial: IndexedMessage[] = Object.freeze([]);
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
    const initial: IndexedMessage[] = Object.freeze([
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
    const initial: IndexedMessage[] = Object.freeze([
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
    const initial: IndexedMessage[] = Object.freeze([
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
    const initial: IndexedMessage[] = Object.freeze([
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
    const initial: IndexedMessage[] = Object.freeze([
      { index: 0, message: Object.freeze(msg('user', 'hi')) },
    ]);

    const event = { type: 'partial', message: msg('assistant', 'x') } as any;
    const result = reduceMessageHistory(initial, event);

    expect(result.kind).toBe('noop');
    expect(result.messages).toEqual(initial);
  });
});
