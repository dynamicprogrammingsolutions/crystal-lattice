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
    plugin: 'session_list_harness',
    action_id: 'set_status',
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
        plugin: 'session_list_harness',
        id: 'set_status',
        label: 'Set status',
        inputs: {
          session_id: { type: 'string', required: true },
          status: { type: 'string', required: true },
        },
      },
    ],
    listApplicationUiSchema: async () => [
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
        plugin: 'session_list_harness',
        id: 'edit-status',
        label: 'Edit status',
        icon: 'edit-3',
        action_id: 'set_status',
        param_map: {
          session_id: '$session.session_id',
          status: '$dialog.status',
        },
        dialog: {
          kind: 'form',
          title: 'Edit status',
          inputs: [
            {
              name: 'status',
              type: 'select',
              label: 'Status',
              default: 'todo',
              prefill_from: '$session.metadata.status',
              options: [
                { value: 'todo', label: 'To do' },
                { value: 'done', label: 'Done' },
              ],
            },
          ],
        },
        rich_ui: {
          value_path: 'metadata.status',
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
