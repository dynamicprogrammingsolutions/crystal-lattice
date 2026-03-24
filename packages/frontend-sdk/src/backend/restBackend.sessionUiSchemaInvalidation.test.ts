import { describe, expect, it, vi } from 'vitest';

import { RestAgentBackend } from './restBackend';
import { subscribeSessionUiSchemaInvalidated } from '../uiSchema/sessionUiSchemaInvalidation';
import type { Transport } from '../transport/transport';

function createTransport(responseData: unknown, status = 200) {
  const requestMock = vi.fn(async () => ({ status, data: responseData }));
  const transport: Transport = {
    request: requestMock as unknown as Transport['request'],
  };
  return { transport, requestMock };
}

describe('RestAgentBackend session ui schema invalidation', () => {
  it('emits invalidation after patchSessionOverrides', async () => {
    const { transport } = createTransport({});
    const backend = new RestAgentBackend({ transport });
    const onInvalidate = vi.fn();

    const unsubscribe = subscribeSessionUiSchemaInvalidated(backend, 's1', onInvalidate);
    try {
      await backend.patchSessionOverrides('s1', { k: 'v' });
    } finally {
      unsubscribe();
    }

    expect(onInvalidate).toHaveBeenCalledTimes(1);
    expect(onInvalidate).toHaveBeenCalledWith(
      expect.objectContaining({ sessionId: 's1', reason: 'session_overrides_updated' }),
    );
  });

  it('does not emit invalidation when patchSessionOverrides fails', async () => {
    const requestMock = vi.fn(async () => {
      throw new Error('network');
    });
    const transport: Transport = {
      request: requestMock as unknown as Transport['request'],
    };
    const backend = new RestAgentBackend({ transport });
    const onInvalidate = vi.fn();

    const unsubscribe = subscribeSessionUiSchemaInvalidated(backend, 's1', onInvalidate);
    try {
      await expect(backend.patchSessionOverrides('s1', { k: 'v' })).rejects.toThrow('network');
    } finally {
      unsubscribe();
    }

    expect(onInvalidate).not.toHaveBeenCalled();
  });

  it('emits invalidation after setSessionPlugins', async () => {
    const { transport } = createTransport({});
    const backend = new RestAgentBackend({ transport });
    const onInvalidate = vi.fn();

    const unsubscribe = subscribeSessionUiSchemaInvalidated(backend, 's1', onInvalidate);
    try {
      await backend.setSessionPlugins('s1', ['p1']);
    } finally {
      unsubscribe();
    }

    expect(onInvalidate).toHaveBeenCalledTimes(1);
    expect(onInvalidate).toHaveBeenCalledWith(
      expect.objectContaining({ sessionId: 's1', reason: 'session_plugins_updated' }),
    );
  });
});
