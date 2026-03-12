import { describe, expect, it } from 'vitest';

import {
  mergeSessionScopedActionElements,
  selectSessionScopedActionElements,
} from '../actionSources';

describe('session-scoped action sources', () => {
  it('selects only valid session-scoped action elements from UI schema', () => {
    const result = selectSessionScopedActionElements({
      uiSchemaElements: [
        { ui_type: 'session_action', plugin: 'provider_ext', id: 'compact', action_id: 'compact', label: 'Compact' },
        { ui_type: 'message_action', plugin: 'provider_ext', id: 'annotate', action_id: 'annotate', label: 'Annotate' },
        { ui_type: 'session_action', plugin: 'broken', id: '', action_id: 'bad', label: 'Broken' },
        { ui_type: 'status_bar', plugin: 'meta', data: 'x' },
      ],
      uiType: 'session_action',
    });

    expect(result).toEqual([
      {
        ui_type: 'session_action',
        plugin: 'provider_ext',
        id: 'compact',
        action_id: 'compact',
        label: 'Compact',
      },
    ]);
  });

  it('merges application and session-scoped actions while preferring UI schema collisions', () => {
    const result = mergeSessionScopedActionElements({
      applicationActions: [
        {
          ui_type: 'session_action',
          plugin: 'application_actions',
          id: 'reload_native',
          action_id: 'reload_native',
          label: 'Reload native',
        },
        {
          ui_type: 'session_action',
          plugin: 'application_actions',
          id: 'copy_session',
          action_id: 'copy_session',
          label: 'Copy session',
        },
      ],
      uiSchemaElements: [
        {
          ui_type: 'session_action',
          plugin: 'provider_ext',
          id: 'reload_native',
          action_id: 'compact_native_history',
          label: 'Compact native history',
          action_owner: 'provider_extension',
        },
        {
          ui_type: 'session_action',
          plugin: 'provider_ext',
          id: 'trim_reasoning',
          action_id: 'trim_reasoning',
          label: 'Trim reasoning',
          action_owner: 'provider_extension',
        },
      ],
      uiType: 'session_action',
    });

    expect(result).toEqual([
      {
        ui_type: 'session_action',
        plugin: 'provider_ext',
        id: 'reload_native',
        action_id: 'compact_native_history',
        label: 'Compact native history',
        action_owner: 'provider_extension',
      },
      {
        ui_type: 'session_action',
        plugin: 'application_actions',
        id: 'copy_session',
        action_id: 'copy_session',
        label: 'Copy session',
      },
      {
        ui_type: 'session_action',
        plugin: 'provider_ext',
        id: 'trim_reasoning',
        action_id: 'trim_reasoning',
        label: 'Trim reasoning',
        action_owner: 'provider_extension',
      },
    ]);
  });
});