import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../backend/backend';
import type { SessionSummary } from '../types/sessions';
import { SessionContextController } from './sessionContextController';

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((nextResolve, nextReject) => {
    resolve = nextResolve;
    reject = nextReject;
  });
  return { promise, resolve, reject };
}

function createBackend(overrides?: Partial<AgentBackend>): AgentBackend {
  return {
    getSessionSummary: vi.fn(async (sessionId: string) => ({
      session_id: sessionId,
      modified: 1,
      preview: '',
      metadata: {},
    })),
    ...overrides,
  } as AgentBackend;
}

describe('SessionContextController', () => {
  it('keeps cached summary available while refreshing', async () => {
    const firstSummary: SessionSummary = {
      session_id: 's1',
      modified: 1,
      preview: 'first',
      metadata: { state: 'old' },
    };
    const secondSummary: SessionSummary = {
      session_id: 's1',
      modified: 2,
      preview: 'second',
      metadata: { state: 'new' },
    };
    const backend = createBackend({
      getSessionSummary: vi.fn(async () => firstSummary),
    });

    const first = new SessionContextController({ backend, cacheKey: 'c1', sessionId: 's1' });
    await first.load();

    const reload = deferred<SessionSummary>();
    (backend.getSessionSummary as any).mockImplementationOnce(async () => reload.promise);

    const second = new SessionContextController({ backend, cacheKey: 'c1', sessionId: 's1' });
    expect(second.getSnapshot().summary).toEqual(firstSummary);
    expect(second.getSnapshot().loading).toBe(false);

    const pending = second.load();
    expect(second.getSnapshot().summary).toEqual(firstSummary);
    expect(second.getSnapshot().loading).toBe(false);
    expect(second.getSnapshot().refreshing).toBe(true);

    reload.resolve(secondSummary);
    await pending;

    expect(second.getSnapshot().summary).toEqual(secondSummary);
    expect(second.getSnapshot().refreshing).toBe(false);
    expect(second.getSnapshot().error).toBeNull();
  });

  it('preserves the current summary when refresh fails', async () => {
    const initialSummary: SessionSummary = {
      session_id: 's1',
      modified: 1,
      preview: 'first',
      metadata: { state: 'old' },
    };
    const backend = createBackend({
      getSessionSummary: vi.fn(async () => {
        throw new Error('offline');
      }),
    });
    const controller = new SessionContextController({
      backend,
      cacheKey: 'c2',
      sessionId: 's1',
      initialSummary,
    });

    await controller.load();

    expect(controller.getSnapshot().summary).toEqual(initialSummary);
    expect(controller.getSnapshot().loading).toBe(false);
    expect(controller.getSnapshot().refreshing).toBe(false);
    expect(controller.getSnapshot().error).toBe('offline');
  });

  it('loads only when stale', async () => {
    const backend = createBackend();
    const controller = new SessionContextController({
      backend,
      cacheKey: 'c3',
      sessionId: 's1',
      initialSummary: {
        session_id: 's1',
        modified: 1,
        preview: 'first',
        metadata: {},
      },
      initialLoadedAt: 1000,
    });

    await controller.loadIfStale({ staleMs: 1000, nowMs: 1200 });
    expect(backend.getSessionSummary).not.toHaveBeenCalled();

    await controller.loadIfStale({ staleMs: 1000, nowMs: 2200 });
    expect(backend.getSessionSummary).toHaveBeenCalledTimes(1);
  });
});