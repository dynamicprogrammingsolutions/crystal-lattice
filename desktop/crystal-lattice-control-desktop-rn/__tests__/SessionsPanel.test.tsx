import React from 'react';

let mockSessions: any[] = [];

jest.mock('@crystal-lattice/frontend-sdk-react', () => {
  const ReactModule = require('react');
  return {
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
      actionsById: {},
      sessionActions: [],
      messageActions: [],
      sessionListActions: [],
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
      sessionListDiagnostics: [],
    }),
    useHydrateControllerFromCache: () => {},
    usePersistentPinnedActions: () => ({
      loaded: true,
      pinned: [],
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

import { render } from '@testing-library/react-native';

import { SessionsPanel } from '../src/panels/SessionsPanel';

describe('SessionsPanel', () => {
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
          meta: 'Server first meta',
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
        .map((title) => title.props.children),
    ).toEqual(['Server first title', 'Server second title']);
    expect(
      rendered.getByTestId('session-subtitle-server-first').props.children,
    ).toBe('Server first subtitle');
    expect(rendered.getByTestId('session-meta-server-first').props.children).toBe(
      'Server first meta',
    );
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
});
