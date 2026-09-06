import React from 'react';
import { render, waitFor } from '@testing-library/react-native';

const mockConnection = {
  id: 'connection',
  name: 'Local',
  kind: 'manual',
  host: '127.0.0.1',
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
    sortedConnectionRecords: [mockConnection],
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
  ConnectionsPanel: () => {
    const ReactModule = require('react');
    const { View } = require('react-native');
    return ReactModule.createElement(View, { testID: 'connections-panel' });
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
  SessionTabs: () => {
    const ReactModule = require('react');
    const { View } = require('react-native');
    return ReactModule.createElement(View, { testID: 'session-tabs' });
  },
}));
jest.mock('../src/tabs/ChatPaneTabStack', () => ({
  ChatPaneTabStack: () => {
    const ReactModule = require('react');
    const { View } = require('react-native');
    return ReactModule.createElement(View, { testID: 'chat-stack' });
  },
}));
jest.mock('../src/ui/DesktopGlobalDisplayLayer', () => ({
  DesktopGlobalDisplayLayer: ({ children }: any) => children,
}));

import { DesktopRoot } from '../src/DesktopRoot';

test('restores an active preview and attempts to reopen its connection at startup', async () => {
  render(<DesktopRoot />);
  await waitFor(() =>
    expect(mockOpenConnection).toHaveBeenCalledWith(mockConnection),
  );
  expect(mockOpenConnection).toHaveBeenCalledTimes(1);
});
