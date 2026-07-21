import { describe, expect, it, vi } from 'vitest';

import { PluginsRegistry } from './pluginsRegistry';
import type { AgentBackend } from '../backend/backend';
import { emitServerSettingsInvalidated } from '../serverSettings/serverSettingsInvalidation';

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

function sessionListAction(id: string, label = 'List') {
  return {
    id,
    ui_type: 'session_list_action',
    plugin: 'fixture',
    label,
    action_id: `${id}-action`,
    dialog: { kind: 'none' },
  };
}

describe('PluginsRegistry', () => {
  it('does not poison the cache after a failed load and retries on the next load', async () => {
    const backend = createBackend();
    (backend.listApplicationActions as any)
      .mockRejectedValueOnce(new Error('boom'))
      .mockResolvedValueOnce([{ id: 'action-1', label: 'Action 1' }]);
    (backend.listApplicationUiSchema as any)
      .mockResolvedValueOnce([sessionListAction('session-list-action')]);

    const first = new PluginsRegistry({ backend, cacheKey: 'plugins-registry-retry' });
    await first.load();
    expect(first.getSnapshot().error).toBe('boom');
    expect(first.getSnapshot().sessionListActions).toEqual([]);

    (backend.listApplicationUiSchema as any).mockResolvedValueOnce([
      sessionListAction('session-list-action'),
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
      .mockResolvedValueOnce([sessionListAction('session-list-action')])
      .mockResolvedValueOnce([sessionListAction('session-list-action')]);

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
      .mockResolvedValueOnce([sessionListAction('session-list-action-1', 'List 1')])
      .mockResolvedValueOnce([sessionListAction('session-list-action-2', 'List 2')]);

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

  it('keeps an ordinary list action when rich_ui is malformed', async () => {
    const backend = createBackend();
    (backend.listApplicationActions as any).mockResolvedValueOnce([]);
    (backend.listApplicationUiSchema as any).mockResolvedValueOnce([
      {
        ...sessionListAction('ordinary-fallback'),
        dialog: { kind: 'confirm', message: 'Continue?' },
        rich_ui: { value_path: 'metadata.value' },
      },
    ]);

    const registry = new PluginsRegistry({
      backend,
      cacheKey: 'plugins-registry-rich-fallback',
    });
    await registry.load();

    expect(registry.getSnapshot().sessionListActions).toHaveLength(1);
    expect(registry.getSnapshot().sessionListActions[0].dialog.kind).toBe('confirm');
    expect(registry.getSnapshot().sessionListActions[0].rich_ui).toBeUndefined();
    expect(
      registry.getSnapshot().sessionListDiagnostics.map((diagnostic) => diagnostic.code),
    ).toContain('invalid_session_list_rich_ui');
  });

  it('publishes normalized filters and an explicit main-search conflict', async () => {
    const backend = createBackend();
    (backend.listApplicationActions as any).mockResolvedValueOnce([]);
    (backend.listApplicationUiSchema as any).mockResolvedValueOnce([
      {
        ui_type: 'session_list_filter',
        plugin: 'first',
        id: 'first-search',
        label: 'First',
        data: 'session_id',
        type: 'text',
        match: 'contains',
        main_search: true,
      },
      {
        ui_type: 'session_list_filter',
        plugin: 'filters',
        id: 'archived',
        label: 'Archived',
        data: 'metadata.archived',
        type: 'boolean',
        match: 'equals',
        default: false,
      },
      {
        ui_type: 'session_list_filter',
        plugin: 'second',
        id: 'second-search',
        label: 'Second',
        data: 'preview',
        type: 'text',
        match: 'contains',
        main_search: true,
      },
    ]);

    const registry = new PluginsRegistry({
      backend,
      cacheKey: 'plugins-registry-filter-conflict',
    });
    await registry.load();

    const snapshot = registry.getSnapshot();
    expect(snapshot.sessionListFilterSchema.mainSearch).toBeNull();
    expect(snapshot.sessionListFilterSchema.mainSearchConflict).toBe(true);
    expect(snapshot.sessionListFilterSchema.filters.map((filter) => filter.id)).toEqual([
      'archived',
    ]);
    expect(snapshot.sessionListDiagnostics.map((item) => item.code)).toContain(
      'ambiguous_session_list_main_search',
    );
  });

  it('refreshes application session-list declarations after server settings change', async () => {
    const backend = createBackend();
    (backend.listApplicationActions as any).mockResolvedValue([]);
    (backend.listApplicationUiSchema as any)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        {
          ui_type: 'session_list_field',
          plugin: 'session_status',
          id: 'session_status_meta',
          role: 'meta',
          data: 'session_status_label',
          order: 100,
        },
      ]);

    const registry = new PluginsRegistry({
      backend,
      cacheKey: 'plugins-registry-server-settings',
    });
    await registry.load();
    expect(registry.getSnapshot().sessionListFields).toEqual([]);

    emitServerSettingsInvalidated(backend, {
      reason: 'server_settings_updated',
    });

    await vi.waitFor(() => {
      expect(registry.getSnapshot().sessionListFields).toEqual([
        expect.objectContaining({ id: 'session_status_meta', order: 100 }),
      ]);
    });
    expect(backend.listApplicationUiSchema).toHaveBeenCalledTimes(2);

    registry.close();
    emitServerSettingsInvalidated(backend, {
      reason: 'server_settings_updated',
    });
    await Promise.resolve();
    expect(backend.listApplicationUiSchema).toHaveBeenCalledTimes(2);
  });
});