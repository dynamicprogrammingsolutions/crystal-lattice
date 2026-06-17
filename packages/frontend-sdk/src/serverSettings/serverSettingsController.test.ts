import { describe, expect, it, vi } from 'vitest';

import type { AgentBackend } from '../backend/backend';
import { ServerSettingsController } from './serverSettingsController';

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
    listApplicationUiSchema: vi.fn(async () => []),
    getServerSettings: vi.fn(async () => ({})),
    patchServerSettings: vi.fn(async () => {}),
    deleteServerSetting: vi.fn(async () => {}),
    ...overrides,
  } as AgentBackend;
}

describe('ServerSettingsController', () => {
  it('loads only server-scoped config elements from application UI schema', async () => {
    const backend = createBackend({
      listApplicationUiSchema: vi.fn(async () => [
        {
          key: 'server_mode',
          ui_type: 'config',
          scope: 'server',
          type: 'select',
        },
        {
          key: 'session_mode',
          ui_type: 'config',
          scope: 'session',
          type: 'text',
        },
        {
          ui_type: 'status_bar',
          id: 'status',
          label: 'Status',
        },
      ]),
      getServerSettings: vi.fn(async () => ({ server_mode: 'fast' })),
    });

    const controller = new ServerSettingsController({ backend, cacheKey: 'c1' });
    await controller.load();

    expect(controller.getSnapshot().elements).toEqual([
      {
        key: 'server_mode',
        ui_type: 'config',
        scope: 'server',
        type: 'select',
      },
    ]);
    expect(controller.getSnapshot().settings).toEqual({ server_mode: 'fast' });

    controller.dispose();
  });

  it('hydrates from cache and refreshes live settings', async () => {
    const backend = createBackend({
      listApplicationUiSchema: vi.fn(async () => [
        { key: 'server_mode', ui_type: 'config', scope: 'server', type: 'text' },
      ]),
      getServerSettings: vi.fn(async () => ({ server_mode: 'first' })),
    });

    const first = new ServerSettingsController({ backend, cacheKey: 'c1' });
    await first.load();

    const schemaReload = deferred<any[]>();
    const settingsReload = deferred<Record<string, any>>();
    (backend.listApplicationUiSchema as any).mockImplementationOnce(async () => schemaReload.promise);
    (backend.getServerSettings as any).mockImplementationOnce(async () => settingsReload.promise);

    const second = new ServerSettingsController({ backend, cacheKey: 'c1' });
    expect(second.getSnapshot().settings).toEqual({ server_mode: 'first' });
    expect(second.getSnapshot().loading).toBe(false);

    const pendingLoad = second.load();
    expect(second.getSnapshot().refreshing).toBe(true);
    expect(second.getSnapshot().statusMessage).toBe('Refreshing settings...');

    schemaReload.resolve([{ key: 'enabled', ui_type: 'config', scope: 'server', type: 'checkbox' }]);
    settingsReload.resolve({ enabled: true });
    await pendingLoad;

    expect(second.getSnapshot().elements).toEqual([
      { key: 'enabled', ui_type: 'config', scope: 'server', type: 'checkbox' },
    ]);
    expect(second.getSnapshot().settings).toEqual({ enabled: true });

    first.dispose();
    second.dispose();
  });

  it('optimistically patches and deletes server settings', async () => {
    const backend = createBackend({
      listApplicationUiSchema: vi.fn(async () => [
        { key: 'enabled', ui_type: 'config', scope: 'server', type: 'checkbox' },
      ]),
      getServerSettings: vi.fn(async () => ({ enabled: false })),
      patchServerSettings: vi.fn(async () => {}),
      deleteServerSetting: vi.fn(async () => {}),
    });

    const controller = new ServerSettingsController({ backend, cacheKey: 'c1' });
    await controller.load();

    await controller.patchSetting('enabled', true);
    expect(backend.patchServerSettings).toHaveBeenCalledWith({ enabled: true });
    expect(controller.getSnapshot().settings.enabled).toBe(true);

    await controller.deleteSetting('enabled');
    expect(backend.deleteServerSetting).toHaveBeenCalledWith('enabled');
    expect(controller.getSnapshot().settings).toEqual({});

    controller.dispose();
  });
});