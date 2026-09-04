import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';
import type {
  AgentBackend,
  ExecuteActionResponse,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import { ApplicationPluginsProvider } from '@crystal-lattice/frontend-sdk-react';

import { ChatPane } from '../chat/ChatPane';
import { useDesktopTheme } from '../theme/useDesktopTheme';

const SESSION_ID = 'desktop-rich-session-ui';

function actionResponse(actionId: string): ExecuteActionResponse {
  return {
    status: 'ok',
    plugin: 'rich_session_ui',
    action_id: actionId,
    result: {
      mutations: {
        created_session_ids: [],
        updated_session_ids: [SESSION_ID],
        deleted_session_ids: [],
      },
      ui_effects: {
        reload_session_ids: [SESSION_ID],
      },
    },
  };
}

function createHarnessBackend(options: {
  onModelChange: (value: string) => void;
  onAction: (value: string) => void;
  onSummaryChange: (summary: SessionSummary) => void;
}): AgentBackend {
  let overrides: Record<string, unknown> = {};
  let summary: SessionSummary = {
    session_id: SESSION_ID,
    modified: 1,
    preview: 'Desktop rich UI harness',
    metadata: { enabled: false, status: 'todo' },
  };

  return {
    kind: 'inProcess',
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: true,
      sessionConfigOverrides: true,
      sessionPlugins: false,
      applicationActions: true,
      applicationConfig: false,
    }),
    listAgents: async () => ['anthropic'],
    listSessions: async () => [summary],
    getSessionSummary: async () => summary,
    getSessionAgent: async () => 'anthropic',
    switchSessionAgent: async () => {},
    listMessages: async () => ({
      messages: [],
      cursorEventId: '0',
      activeRequestId: null,
    }),
    getLatestEventId: async () => '0',
    listEvents: async () => ({
      events: [],
      latestEventId: '0',
      cursorExpired: false,
    }),
    getSessionUiSchema: async () => [
      {
        ui_type: 'config',
        plugin: 'anthropic',
        type: 'dropdown',
        key: 'model',
        label: 'Model',
        options: [
          { value: 'claude-a', label: 'Claude A' },
          { value: 'claude-b', label: 'Claude B' },
        ],
        allow_custom_value: true,
        rich_ui: {
          kind: 'dropdown',
          label: 'Model',
          options: [
            { value: 'claude-a', label: 'Claude A' },
            { value: 'claude-b', label: 'Claude B' },
          ],
          allow_custom_value: true,
          custom_value_label: 'Other model…',
          custom_value_placeholder: 'Enter a model ID',
          placements: ['composer'],
          default_pinned: true,
          icon: 'cpu',
        },
      },
    ],
    getSessionApplicationUiSchema: async () => [
      {
        ui_type: 'session_action',
        plugin: 'rich_session_ui',
        id: 'toggle_feature',
        label: 'Toggle feature',
        icon: 'zap',
        action_id: 'toggle_feature',
        dialog: { kind: 'none' },
        rich_ui: {
          kind: 'toggle',
          value_path: 'metadata.enabled',
          missing_value: false,
          active_value: true,
          default_pinned: true,
          placements: ['session_header'],
          appearance: {
            active: { tone: 'success' },
            inactive: { tone: 'muted' },
          },
        },
      },
      {
        ui_type: 'session_action',
        plugin: 'rich_session_ui',
        id: 'set_status',
        label: 'Set status',
        icon: 'circle',
        action_id: 'set_status',
        param_map: { status: '$dialog.status' },
        dialog: {
          kind: 'form',
          inputs: [
            {
              name: 'status',
              type: 'select',
              options: [
                { value: 'todo', label: 'To do' },
                { value: 'done', label: 'Done' },
              ],
            },
          ],
        },
        rich_ui: {
          kind: 'list',
          value_path: 'metadata.status',
          missing_value: 'todo',
          input_name: 'status',
          default_pinned: true,
          placements: ['composer'],
          options: [
            { value: 'todo', label: 'To do', tone: 'muted' },
            { value: 'done', label: 'Done', tone: 'success' },
          ],
        },
      },
    ],
    listApplicationActions: async () => [
      {
        plugin: 'rich_session_ui',
        id: 'toggle_feature',
        label: 'Toggle feature',
        inputs: {},
      },
      {
        plugin: 'rich_session_ui',
        id: 'set_status',
        label: 'Set status',
        inputs: { status: { type: 'string', required: true } },
      },
    ],
    listApplicationUiSchema: async () => [],
    executeAction: async (params: {
      actionId: string;
      inputs: Record<string, unknown>;
    }) => {
      if (params.actionId === 'toggle_feature') {
        const enabled = summary.metadata?.enabled !== true;
        summary = {
          ...summary,
          modified: summary.modified + 1,
          metadata: { ...summary.metadata, enabled },
        };
        options.onSummaryChange(summary);
        options.onAction(`toggle_feature:${String(enabled)}`);
      } else if (params.actionId === 'set_status') {
        const status =
          typeof params.inputs.status === 'string'
            ? params.inputs.status
            : 'missing';
        summary = {
          ...summary,
          modified: summary.modified + 1,
          metadata: { ...summary.metadata, status },
        };
        options.onSummaryChange(summary);
        options.onAction(`set_status:${status}`);
      }
      return actionResponse(params.actionId);
    },
    getSessionOverrides: async () => overrides,
    patchSessionOverrides: async (
      _sessionId: string,
      values: Record<string, unknown>,
    ) => {
      overrides = { ...overrides, ...values };
      options.onModelChange(
        typeof overrides.model === 'string' ? overrides.model : 'claude-a',
      );
    },
    deleteSessionOverride: async (_sessionId: string, key: string) => {
      const next = { ...overrides };
      delete next[key];
      overrides = next;
      options.onModelChange('claude-a');
    },
    getSessionConfigSchema: async () => [
      { key: 'model', type: 'string', default: 'claude-a' },
    ],
    getSessionBaseConfig: async () => ({ model: 'claude-a' }),
    listSessionSnapshots: async () => [],
    getSelectedSessionSnapshot: async () => null,
    listSessionNotifications: async () => [],
    listApplicationNotifications: async () => [],
  } as unknown as AgentBackend;
}

