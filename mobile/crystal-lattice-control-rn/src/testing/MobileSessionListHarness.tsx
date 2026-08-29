import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type {
  AgentBackend,
  ExecuteActionResponse,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  MARKDOWN_BASE_FONT_SIZES,
  applyDisplayTypographyPreset,
} from '@crystal-lattice/frontend-rn-components';

import { ApplicationPluginsProvider } from '../ApplicationPluginsContext';
import { PinnedActionsProvider } from '../PinnedActionsContext';
import SessionsScreen from '../SessionsScreen';
import { ThemeProvider, lightTheme } from '../theme';

const SESSION_SUMMARIES: SessionSummary[] = [
  {
    session_id: 'server-first',
    modified: 1,
    preview: 'conflicting first preview',
    metadata: {
      local_title: 'Local first title',
      pinned: true,
      status: 'done',
    },
    presentation: {
      title: 'Server first title',
      subtitle: 'Server first subtitle',
      meta: 'Server first meta',
    },
  },
  {
    session_id: 'server-second',
    modified: 99,
    preview: 'conflicting second preview',
    metadata: {
      local_title: 'Local second title',
      status: 'todo',
    },
    presentation: {
      title: 'Server second title',
      subtitle: null,
      meta: null,
    },
  },
];

function successfulActionResponse(actionId: string): ExecuteActionResponse {
  return {
    status: 'ok',
    plugin: 'session_status',
    action_id: actionId,
    result: {
      mutations: {
        created_session_ids: [],
        updated_session_ids: ['server-first'],
        deleted_session_ids: [],
      },
      ui_effects: {},
    },
  };
}

function createHarnessBackend(
  onSubmit: (value: string) => void,
): AgentBackend {
  const execute = async (params: {
    sessionId?: string;
    actionId?: string;
    inputs: Record<string, unknown>;
  }): Promise<ExecuteActionResponse> => {
    const sessionId =
      typeof params.inputs.session_id === 'string'
        ? params.inputs.session_id
        : params.sessionId || 'missing-session';
    const status =
      typeof params.inputs.status === 'string'
        ? params.inputs.status
        : 'missing-status';
    const actionId = params.actionId || 'missing-action';
    onSubmit(`${sessionId}:${actionId}:${status}`);
    return successfulActionResponse(actionId);
  };

  return {
    kind: 'inProcess',
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: false,
      sessionConfigOverrides: false,
      sessionPlugins: false,
      applicationActions: true,
      applicationConfig: false,
    }),
    listAgents: async () => ['default'],
    listSessions: async () => SESSION_SUMMARIES,
    listApplicationActions: async () => [
      {
        plugin: 'session_status',
        id: 'set_session_status',
        label: 'Set status',
        inputs: {
          session_id: { type: 'string', required: true },
          status: { type: 'string', required: true },
        },
      },
      {
        plugin: 'session_pinned',
        id: 'toggle_session_pinned',
        label: 'Toggle pin',
        inputs: { session_id: { type: 'string', required: true } },
      },
      {
        plugin: 'session_archive',
        id: 'toggle_session_archived',
        label: 'Toggle archive',
        inputs: { session_id: { type: 'string', required: true } },
      },
    ],
    listApplicationUiSchema: async () => [
      {
        ui_type: 'session_list_filter',
        plugin: 'session_list_harness',
        id: 'session_search',
        label: 'Search',
        icon: 'search',
        order: 0,
        data: [
          'session_id',
          'preview',
          'presentation.title',
          'presentation.subtitle',
          'presentation.meta',
        ],
        type: 'text',
        match: 'contains',
        case_sensitive: false,
        default: '',
        main_search: true,
      },
      {
        ui_type: 'session_list_filter',
        plugin: 'session_archive',
        id: 'archive_state',
        label: 'Archive state',
        icon: 'archive',
        order: 30,
        data: 'metadata.archived',
        type: 'boolean',
        match: 'equals',
        missing_value: false,
        default: false,
        options: [
          { value: false, label: 'Not archived', tone: 'muted' },
          { value: true, label: 'Archived', tone: 'primary' },
        ],
      },
      {
        ui_type: 'session_list_filter',
        plugin: 'session_pinned',
        id: 'pinned_state',
        label: 'Pinned',
        icon: 'star',
        order: 10,
        data: 'metadata.pinned',
        type: 'boolean',
        match: 'equals',
        missing_value: false,
        default: null,
        options: [
          {
            value: false,
            label: 'Not pinned',
            icon: 'star',
            tone: 'muted',
          },
          {
            value: true,
            label: 'Pinned',
            icon: 'star',
            tone: 'highlight',
          },
        ],
      },
      {
        ui_type: 'session_list_filter',
        plugin: 'session_status',
        id: 'session_status',
        label: 'Status',
        icon: 'circle',
        order: 20,
        data: 'metadata.status',
        type: 'select',
        match: 'one_of',
        multiple: true,
        missing_value: 'todo',
        default: [],
        options: [
          { value: 'todo', label: 'To do', tone: 'muted' },
          { value: 'in_progress', label: 'In progress', tone: 'primary' },
          { value: 'blocked', label: 'Blocked', tone: 'danger' },
          { value: 'done', label: 'Done', tone: 'success' },
        ],
      },
      {
        ui_type: 'session_list_field',
        plugin: 'session_list_harness',
        id: 'local-title',
        role: 'title',
        data: 'metadata.local_title',
        template: '{{data}}',
        order: 0,
      },
      {
        ui_type: 'session_list_action',
        plugin: 'session_pinned',
        id: 'toggle_session_pinned',
        label: 'Pin/unpin session',
        icon: 'star',
        order: 10,
        action_id: 'toggle_session_pinned',
        param_map: { session_id: '$session.session_id' },
        dialog: { kind: 'none' },
        rich_ui: {
          kind: 'toggle',
          value_path: 'metadata.pinned',
          missing_value: false,
          active_value: true,
          default_pinned: true,
          placements: ['header_trailing', 'actions_bar'],
          appearance: {
            active: { tone: 'highlight' },
            inactive: { tone: 'muted' },
          },
        },
      },
      {
        ui_type: 'session_list_action',
        plugin: 'session_archive',
        id: 'toggle_session_archived',
        label: 'Archive/restore session',
        icon: 'archive',
        order: 20,
        action_id: 'toggle_session_archived',
        param_map: { session_id: '$session.session_id' },
        dialog: { kind: 'none' },
        rich_ui: {
          kind: 'toggle',
          value_path: 'metadata.archived',
          missing_value: false,
          active_value: true,
          default_pinned: true,
          appearance: {
            active: { tone: 'primary' },
            inactive: { tone: 'muted' },
          },
        },
      },
      {
        ui_type: 'session_list_action',
        plugin: 'session_status',
        id: 'set_session_status',
        label: 'Set status',
        icon: 'circle',
        action_id: 'set_session_status',
        param_map: {
          session_id: '$session.session_id',
          status: '$dialog.status',
        },
        dialog: {
          kind: 'form',
          title: 'Set status',
          inputs: [
            {
              name: 'status',
              type: 'select',
              label: 'Status',
              default: 'todo',
              prefill_from: '$session.metadata.status',
              options: [
                { value: 'todo', label: 'To do', tone: 'muted' },
                {
                  value: 'in_progress',
                  label: 'In progress',
                  tone: 'primary',
                },
                { value: 'blocked', label: 'Blocked', tone: 'danger' },
                { value: 'done', label: 'Done', tone: 'success' },
              ],
            },
          ],
        },
        rich_ui: {
          kind: 'list',
          value_path: 'metadata.status',
          missing_value: 'todo',
          input_name: 'status',
          default_pinned: false,
          options: [
            { value: 'todo', label: 'To do', tone: 'muted' },
            {
              value: 'in_progress',
              label: 'In progress',
              tone: 'primary',
            },
            { value: 'blocked', label: 'Blocked', tone: 'danger' },
            { value: 'done', label: 'Done', tone: 'success' },
          ],
        },
      },
      {
        ui_type: 'session_list_action',
        plugin: 'session_status',
        id: 'set_session_status_fallback',
        label: 'Set status (fallback)',
        icon: 'circle',
        action_id: 'set_session_status',
        param_map: {
          session_id: '$session.session_id',
          status: '$dialog.status',
        },
        dialog: {
          kind: 'form',
          title: 'Set status (fallback)',
          inputs: [
            {
              name: 'status',
              type: 'select',
              label: 'Status',
              default: 'todo',
              prefill_from: '$session.metadata.status',
              options: [
                { value: 'todo', label: 'To do', tone: 'muted' },
                {
                  value: 'in_progress',
                  label: 'In progress',
                  tone: 'primary',
                },
                { value: 'blocked', label: 'Blocked', tone: 'danger' },
                { value: 'done', label: 'Done', tone: 'success' },
              ],
            },
          ],
        },
        rich_ui: { kind: 'future_list' },
      },
    ],
    executeAction: async (params: {
      actionId?: string;
      inputs: Record<string, unknown>;
    }) =>
      execute({ actionId: params.actionId, inputs: params.inputs }),
    executeSessionAction: async (params: {
      sessionId: string;
      actionId?: string;
      inputs: Record<string, unknown>;
    }) =>
      execute({
        sessionId: params.sessionId,
        actionId: params.actionId,
        inputs: params.inputs,
      }),
  } as unknown as AgentBackend;
}

