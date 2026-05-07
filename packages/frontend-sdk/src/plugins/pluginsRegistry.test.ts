import { describe, expect, it, vi } from 'vitest';

import { PluginsRegistry } from './pluginsRegistry';
import type { AgentBackend } from '../backend/backend';

function createBackend(): AgentBackend {
  return {
    capabilities: {
      applicationActions: true,
      attachmentDrafts: false,
      attachmentDeletion: false,
      attachments: false,
      bridgeSessions: false,
      idempotency: false,
      messageDelete: false,
      messageModify: false,
      pluginConfig: false,
      sessionActions: true,
      sessionAgentSwitch: false,
      sessionConfig: false,
      sessionDelete: false,
      sessionPlugins: false,
      sessionUiSchema: false,
      streamByDefault: false,
    },
    listApplicationActions: vi.fn(),
    listApplicationUiSchema: vi.fn(),
  } as unknown as AgentBackend;
}

describe('PluginsRegistry', () => {
  it('does not poison the cache after a failed load and retries on the next load', async () => {
    const backend = createBackend();
    (backend.listApplicationActions as any)
      .mockRejectedValueOnce(new Error('boom'))
      .mockResolvedValueOnce([{ id: 'action-1', label: 'Action 1' }]);
    (backend.listApplicationUiSchema as any)
      .mockResolvedValueOnce([{ id: 'session-list-action', ui_type: 'session_list_action', label: 'List' }]);

    const first = new PluginsRegistry({ backend, cacheKey: 'plugins-registry-retry' });
    await first.load();
    expect(first.getSnapshot().error).toBe('boom');
    expect(first.getSnapshot().sessionListActions).toEqual([]);

    (backend.listApplicationUiSchema as any).mockResolvedValueOnce([
      { id: 'session-list-action', ui_type: 'session_list_action', label: 'List' },
    ]);
    const second = new PluginsRegistry({ backend, cacheKey: 'plugins-registry-retry' });
    await second.load();

    expect(second.getSnapshot().error).toBeNull();
    expect(second.getSnapshot().actionsById['action-1']).toMatchObject({ id: 'action-1' });
    expect(second.getSnapshot().sessionListActions).toHaveLength(1);
    expect(backend.listApplicationActions).toHaveBeenCalledTimes(2);
    expect(backend.listApplicationUiSchema).toHaveBeenCalledTimes(2);
  });

  it('refresh keeps the last successful data when a reload fails', async () => {
    const backend = createBackend();
    (backend.listApplicationActions as any)
      .mockResolvedValueOnce([{ id: 'action-1', label: 'Action 1' }])
      .mockRejectedValueOnce(new Error('refresh failed'));
    (backend.listApplicationUiSchema as any)
      .mockResolvedValueOnce([{ id: 'session-list-action', ui_type: 'session_list_action', label: 'List' }])
      .mockResolvedValueOnce([{ id: 'session-list-action', ui_type: 'session_list_action', label: 'List' }]);

    const registry = new PluginsRegistry({ backend, cacheKey: 'plugins-registry-refresh' });
    await registry.load();
    expect(registry.getSnapshot().error).toBeNull();
    expect(registry.getSnapshot().sessionListActions).toHaveLength(1);

    await registry.refresh();

    expect(registry.getSnapshot().error).toBe('refresh failed');
    expect(registry.getSnapshot().sessionListActions).toHaveLength(1);
    expect(registry.getSnapshot().actionsById['action-1']).toMatchObject({ id: 'action-1' });
  });

  it('invalidate clears the cache so the next load refetches', async () => {
    const backend = createBackend();
    (backend.listApplicationActions as any)
      .mockResolvedValueOnce([{ id: 'action-1', label: 'Action 1' }])
      .mockResolvedValueOnce([{ id: 'action-2', label: 'Action 2' }]);
    (backend.listApplicationUiSchema as any)
      .mockResolvedValueOnce([{ id: 'session-list-action-1', ui_type: 'session_list_action', label: 'List 1' }])
      .mockResolvedValueOnce([{ id: 'session-list-action-2', ui_type: 'session_list_action', label: 'List 2' }]);

    const first = new PluginsRegistry({ backend, cacheKey: 'plugins-registry-invalidate' });
    await first.load();

    const second = new PluginsRegistry({ backend, cacheKey: 'plugins-registry-invalidate' });
    await second.load();
    expect(backend.listApplicationActions).toHaveBeenCalledTimes(1);

    second.invalidate();
    await second.load();

    expect(backend.listApplicationActions).toHaveBeenCalledTimes(2);
    expect(second.getSnapshot().actionsById['action-2']).toMatchObject({ id: 'action-2' });
    expect(second.getSnapshot().sessionListActions[0]).toMatchObject({ id: 'session-list-action-2' });
  });
});