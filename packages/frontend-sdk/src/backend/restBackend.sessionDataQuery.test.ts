import { describe, expect, it, vi } from 'vitest';

import type { Transport } from '../transport/transport';
import { RestAgentBackend } from './restBackend';

describe('RestAgentBackend session data query', () => {
  it('returns explicitly projected message data without complete-message normalization', async () => {
    const projected = {
      messages: [
        {
          index: 4,
          message: {
            role: 'assistant',
            content: 'visible',
            metadata: { reasoning: 'reasoning' },
          },
        },
      ],
    };
    const transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: projected,
      })),
    } as unknown as Transport;
    const backend = new RestAgentBackend({ transport });

    await expect(
      backend.queryMessages('session/id', {
        start: -10,
        include: [
          '$.messages[*].index',
          '$.messages[*].message.content',
        ],
        exclude: ['$.messages[?(@.message.role == "tool")]'],
      }),
    ).resolves.toEqual(projected);
    expect(transport.request).toHaveBeenCalledWith({
      method: 'GET',
      path:
        '/sessions/session%2Fid/messages?start=-10' +
        '&include=%24.messages%5B*%5D.index' +
        '&include=%24.messages%5B*%5D.message.content' +
        '&exclude=%24.messages%5B%3F(%40.message.role%20%3D%3D%20%22tool%22)%5D',
    });
  });

  it('keeps projected queries separate from complete listMessages normalization', async () => {
    const transport = {
      request: vi
        .fn()
        .mockResolvedValueOnce({
          status: 200,
          data: { messages: [{ index: 0 }] },
        })
        .mockResolvedValueOnce({
          status: 200,
          data: {
            messages: [
              {
                index: 0,
                message: { role: 'assistant', content: 'complete' },
              },
            ],
            cursor_event_id: 'cursor',
          },
        }),
    } as unknown as Transport;
    const backend = new RestAgentBackend({ transport });

    await backend.queryMessages('session', {
      include: ['$.messages[*].index'],
    });
    await expect(backend.listMessages('session')).resolves.toEqual({
      messages: [
        {
          index: 0,
          message: { role: 'assistant', content: 'complete' },
        },
      ],
      cursorEventId: 'cursor',
      activeRequestId: null,
      readonly: false,
      snapshotId: null,
    });
  });
});