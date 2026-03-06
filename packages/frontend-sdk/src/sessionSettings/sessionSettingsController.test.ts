import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../backend/backend';
import { SessionSettingsController } from './sessionSettingsController';

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((nextResolve, nextReject) => {
    resolve = nextResolve;
    reject = nextReject;
  });
  return { promise, resolve, reject };
}

async function flushPromises(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
  await new Promise((resolve) => setTimeout(resolve, 0));
}

function createBackend(overrides?: Partial<AgentBackend>): AgentBackend {
  return {
    getSessionUiSchema: vi.fn(async () => []),
    getSessionOverrides: vi.fn(async () => ({})),
    getSessionConfigSchema: vi.fn(async () => []),
    getSessionBaseConfig: vi.fn(async () => ({})),
    patchSessionOverrides: vi.fn(async () => {}),
    deleteSessionOverride: vi.fn(async () => {}),
    ...overrides,
  } as AgentBackend;
}

describe('SessionSettingsController', () => {
  it('hydrates from cache and refreshes without blocking existing content', async () => {
    const backend = createBackend({
      getSessionUiSchema: vi
        .fn(async () => [
          { key: 'model', ui_type: 'config', type: 'text' },
          { key: 'ignored', ui_type: 'other', type: 'text' },
        ])
        .mockImplementationOnce(async () => [
          { key: 'model', ui_type: 'config', type: 'text' },
          { key: 'ignored', ui_type: 'other', type: 'text' },
        ]),
      getSessionOverrides: vi.fn(async () => ({ model: 'first' })),
      getSessionConfigSchema: vi.fn(async () => [{ key: 'model' }]),
      getSessionBaseConfig: vi.fn(async () => ({ model: 'base' })),
    });

    const first = new SessionSettingsController({ backend, cacheKey: 'c1', sessionId: 's1' });
    await first.load();

    const uiSchemaReload = deferred<any[]>();
    const overridesReload = deferred<Record<string, any>>();
    const configReload = deferred<any[]>();
    const baseReload = deferred<Record<string, any>>();

    (backend.getSessionUiSchema as any).mockImplementationOnce(async () => uiSchemaReload.promise);
    (backend.getSessionOverrides as any).mockImplementationOnce(async () => overridesReload.promise);
    (backend.getSessionConfigSchema as any).mockImplementationOnce(async () => configReload.promise);
    (backend.getSessionBaseConfig as any).mockImplementationOnce(async () => baseReload.promise);

    const second = new SessionSettingsController({ backend, cacheKey: 'c1', sessionId: 's1' });
    expect(second.getSnapshot().elements).toEqual([{ key: 'model', ui_type: 'config', type: 'text' }]);
    expect(second.getSnapshot().overrides).toEqual({ model: 'first' });
    expect(second.getSnapshot().loading).toBe(false);

    const pendingLoad = second.load();
    expect(second.getSnapshot().refreshing).toBe(true);
    expect(second.getSnapshot().statusMessage).toBe('Refreshing settings…');

    uiSchemaReload.resolve([{ key: 'temperature', ui_type: 'config', type: 'text' }]);
    overridesReload.resolve({ temperature: 0.2 });
    configReload.resolve([{ key: 'temperature' }]);
    baseReload.resolve({ temperature: 0.1 });

    await pendingLoad;

    expect(second.getSnapshot().loading).toBe(false);
    expect(second.getSnapshot().refreshing).toBe(false);
    expect(second.getSnapshot().elements).toEqual([
      { key: 'temperature', ui_type: 'config', type: 'text' },
    ]);
    expect(second.getSnapshot().overrides).toEqual({ temperature: 0.2 });

    first.dispose();
    second.dispose();
  });

  it('tracks saving and then shows saved after a successful patch', async () => {
    const reloadUiSchema = deferred<any[]>();
    const reloadOverrides = deferred<Record<string, any>>();
    const reloadConfig = deferred<any[]>();
    const reloadBase = deferred<Record<string, any>>();

    let loadCount = 0;
    const backend = createBackend({
      getSessionUiSchema: vi.fn(async () => {
        loadCount += 1;
        if (loadCount === 1) {
          return [{ key: 'model', ui_type: 'config', type: 'text' }];
        }
        return reloadUiSchema.promise;
      }),
      getSessionOverrides: vi.fn(async () => {
        if (loadCount === 1) {
          return { model: 'first' };
        }
        return reloadOverrides.promise;
      }),
      getSessionConfigSchema: vi.fn(async () => {
        if (loadCount === 1) {
          return [{ key: 'model' }];
        }
        return reloadConfig.promise;
      }),
      getSessionBaseConfig: vi.fn(async () => {
        if (loadCount === 1) {
          return { model: 'base' };
        }
        return reloadBase.promise;
      }),
      patchSessionOverrides: vi.fn(async () => {}),
    });

    const controller = new SessionSettingsController({ backend, cacheKey: 'c1', sessionId: 's1' });
    await controller.load();

    const patchPromise = controller.patchOverride('model', 'second');
    expect(controller.getSnapshot().overrides.model).toBe('second');
    expect(controller.getSnapshot().savingKeys).toEqual(['model']);
    expect(controller.getSnapshot().statusMessage).toBe('Saving…');

    await patchPromise;
    expect(controller.getSnapshot().refreshing).toBe(true);
    expect(controller.getSnapshot().statusTone).toBe('success');
    expect(controller.getSnapshot().statusMessage).toBe('Saved.');

    reloadUiSchema.resolve([{ key: 'model', ui_type: 'config', type: 'text' }]);
    reloadOverrides.resolve({ model: 'second' });
    reloadConfig.resolve([{ key: 'model' }]);
    reloadBase.resolve({ model: 'base' });
    await flushPromises();
    await flushPromises();

    expect(controller.getSnapshot().savingKeys).toEqual([]);
    expect(controller.getSnapshot().overrides.model).toBe('second');
    expect(controller.getSnapshot().statusTone).toBe('success');
    expect(controller.getSnapshot().statusMessage).toBe('Saved.');
    expect(controller.getSnapshot().lastSavedAt).not.toBeNull();

    controller.dispose();
  });

  it('reverts optimistic state and surfaces an error when patch fails', async () => {
    const backend = createBackend({
      getSessionUiSchema: vi.fn(async () => [{ key: 'model', ui_type: 'config', type: 'text' }]),
      getSessionOverrides: vi.fn(async () => ({ model: 'first' })),
      getSessionConfigSchema: vi.fn(async () => [{ key: 'model' }]),
      getSessionBaseConfig: vi.fn(async () => ({ model: 'base' })),
      patchSessionOverrides: vi.fn(async () => {
        throw new Error('network');
      }),
    });

    const controller = new SessionSettingsController({ backend, cacheKey: 'c1', sessionId: 's1' });
    await controller.load();

    const patchPromise = controller.patchOverride('model', 'second');
    expect(controller.getSnapshot().overrides.model).toBe('second');
    expect(controller.getSnapshot().statusMessage).toBe('Saving…');

    await expect(patchPromise).rejects.toThrow('network');

    expect(controller.getSnapshot().overrides.model).toBe('first');
    expect(controller.getSnapshot().savingKeys).toEqual([]);
    expect(controller.getSnapshot().statusTone).toBe('error');
    expect(controller.getSnapshot().statusMessage).toBe('network');

    controller.dispose();
  });
});