export function DesktopRichSessionUiHarness(): React.JSX.Element {
  const theme = useDesktopTheme();
  const [model, setModel] = useState('claude-a');
  const [lastAction, setLastAction] = useState('none');
  const [summary, setSummary] = useState<SessionSummary>({
    session_id: SESSION_ID,
    modified: 1,
    preview: 'Desktop rich UI harness',
    metadata: { enabled: false, status: 'todo' },
  });
  const backend = useMemo(
    () =>
      createHarnessBackend({
        onModelChange: setModel,
        onAction: setLastAction,
        onSummaryChange: setSummary,
      }),
    [],
  );

  return (
    <ThemeProvider theme={theme}>
      <ApplicationPluginsProvider
        backend={backend}
        connectionId="desktop-rich-session-ui"
      >
        <View
          style={styles.root}
          testID="desktop-rich-session-ui-harness-ready"
          accessibilityLabel="Desktop rich session UI harness"
        >
          <View style={styles.statusRow}>
            <Text
              testID="desktop-rich-session-ui-model"
              accessibilityLabel={`Desktop rich model ${model}`}
            >
              {model}
            </Text>
            <Text
              testID="desktop-rich-session-ui-last-action"
              accessibilityLabel={`Desktop rich action ${lastAction}`}
            >
              {lastAction}
            </Text>
          </View>
          <ChatPane
            isVisible
            isActive
            connectionId="desktop-rich-session-ui"
            connectionName="Rich UI harness"
            sessionId={SESSION_ID}
            sessionSummary={summary}
            title="Desktop rich UI harness"
            backend={backend}
            cachedEntry={{
              connectionId: 'desktop-rich-session-ui',
              sessionId: SESSION_ID,
              messages: [],
              cursorEventId: '0',
              activeRequestId: null,
              lastLoadedAt: 1,
              rangeStartText: '-50',
              rangeEndText: '',
              composeText: '',
              scrollAnchor: null,
            }}
            onUpdateCache={() => {}}
          />
        </View>
      </ApplicationPluginsProvider>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  statusRow: {
    minHeight: 24,
    paddingHorizontal: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
});
