import React from 'react';
import { Alert } from 'react-native';
import { render, waitFor } from '@testing-library/react-native';

import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import type { MessagesCache, SessionsCache } from '../src/cache/types';
import { ChatPaneTabStack } from '../src/tabs/ChatPaneTabStack';
import type { DesktopSessionTab } from '../src/tabs/SessionTabs';

const RANGE_ERROR = new Error(
  'HTTP 400 GET /sessions/session-1/messages?start=100&end=150: range selects no messages',
);

const listMessages = jest.fn();

/**
 * Fake backend: `listMessages` is scripted per test; every other method
 * resolves with an empty/default payload so the real ChatPane controllers
 can mount without a server.
 */
function makeFakeBackend(): AgentBackend {
  const target: Record<string, unknown> = {
    kind: 'rest',
    listMessages,
  };
  return new Proxy(target, {
    get(obj, prop, receiver) {
      if (prop in obj) {
        return Reflect.get(obj, prop, receiver);
      }
      if (prop === 'then') {
        return undefined;
      }
      const name = String(prop);
      if (
        name === 'getSelectedSessionSnapshot' ||
        name === 'getLatestEventId'
      ) {
        return async () => null;
      }
      if (name === 'listEvents') {
        return async () => ({
          events: [],
          latestEventId: null,
          cursorExpired: false,
        });
      }
      if (name === 'getSession' || name === 'getSessionRequestStatus') {
        return async () => null;
      }
      return async () => [];
    },
  }) as unknown as AgentBackend;
}

const tabs: DesktopSessionTab[] = [
  {
    tabId: 'conn-1:session-1',
    connectionId: 'conn-1',
    sessionId: 'session-1',
    title: 'Compacted',
  },
];

const sessionsCache: SessionsCache = {
  'conn-1': {
    connectionId: 'conn-1',
    sessions: [],
    lastLoadedAt: null,
  },
};

// Cached absolute range pointing past the compacted history with no
// messages loaded: opening the pane must run the initial range load.
const messagesCache: MessagesCache = {
  'conn-1': {
    'session-1': {
      connectionId: 'conn-1',
      sessionId: 'session-1',
      messages: [],
      lastLoadedAt: null,
      rangeStartText: '100',
      rangeEndText: '150',
    },
  },
};

describe('ChatPane compaction range fallback', () => {
  beforeEach(() => {
    listMessages.mockReset();
    Alert.alert = jest.fn();
  });

  it('falls back to the default range, loads the tail window, and persists the default range without alerting', async () => {
    listMessages
      .mockRejectedValueOnce(RANGE_ERROR)
      .mockResolvedValueOnce({
        messages: [
          { index: 0, message: { role: 'user', content: 'compaction summary' } },
          { index: 1, message: { role: 'assistant', content: 'reply' } },
        ],
        cursorEventId: 'store:5',
        activeRequestId: null,
      });
    const onUpdateCache = jest.fn();
    const backend = makeFakeBackend();

    const screen = render(
      <ChatPaneTabStack
        tabs={tabs}
        activeTabId={tabs[0].tabId}
        styleVariant="toolbarTabs"
        connectionNameById={{ 'conn-1': 'Connection One' }}
        getBackend={() => backend}
        sessionsCache={sessionsCache}
        messagesCache={messagesCache}
        onUpdateCache={onUpdateCache}
        onOpenSessionTab={() => {}}
      />,
    );

    const sessionId = screen.getByTestId('chat-header-session-id');
    expect(sessionId.props.children).toBe('session-1');
    expect(sessionId.props.selectable).toBe(true);

    // The invalid absolute range is requested once, then the default
    // suffix window is loaded automatically.
    await waitFor(
      () => {
        expect(listMessages).toHaveBeenCalledTimes(2);
      },
      { timeout: 5000 },
    );
    expect(listMessages).toHaveBeenNthCalledWith(1, 'session-1', {
      start: 100,
      end: 150,
    });
    expect(listMessages).toHaveBeenNthCalledWith(2, 'session-1', {
      start: -50,
    });

    // The recovered default range is persisted to the messages cache.
    await waitFor(
      () => {
        expect(onUpdateCache).toHaveBeenCalledWith(
          expect.objectContaining({
            connectionId: 'conn-1',
            sessionId: 'session-1',
            rangeStartText: '-50',
            rangeEndText: '',
          }),
        );
      },
      { timeout: 5000 },
    );

    // The fallback is graceful: no error popup for the failed range.
    expect(Alert.alert).not.toHaveBeenCalled();
  });
});
