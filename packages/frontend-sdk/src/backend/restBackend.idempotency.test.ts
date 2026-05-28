import { describe, expect, it, vi } from 'vitest';

import { RestAgentBackend } from './restBackend';
import type { Transport } from '../transport/transport';
import * as idempotency from '../utils/idempotency';

describe('RestAgentBackend idempotency headers', () => {
  it('sendMessage calls /send_message and generates an idempotency key by default', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: { status: 'started', request_id: 'r1', session_id: 's1' },
      })),
    };

    const spy = vi
      .spyOn(idempotency, 'generateIdempotencyKey')
      .mockReturnValue('generated-key');

    const backend = new RestAgentBackend({ transport });
    await backend.sendMessage('s1', {
      message: { role: 'user', content: 'hello' },
    });

    expect(spy).toHaveBeenCalledTimes(1);
    expect(transport.request).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'POST',
        path: '/sessions/s1/send_message',
        headers: expect.objectContaining({
          'Idempotency-Key': 'generated-key',
        }),
      }),
    );
  });

  it('uses a caller-provided idempotency key for sendMessage', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({ status: 200, data: { status: 'started', request_id: 'r1' } })),
    };

    const spy = vi.spyOn(idempotency, 'generateIdempotencyKey');

    const backend = new RestAgentBackend({ transport });
    await backend.sendMessage('s1', {
      message: { role: 'user', content: 'hello' },
      idempotencyKey: 'provided-key',
    });

    expect(spy).not.toHaveBeenCalled();
    expect(transport.request).toHaveBeenCalledWith(
      expect.objectContaining({
        headers: expect.objectContaining({
          'Idempotency-Key': 'provided-key',
        }),
      }),
    );
  });

  it('adds idempotency keys to legacy send/appendMessage/executeAction requests', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({ status: 200, data: {} })),
    };

    vi.spyOn(idempotency, 'generateIdempotencyKey').mockReturnValue('generated-key');

    const backend = new RestAgentBackend({ transport });
    await backend.appendMessage('s1', { role: 'user', content: 'hi' });
    await backend.send('s1', { configOverrides: {} });
    await backend.executeAction({ pluginId: 'p1', actionId: 'a1', inputs: {} });

    expect(transport.request).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'POST',
        path: '/sessions/s1/messages',
        headers: expect.objectContaining({
          'Idempotency-Key': 'generated-key',
        }),
      }),
    );

    expect(transport.request).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'POST',
        path: '/sessions/s1/send',
        headers: expect.objectContaining({
          'Idempotency-Key': 'generated-key',
        }),
      }),
    );

    expect(transport.request).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'POST',
        path: '/actions',
        headers: expect.objectContaining({
          'Idempotency-Key': 'generated-key',
        }),
      }),
    );
  });

  it('adds idempotency keys to session-scoped action requests', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({ status: 200, data: { status: 'ok', result: {} } })),
    };

    vi.spyOn(idempotency, 'generateIdempotencyKey').mockReturnValue('generated-key');

    const backend = new RestAgentBackend({ transport });
    await backend.executeSessionAction!({
      sessionId: 's1',
      pluginId: 'session_title',
      actionId: 'set_session_title',
      inputs: { title: 'Hello' },
    });

    expect(transport.request).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'POST',
        path: '/sessions/s1/actions',
        headers: expect.objectContaining({
          'Idempotency-Key': 'generated-key',
        }),
      }),
    );
  });

  it('forwards action_owner in executeAction payloads', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({ status: 200, data: { status: 'ok', result: {} } })),
    };

    const backend = new RestAgentBackend({ transport });
    await backend.executeAction({
      pluginId: 'provider_ext',
      actionId: 'compact_native_history',
      actionOwner: 'provider_extension',
      inputs: { end_index: 12 },
    });

    expect(transport.request).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'POST',
        path: '/actions',
        body: {
          plugin: 'provider_ext',
          action_id: 'compact_native_history',
          action_owner: 'provider_extension',
          inputs: { end_index: 12 },
        },
      }),
    );
  });
});
