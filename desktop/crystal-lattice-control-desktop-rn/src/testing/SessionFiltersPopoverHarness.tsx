import React, { useMemo, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';
import type {
  AgentBackend,
  ApplicationUiElement,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';

import { SessionsPanel } from '../panels/SessionsPanel';
import { useDesktopTheme } from '../theme/useDesktopTheme';

const CONNECTION_ID = 'session-rich-actions-popover-harness';

const SESSION_SUMMARIES: SessionSummary[] = [
  {
    session_id: 'pinned-done',
    modified: 3,
    preview: 'Pinned completed session',
    metadata: {
      pinned: true,
      status: 'done',
    },
    presentation: {
      title: 'Pinned done',
      subtitle: 'Pinned session',
      meta: 'Done',
    },
  },
  {
    session_id: 'todo-session',
    modified: 2,
    preview: 'Unpinned todo session',
    metadata: {
      status: 'todo',
    },
    presentation: {
      title: 'Todo session',
      subtitle: 'Unpinned session',
      meta: 'To do',
    },
  },
  {
    session_id: 'blocked-session',
    modified: 1,
    preview: 'Blocked session',
    metadata: {
      status: 'blocked',
    },
    presentation: {
      title: 'Blocked session',
      subtitle: 'Needs attention',
      meta: 'Blocked',
    },
  },
];

const FILTER_ELEMENTS: ApplicationUiElement[] = [
  {
    ui_type: 'session_list_filter',
    plugin: 'session_main_search',
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
      {
        value: 'in_progress',
        label: 'In progress',
        tone: 'primary',
      },
      { value: 'blocked', label: 'Blocked', tone: 'danger' },
      { value: 'done', label: 'Done', tone: 'success' },
    ],
  },
];

const ACTION_ELEMENTS: ApplicationUiElement[] = [
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
      default_pinned: false,
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
    order: 30,
    action_id: 'set_session_status',
    param_map: {
      session_id: '$session.session_id',
      status: '$dialog.status',
    },
    dialog: {
      kind: 'form',
      title: 'Set status',
      inputs: [{ name: 'status', type: 'select', default: 'todo' }],
    },
    rich_ui: {
      kind: 'list',
      value_path: 'metadata.status',
      missing_value: 'todo',
      input_name: 'status',
      default_pinned: true,
      options: [
        { value: 'todo', label: 'To do', tone: 'muted' },
        { value: 'in_progress', label: 'In progress', tone: 'primary' },
        { value: 'blocked', label: 'Blocked', tone: 'danger' },
        { value: 'done', label: 'Done', tone: 'success' },
      ],
    },
  },
];

function createHarnessBackend(
  sessionsRef: React.MutableRefObject<SessionSummary[]>,
): AgentBackend {
  const execute = async (params: {
    actionId?: string;
    sessionId?: string;
    inputs: Record<string, unknown>;
  }) => {
    const actionId = params.actionId ?? 'unknown';
    const sessionId =
      typeof params.inputs.session_id === 'string'
        ? params.inputs.session_id
        : params.sessionId;
    if (!sessionId) {
      return { status: 'error', message: 'missing session_id' };
    }
    sessionsRef.current = sessionsRef.current.map(session => {
      if (session.session_id !== sessionId) {
        return session;
      }
      const metadata = { ...(session.metadata ?? {}) };
      if (actionId === 'toggle_session_pinned') {
        metadata.pinned = metadata.pinned !== true;
      } else if (actionId === 'toggle_session_archived') {
        metadata.archived = metadata.archived !== true;
      } else if (
        actionId === 'set_session_status' &&
        typeof params.inputs.status === 'string'
      ) {
        metadata.status = params.inputs.status;
      }
      const status =
        typeof metadata.status === 'string' ? metadata.status : 'todo';
      return {
        ...session,
        metadata,
        presentation: {
          title: session.presentation?.title ?? session.session_id,
          subtitle: session.presentation?.subtitle ?? null,
          meta: `Status: ${status.replace('_', ' ')}`,
        },
      };
    });
    return {
      status: 'ok',
      plugin:
        actionId === 'set_session_status' ? 'session_status' : 'session_pinned',
      action_id: actionId,
      result: {
        mutations: {
          created_session_ids: [],
          updated_session_ids: [sessionId],
          deleted_session_ids: [],
        },
        ui_effects: {},
      },
    };
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
    listSessions: async () => sessionsRef.current,
    listApplicationActions: async () => [
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
      ...FILTER_ELEMENTS,
      ...ACTION_ELEMENTS,
    ],
    executeAction: async (params: any) =>
      execute({ actionId: params.actionId, inputs: params.inputs }),
    executeSessionAction: async (params: any) =>
      execute({
        actionId: params.actionId,
        sessionId: params.sessionId,
        inputs: params.inputs,
      }),
  } as unknown as AgentBackend;
}

export function SessionFiltersPopoverHarness(): React.JSX.Element {
  const theme = useDesktopTheme();
  const sessionsRef = useRef(SESSION_SUMMARIES);
  const [watched, setWatched] = useState(false);
  const [noteEditCount, setNoteEditCount] = useState(0);
  const backend = useMemo(() => createHarnessBackend(sessionsRef), []);

  return (
    <ThemeProvider theme={theme}>
      <View style={styles.root} testID="session-filters-popover-harness-ready">
        <View
          accessible
          testID="session-filters-watchlist-marker"
          accessibilityLabel={`Sessions Watchlist ${
            watched ? 'watched' : 'not watched'
          }`}
          style={styles.accessibilityMarker}
        />
        <Text testID="session-filters-watchlist-state">
          {watched ? 'watched' : 'not-watched'}
        </Text>
        <View
          accessible
          testID="session-filters-note-marker"
          accessibilityLabel={`Sessions local note edits ${noteEditCount}`}
          style={styles.accessibilityMarker}
        />
        <Text testID="session-filters-note-state">{noteEditCount}</Text>
        <SessionsPanel
          focusedConnectionId={CONNECTION_ID}
          focusedConnectionName="Filter harness"
          connectionBaseUrl="http://127.0.0.1:9999"
          connectionId={CONNECTION_ID}
          backend={backend}
          cachedSessions={SESSION_SUMMARIES}
          cachedLastLoadedAt={1}
          isOnline
          followActiveTabEnabled={false}
          onUpdateCache={() => {}}
          onOpenSessionTab={() => {}}
          sessionNotes={
            noteEditCount > 0 ? { 'pinned-done': 'Harness note' } : {}
          }
          onEditSessionNote={() => setNoteEditCount(current => current + 1)}
          isSessionWatched={() => watched}
          onToggleSessionWatchlist={() => setWatched(current => !current)}
        />
      </View>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  accessibilityMarker: {
    width: 1,
    height: 1,
  },
});
