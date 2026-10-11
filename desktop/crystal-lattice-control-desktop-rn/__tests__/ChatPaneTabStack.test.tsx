import React from 'react';

import { render } from '@testing-library/react-native';

import type { MessagesCache, SessionsCache } from '../src/cache/types';
import { ChatPaneTabStack } from '../src/tabs/ChatPaneTabStack';
import type { DesktopSessionTab } from '../src/tabs/SessionTabs';
import { SessionTabs } from '../src/tabs/SessionTabs';

jest.mock('@crystal-lattice/frontend-sdk-react', () => {
  const React = require('react');

  return {
    ...jest.requireActual('@crystal-lattice/frontend-sdk-react'),
    ApplicationPluginsProvider: ({ children }: { children: React.ReactNode }) =>
      React.createElement(React.Fragment, null, children),
  };
});

jest.mock('../src/chat/ChatPane', () => {
  const React = require('react');
  const { Pressable, Text, View } = require('react-native');

  return {
    ChatPane: ({
      sessionId,
      isActive,
      cachedEntry,
      onBeforeSessionMutation,
    }: {
      sessionId: string;
      isActive: boolean;
      cachedEntry: unknown;
      onBeforeSessionMutation?: () => void;
    }) =>
      React.createElement(
        View,
        { testID: `chat-pane-${sessionId}` },
        React.createElement(Text, null, `pane:${sessionId}`),
        React.createElement(
          Text,
          null,
          `active:${sessionId}:${isActive ? 'yes' : 'no'}`,
        ),
        React.createElement(
          Text,
          null,
          `cache:${sessionId}:${cachedEntry ? 'yes' : 'no'}`,
        ),
        React.createElement(
          Pressable,
          {
            testID: `mutate-${sessionId}`,
            onPress: onBeforeSessionMutation,
          },
          React.createElement(Text, null, `mutate:${sessionId}`),
        ),
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

function renderTabsUi(
  activeTabId: string | null,
  visibleTabs: DesktopSessionTab[],
  workspaceVisible = true,
) {
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
        workspaceVisible={workspaceVisible}
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
  const includeHiddenElements = { includeHiddenElements: true };
  it('keeps all tab labels visible while mounting only the 3 warm panes', () => {
    const screen = render(renderTabsUi(tabs[0].tabId, tabs.slice(0, 1)));

    screen.rerender(renderTabsUi(tabs[1].tabId, tabs.slice(0, 2)));
    screen.rerender(renderTabsUi(tabs[2].tabId, tabs.slice(0, 3)));
    screen.rerender(renderTabsUi(tabs[3].tabId, tabs));

    expect(screen.getByText('One')).toBeTruthy();
    expect(screen.getByText('Two')).toBeTruthy();
    expect(screen.getByText('Three')).toBeTruthy();
    expect(screen.getByText('Four')).toBeTruthy();

    expect(
      screen.queryByTestId('chat-pane-session-1', includeHiddenElements),
    ).toBeNull();
    expect(
      screen.getByTestId('chat-pane-session-2', includeHiddenElements),
    ).toBeTruthy();
    expect(
      screen.getByTestId('chat-pane-session-3', includeHiddenElements),
    ).toBeTruthy();
    expect(screen.getByTestId('chat-pane-session-4')).toBeTruthy();
    expect(screen.queryByTestId('chat-pane-session-2')).toBeNull();

    expect(
      screen.getByText('active:session-2:yes', includeHiddenElements),
    ).toBeTruthy();
    expect(
      screen.getByText('active:session-3:yes', includeHiddenElements),
    ).toBeTruthy();
    expect(screen.getByText('active:session-4:yes')).toBeTruthy();
  });

  it('remounts an older tab into the warm set from cached data when reselected', () => {
    const screen = render(renderTabsUi(tabs[0].tabId, tabs.slice(0, 1)));

    screen.rerender(renderTabsUi(tabs[1].tabId, tabs.slice(0, 2)));
    screen.rerender(renderTabsUi(tabs[2].tabId, tabs.slice(0, 3)));
    screen.rerender(renderTabsUi(tabs[3].tabId, tabs));

    expect(
      screen.queryByTestId('chat-pane-session-1', includeHiddenElements),
    ).toBeNull();

    screen.rerender(renderTabsUi(tabs[0].tabId, tabs));

    expect(screen.getByTestId('chat-pane-session-1')).toBeTruthy();
    expect(
      screen.queryByTestId('chat-pane-session-2', includeHiddenElements),
    ).toBeNull();
    expect(
      screen.getByTestId('chat-pane-session-3', includeHiddenElements),
    ).toBeTruthy();
    expect(
      screen.getByTestId('chat-pane-session-4', includeHiddenElements),
    ).toBeTruthy();

    expect(screen.getByText('active:session-1:yes')).toBeTruthy();
    expect(
      screen.getByText('active:session-3:yes', includeHiddenElements),
    ).toBeTruthy();
    expect(
      screen.getByText('active:session-4:yes', includeHiddenElements),
    ).toBeTruthy();
    expect(screen.getByText('cache:session-1:yes')).toBeTruthy();
  });

  it('keeps the 3 warm panes mounted while Home hides the Chat workspace', () => {
    const screen = render(renderTabsUi(tabs[0].tabId, tabs.slice(0, 1)));
    const includeHiddenElements = { includeHiddenElements: true };

    screen.rerender(renderTabsUi(tabs[1].tabId, tabs.slice(0, 2)));
    screen.rerender(renderTabsUi(tabs[2].tabId, tabs.slice(0, 3)));
    screen.rerender(renderTabsUi(tabs[3].tabId, tabs));
    screen.rerender(renderTabsUi(null, tabs, false));

    expect(
      screen.queryByTestId('chat-pane-session-1', includeHiddenElements),
    ).toBeNull();
    expect(
      screen.getByTestId('chat-pane-session-2', includeHiddenElements),
    ).toBeTruthy();
    expect(
      screen.getByTestId('chat-pane-session-3', includeHiddenElements),
    ).toBeTruthy();
    expect(
      screen.getByTestId('chat-pane-session-4', includeHiddenElements),
    ).toBeTruthy();
    expect(
      screen.getByTestId('desktop-chat-pane-stack', includeHiddenElements).props
        .pointerEvents,
    ).toBe('none');

    screen.rerender(renderTabsUi(tabs[2].tabId, tabs, true));

    expect(
      screen.queryByTestId('chat-pane-session-1', includeHiddenElements),
    ).toBeNull();
    expect(
      screen.getByTestId('chat-pane-session-2', includeHiddenElements),
    ).toBeTruthy();
    expect(screen.getByTestId('chat-pane-session-3')).toBeTruthy();
    expect(
      screen.getByTestId('chat-pane-session-4', includeHiddenElements),
    ).toBeTruthy();
  });

  it('promotes the matching preview identity before a Chat mutation', () => {
    const onPromotePreview = jest.fn();
    const screen = render(
      <ChatPaneTabStack
        tabs={[tabs[0]]}
        activeTabId={tabs[0].tabId}
        styleVariant="toolbarTabs"
        connectionNameById={{ 'conn-1': 'Connection One' }}
        getBackend={() => null}
        sessionsCache={sessionsCache}
        messagesCache={messagesCache}
        onUpdateCache={() => {}}
        onOpenSessionTab={() => {}}
        onPromotePreview={onPromotePreview}
      />,
    );
    const { fireEvent } = require('@testing-library/react-native');
    fireEvent.press(screen.getByTestId('mutate-session-1'));
    expect(onPromotePreview).toHaveBeenCalledWith(tabs[0].tabId);
  });
});
