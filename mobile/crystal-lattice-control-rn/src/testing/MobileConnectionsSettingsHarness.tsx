import React, { useMemo, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import type {
  ConnectionRecord,
  Transport,
} from '@crystal-lattice/frontend-sdk';
import {
  MarkdownDisplayPreferencesProvider,
  applyDisplayTypographyPreset,
} from '@crystal-lattice/frontend-rn-components';

import ConnectedRoot from '../ConnectedRoot';
import { PinnedActionsProvider } from '../PinnedActionsContext';
import SelectableMarkdownMessageContent from '../components/SelectableMarkdownMessageContent';
import MessageBubble from '../components/MessageBubble';
import { lightTheme, ThemeProvider } from '../theme';
import { usePersistedMarkdownDisplayPreferences } from '../useMarkdownDisplayPreferences';

const CONNECTIONS: ConnectionRecord[] = [
  {
    id: 'active',
    kind: 'manual',
    name: 'Active server',
    host: '127.0.0.1',
    port: 8080,
    lastUsedAt: 2,
  },
  {
    id: 'closed',
    kind: 'manual',
    name: 'Closed server',
    host: '127.0.0.1',
    port: 8081,
    lastUsedAt: 1,
  },
];

const transport = {
  request: async () => ({
    status: 200,
    headers: {},
    data: { message: 'healthy' },
  }),
} as unknown as Transport;

export function MobileConnectionsSettingsHarness(): React.JSX.Element {
  const {
    preferences,
    setPreferences,
    hydrated,
  } = usePersistedMarkdownDisplayPreferences();
  const [activeConnectionId, setActiveConnectionId] = useState<string | null>('active');
  const [lastAction, setLastAction] = useState('ready');
  const activeTransport = useMemo(
    () => (activeConnectionId ? transport : null),
    [activeConnectionId],
  );
  const theme = useMemo(
    () => applyDisplayTypographyPreset(lightTheme, preferences.baseFontSize),
    [preferences.baseFontSize],
  );

  if (!hydrated) {
    return <ActivityIndicator testID="connections-settings-harness-loading" />;
  }

  return (
    <ThemeProvider theme={theme}>
      <MarkdownDisplayPreferencesProvider
        value={preferences}
        onChange={setPreferences}
      >
        <PinnedActionsProvider>
          <SafeAreaProvider>
          <View style={styles.root} testID="connections-settings-harness-ready">
            <View style={styles.markdownPreview} testID="markdown-preview">
              <View testID="markdown-preview-h1">
                <SelectableMarkdownMessageContent text="# Heading" />
              </View>
              <View testID="markdown-preview-body">
                <SelectableMarkdownMessageContent text="Body text" />
              </View>
              <MessageBubble
                index={99}
                message={{
                  role: 'assistant',
                  content: '',
                  metadata: { footer: 'Representative message footer' },
                }}
                footerElements={[
                  {
                    ui_type: 'message_footer',
                    data: 'metadata.footer',
                    template: '{{data}}',
                  } as any,
                ]}
              />
              <Text
                testID="footer-geometry-probe"
                style={{
                  alignSelf: 'flex-start',
                  fontSize: theme.typography.fontSize.tiny,
                  lineHeight: theme.typography.lineHeight.tiny,
                  color: theme.text,
                }}
              >
                Footer geometry probe
              </Text>
            </View>
            <Text testID="connections-harness-last-action">{lastAction}</Text>
            <View style={styles.connections}>
              <ConnectedRoot
                backend={null}
                transport={activeTransport}
                onDisconnect={() => {
                  setActiveConnectionId(null);
                  setLastAction('disconnected');
                }}
                connections={CONNECTIONS}
                connectionsLoading={false}
                onSelectConnectionRecord={(record) => {
                  setActiveConnectionId(record.id);
                  setLastAction(`opened:${record.id}`);
                }}
                onNewConnectionRequested={() => setLastAction('newConnection')}
                renderConnectionWizard={() => null}
                onDeleteConnectionRecord={(record) => setLastAction(`deleted:${record.id}`)}
                activeConnectionId={activeConnectionId}
                sessionsCache={{}}
                onUpdateSessionsCache={() => {}}
                messagesCache={{}}
                onUpdateMessagesCache={() => {}}
                onSaveMessagesComposeText={() => {}}
                onSaveMessagesScrollAnchor={() => {}}
                onSaveMessagesHistoryRange={() => {}}
                debugTimeline={[]}
                onAppendDebugTimelineEntry={() => {}}
              />
            </View>
          </View>
          </SafeAreaProvider>
        </PinnedActionsProvider>
      </MarkdownDisplayPreferencesProvider>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  markdownPreview: {
    paddingHorizontal: 16,
    paddingTop: 4,
  },
  connections: {
    flex: 1,
  },
});