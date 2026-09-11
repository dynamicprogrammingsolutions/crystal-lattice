import React from 'react';

let mockSessions: any[] = [];
let mockFilterSchema: any = null;
let mockSessionListActions: any[] = [];
let mockActionsById: Record<string, any> = {};
let mockPinnedSessionListActions: string[] = [];
let mockApplicationActions: any[] = [];

jest.mock('@crystal-lattice/frontend-sdk-react', () => {
  const ReactModule = require('react');
  const actual = jest.requireActual('@crystal-lattice/frontend-sdk-react');
  const {
    normalizeSessionListFilterSchema,
  } = require('@crystal-lattice/frontend-sdk');
  return {
    ...actual,
    ApplicationPluginsProvider: ({ children }: any) =>
      ReactModule.createElement(ReactModule.Fragment, null, children),
    useAgentsController: () => ({
      controller: {
        ensureLoaded: jest.fn(async () => ['default']),
      },
      state: {
        agents: ['default'],
        loading: false,
        error: null,
      },
    }),
    useApplicationPlugins: () => ({
      actionsById: mockActionsById,
      actionsByKey: {},
      applicationActions: mockApplicationActions,
      sessionActions: [],
      messageActions: [],
      sessionListActions: mockSessionListActions,
      sessionListFields: [
        {
          ui_type: 'session_list_field',
          plugin: 'fixture',
          id: 'local-title',
          role: 'title',
          data: 'metadata.local_title',
        },
      ],
      sessionListFilterSchema:
        mockFilterSchema ?? normalizeSessionListFilterSchema([]),
      sessionListDiagnostics: [],
    }),
    useHydrateControllerFromCache: () => {},
    usePersistentPinnedActions: () => ({
      loaded: true,
      pinned: mockPinnedSessionListActions,
      setPinned: jest.fn(),
    }),
    usePluginActionDialog: () => ({
      activeElement: null,
      context: null,
      openForElement: jest.fn(),
      handleSubmit: jest.fn(),
      handleCancel: jest.fn(),
    }),
    useSessionsController: () => ({
      controller: {
        hydrateFromCache: jest.fn(),
        load: jest.fn(async () => mockSessions),
        loadIfStale: jest.fn(async () => null),
      },
      state: {
        sessions: mockSessions,
        loading: false,
        error: null,
        lastLoadedAt: 1,
      },
    }),
  };
});

jest.mock('../src/windows/useMacOSApplicationActionDialog', () => ({
  useMacOSApplicationActionDialog: () => {},
}));

jest.mock('../src/panels/useSessionsPanelTabAutoSelect', () => ({
  useSessionsPanelTabAutoSelect: () => ({
    selectedSessionId: null,
    onUserSelectSessionId: jest.fn(),
    scrollViewRef: { current: null },
    getRowLayoutHandler: () => jest.fn(),
    rowLayoutsRef: { current: {} },
  }),
}));

import { fireEvent, render } from '@testing-library/react-native';
import { normalizeSessionListFilterSchema } from '@crystal-lattice/frontend-sdk';

import { SessionsPanel } from '../src/panels/SessionsPanel';
import { MessageLimitPopoverView } from '../src/windows/MessageLimitPopoverView';
import { clearActiveDesktopPopover } from '../src/windows/desktopPopoverCoordinator';

