import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type {
  AgentBackend,
  ExecuteActionResponse,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';

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

function successfulActionResponse(): ExecuteActionResponse {
  return {
    status: 'ok',
    plugin: 'session_status',
    action_id: 'set_session_status',
    result: {
      mutations: {
        created_session_ids: [],
        updated_session_ids: [],
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
    onSubmit(`${sessionId}:${status}`);
    return successfulActionResponse();
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
            tone: 'warning',
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
      },
    ],
    executeAction: async (params: {
      inputs: Record<string, unknown>;
    }) =>
      execute({ inputs: params.inputs }),
    executeSessionAction: async (params: {
      sessionId: string;
      inputs: Record<string, unknown>;
    }) =>
      execute({
        sessionId: params.sessionId,
        inputs: params.inputs,
      }),
  } as unknown as AgentBackend;
}

export function MobileSessionListHarness(): React.JSX.Element {
  const [submittedValue, setSubmittedValue] = useState('none');
  const backend = useMemo(
    () => createHarnessBackend(setSubmittedValue),
    [],
  );

  return (
    <ThemeProvider theme={lightTheme}>
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
