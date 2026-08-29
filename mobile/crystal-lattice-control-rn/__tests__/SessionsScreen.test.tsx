import React from 'react';
import { StyleSheet } from 'react-native';
import { fireEvent, screen } from '@testing-library/react-native';

import {
  buildActionDialogInitialValues,
  normalizeSessionListActionElement,
  normalizeSessionListFilterSchema,
  type SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import {
  MARKDOWN_BASE_FONT_SIZES,
  applyDisplayTypographyPreset,
} from '@crystal-lattice/frontend-rn-components';
import {
  useAgentsController,
  useHydrateControllerFromCache,
  useSessionsController,
} from '@crystal-lattice/frontend-sdk-react';

import {
  useApplicationPlugins,
  useApplicationPluginsContext,
} from '../src/ApplicationPluginsContext';
import SessionsScreen, {
  createSessionsScreenStyles,
} from '../src/SessionsScreen';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';
import { ThemeProvider, lightTheme } from '../src/theme';

jest.mock('@crystal-lattice/frontend-sdk-react', () => {
  const actual = jest.requireActual('@crystal-lattice/frontend-sdk-react');
  return {
    __esModule: true,
    ...actual,
    useAgentsController: jest.fn(),
    useHydrateControllerFromCache: jest.fn(),
    useSessionsController: jest.fn(),
  };
});

jest.mock('../src/ApplicationPluginsContext', () => ({
  __esModule: true,
  useApplicationPlugins: jest.fn(),
  useApplicationPluginsContext: jest.fn(),
}));

jest.mock('../src/usePersistentPinnedActions', () => ({
  __esModule: true,
  usePersistentPinnedActions: () => ({
    pinned: [],
    setPinned: jest.fn(),
  }),
}));

jest.mock('@crystal-lattice/frontend-rn-components', () => {
  const actual = jest.requireActual('@crystal-lattice/frontend-rn-components');
  const ReactModule = require('react');
  const { Text, TouchableOpacity, View } = require('react-native');
  const {
    buildActionDialogInitialValues: buildInitialValues,
  } = require('@crystal-lattice/frontend-sdk');

  return {
    __esModule: true,
    ...actual,
    ActionsMenuBar: ({ baseActions }: any) =>
      ReactModule.createElement(
        View,
        { testID: 'mock-sessions-actions-menu' },
        (baseActions || []).map((action: any) =>
          ReactModule.createElement(
            Text,
            {
              key: action.key,
              testID: `mock-sessions-action-${String(action.key).replace(/\u0000/g, '-')}`,
            },
            action.label,
          ),
        ),
      ),
    SessionListActionsBar: ({
      pluginActions,
      session,
      onExecuteAction,
      onFallbackAction,
      onPresentRichList,
    }: any) =>
      ReactModule.createElement(
        View,
        null,
        (pluginActions || []).map((action: any) =>
          ReactModule.createElement(
            TouchableOpacity,
            {
              key: action.id,
              testID: `mock-session-action-${action.id}`,
              onPress: () => {
                if (action.rich_ui?.kind === 'toggle') {
                  onExecuteAction(action);
                } else if (action.rich_ui?.kind === 'list') {
                  onPresentRichList(action);
                } else {
                  onFallbackAction(action);
                }
              },
            },
            ReactModule.createElement(Text, null, action.label),
          ),
        ),
      ),
    ApplicationActionDialog: ({
      visible,
      dialog,
      prefillContext,
      titleFallback,
    }: any) => {
      if (!visible) {
        return null;
      }
      const inputs = dialog?.kind === 'form' && Array.isArray(dialog.inputs)
        ? dialog.inputs
        : [];
      const values = buildInitialValues(inputs, prefillContext);
      return ReactModule.createElement(
        View,
        { testID: 'mock-application-action-dialog' },
        ReactModule.createElement(Text, null, dialog?.title || titleFallback),
        inputs.map((input: any) =>
          ReactModule.createElement(
            Text,
            {
              key: input.name,
              testID: `mock-dialog-value-${input.name}`,
            },
            values[input.name],
          ),
        ),
      );
    },
  };
});

const mockUseSessionsController =
  useSessionsController as jest.MockedFunction<typeof useSessionsController>;
const mockUseAgentsController =
  useAgentsController as jest.MockedFunction<typeof useAgentsController>;
const mockUseHydrateControllerFromCache =
  useHydrateControllerFromCache as jest.MockedFunction<
    typeof useHydrateControllerFromCache
  >;
const mockUseApplicationPlugins =
  useApplicationPlugins as jest.MockedFunction<typeof useApplicationPlugins>;
const mockUseApplicationPluginsContext =
  useApplicationPluginsContext as jest.MockedFunction<
    typeof useApplicationPluginsContext
  >;

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
      meta: 'Server first meta · Status: Done',
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

const EMPTY_FILTER_SCHEMA = normalizeSessionListFilterSchema([]);

const normalizedAction = normalizeSessionListActionElement({
  ui_type: 'session_list_action',
  id: 'edit-status',
  plugin: 'fixture',
  label: 'Edit status',
  action_id: 'set_status',
  dialog: {
    kind: 'form',
    title: 'Edit status form',
    inputs: [
      {
        name: 'status',
        type: 'select',
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
});

const sessionsController = {
  load: jest.fn(async () => SESSION_SUMMARIES),
  loadIfStale: jest.fn(async () => null),
  createSession: jest.fn(),
  hydrateFromCache: jest.fn(),
};
const agentsController = {
  ensureLoaded: jest.fn(async () => ['default']),
};
const refreshApplicationPlugins = jest.fn(async () => {});

function applicationPluginsResult(
  sessionListFilterSchema = EMPTY_FILTER_SCHEMA,
) {
  return {
    actionsById: {
      set_status: {
        id: 'set_status',
        plugin: 'fixture',
        label: 'Set status',
        inputs: {},
      },
    },
    sessionActions: [],
    messageActions: [],
    sessionListActions: [normalizedAction.value!],
    sessionListFields: [
      {
        ui_type: 'session_list_field',
        plugin: 'fixture',
        id: 'local-title',
        role: 'title',
        data: 'metadata.local_title',
      },
    ],
    sessionListFilterSchema,
    sessionListDiagnostics: normalizedAction.diagnostics,
  };
}

function renderScreen(connectionId = 'component-test') {
  return renderWithMobileProviders(
    <SessionsScreen
      backend={{ kind: 'test' } as any}
      connectionId={connectionId}
      cachedSessions={SESSION_SUMMARIES}
      lastLoadedAt={1}
      isActive
      onUpdateCache={jest.fn()}
      onSelectSession={jest.fn()}
    />,
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  sessionsController.load.mockResolvedValue(SESSION_SUMMARIES);
  sessionsController.loadIfStale.mockResolvedValue(null);
  agentsController.ensureLoaded.mockResolvedValue(['default']);
  refreshApplicationPlugins.mockResolvedValue();

  mockUseSessionsController.mockReturnValue({
    controller: sessionsController as any,
    state: {
      sessions: SESSION_SUMMARIES,
      loading: false,
      error: null,
      lastLoadedAt: 1,
    },
  });
  mockUseAgentsController.mockReturnValue({
    controller: agentsController as any,
    state: {
      agents: ['default'],
      loading: false,
      error: null,
    },
  });
  mockUseHydrateControllerFromCache.mockImplementation(() => {});
  mockUseApplicationPlugins.mockReturnValue(applicationPluginsResult());
  mockUseApplicationPluginsContext.mockReturnValue({
    actionsById: {},
    sessionActions: [],
    messageActions: [],
    sessionListActions: [],
    sessionListFields: [],
    sessionListFilterSchema: EMPTY_FILTER_SCHEMA,
    sessionListDiagnostics: [],
    loading: false,
    error: null,
    refresh: refreshApplicationPlugins,
    invalidate: jest.fn(),
  });
});

test('hosts screen-independent application actions in the Sessions header', () => {
  mockUseApplicationPlugins.mockReturnValue({
    ...applicationPluginsResult(),
    applicationActions: [
      {
        ui_type: 'application_action',
        plugin: 'application_config',
        id: 'reload_application',
        label: 'Reload application',
        action_id: 'reload_application',
      },
    ],
  });

  renderScreen();

  expect(screen.getByTestId('sessions-screen-title').props.children).toBe(
    'Sessions',
  );
  expect(screen.getByTestId('mock-sessions-actions-menu')).toBeTruthy();
  expect(screen.getByTestId('mock-sessions-action-serverSettings').props.children).toBe(
    'Server settings',
  );
  expect(screen.getByTestId('mock-sessions-action-refreshSessions').props.children).toBe(
    'Refresh sessions',
  );
  expect(screen.getByTestId('mock-sessions-action-newSession').props.children).toBe(
    'New session',
  );
  expect(
    screen.getByTestId(
      'mock-sessions-action-application_config-reload_application',
    ).props.children,
  ).toBe('Reload application');
});

test('renders application-derived presentation in server order', () => {
  renderScreen();

  const titles = screen.getAllByTestId(/session-title-/);
  expect(titles.map((title) => title.props.children)).toEqual([
    'Server first title',
    'Server second title',
  ]);
  expect(screen.getByTestId('session-subtitle-server-first').props.children).toBe(
    'Server first subtitle',
  );
  expect(screen.getByTestId('session-meta-server-first').props.children).toBe(
    'Server first meta · Status: Done',
  );
  expect(screen.getByTestId('session-id-server-first').props.children).toBe(
    'server-first',
  );
  expect(
    screen.getByTestId('session-preview-server-second').props.children,
  ).toBe('conflicting second preview');
  expect(screen.queryByText('Local first title')).toBeNull();
});

test('maps mobile session-card text to the active semantic preset', () => {
  const largestPreset =
    MARKDOWN_BASE_FONT_SIZES[MARKDOWN_BASE_FONT_SIZES.length - 1];
  const theme = applyDisplayTypographyPreset(lightTheme, largestPreset);
  const styles = createSessionsScreenStyles(theme);

  expect(StyleSheet.flatten(styles.sessionTitle)).toMatchObject({
    fontSize: theme.typography.fontSize.large,
    lineHeight: theme.typography.lineHeight.large,
  });
  expect(StyleSheet.flatten(styles.sessionSubtitle)).toMatchObject({
    fontSize: theme.typography.fontSize.normal,
    lineHeight: theme.typography.lineHeight.normal,
  });
  expect(StyleSheet.flatten(styles.sessionPreview)).toMatchObject({
    fontSize: theme.typography.fontSize.normal,
    lineHeight: theme.typography.lineHeight.normal,
  });
  expect(StyleSheet.flatten(styles.sessionId)).toMatchObject({
    fontSize: theme.typography.fontSize.small,
    lineHeight: theme.typography.lineHeight.small,
  });
  expect(StyleSheet.flatten(styles.sessionMeta)).toMatchObject({
    fontSize: theme.typography.fontSize.tiny,
    lineHeight: theme.typography.lineHeight.tiny,
  });
  expect(StyleSheet.flatten(styles.screenTitle).marginLeft).toBe(
    StyleSheet.flatten(styles.sessionItem).padding +
      StyleSheet.flatten(styles.sessionItem).borderWidth,
  );
  expect(StyleSheet.flatten(styles.input).paddingHorizontal).toBe(
    StyleSheet.flatten(styles.sessionItem).padding,
  );
});

test('opens the ordinary form when malformed rich UI falls back', () => {
  expect(normalizedAction.value?.rich_ui).toBeUndefined();
  expect(normalizedAction.diagnostics.map((diagnostic) => diagnostic.code)).toContain(
    'invalid_session_list_rich_ui',
  );

  renderScreen();
  fireEvent.press(screen.getAllByTestId('mock-session-action-edit-status')[0]);

  expect(screen.getByTestId('mock-application-action-dialog')).toBeTruthy();
  expect(screen.getByText('Edit status form')).toBeTruthy();
  expect(screen.getByTestId('mock-dialog-value-status').props.children).toBe('done');
  expect(
    buildActionDialogInitialValues(
      normalizedAction.value!.dialog.inputs!,
      { session: SESSION_SUMMARIES[0] },
    ),
  ).toEqual({ status: 'done' });
});

test('keeps a presentation-aware fallback search when no plugin declares one', () => {
  renderScreen();

  expect(screen.getByTestId('session-main-search')).toBeTruthy();
  expect(screen.queryByTestId('session-filters-open')).toBeNull();

  fireEvent.changeText(
    screen.getByTestId('session-main-search'),
    'Server first title',
  );
  expect(screen.getByTestId('session-row-server-first')).toBeTruthy();
  expect(screen.queryByTestId('session-row-server-second')).toBeNull();
});

test('distinguishes an empty store from a filtered-empty result', () => {
  mockUseSessionsController.mockReturnValue({
    controller: sessionsController as any,
    state: {
      sessions: [],
      loading: false,
      error: null,
      lastLoadedAt: 1,
    },
  });

  renderScreen();
  expect(
    screen.getByText('No sessions found. Create one to get started.'),
  ).toBeTruthy();
  expect(
    screen.queryByText('No sessions match the active search or filters.'),
  ).toBeNull();
});

test('uses plugin search and all non-main filter controls with Reset and Show all', () => {
  const sessions: SessionSummary[] = [
    {
      session_id: 'alpha-session',
      modified: 3,
      preview: 'preview one',
      metadata: {
        archived: false,
        owner: 'alice',
        status: 'todo',
        note: 'one',
      },
      presentation: {
        title: 'Presentation one',
        subtitle: null,
        meta: null,
      },
    },
    {
      session_id: 'beta-session',
      modified: 2,
      preview: 'preview two',
      metadata: {
        archived: true,
        owner: 'alice',
        status: 'done',
        note: 'two',
      },
      presentation: {
        title: 'Presentation two',
        subtitle: null,
        meta: null,
      },
    },
    {
      session_id: 'gamma-session',
      modified: 1,
      preview: 'preview three',
      metadata: {
        owner: 'bob',
        status: 'blocked',
        note: 'three',
      },
      presentation: {
        title: 'Presentation three',
        subtitle: null,
        meta: null,
      },
    },
  ];
  mockUseSessionsController.mockReturnValue({
    controller: sessionsController as any,
    state: {
      sessions,
      loading: false,
      error: null,
      lastLoadedAt: 1,
    },
  });
  const schema = normalizeSessionListFilterSchema([
    {
      ui_type: 'session_list_filter',
      id: 'session_search',
      label: 'Find session IDs',
      data: 'session_id',
      type: 'text',
      match: 'contains',
      main_search: true,
    },
    {
      ui_type: 'session_list_filter',
      id: 'archived',
      label: 'Archived',
      data: 'metadata.archived',
      type: 'boolean',
      match: 'equals',
      missing_value: false,
      default: false,
      options: [
        {
          value: false,
          label: 'Current only',
          icon: 'inbox',
          tone: 'success',
        },
        {
          value: true,
          label: 'Archived only',
          icon: 'archive',
          tone: 'warning',
        },
      ],
    },
    {
      ui_type: 'session_list_filter',
      id: 'owner',
      label: 'Owner',
      data: 'metadata.owner',
      type: 'select',
      match: 'equals',
      options: [
        { value: 'alice', label: 'Alice' },
        { value: 'bob', label: 'Bob' },
      ],
    },
    {
      ui_type: 'session_list_filter',
      id: 'status',
      label: 'Status',
      data: 'metadata.status',
      type: 'select',
      match: 'one_of',
      multiple: true,
      options: [
        { value: 'todo', label: 'To do' },
        { value: 'blocked', label: 'Blocked' },
        { value: 'done', label: 'Done' },
      ],
    },
    {
      ui_type: 'session_list_filter',
      id: 'note',
      label: 'Note',
      data: 'metadata.note',
      type: 'text',
      match: 'equals',
    },
  ]);
  mockUseApplicationPlugins.mockReturnValue(applicationPluginsResult(schema));

  renderScreen();

  expect(screen.getByTestId('session-main-search').props.placeholder).toBe(
    'Find session IDs',
  );
  expect(screen.getByTestId('session-row-alpha-session')).toBeTruthy();
  expect(screen.getByTestId('session-row-gamma-session')).toBeTruthy();
  expect(screen.queryByTestId('session-row-beta-session')).toBeNull();
  expect(screen.getByTestId('session-filters-active-count').props.children).toBe(
    1,
  );

  fireEvent.changeText(
    screen.getByTestId('session-main-search'),
    'Presentation one',
  );
  expect(screen.queryByTestId('session-row-alpha-session')).toBeNull();
  expect(
    screen.getByText('No sessions match the active search or filters.'),
  ).toBeTruthy();
  fireEvent.changeText(screen.getByTestId('session-main-search'), '');

  fireEvent.press(screen.getByTestId('session-filters-open'));
  expect(screen.getByText(/Current only/)).toBeTruthy();
  expect(screen.getByText(/Archived only/)).toBeTruthy();
  expect(
    screen.getByTestId('session-filter-archived-option-false-icon'),
  ).toBeTruthy();
  fireEvent.press(screen.getByTestId('session-filter-archived-option-any'));
  expect(screen.getByTestId('session-row-beta-session')).toBeTruthy();

  fireEvent.press(screen.getByTestId('session-filter-owner-option-0'));
  fireEvent.press(screen.getByTestId('session-filter-status-option-0'));
  expect(screen.getByTestId('session-row-alpha-session')).toBeTruthy();
  expect(screen.queryByTestId('session-row-beta-session')).toBeNull();
  expect(screen.queryByTestId('session-row-gamma-session')).toBeNull();
  fireEvent.press(screen.getByTestId('session-filter-status-option-2'));
  expect(screen.getByTestId('session-row-alpha-session')).toBeTruthy();
  expect(screen.getByTestId('session-row-beta-session')).toBeTruthy();

  fireEvent.press(screen.getByTestId('session-filters-show-all'));
  expect(screen.getByTestId('session-row-alpha-session')).toBeTruthy();
  expect(screen.getByTestId('session-row-beta-session')).toBeTruthy();
  expect(screen.getByTestId('session-row-gamma-session')).toBeTruthy();
  expect(screen.queryByTestId('session-filters-active-count')).toBeNull();

  fireEvent.changeText(
    screen.getByTestId('session-filter-note-text'),
    'three',
  );
  expect(screen.queryByTestId('session-row-alpha-session')).toBeNull();
  expect(screen.queryByTestId('session-row-beta-session')).toBeNull();
  expect(screen.getByTestId('session-row-gamma-session')).toBeTruthy();
  fireEvent.press(screen.getByTestId('session-filters-show-all'));

  fireEvent.press(screen.getByTestId('session-filters-reset'));
  expect(screen.getByTestId('session-row-alpha-session')).toBeTruthy();
  expect(screen.queryByTestId('session-row-beta-session')).toBeNull();
  expect(screen.getByTestId('session-row-gamma-session')).toBeTruthy();
});

test('uses the built-in pin and status filter declarations', () => {
  const sessions: SessionSummary[] = [
    {
      session_id: 'ordinary-todo',
      modified: 2,
      preview: 'ordinary',
      metadata: {},
      presentation: {
        title: 'Ordinary todo',
        subtitle: null,
        meta: null,
      },
    },
    {
      session_id: 'pinned-done',
      modified: 1,
      preview: 'pinned',
      metadata: {
        pinned: true,
        status: 'done',
      },
      presentation: {
        title: 'Pinned done',
        subtitle: null,
        meta: null,
      },
    },
  ];
  mockUseSessionsController.mockReturnValue({
    controller: sessionsController as any,
    state: {
      sessions,
      loading: false,
      error: null,
      lastLoadedAt: 1,
    },
  });
  mockUseApplicationPlugins.mockReturnValue(
    applicationPluginsResult(
      normalizeSessionListFilterSchema([
        {
          ui_type: 'session_list_filter',
          id: 'session_search',
          label: 'Search',
          data: 'session_id',
          type: 'text',
          match: 'contains',
          main_search: true,
        },
        {
          ui_type: 'session_list_filter',
          id: 'session_title_search',
          label: 'Title / subtitle',
          data: ['presentation.title', 'presentation.subtitle'],
          type: 'text',
          match: 'contains',
        },
        {
          ui_type: 'session_list_filter',
          id: 'session_first_message_search',
          label: 'First message',
          data: 'first_user_message',
          type: 'text',
          match: 'contains',
        },
        {
          ui_type: 'session_list_filter',
          id: 'pinned_state',
          label: 'Pinned',
          icon: 'star',
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
          id: 'session_status',
          label: 'Status',
          icon: 'circle',
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
      ]),
    ),
  );

  renderScreen();
  expect(screen.getByTestId('session-row-ordinary-todo')).toBeTruthy();
  expect(screen.getByTestId('session-row-pinned-done')).toBeTruthy();
  expect(screen.queryByTestId('session-filters-active-count')).toBeNull();

  fireEvent.press(screen.getByTestId('session-filters-open'));
  expect(screen.getByTestId('session-filter-session_title_search-text')).toBeTruthy();
  expect(
    screen.getByTestId('session-filter-session_first_message_search-text'),
  ).toBeTruthy();
  expect(screen.getByText('Not pinned')).toBeTruthy();
  expect(screen.getAllByText('Pinned')).toHaveLength(2);
  expect(
    screen.getByTestId('session-filter-pinned_state-option-true-icon'),
  ).toBeTruthy();
  fireEvent.press(
    screen.getByTestId('session-filter-pinned_state-option-true'),
  );
  expect(screen.queryByTestId('session-row-ordinary-todo')).toBeNull();
  expect(screen.getByTestId('session-row-pinned-done')).toBeTruthy();

  fireEvent.press(
    screen.getByTestId('session-filter-session_status-option-3'),
  );
  expect(screen.getByTestId('session-filters-active-count').props.children).toBe(
    2,
  );

  fireEvent.press(screen.getByTestId('session-filters-show-all'));
  expect(screen.getByTestId('session-row-ordinary-todo')).toBeTruthy();
  expect(screen.getByTestId('session-row-pinned-done')).toBeTruthy();
  expect(screen.queryByTestId('session-filters-active-count')).toBeNull();

  fireEvent.press(screen.getByTestId('session-filter-session_status-option-0'));
  expect(screen.getByTestId('session-row-ordinary-todo')).toBeTruthy();
  expect(screen.queryByTestId('session-row-pinned-done')).toBeNull();
});

test('reports competing main searches and keeps fallback search usable', () => {
  const conflicted = normalizeSessionListFilterSchema([
    {
      ui_type: 'session_list_filter',
      id: 'first-search',
      label: 'First',
      data: 'session_id',
      type: 'text',
      match: 'contains',
      main_search: true,
    },
    {
      ui_type: 'session_list_filter',
      id: 'second-search',
      label: 'Second',
      data: 'preview',
      type: 'text',
      match: 'contains',
      main_search: true,
    },
  ]);
  mockUseApplicationPlugins.mockReturnValue(
    applicationPluginsResult(conflicted),
  );

  renderScreen();
  expect(screen.getByTestId('session-filter-schema-warning')).toBeTruthy();

  fireEvent.changeText(
    screen.getByTestId('session-main-search'),
    'Server second title',
  );
  expect(screen.queryByTestId('session-row-server-first')).toBeNull();
  expect(screen.getByTestId('session-row-server-second')).toBeTruthy();
});

test('resets search state when the active connection changes', () => {
  const rendered = renderScreen('connection-a');
  fireEvent.changeText(screen.getByTestId('session-main-search'), 'server-first');
  expect(screen.queryByTestId('session-row-server-second')).toBeNull();

  rendered.rerender(
    <ThemeProvider theme={lightTheme}>
      <SessionsScreen
        backend={{ kind: 'test' } as any}
        connectionId="connection-b"
        cachedSessions={SESSION_SUMMARIES}
        lastLoadedAt={1}
        isActive
        onUpdateCache={jest.fn()}
        onSelectSession={jest.fn()}
      />
    </ThemeProvider>,
  );

  expect(rendered.getByTestId('session-main-search').props.value).toBe('');
  expect(rendered.getByTestId('session-row-server-first')).toBeTruthy();
  expect(rendered.getByTestId('session-row-server-second')).toBeTruthy();
});

test('resets stale values when the declaration identity changes', () => {
  const rendered = renderScreen('connection-a');
  fireEvent.changeText(screen.getByTestId('session-main-search'), 'server-first');
  expect(screen.queryByTestId('session-row-server-second')).toBeNull();

  mockUseApplicationPlugins.mockReturnValue(
    applicationPluginsResult(
      normalizeSessionListFilterSchema([
        {
          ui_type: 'session_list_filter',
          id: 'replacement-search',
          label: 'Replacement search',
          data: 'session_id',
          type: 'text',
          match: 'contains',
          main_search: true,
        },
      ]),
    ),
  );
  rendered.rerender(
    <ThemeProvider theme={lightTheme}>
      <SessionsScreen
        backend={{ kind: 'test' } as any}
        connectionId="connection-a"
        cachedSessions={SESSION_SUMMARIES}
        lastLoadedAt={1}
        isActive
        onUpdateCache={jest.fn()}
        onSelectSession={jest.fn()}
      />
    </ThemeProvider>,
  );

  expect(rendered.getByTestId('session-main-search').props.value).toBe('');
  expect(rendered.getByTestId('session-main-search').props.placeholder).toBe(
    'Replacement search',
  );
  expect(rendered.getByTestId('session-row-server-first')).toBeTruthy();
  expect(rendered.getByTestId('session-row-server-second')).toBeTruthy();
});
