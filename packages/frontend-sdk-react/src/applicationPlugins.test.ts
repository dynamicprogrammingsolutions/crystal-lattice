import { describe, expect, it, vi } from 'vitest';

import {
  selectApplicationPlugins,
  type ApplicationPluginsContextValue,
} from './applicationPlugins';
import { normalizeSessionListFilterSchema } from '@crystal-lattice/frontend-sdk';

describe('selectApplicationPlugins', () => {
  it('propagates session-list diagnostics with the plugin collections', () => {
    const diagnostic = {
      code: 'invalid_session_list_rich_ui',
      message: 'rich_ui.kind must be a non-empty string',
      elementId: 'edit-status',
    };
    const context: ApplicationPluginsContextValue = {
      actionsById: {},
      sessionActions: [],
      messageActions: [],
      sessionListActions: [],
      sessionListFields: [],
      sessionListFilterSchema: normalizeSessionListFilterSchema([]),
      sessionListPinnedToggles: [],
      sessionListDiagnostics: [diagnostic],
      loading: false,
      error: null,
      refresh: vi.fn(async () => {}),
      invalidate: vi.fn(),
    };

    expect(selectApplicationPlugins(context)).toEqual({
      actionsById: {},
      sessionActions: [],
      messageActions: [],
      sessionListActions: [],
      sessionListFields: [],
      sessionListFilterSchema: normalizeSessionListFilterSchema([]),
      sessionListPinnedToggles: [],
      sessionListDiagnostics: [diagnostic],
    });
  });

  it('propagates the normalized filter schema used by frontend session lists', () => {
    const schema = normalizeSessionListFilterSchema([
      {
        ui_type: 'session_list_filter',
        id: 'session-search',
        label: 'Search',
        data: 'session_id',
        type: 'text',
        match: 'contains',
        main_search: true,
      },
    ]);
    const context: ApplicationPluginsContextValue = {
      actionsById: {},
      sessionActions: [],
      messageActions: [],
      sessionListActions: [],
      sessionListFields: [],
      sessionListFilterSchema: schema,
      sessionListPinnedToggles: [],
      sessionListDiagnostics: [],
      loading: false,
      error: null,
      refresh: vi.fn(async () => {}),
      invalidate: vi.fn(),
    };

    expect(selectApplicationPlugins(context).sessionListFilterSchema).toBe(
      schema,
    );
  });
});
