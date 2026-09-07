import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';

import type {
  AgentBackend,
  ExecuteActionResponse,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';

import { ApplicationPluginsProvider } from '../ApplicationPluginsContext';
import { PinnedActionsProvider } from '../PinnedActionsContext';
import SessionChatScreen from '../SessionChatScreen';
import GlobalDisplayLayer from '../components/GlobalDisplayLayer';
import { ThemeProvider, lightTheme } from '../theme';

const SESSION_ID = 'rich-session-ui';
const CONNECTION_ID = 'rich-session-ui-followup-v2';

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
}): AgentBackend {
  let overrides: Record<string, unknown> = {};
  let summary: SessionSummary = {
    session_id: SESSION_ID,
    modified: 1,
    preview: 'Rich UI harness',
    metadata: {
      enabled: false,
      status: 'todo',
    },
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
        icon: 'cpu',
        options: [
          { value: 'claude-a', label: 'Claude A' },
          { value: 'claude-b', label: 'Claude B' },
        ],
        placeholder: 'Search models or enter a model ID',
        custom_value: {
          enabled: true,
          pattern: '^[^\\s]+$',
          option_label: "Use '{value}' as a custom model ID",
        },
        rich_ui: {
          kind: 'dropdown',
          label: 'Model',
          show_label: false,
          options: [
            { value: 'claude-a', label: 'Claude A' },
            { value: 'claude-b', label: 'Claude B' },
          ],
          placeholder: 'Search models or enter a model ID',
          custom_value: {
            enabled: true,
            pattern: '^[^\\s]+$',
            option_label: "Use '{value}' as a custom model ID",
          },
          placements: ['composer'],
          default_pinned: true,
        },
      },
      {
        ui_type: 'config',
        plugin: 'anthropic',
        type: 'select',
        key: 'reasoning_effort',
        label: 'Reasoning effort',
        icon: 'sliders',
        options: [
          { value: 'medium', label: 'Medium' },
          { value: 'high', label: 'High' },
        ],
        rich_ui: {
          kind: 'dropdown',
          label: 'Reasoning effort',
          show_label: false,
          show_icon: false,
          options: [
            { value: 'medium', label: 'Medium' },
            { value: 'high', label: 'High' },
          ],
          placements: ['composer'],
          default_pinned: true,
        },
      },
      {
        ui_type: 'config',
        plugin: 'claude_web_search_tool',
        type: 'checkbox',
        key: 'web_search_enabled',
        label: 'Enable web search',
        icon: 'globe',
        rich_ui: {
          kind: 'toggle',
          label: 'Web search',
          show_label: false,
          placements: ['composer'],
          default_pinned: true,
          options: [
            {
              value: false,
              label: 'Off',
              icon: 'globe',
              tone: 'primary',
            },
            {
              value: true,
              label: 'On',
              icon: 'globe',
              tone: 'success',
            },
          ],
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
        param_map: {
          status: '$dialog.status',
        },
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
        inputs: {
          status: { type: 'string', required: true },
        },
      },
    ],
    listApplicationUiSchema: async () => [],
    executeAction: async (params: {
      actionId: string;
      inputs: Record<string, unknown>;
    }) => {
      if (params.actionId === 'toggle_feature') {
        const nextEnabled = summary.metadata?.enabled !== true;
        summary = {
          ...summary,
          modified: summary.modified + 1,
          metadata: {
            ...summary.metadata,
            enabled: nextEnabled,
          },
        };
        options.onAction(`toggle_feature:${String(nextEnabled)}`);
      } else if (params.actionId === 'set_status') {
        const status =
          typeof params.inputs.status === 'string'
            ? params.inputs.status
            : 'missing';
        summary = {
          ...summary,
          modified: summary.modified + 1,
          metadata: {
            ...summary.metadata,
            status,
          },
        };
        options.onAction(`set_status:${status}`);
      }
      return actionResponse(params.actionId);
    },
    getSessionOverrides: async () => overrides,
    patchSessionOverrides: async (
      _sessionId: string,
      values: Record<string, unknown>
    ) => {
      overrides = { ...overrides, ...values };
      options.onModelChange(
        typeof overrides.model === 'string' ? overrides.model : 'claude-a'
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
      { key: 'reasoning_effort', type: 'string', default: 'medium' },
      { key: 'web_search_enabled', type: 'boolean', default: false },
    ],
    getSessionBaseConfig: async () => ({
      model: 'claude-a',
      reasoning_effort: 'medium',
      web_search_enabled: false,
    }),
    listSessionSnapshots: async () => [],
    getSelectedSessionSnapshot: async () => null,
    listSessionNotifications: async () => [],
    listApplicationNotifications: async () => [],
  } as unknown as AgentBackend;
}

export function MobileRichSessionUiHarness(): React.JSX.Element {
  const [model, setModel] = useState('claude-a');
  const [lastAction, setLastAction] = useState('none');
  const backend = useMemo(
    () =>
      createHarnessBackend({
        onModelChange: setModel,
        onAction: setLastAction,
      }),
    []
  );
  const sessionSummary: SessionSummary = {
    session_id: SESSION_ID,
    modified: 1,
    preview: 'Rich UI harness',
    metadata: {
      enabled: false,
      status: 'todo',
    },
  };

  return (
    <SafeAreaProvider>
      <ThemeProvider theme={lightTheme}>
        <SafeAreaView
          style={styles.root}
          testID="rich-session-ui-harness-ready"
        >
          <View style={styles.statusRow}>
            <Text testID="rich-session-ui-model">{model}</Text>
            <Text testID="rich-session-ui-last-action">{lastAction}</Text>
          </View>
          <PinnedActionsProvider>
            <ApplicationPluginsProvider
              backend={backend}
              connectionId={CONNECTION_ID}
            >
              <GlobalDisplayLayer
                backend={backend}
                connectionId={CONNECTION_ID}
              >
                <View style={styles.screen}>
                  <SessionChatScreen
                    backend={backend}
                    connectionId={CONNECTION_ID}
                    isActive
                    sessionId={SESSION_ID}
                    sessionSummary={sessionSummary}
                    cachedMessages={[]}
                    lastLoadedAt={1}
                    cachedEventsCursorId="0"
                    cachedActiveRequestId={null}
                    onUpdateCache={() => {}}
                    onUpdateSessionSummaries={() => {}}
                    onBack={() => {}}
                    onNavigateToSession={() => {}}
                    initialComposeText=""
                    initialScrollAnchor={null}
                    initialRangeStartText="-50"
                    initialRangeEndText=""
                    onSaveComposeText={() => {}}
                    onSaveScrollAnchor={() => {}}
                    onSaveHistoryRange={() => {}}
                    debugTimeline={[]}
                    onAppendDebugTimelineEntry={() => {}}
                  />
                </View>
              </GlobalDisplayLayer>
            </ApplicationPluginsProvider>
          </PinnedActionsProvider>
        </SafeAreaView>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: lightTheme.background,
  },
  statusRow: {
    minHeight: 24,
    paddingHorizontal: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  screen: {
    flex: 1,
    paddingHorizontal: 8,
  },
});
