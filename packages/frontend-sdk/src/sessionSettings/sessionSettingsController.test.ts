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
    getSessionApplicationUiSchema: vi.fn(async () => []),
    getSessionOverrides: vi.fn(async () => ({})),
    getSessionConfigSchema: vi.fn(async () => []),
    getSessionBaseConfig: vi.fn(async () => ({})),
    patchSessionOverrides: vi.fn(async () => {}),
    deleteSessionOverride: vi.fn(async () => {}),
    ...overrides,
  } as AgentBackend;
}

describe('SessionSettingsController', () => {
  it('includes config elements from session application UI schema', async () => {
    const backend = createBackend({
      getSessionUiSchema: vi.fn(async () => [
        { key: 'model', ui_type: 'config', type: 'text' },
      ]),
      getSessionApplicationUiSchema: vi.fn(async () => [
        {
          key: 'application_setting',
          ui_type: 'config',
          type: 'checkbox',
          label: 'Application setting',
        },
        {
          ui_type: 'status_bar',
          id: 'application_status',
          label: 'Application status',
        },
        {
          ui_type: 'session_action',
          plugin: 'settings',
          id: 'anchored',
          label: 'Anchored',
          action_id: 'anchored',
          rich_ui: {
            kind: 'button',
            placements: ['session_settings'],
            anchor_key: 'application_setting',
          },
        },
        {
          ui_type: 'session_action',
          plugin: 'settings',
          id: 'header-only',
          label: 'Header only',
          action_id: 'header-only',
        },
      ]),
    });

    const controller = new SessionSettingsController({ backend, cacheKey: 'c1', sessionId: 's1' });
    await controller.load();

    expect(controller.getSnapshot().elements).toEqual([
      { key: 'model', ui_type: 'config', type: 'text' },
      {
        key: 'application_setting',
        ui_type: 'config',
        type: 'checkbox',
        label: 'Application setting',
      },
    ]);
    expect(backend.getSessionApplicationUiSchema).toHaveBeenCalledWith('s1');
    expect(controller.getSnapshot().actions).toEqual([
      expect.objectContaining({
        id: 'anchored',
        rich_ui: expect.objectContaining({
          kind: 'button',
          placements: ['session_settings'],
          anchor_key: 'application_setting',
        }),
      }),
    ]);

    controller.dispose();
  });

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
    expect(second.getSnapshot().actions).toEqual([]);
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

  describe('type coercion in patchOverride', () => {
    it('coerces string "42" to int 42 for number type element', async () => {
      const backend = createBackend({
        getSessionUiSchema: vi.fn(async () => [
          { key: 'seed', ui_type: 'config', type: 'number' },
        ]),
        getSessionOverrides: vi.fn(async () => ({})),
        getSessionConfigSchema: vi.fn(async () => []),
        getSessionBaseConfig: vi.fn(async () => ({})),
        patchSessionOverrides: vi.fn(async () => {}),
      });

      const controller = new SessionSettingsController({ backend, cacheKey: 'c1', sessionId: 's1' });
      await controller.load();

      await controller.patchOverride('seed', '42');

      // Check optimistic state has coerced value
      expect(controller.getSnapshot().overrides.seed).toBe(42);
      expect(typeof controller.getSnapshot().overrides.seed).toBe('number');

      // Check backend was called with coerced value
      expect(backend.patchSessionOverrides).toHaveBeenCalledWith('s1', { seed: 42 });

      controller.dispose();
    });

    it('coerces string "0.7" to float 0.7 for number type element', async () => {
      const backend = createBackend({
        getSessionUiSchema: vi.fn(async () => [
          { key: 'temperature', ui_type: 'config', type: 'number' },
        ]),
        getSessionOverrides: vi.fn(async () => ({ temperature: 0.5 })),
        getSessionConfigSchema: vi.fn(async () => []),
        getSessionBaseConfig: vi.fn(async () => ({})),
        patchSessionOverrides: vi.fn(async () => {}),
      });

      const controller = new SessionSettingsController({ backend, cacheKey: 'c1', sessionId: 's1' });
      await controller.load();

      await controller.patchOverride('temperature', '0.7');

      expect(controller.getSnapshot().overrides.temperature).toBe(0.7);
      expect(typeof controller.getSnapshot().overrides.temperature).toBe('number');
      expect(backend.patchSessionOverrides).toHaveBeenCalledWith('s1', { temperature: 0.7 });

      controller.dispose();
    });

    it('coerces string "true" to boolean true for checkbox type element', async () => {
      const backend = createBackend({
        getSessionUiSchema: vi.fn(async () => [
          { key: 'enable_thinking', ui_type: 'config', type: 'checkbox' },
        ]),
        getSessionOverrides: vi.fn(async () => ({ enable_thinking: false })),
        getSessionConfigSchema: vi.fn(async () => []),
        getSessionBaseConfig: vi.fn(async () => ({})),
        patchSessionOverrides: vi.fn(async () => {}),
      });

      const controller = new SessionSettingsController({ backend, cacheKey: 'c1', sessionId: 's1' });
      await controller.load();

      await controller.patchOverride('enable_thinking', 'true');

      expect(controller.getSnapshot().overrides.enable_thinking).toBe(true);
      expect(typeof controller.getSnapshot().overrides.enable_thinking).toBe('boolean');
      expect(backend.patchSessionOverrides).toHaveBeenCalledWith('s1', { enable_thinking: true });

      controller.dispose();
    });

    it('leaves select type values as strings', async () => {
      const backend = createBackend({
        getSessionUiSchema: vi.fn(async () => [
          { key: 'model', ui_type: 'config', type: 'select', options: ['a', 'b', 'c'] },
        ]),
        getSessionOverrides: vi.fn(async () => ({ model: 'a' })),
        getSessionConfigSchema: vi.fn(async () => []),
        getSessionBaseConfig: vi.fn(async () => ({})),
        patchSessionOverrides: vi.fn(async () => {}),
      });

      const controller = new SessionSettingsController({ backend, cacheKey: 'c1', sessionId: 's1' });
      await controller.load();

      await controller.patchOverride('model', 'b');

      expect(controller.getSnapshot().overrides.model).toBe('b');
      expect(typeof controller.getSnapshot().overrides.model).toBe('string');
      expect(backend.patchSessionOverrides).toHaveBeenCalledWith('s1', { model: 'b' });

      controller.dispose();
    });

    it('leaves unknown element types unchanged', async () => {
      const backend = createBackend({
        getSessionUiSchema: vi.fn(async () => [
          { key: 'custom', ui_type: 'config' }, // no type field
        ]),
        getSessionOverrides: vi.fn(async () => ({})),
        getSessionConfigSchema: vi.fn(async () => []),
        getSessionBaseConfig: vi.fn(async () => ({})),
        patchSessionOverrides: vi.fn(async () => {}),
      });

      const controller = new SessionSettingsController({ backend, cacheKey: 'c1', sessionId: 's1' });
      await controller.load();

      // Value is passed through unchanged when element has no type
      await controller.patchOverride('custom', '42');

      expect(controller.getSnapshot().overrides.custom).toBe('42');
      expect(typeof controller.getSnapshot().overrides.custom).toBe('string');
      expect(backend.patchSessionOverrides).toHaveBeenCalledWith('s1', { custom: '42' });

      controller.dispose();
    });

    it('coerces numeric string for web_fetch_timeout_seconds example', async () => {
      const backend = createBackend({
        getSessionUiSchema: vi.fn(async () => [
          {
            key: 'web_fetch_timeout_seconds',
            ui_type: 'config',
            type: 'number',
            label: 'URL fetch timeout',
            description: 'Seconds to wait for URL response',
          },
        ]),
        getSessionOverrides: vi.fn(async () => ({ web_fetch_timeout_seconds: 10 })),
        getSessionConfigSchema: vi.fn(async () => []),
        getSessionBaseConfig: vi.fn(async () => ({})),
        patchSessionOverrides: vi.fn(async () => {}),
      });

      const controller = new SessionSettingsController({ backend, cacheKey: 'c1', sessionId: 's1' });
      await controller.load();

      // Simulate user entering "30" in a text input
      await controller.patchOverride('web_fetch_timeout_seconds', '30');

      expect(controller.getSnapshot().overrides.web_fetch_timeout_seconds).toBe(30);
      expect(typeof controller.getSnapshot().overrides.web_fetch_timeout_seconds).toBe('number');
      expect(backend.patchSessionOverrides).toHaveBeenCalledWith('s1', { web_fetch_timeout_seconds: 30 });

      controller.dispose();
    });
  });
});