import { describe, expect, it } from 'vitest';

import { selectPendingToolPrompts } from './selectPendingToolPrompts';
import type { IndexedMessage } from '../types/messages';

describe('selectPendingToolPrompts', () => {
  it('returns empty when no messages', () => {
    expect(selectPendingToolPrompts([])).toEqual([]);
  });

  it('skips assistant without pending_prompt', () => {
    const messages: IndexedMessage[] = [
      {
        index: 0,
        message: {
          role: 'assistant',
          content: 'hi',
          metadata: { tool_calls: [] },
        },
      },
    ];
    expect(selectPendingToolPrompts(messages)).toEqual([]);
  });

  it('returns row when interception_current.pending_prompt has buttons', () => {
    const messages: IndexedMessage[] = [
      {
        index: 2,
        message: {
          role: 'assistant',
          content: 'call tool',
          metadata: {
            interception_current: {
              phase: 'tool_call',
              tool_call_id: 'call_1',
              tool_name: 'add',
              plugin: 'interceptor_calculator',
              pending_prompt: {
                id: 'p1',
                title: 'Allow?',
                message: 'Choose',
                buttons: [{ id: 'ok', label: 'OK', default: true }],
              },
            },
          },
        },
      },
    ];
    const rows = selectPendingToolPrompts(messages);
    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      messageIndex: 2,
      phase: 'tool_call',
      toolCallId: 'call_1',
      toolName: 'add',
      plugin: 'interceptor_calculator',
      prompt: expect.objectContaining({ id: 'p1' }),
    });
  });

  it('ignores assistant when buttons array is empty', () => {
    const messages: IndexedMessage[] = [
      {
        index: 0,
        message: {
          role: 'assistant',
          content: 'x',
          metadata: {
            interception_current: {
              pending_prompt: { id: 'x', buttons: [] },
            },
          },
        },
      },
    ];
    expect(selectPendingToolPrompts(messages)).toEqual([]);
  });
});
