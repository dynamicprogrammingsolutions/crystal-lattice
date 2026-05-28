import { describe, expect, it, vi } from 'vitest';

import { RestAgentBackend } from './restBackend';
import { subscribeSessionUiSchemaInvalidated } from '../uiSchema/sessionUiSchemaInvalidation';
import type { Transport } from '../transport/transport';

describe('RestAgentBackend session ui schema invalidation', () => {
  it('emits invalidation after patchSessionOverrides', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({ status: 200, data: {} })),
    };
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
    const transport: Transport = {
      request: vi.fn(async () => {
        throw new Error('network');
      }),
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
    const transport: Transport = {
      request: vi.fn(async () => ({ status: 200, data: {} })),
    };
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

  it('emits invalidation for affected sessions after successful action execution', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: {
          status: 'ok',
          plugin: 'p1',
          action_id: 'a1',
          result: {
            mutations: {
              updated_session_ids: ['s1', 's2'],
            },
            ui_effects: {
              reload_session_ids: ['s2', 's3'],
            },
          },
        },
      })),
    };
    const backend = new RestAgentBackend({ transport });
    const onS1 = vi.fn();
    const onS2 = vi.fn();
    const onS3 = vi.fn();

    const unsub1 = subscribeSessionUiSchemaInvalidated(backend, 's1', onS1);
    const unsub2 = subscribeSessionUiSchemaInvalidated(backend, 's2', onS2);
    const unsub3 = subscribeSessionUiSchemaInvalidated(backend, 's3', onS3);
    try {
      await backend.executeAction({
        pluginId: 'p1',
        actionId: 'a1',
        inputs: {},
      });
    } finally {
      unsub1();
      unsub2();
      unsub3();
    }

    expect(onS1).toHaveBeenCalledTimes(1);
    expect(onS2).toHaveBeenCalledTimes(1);
    expect(onS3).toHaveBeenCalledTimes(1);
    expect(onS1).toHaveBeenCalledWith(
      expect.objectContaining({ sessionId: 's1', reason: 'action_session_updated' }),
    );
    expect(onS2).toHaveBeenCalledWith(
      expect.objectContaining({ sessionId: 's2', reason: 'action_session_updated' }),
    );
    expect(onS3).toHaveBeenCalledWith(
      expect.objectContaining({ sessionId: 's3', reason: 'action_session_updated' }),
    );
  });

  it('emits invalidation after successful session-scoped action execution', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: {
          status: 'ok',
          plugin: 'session_title',
          action_id: 'set_session_title',
          result: {
            mutations: {
              updated_session_ids: ['s1'],
            },
            ui_effects: {},
          },
        },
      })),
    };
    const backend = new RestAgentBackend({ transport });
    const onInvalidate = vi.fn();

    const unsubscribe = subscribeSessionUiSchemaInvalidated(backend, 's1', onInvalidate);
    try {
      await backend.executeSessionAction!({
        sessionId: 's1',
        pluginId: 'session_title',
        actionId: 'set_session_title',
        inputs: { session_id: 's1', title: 'Cloud title' },
      });
    } finally {
      unsubscribe();
    }

    expect(onInvalidate).toHaveBeenCalledTimes(1);
    expect(onInvalidate).toHaveBeenCalledWith(
      expect.objectContaining({ sessionId: 's1', reason: 'action_session_updated' }),
    );
  });

  it('does not emit invalidation after failed action execution', async () => {
    const transport: Transport = {
      request: vi.fn(async () => ({
        status: 200,
        data: {
          status: 'error',
          message: 'boom',
        },
      })),
    };
    const backend = new RestAgentBackend({ transport });
    const onInvalidate = vi.fn();

    const unsubscribe = subscribeSessionUiSchemaInvalidated(backend, 's1', onInvalidate);
    try {
      await backend.executeAction({
        pluginId: 'p1',
        actionId: 'a1',
        inputs: {},
      });
    } finally {
      unsubscribe();
    }

    expect(onInvalidate).not.toHaveBeenCalled();
  });
});
