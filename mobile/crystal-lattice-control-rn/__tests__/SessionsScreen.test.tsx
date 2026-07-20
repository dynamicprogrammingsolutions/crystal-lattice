import React from 'react';
import { fireEvent, screen } from '@testing-library/react-native';

import {
  buildActionDialogInitialValues,
  normalizeSessionListActionElement,
  type SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import {
  useAgentsController,
  useHydrateControllerFromCache,
  useSessionsController,
} from '@crystal-lattice/frontend-sdk-react';

import {
  useApplicationPlugins,
  useApplicationPluginsContext,
} from '../src/ApplicationPluginsContext';
import SessionsScreen from '../src/SessionsScreen';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';

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
    SessionActionsBar: ({ extraActions, onAction }: any) =>
      ReactModule.createElement(
        View,
        null,
        (extraActions || []).map((action: any) =>
          ReactModule.createElement(
            TouchableOpacity,
            {
              key: action.key,
              testID: `mock-session-action-${action.key}`,
              onPress: () => onAction(action.key),
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

function renderScreen() {
  return renderWithMobileProviders(
    <SessionsScreen
      backend={{ kind: 'test' } as any}
      connectionId="component-test"
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
  mockUseApplicationPlugins.mockReturnValue({
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
    sessionListPinnedToggles: [],
    sessionListDiagnostics: normalizedAction.diagnostics,
  });
  mockUseApplicationPluginsContext.mockReturnValue({
    actionsById: {},
    sessionActions: [],
    messageActions: [],
    sessionListActions: [],
    sessionListFields: [],
    sessionListPinnedToggles: [],
    sessionListDiagnostics: [],
    loading: false,
    error: null,
    refresh: refreshApplicationPlugins,
    invalidate: jest.fn(),
  });
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
    'Server first meta',
  );
  expect(screen.queryByText('Local first title')).toBeNull();
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
