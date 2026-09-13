import React from 'react';
import { fireEvent, render, waitFor } from '@testing-library/react-native';

const mockConnection = {
  id: 'connection',
  name: 'Local',
  kind: 'manual',
  host: '127.0.0.1',
  port: 9000,
};
const mockOtherConnection = {
  id: 'other',
  name: 'Other',
  kind: 'manual',
  host: '127.0.0.2',
  port: 9000,
};
const mockOpenConnection = jest.fn(async () => ({
  listSessions: jest.fn(async () => []),
}));
jest.mock('../src/storage/asyncStorageKeyValueStore', () => {
  const store = {
    get: jest.fn(async (key: string) =>
      key === 'clc_open_tabs_v1'
        ? JSON.stringify({
            version: 2,
            activeWorkspace: {
              kind: 'session',
              tabId: 'connection:preview',
            },
            permanentTabs: [],
            previewTab: {
              connectionId: 'connection',
              sessionId: 'preview',
              title: 'Preview',
            },
          })
        : null,
    ),
    set: jest.fn(async () => {}),
    delete: jest.fn(async () => {}),
  };
  return { asyncStorageKeyValueStore: store };
});

jest.mock('../src/connections/usePersistedConnections', () => ({
  usePersistedConnections: () => ({
    hydrated: true,
    sortedConnectionRecords: [mockOtherConnection, mockConnection],
    upsertConnection: jest.fn(),
    deleteConnection: jest.fn(),
    touchConnection: jest.fn(),
    clearConnections: jest.fn(),
  }),
}));

jest.mock('../src/connections/useOpenConnections', () => ({
  useOpenConnections: () => ({
    openConnectionsById: {},
    openConnection: mockOpenConnection,
    closeConnection: jest.fn(),
    closeAllConnections: jest.fn(),
    getBackend: jest.fn(() => null),
  }),
}));

jest.mock('../src/cache/useSessionsCache', () => ({
  useSessionsCache: () => ({
    sessionsCache: {},
    updateSessionsCache: jest.fn(),
    deleteConnectionSessionsCache: jest.fn(),
    clearSessionsCache: jest.fn(),
  }),
}));

jest.mock('../src/cache/useMessagesCache', () => ({
  useMessagesCache: () => ({
    messagesCache: {},
    hydrated: true,
    updateMessagesCache: jest.fn(),
    deleteConnectionMessagesCache: jest.fn(),
    clearMessagesCache: jest.fn(),
  }),
}));

jest.mock('@crystal-lattice/frontend-sdk-react', () => ({
  ...jest.requireActual('@crystal-lattice/frontend-sdk-react'),
  useSessionRequestStatuses: () => ({}),
}));

jest.mock('../src/panels/ConnectionsPanel', () => ({
  ConnectionsPanel: ({
    focusedConnectionId,
  }: {
    focusedConnectionId: string | null;
  }) => {
    const ReactModule = require('react');
    const { View } = require('react-native');
    return ReactModule.createElement(View, {
      testID: 'connections-panel',
      accessibilityLabel: `focused:${focusedConnectionId ?? 'none'}`,
    });
  },
}));
jest.mock('../src/panels/SessionsPanel', () => ({
  SessionsPanel: () => {
    const ReactModule = require('react');
    const { View } = require('react-native');
    return ReactModule.createElement(View, { testID: 'sessions-panel' });
  },
}));
jest.mock('../src/panels/HistoryPanel', () => ({
  HistoryPanel: () => {
    const ReactModule = require('react');
    const { View } = require('react-native');
    return ReactModule.createElement(View, { testID: 'history-panel' });
  },
}));
jest.mock('../src/home/DesktopHomeView', () => ({
  DesktopHomeView: () => {
    const ReactModule = require('react');
    const { View } = require('react-native');
    return ReactModule.createElement(View, { testID: 'home-view' });
  },
}));
jest.mock('../src/tabs/SessionTabs', () => ({
  SessionTabs: ({
    onSelectHome,
    onSelectTab,
  }: {
    onSelectHome: () => void;
    onSelectTab: (tabId: string) => void;
  }) => {
    const ReactModule = require('react');
    const { Pressable, View } = require('react-native');
    return ReactModule.createElement(
      View,
      { testID: 'session-tabs' },
      ReactModule.createElement(Pressable, {
        testID: 'select-home',
        onPress: onSelectHome,
      }),
      ReactModule.createElement(Pressable, {
        testID: 'select-preview',
        onPress: () => onSelectTab('connection:preview'),
      }),
    );
  },
}));
jest.mock('../src/tabs/ChatPaneTabStack', () => ({
  ChatPaneTabStack: ({ workspaceVisible }: { workspaceVisible: boolean }) => {
    const ReactModule = require('react');
    const { View } = require('react-native');
    return ReactModule.createElement(View, {
      testID: 'chat-stack',
      accessibilityLabel: workspaceVisible ? 'visible' : 'hidden',
    });
  },
}));
jest.mock('../src/ui/DesktopGlobalDisplayLayer', () => ({
  DesktopGlobalDisplayLayer: ({ children }: any) => children,
}));

import { DesktopRoot } from '../src/DesktopRoot';

beforeEach(() => {
  mockOpenConnection.mockClear();
});

test('restores an active preview and attempts to reopen its connection at startup', async () => {
  const screen = render(<DesktopRoot />);
  await waitFor(() =>
    expect(mockOpenConnection).toHaveBeenCalledWith(mockConnection),
  );
  expect(mockOpenConnection).toHaveBeenCalledTimes(1);

  expect(screen.getByTestId('chat-stack').props.accessibilityLabel).toBe(
    'visible',
  );
  expect(screen.getByTestId('connections-panel').props.accessibilityLabel).toBe(
    'focused:other',
  );
  fireEvent.press(screen.getByTestId('select-preview'));
  expect(screen.getByTestId('connections-panel').props.accessibilityLabel).toBe(
    'focused:other',
  );
  fireEvent.press(screen.getByTestId('select-home'));
  expect(screen.getByTestId('home-view')).toBeTruthy();
  expect(screen.getByTestId('chat-stack').props.accessibilityLabel).toBe(
    'hidden',
  );
});

test('focuses the owning connection when Sessions follow active tab is enabled', async () => {
  const screen = render(<DesktopRoot initialSessionsFollowActiveTabEnabled />);
  await waitFor(() =>
    expect(mockOpenConnection).toHaveBeenCalledWith(mockConnection),
  );
  await waitFor(() =>
    expect(
      screen.getByTestId('connections-panel').props.accessibilityLabel,
    ).toBe('focused:connection'),
  );
});
