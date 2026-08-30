import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import type { ConnectionRecord } from '@crystal-lattice/frontend-sdk';

import ConnectedRoot from '../ConnectedRoot';
import { HomeWorkspaceProvider } from '../HomeWorkspaceContext';
import { PinnedActionsProvider } from '../PinnedActionsContext';
import { ThemeProvider, lightTheme } from '../theme';

const now = Date.now() / 1000;
const connections: ConnectionRecord[] = [
  {
    id: 'office',
    kind: 'cloud',
    name: 'Office',
    orchestratorUrl: 'https://cloud.test',
    connectionId: 'office-runtime',
    token: 'token',
    lastUsedAt: 2,
  },
  {
    id: 'laptop',
    kind: 'cloud',
    name: 'Laptop',
    orchestratorUrl: 'https://cloud.test',
    connectionId: 'laptop-runtime',
    token: 'token',
    lastUsedAt: 1,
  },
];

export function MobileHomeHarness(): React.JSX.Element {
  const [lastAction, setLastAction] = useState('ready');

  return (
    <ThemeProvider theme={lightTheme}>
      <PinnedActionsProvider>
        <HomeWorkspaceProvider>
          <SafeAreaProvider>
            <View style={styles.root} testID="home-harness-ready">
              <Text testID="home-harness-last-action">{lastAction}</Text>
              <ConnectedRoot
                backend={null}
                transport={null}
                onDisconnect={() => {}}
                connections={connections}
                connectionsLoading={false}
                onSelectConnectionRecord={async (record) => {
                  setLastAction(`opened:${record.id}`);
                  return true;
                }}
                onNewConnectionRequested={() => setLastAction('newConnection')}
                renderConnectionWizard={() => null}
                onDeleteConnectionRecord={() => {}}
                activeConnectionId={null}
                sessionsCache={{
                  office: {
                    connectionId: 'office',
                    lastLoadedAt: Date.now(),
                    sessions: [
                      {
                        session_id: 'shared',
                        modified: now - 20,
                        preview: 'Office shared session',
                      },
                    ],
                  },
                  laptop: {
                    connectionId: 'laptop',
                    lastLoadedAt: Date.now(),
                    sessions: [
                      {
                        session_id: 'shared',
                        modified: now - 10,
                        preview: 'Laptop shared session',
                      },
                      {
                        session_id: 'older',
                        modified: now - 2 * 24 * 60 * 60,
                        preview: 'Older laptop session',
                      },
                    ],
                  },
                }}
                onUpdateSessionsCache={() => {}}
                messagesCache={{
                  laptop: {
                    older: {
                      connectionId: 'laptop',
                      sessionId: 'older',
                      messages: [],
                      lastLoadedAt: Date.now(),
                      eventsCursorId: null,
                      activeRequestId: null,
                      composeText: '',
                      rangeStartText: '-50',
                      rangeEndText: '',
                    },
                  },
                }}
                onUpdateMessagesCache={() => {}}
                onSaveMessagesComposeText={() => {}}
                onSaveMessagesScrollAnchor={() => {}}
                onSaveMessagesHistoryRange={() => {}}
                debugTimeline={[]}
                onAppendDebugTimelineEntry={() => {}}
              />
            </View>
          </SafeAreaProvider>
        </HomeWorkspaceProvider>
      </PinnedActionsProvider>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
});