describe('SessionsPanel', () => {
  beforeEach(() => {
    clearActiveDesktopPopover();
    mockFilterSchema = null;
    mockSessionListActions = [];
    mockActionsById = {};
    mockPinnedSessionListActions = [];
    mockApplicationActions = [];
  });

  test('uses one sessions action bar for built-ins and application actions', () => {
    mockApplicationActions = [
      {
        ui_type: 'application_action',
        plugin: 'application_config',
        id: 'reload_application',
        label: 'Reload application',
        action_id: 'reload_application',
      },
    ];
    const screen = render(
      <SessionsPanel
        focusedConnectionId="connection"
        focusedConnectionName="Connection"
        connectionId="connection"
        backend={{} as any}
        cachedSessions={[]}
        cachedLastLoadedAt={null}
        isOnline
        onUpdateCache={() => {}}
        onOpenSessionTab={() => {}}
      />,
    );
    expect(screen.getByTestId('sessions-actions-menu')).toBeTruthy();
    expect(screen.getByText('Server settings')).toBeTruthy();
    expect(screen.getByText('Refresh sessions')).toBeTruthy();
    expect(screen.getByText('New session')).toBeTruthy();
    expect(screen.getByText('Reload application')).toBeTruthy();
  });

  it('reports only the currently rendered Sessions window for status polling', () => {
    mockSessions = Array.from({ length: 80 }, (_value, index) => ({
      session_id: `session-${index}`,
      modified: 80 - index,
      preview: `Session ${index}`,
      presentation: {
        title: `Session ${index}`,
        subtitle: null,
        meta: null,
      },
    }));
    const onVisibleSessionIdsChange = jest.fn();
    const screen = render(
      <SessionsPanel
        focusedConnectionId="connection"
        focusedConnectionName="Connection"
        connectionId="connection"
        backend={{} as any}
        cachedSessions={mockSessions}
        cachedLastLoadedAt={null}
        isOnline
        onUpdateCache={() => {}}
        onOpenSessionTab={() => {}}
        onVisibleSessionIdsChange={onVisibleSessionIdsChange}
      />,
    );

    const renderedIds = screen
      .getAllByTestId(/^session-row-/)
      .map(row => String(row.props.testID).replace('session-row-', ''));
    expect(renderedIds.length).toBeLessThan(mockSessions.length);
    expect(onVisibleSessionIdsChange).toHaveBeenLastCalledWith({
      connectionId: 'connection',
      sessionIds: renderedIds,
    });
  });

  it('renders server presentation in server order and propagates it to tabs', () => {
    mockSessions = [
      {
        session_id: 'server-first',
        modified: 1,
        preview: 'conflicting first preview',
        metadata: {
          local_title: 'Local first title',
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
        },
        presentation: {
          title: 'Server second title',
          subtitle: null,
          meta: null,
        },
      },
    ];
    const onUpdateOpenTabsPresentation = jest.fn();
    const rendered = render(
      <SessionsPanel
        focusedConnectionId="connection-1"
        focusedConnectionName="Local"
        connectionId="connection-1"
        backend={{ kind: 'test' } as any}
        cachedSessions={mockSessions}
        cachedLastLoadedAt={1}
        isOnline={false}
        followActiveTabEnabled={false}
        onUpdateCache={jest.fn()}
        onOpenSessionTab={jest.fn()}
        onUpdateOpenTabsPresentation={onUpdateOpenTabsPresentation}
      />,
    );

    expect(
      rendered
        .getAllByTestId(/session-title-/)
        .map(title => title.props.children),
    ).toEqual(['Server first title', 'Server second title']);
    expect(
      rendered.getByTestId('session-subtitle-server-first').props.children,
    ).toBe('Server first subtitle');
    expect(
      rendered.getByTestId('session-meta-server-first').props.children,
    ).toBe('Server first meta · Status: Done');
    expect(rendered.queryByText('Local first title')).toBeNull();
    expect(onUpdateOpenTabsPresentation).toHaveBeenCalledWith({
      connectionId: 'connection-1',
      presentations: {
        'server-first': {
          title: 'Server first title',
          subtitle: 'Server first subtitle',
        },
        'server-second': {
          title: 'Server second title',
          subtitle: null,
        },
      },
    });
  });

  it('keeps single click light, applies configured double click, and aligns the complementary button before actions', () => {
    mockSessions = [
      {
        session_id: 'interaction',
        modified: 1,
        preview: 'Interaction',
        presentation: {
          title: 'Interaction session',
          subtitle: 'Subtitle',
          meta: null,
        },
      },
    ];
    const onOpenSessionTab = jest.fn();
    const now = jest
      .spyOn(Date, 'now')
      .mockReturnValueOnce(100)
      .mockReturnValueOnce(200);
    const rendered = render(
      <SessionsPanel
        focusedConnectionId="connection-1"
        focusedConnectionName="Local"
        connectionId="connection-1"
        backend={{ kind: 'test' } as any}
        cachedSessions={mockSessions}
        cachedLastLoadedAt={1}
        isOnline
        followActiveTabEnabled={false}
        onUpdateCache={jest.fn()}
        onOpenSessionTab={onOpenSessionTab}
        sessionDoubleClickAction="open"
        requestStatuses={{
          interaction: {
            session_id: 'interaction',
            request_id: null,
            state: 'succeeded',
            basis: 'session_tail',
            session_modified: 1,
          },
        }}
        sessionNotes={{ interaction: 'Local note' }}
        onEditSessionNote={() => {}}
      />,
    );

    const row = rendered.getByTestId('session-row-interaction');
    fireEvent.press(row);
    expect(onOpenSessionTab).not.toHaveBeenCalled();
    fireEvent.press(row);
    expect(onOpenSessionTab).toHaveBeenLastCalledWith(
      expect.objectContaining({ sessionId: 'interaction', mode: 'open' }),
    );

    fireEvent.press(
      rendered.getByTestId('desktop-session-preview-interaction'),
    );
    expect(onOpenSessionTab).toHaveBeenLastCalledWith(
      expect.objectContaining({ sessionId: 'interaction', mode: 'preview' }),
    );
    expect(rendered.getByText('Completed')).toBeTruthy();
    expect(rendered.getByText('Local note')).toBeTruthy();

    const actionRow = rendered.getByTestId(
      'desktop-session-actions-row-interaction',
    );
    const button = rendered.getByTestId('desktop-session-preview-interaction');
    expect(actionRow.props.style.alignItems).toBe('center');
    expect(actionRow.findAll(node => node === button).length).toBe(1);
    now.mockRestore();
  });

  it('uses the first declared header action and separately renders an actions-bar placement', () => {
    mockSessions = [
      {
        session_id: 'pinned',
        modified: 1,
        preview: 'pinned preview',
        metadata: { pinned: true },
        presentation: {
          title: 'Pinned session',
          subtitle: null,
          meta: null,
        },
      },
    ];
    mockSessionListActions = [
      {
        ui_type: 'session_list_action',
        plugin: 'fixture',
        id: 'toggle_session_pinned',
        label: 'Pin/unpin session',
        icon: 'star',
        order: 10,
        action_id: 'toggle_session_pinned',
        dialog: { kind: 'none' },
        rich_ui: {
          kind: 'toggle',
          value_path: 'metadata.pinned',
          missing_value: false,
          active_value: true,
          placements: ['header_trailing', 'actions_bar'],
          appearance: {
            active: { tone: 'highlight' },
            inactive: { tone: 'muted' },
          },
        },
      },
      {
        ui_type: 'session_list_action',
        plugin: 'fixture',
        id: 'second_header_action',
        label: 'Second header action',
        icon: 'star',
        order: 20,
        action_id: 'second_header_action',
        dialog: { kind: 'none' },
        rich_ui: {
          kind: 'toggle',
          value_path: 'metadata.pinned',
          missing_value: false,
          active_value: true,
          placements: ['header_trailing', 'actions_bar'],
          appearance: {
            active: { tone: 'primary' },
            inactive: { tone: 'muted' },
          },
        },
      },
    ];
    mockPinnedSessionListActions = [
      'toggle_session_pinned',
      'second_header_action',
    ];

    const rendered = render(
      <SessionsPanel
        focusedConnectionId="connection-1"
        focusedConnectionName="Local"
        connectionId="connection-1"
        backend={{ kind: 'test' } as any}
        cachedSessions={mockSessions}
        cachedLastLoadedAt={1}
        isOnline
        followActiveTabEnabled={false}
        onUpdateCache={jest.fn()}
        onOpenSessionTab={jest.fn()}
      />,
    );

    expect(
      rendered.getByTestId(
        'session-rich-header-pinned-header_trailing-toggle_session_pinned',
      ).props.accessibilityState.selected,
    ).toBe(true);
    expect(
      rendered.queryByTestId(
        'session-rich-header-pinned-header_trailing-second_header_action',
      ),
    ).toBeNull();
    expect(
      rendered.getByTestId('session-rich-action-pinned-second_header_action'),
    ).toBeTruthy();
  });

  it('keeps fallback search without a plugin and resets its visible window', () => {
    mockSessions = Array.from({ length: 120 }, (_, index) => ({
      session_id: `session-${String(index).padStart(3, '0')}`,
      modified: 120 - index,
      preview: `preview ${index}`,
      metadata: {},
      presentation: {
        title: index === 110 ? 'Needle presentation' : `Title ${index}`,
        subtitle: null,
        meta: null,
      },
    }));
    const rendered = render(
      <SessionsPanel
        focusedConnectionId="connection-1"
        focusedConnectionName="Local"
        connectionId="connection-1"
        backend={{ kind: 'test' } as any}
        cachedSessions={mockSessions}
        cachedLastLoadedAt={1}
        isOnline={false}
        followActiveTabEnabled={false}
        onUpdateCache={jest.fn()}
        onOpenSessionTab={jest.fn()}
      />,
    );

    expect(rendered.getByTestId('session-main-search')).toBeTruthy();
    expect(rendered.queryByTestId('session-filters-open')).toBeNull();
    fireEvent.press(rendered.getByText('70 items hidden below'));
    fireEvent.press(rendered.getByText('20 items hidden below'));
    expect(rendered.getByText('20 items hidden above')).toBeTruthy();
    fireEvent.changeText(
      rendered.getByTestId('session-main-search'),
      'Needle presentation',
    );
    expect(rendered.getByTestId('session-row-session-110')).toBeTruthy();
    expect(rendered.queryByText(/items hidden above/)).toBeNull();
    expect(rendered.queryByText(/items hidden below/)).toBeNull();
  });

  it('renders built-in filters through the native desktop popover coordinator', () => {
    mockFilterSchema = normalizeSessionListFilterSchema([
      {
        ui_type: 'session_list_filter',
        id: 'session_search',
        label: 'Find IDs',
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
        data: 'metadata.favorite',
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
          { value: 'in_progress', label: 'In progress', tone: 'primary' },
          { value: 'blocked', label: 'Blocked', tone: 'danger' },
          { value: 'done', label: 'Done', tone: 'success' },
        ],
      },
    ]);
    mockSessions = [
      {
        session_id: 'visible',
        modified: 2,
        preview: 'visible',
        metadata: {},
        presentation: {
          title: 'Visible',
          subtitle: null,
          meta: null,
        },
      },
      {
        session_id: 'pinned-done',
        modified: 1,
        preview: 'pinned',
        metadata: { favorite: true, status: 'done' },
        presentation: {
          title: 'Pinned done',
          subtitle: null,
          meta: null,
        },
      },
    ];
    const rendered = render(
      <>
        <SessionsPanel
          focusedConnectionId="connection-1"
          focusedConnectionName="Local"
          connectionId="connection-1"
          backend={{ kind: 'test' } as any}
          cachedSessions={mockSessions}
          cachedLastLoadedAt={1}
          isOnline={false}
          followActiveTabEnabled={false}
          onUpdateCache={jest.fn()}
          onOpenSessionTab={jest.fn()}
        />
        <MessageLimitPopoverView />
      </>,
    );

    expect(rendered.getByTestId('session-main-search').props.placeholder).toBe(
      'Find IDs',
    );
    expect(rendered.getByTestId('session-row-visible')).toBeTruthy();
    expect(rendered.getByTestId('session-row-pinned-done')).toBeTruthy();
    expect(rendered.queryByTestId('session-filters-active-count')).toBeNull();
    fireEvent.press(rendered.getByTestId('session-filters-open'));
    expect(rendered.getByTestId('desktop-popover-root')).toBeTruthy();
    expect(rendered.getByTestId('session-filters-panel')).toBeTruthy();
    expect(
      rendered.getByTestId('session-filter-session_title_search'),
    ).toBeTruthy();
    expect(
      rendered.getByTestId('session-filter-session_first_message_search'),
    ).toBeTruthy();
    expect(rendered.getByTestId('session-filter-pinned_state')).toBeTruthy();
    expect(rendered.getByTestId('session-filter-session_status')).toBeTruthy();
    expect(
      rendered.getByTestId('session-filter-pinned_state-option-true-icon'),
    ).toBeTruthy();

    fireEvent.press(
      rendered.getByTestId('session-filter-pinned_state-option-true'),
    );
    expect(rendered.queryByTestId('session-row-visible')).toBeNull();
    expect(rendered.getByTestId('session-row-pinned-done')).toBeTruthy();
    fireEvent.press(
      rendered.getByTestId('session-filter-session_status-option-3'),
    );
    expect(
      rendered.getByTestId('session-filters-active-count').props.children,
    ).toBe(2);
    fireEvent.press(
      rendered.getByTestId('session-filter-session_status-option-2'),
    );
    expect(rendered.getByTestId('session-row-pinned-done')).toBeTruthy();

    fireEvent.press(rendered.getByTestId('session-filters-show-all'));
    expect(rendered.getByTestId('session-row-visible')).toBeTruthy();
    expect(rendered.getByTestId('session-row-pinned-done')).toBeTruthy();
    expect(rendered.queryByTestId('session-filters-active-count')).toBeNull();
    fireEvent.press(rendered.getByTestId('session-filters-close'));
    expect(rendered.queryByTestId('desktop-popover-root')).toBeNull();
    expect(rendered.queryByTestId('session-filters-panel')).toBeNull();
  });
});
