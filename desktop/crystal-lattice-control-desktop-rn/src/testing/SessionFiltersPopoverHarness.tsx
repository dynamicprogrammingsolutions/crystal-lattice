import React, { useMemo } from 'react';
import { StyleSheet, View } from 'react-native';

import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';
import type {
  AgentBackend,
  ApplicationUiElement,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';

import { SessionsPanel } from '../panels/SessionsPanel';
import { useDesktopTheme } from '../theme/useDesktopTheme';

const CONNECTION_ID = 'session-filters-popover-harness';

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

function createHarnessBackend(): AgentBackend {
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
    listApplicationActions: async () => [],
    listApplicationUiSchema: async () => FILTER_ELEMENTS,
  } as unknown as AgentBackend;
}

export function SessionFiltersPopoverHarness(): React.JSX.Element {
  const theme = useDesktopTheme();
  const backend = useMemo(() => createHarnessBackend(), []);

  return (
    <ThemeProvider theme={theme}>
      <View style={styles.root} testID="session-filters-popover-harness-ready">
        <SessionsPanel
          focusedConnectionId={CONNECTION_ID}
          focusedConnectionName="Filter harness"
          connectionId={CONNECTION_ID}
          backend={backend}
          cachedSessions={SESSION_SUMMARIES}
          cachedLastLoadedAt={1}
          isOnline={false}
          followActiveTabEnabled={false}
          onUpdateCache={() => {}}
          onOpenSessionTab={() => {}}
        />
      </View>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
});