import React from 'react';

import { render } from '@testing-library/react-native';

import type { MessagesCache, SessionsCache } from '../src/cache/types';
import { ChatPaneTabStack } from '../src/tabs/ChatPaneTabStack';
import type { DesktopSessionTab } from '../src/tabs/SessionTabs';
import { SessionTabs } from '../src/tabs/SessionTabs';

jest.mock('@crystal-lattice/frontend-sdk-react', () => {
  const React = require('react');

  return {
    ApplicationPluginsProvider: ({ children }: { children: React.ReactNode }) =>
      React.createElement(React.Fragment, null, children),
  };
});

jest.mock('../src/chat/ChatPane', () => {
  const React = require('react');
  const { Text, View } = require('react-native');

  return {
    ChatPane: ({
      sessionId,
      isActive,
      cachedEntry,
    }: {
      sessionId: string;
      isActive: boolean;
      cachedEntry: unknown;
    }) =>
      React.createElement(
        View,
        { testID: `chat-pane-${sessionId}` },
        React.createElement(Text, null, `pane:${sessionId}`),
        React.createElement(Text, null, `active:${sessionId}:${isActive ? 'yes' : 'no'}`),
        React.createElement(Text, null, `cache:${sessionId}:${cachedEntry ? 'yes' : 'no'}`),
      ),
  };
});

const tabs: DesktopSessionTab[] = [
  {
    tabId: 'conn-1:session-1',
    connectionId: 'conn-1',
    sessionId: 'session-1',
    title: 'One',
    subtitle: 'First',
  },
  {
    tabId: 'conn-1:session-2',
    connectionId: 'conn-1',
    sessionId: 'session-2',
    title: 'Two',
    subtitle: 'Second',
  },
  {
    tabId: 'conn-1:session-3',
    connectionId: 'conn-1',
    sessionId: 'session-3',
    title: 'Three',
    subtitle: 'Third',
  },
  {
    tabId: 'conn-1:session-4',
    connectionId: 'conn-1',
    sessionId: 'session-4',
    title: 'Four',
    subtitle: 'Fourth',
  },
];

const sessionsCache: SessionsCache = {
  'conn-1': {
    connectionId: 'conn-1',
    sessions: [],
    lastLoadedAt: null,
  },
};

const messagesCache: MessagesCache = {
  'conn-1': {
    'session-1': {
      connectionId: 'conn-1',
      sessionId: 'session-1',
      messages: [],
      lastLoadedAt: 1,
    },
    'session-2': {
      connectionId: 'conn-1',
      sessionId: 'session-2',
      messages: [],
      lastLoadedAt: 2,
    },
    'session-3': {
      connectionId: 'conn-1',
      sessionId: 'session-3',
      messages: [],
      lastLoadedAt: 3,
    },
    'session-4': {
      connectionId: 'conn-1',
      sessionId: 'session-4',
      messages: [],
      lastLoadedAt: 4,
    },
  },
};

function renderTabsUi(activeTabId: string | null, visibleTabs: DesktopSessionTab[]) {
  return (
    <>
      <SessionTabs
        tabs={visibleTabs}
        activeTabId={activeTabId}
        styleVariant="toolbarTabs"
        connectionNameById={{ 'conn-1': 'Connection One' }}
        onSelectTab={() => {}}
        onCloseTab={() => {}}
      />
      <ChatPaneTabStack
        tabs={visibleTabs}
        activeTabId={activeTabId}
        styleVariant="toolbarTabs"
        connectionNameById={{ 'conn-1': 'Connection One' }}
        getBackend={() => null}
        sessionsCache={sessionsCache}
        messagesCache={messagesCache}
        onUpdateCache={() => {}}
        onOpenSessionTab={() => {}}
      />
    </>
  );
}

describe('ChatPaneTabStack', () => {
  it('keeps all tab labels visible while mounting only the 3 warm panes', () => {
    const screen = render(renderTabsUi(tabs[0].tabId, tabs.slice(0, 1)));

    screen.rerender(renderTabsUi(tabs[1].tabId, tabs.slice(0, 2)));
    screen.rerender(renderTabsUi(tabs[2].tabId, tabs.slice(0, 3)));
    screen.rerender(renderTabsUi(tabs[3].tabId, tabs));

    expect(screen.getByText('One')).toBeTruthy();
    expect(screen.getByText('Two')).toBeTruthy();
    expect(screen.getByText('Three')).toBeTruthy();
    expect(screen.getByText('Four')).toBeTruthy();

    expect(screen.queryByTestId('chat-pane-session-1')).toBeNull();
    expect(screen.getByTestId('chat-pane-session-2')).toBeTruthy();
    expect(screen.getByTestId('chat-pane-session-3')).toBeTruthy();
    expect(screen.getByTestId('chat-pane-session-4')).toBeTruthy();

    expect(screen.getByText('active:session-2:yes')).toBeTruthy();
    expect(screen.getByText('active:session-3:yes')).toBeTruthy();
    expect(screen.getByText('active:session-4:yes')).toBeTruthy();
  });

  it('remounts an older tab into the warm set from cached data when reselected', () => {
    const screen = render(renderTabsUi(tabs[0].tabId, tabs.slice(0, 1)));

    screen.rerender(renderTabsUi(tabs[1].tabId, tabs.slice(0, 2)));
    screen.rerender(renderTabsUi(tabs[2].tabId, tabs.slice(0, 3)));
    screen.rerender(renderTabsUi(tabs[3].tabId, tabs));

    expect(screen.queryByTestId('chat-pane-session-1')).toBeNull();

    screen.rerender(renderTabsUi(tabs[0].tabId, tabs));

    expect(screen.getByTestId('chat-pane-session-1')).toBeTruthy();
    expect(screen.queryByTestId('chat-pane-session-2')).toBeNull();
    expect(screen.getByTestId('chat-pane-session-3')).toBeTruthy();
    expect(screen.getByTestId('chat-pane-session-4')).toBeTruthy();

    expect(screen.getByText('active:session-1:yes')).toBeTruthy();
    expect(screen.getByText('active:session-3:yes')).toBeTruthy();
    expect(screen.getByText('active:session-4:yes')).toBeTruthy();
    expect(screen.getByText('cache:session-1:yes')).toBeTruthy();
  });
});