interface MobileSessionListHarnessProps {
  clcDisplayPreset?: string;
}

export function MobileSessionListHarness({
  clcDisplayPreset,
}: MobileSessionListHarnessProps): React.JSX.Element {
  const [submittedValue, setSubmittedValue] = useState('none');
  const backend = useMemo(
    () => createHarnessBackend(setSubmittedValue),
    [],
  );
  const theme = useMemo(() => {
    const baseFontSize =
      clcDisplayPreset === 'largest'
        ? MARKDOWN_BASE_FONT_SIZES[MARKDOWN_BASE_FONT_SIZES.length - 1]
        : DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize;
    return applyDisplayTypographyPreset(lightTheme, baseFontSize);
  }, [clcDisplayPreset]);

  return (
    <ThemeProvider theme={theme}>
      <PinnedActionsProvider>
        <ApplicationPluginsProvider
          backend={backend}
          connectionId="session-list-harness"
        >
          <View style={styles.root} testID="session-list-harness-ready">
            <SessionsScreen
              backend={backend}
              connectionId="session-list-harness"
              cachedSessions={SESSION_SUMMARIES}
              lastLoadedAt={1}
              isActive
              onUpdateCache={() => {}}
              onSelectSession={() => {}}
            />
            <Text
              style={styles.submission}
              testID="session-list-harness-submission"
            >
              {submittedValue}
            </Text>
          </View>
        </ApplicationPluginsProvider>
      </PinnedActionsProvider>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  submission: {
    minHeight: 20,
    paddingHorizontal: 12,
    paddingVertical: 2,
    color: '#000000',
    fontSize: 12,
  },
});
