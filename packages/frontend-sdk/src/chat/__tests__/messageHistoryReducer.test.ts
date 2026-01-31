import { describe, expect, it } from 'vitest';

import { reduceMessageHistory } from '../messageHistoryReducer';
import type { ApiMessage, IndexedMessage } from '../../types/messages';

function msg(role: ApiMessage['role'], content: string, metadata?: ApiMessage['metadata']): ApiMessage {
  return { role, content, metadata: metadata ?? null };
}

function expectMonotonicIncreasing(indices: number[]): void {
  for (let idx = 1; idx < indices.length; idx += 1) {
    expect(indices[idx]).toBeGreaterThan(indices[idx - 1]);
  }
}

describe('reduceMessageHistory', () => {
  it('appends final messages contiguously', () => {
    const initial: IndexedMessage[] = Object.freeze([
      { index: 7, message: Object.freeze(msg('user', 'hello')) },
    ]);

    const event = {
      type: 'final',
      messages: [msg('assistant', 'a'), msg('assistant', 'b')],
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result).toHaveLength(3);
    expect(result.slice(1).map((item) => item.message.content)).toEqual(['a', 'b']);

    const appendedIndices = result.slice(1).map((item) => item.index);
    expect(appendedIndices[0]).toBe(initial[0].index + 1);
    expect(appendedIndices[1]).toBe(appendedIndices[0] + 1);
    expectMonotonicIncreasing(result.map((item) => item.index));
  });

  it('filters out non-messages in final/tool_results payloads', () => {
    const initial: IndexedMessage[] = Object.freeze([]);
    const event = {
      type: 'tool_results',
      messages: [msg('tool', 'ok'), { nope: true }],
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result).toHaveLength(1);
    expect(result[0].message.content).toBe('ok');
  });

  it('appends message_appended.message when present', () => {
    const initial: IndexedMessage[] = Object.freeze([
      { index: 0, message: Object.freeze(msg('user', 'hi')) },
    ]);

    const event = {
      type: 'message_appended',
      message: msg('assistant', 'reply'),
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result).toHaveLength(2);
    expect(result[1].index).toBe(1);
    expect(result[1].message.content).toBe('reply');
  });

  it('synthesizes a message_appended message from role/content when needed', () => {
    const initial: IndexedMessage[] = Object.freeze([]);
    const event = {
      type: 'message_appended',
      role: 'user',
      content: 'hello',
      metadata: { timestamp: 'now' },
    } as any;

    const result = reduceMessageHistory(initial, event);
    expect(result).toHaveLength(1);
    expect(result[0].index).toBe(0);
    expect(result[0].message.role).toBe('user');
    expect(result[0].message.content).toBe('hello');
  });

  it('no-ops for unsupported event types', () => {
    const initial: IndexedMessage[] = Object.freeze([
      { index: 0, message: Object.freeze(msg('user', 'hi')) },
    ]);

    const event = { type: 'partial', message: msg('assistant', 'x') } as any;
    const result = reduceMessageHistory(initial, event);

    expect(result).toEqual(initial);
  });
});
