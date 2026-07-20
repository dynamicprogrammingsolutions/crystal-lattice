import { describe, expect, it, vi } from 'vitest';

import {
  selectApplicationPlugins,
  type ApplicationPluginsContextValue,
} from './applicationPlugins';

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
      sessionListPinnedToggles: [],
      sessionListDiagnostics: [diagnostic],
    });
  });
});
