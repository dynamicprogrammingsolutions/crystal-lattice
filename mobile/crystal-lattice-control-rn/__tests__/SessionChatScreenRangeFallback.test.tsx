import React from 'react';
import { AppState, View } from 'react-native';

import { render, waitFor } from '@testing-library/react-native';

import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

import { ApplicationPluginsProvider } from '../src/ApplicationPluginsContext';
import { PinnedActionsProvider } from '../src/PinnedActionsContext';
import SessionChatScreen from '../src/SessionChatScreen';
import { ThemeProvider, lightTheme } from '../src/theme';

const CONNECTION_ID = 'range-fallback';
const SESSION_ID = 'session-1';

const RANGE_ERROR = new Error(
  'HTTP 400 GET /sessions/session-1/messages?start=100&end=150: range selects no messages',
);

const TAIL_MESSAGES = [
  {
    index: 0,
    message: { role: 'user', content: 'compaction summary' },
  },
  {
    index: 1,
    message: { role: 'assistant', content: 'reply' },
  },
];

// Mirrors the server behaviour after compaction: an absolute range that
// starts past the rewritten history selects no messages and is rejected
// with HTTP 400, while the default suffix window loads the tail.
function makeBackend(listMessages: jest.Mock): AgentBackend {
  return {
    kind: 'rest',
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: false,
      sessionConfigOverrides: false,
      sessionPlugins: false,
      applicationActions: false,
      applicationConfig: false,
    }),
    listAgents: async () => ['default'],
    getSessionAgent: async () => 'default',
    listMessages,
    getSessionSummary: async () => null,
    getSelectedSessionSnapshot: async () => null,
    listSessionSnapshots: async () => [],
    listSessionPlugins: async () => [],
    getSessionUiSchema: async () => [],
    getSessionApplicationUiSchema: async () => [],
    getSessionOverrides: async () => ({}),
    getSessionConfigSchema: async () => [],
    getSessionBaseConfig: async () => ({}),
    listApplicationActions: async () => [],
    listApplicationUiSchema: async () => [],
    getLatestEventId: async () => null,
    listEvents: async () => ({
      events: [],
      latestEventId: null,
      cursorExpired: false,
    }),
  } as unknown as AgentBackend;
}

describe('SessionChatScreen compaction range fallback', () => {
  beforeEach(() => {
    (AppState as any).currentState = 'active';
  });

  it('falls back to the default range, loads the tail window, and saves the default range without alerting', async () => {
    const listMessages = jest
      .fn<Promise<any>, [string, { start?: number; end?: number }?]>()
      .mockRejectedValueOnce(RANGE_ERROR)
      .mockResolvedValueOnce({
        messages: TAIL_MESSAGES,
        cursorEventId: 'store:5',
        activeRequestId: null,
        readonly: false,
        snapshotId: null,
      });
    const backend = makeBackend(listMessages);
    const onUpdateCache = jest.fn();
    const onSaveHistoryRange = jest.fn();
    const { Alert } = require('react-native');
    Alert.alert = jest.fn();

    render(
      <ThemeProvider theme={lightTheme}>
        <PinnedActionsProvider>
          <ApplicationPluginsProvider
            backend={backend}
            connectionId={CONNECTION_ID}
          >
            <View>
              <SessionChatScreen
                backend={backend}
                connectionId={CONNECTION_ID}
                isActive
                sessionId={SESSION_ID}
                sessionSummary={null}
                cachedMessages={null}
                lastLoadedAt={null}
                cachedEventsCursorId={null}
                cachedActiveRequestId={null}
                onUpdateCache={onUpdateCache}
                onBack={() => {}}
                initialComposeText=""
                initialScrollAnchor={null}
                initialRangeStartText="100"
                initialRangeEndText="150"
                onSaveComposeText={() => {}}
                onSaveScrollAnchor={() => {}}
                onSaveHistoryRange={onSaveHistoryRange}
                debugTimeline={[]}
                onAppendDebugTimelineEntry={() => {}}
              />
            </View>
          </ApplicationPluginsProvider>
        </PinnedActionsProvider>
      </ThemeProvider>,
    );

    // The invalid absolute range is requested once, then the default
    // suffix window is loaded automatically.
    await waitFor(
      () => {
        expect(listMessages).toHaveBeenCalledTimes(2);
      },
      { timeout: 5000 },
    );
    expect(listMessages).toHaveBeenNthCalledWith(1, SESSION_ID, {
      start: 100,
      end: 150,
    });
    expect(listMessages).toHaveBeenNthCalledWith(2, SESSION_ID, {
      start: -50,
    });

    // The recovered default range is persisted via the history-range save.
    await waitFor(
      () => {
        expect(onSaveHistoryRange).toHaveBeenCalledWith('-50', '');
      },
      { timeout: 5000 },
    );

    // The fallback is graceful: no error popup for the failed range.
    expect(Alert.alert).not.toHaveBeenCalled();
  });
});
