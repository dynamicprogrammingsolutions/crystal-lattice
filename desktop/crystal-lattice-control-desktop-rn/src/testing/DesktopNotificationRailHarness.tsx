import React, { useEffect, useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  type AgentBackend,
  type SessionNotification,
} from '@crystal-lattice/frontend-sdk';
import {
  SessionNotificationsHost,
  ThemeProvider,
} from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { ActionResultInlineCard } from '../ui/ActionResultInlineCard';
import {
  DesktopConnectionDisplayRail,
  DesktopGlobalDisplayLayer,
} from '../ui/DesktopGlobalDisplayLayer';

function createBackend(): AgentBackend {
  return {
    kind: 'inProcess',
    getLatestEventId: async () => '0',
    listEvents: async () => ({
      events: [],
      latestEventId: '0',
      cursorExpired: false,
    }),
  } as unknown as AgentBackend;
}

const SESSION_NOTIFICATION: SessionNotification = {
  id: 'desktop-session-notification',
  key: 'desktop:session',
  kind: 'notification',
  status: 'pending',
  severity: 'warning',
  title: 'Active session notification',
  body: 'Session notification in the shared message-area rail.',
  created_at: '2026-07-31T00:00:00Z',
  updated_at: '2026-07-31T00:00:00Z',
  source: { plugin: 'desktop_notification_rail_harness' },
  display: {
    format: 'text',
    title: 'Active session notification',
    body: 'Session notification in the shared message-area rail.',
    variant: 'warning',
    presentation: 'modal',
    dismissible: true,
  },
  model_visibility: 'hidden',
};

export function DesktopNotificationRailHarness(): React.JSX.Element {
  const theme = useDesktopTheme();
  const first = useMemo(() => createBackend(), []);
  const second = useMemo(() => createBackend(), []);

  useEffect(() => {
    const timer = setTimeout(() => {
      emitDisplayPresentation(
        first,
        normalizeDisplayEnvelope({
          id: 'first-connection-notification',
          source: 'action_response',
          ownershipScope: 'connection',
          connectionId: 'first',
          display: {
            format: 'text',
            title: 'First application notification',
            body: 'Banner from the first open connection.',
            variant: 'success',
            presentation: 'banner',
          },
        }),
      );
      emitDisplayPresentation(
        second,
        normalizeDisplayEnvelope({
          id: 'second-connection-notification',
          source: 'action_response',
          ownershipScope: 'connection',
          connectionId: 'second',
          display: {
            format: 'text',
            title: 'Second application notification',
            body: 'Desktop modal fallback from the second connection.',
            variant: 'info',
            presentation: 'modal',
          },
        }),
      );
    }, 100);
    return () => clearTimeout(timer);
  }, [first, second]);

  return (
    <ThemeProvider theme={theme}>
      <DesktopGlobalDisplayLayer
        openConnectionsById={{
          first: {
            status: 'open',
            baseUrl: 'http://first',
            backend: first as any,
          },
          second: {
            status: 'open',
            baseUrl: 'http://second',
            backend: second as any,
          },
        }}
        connectionNameById={{
          first: 'First connection',
          second: 'Second connection',
        }}
      >
        <View style={styles.root} testID="desktop-notification-rail-harness-ready">
          <View style={styles.header}>
            <Text style={styles.title}>Notification rail chat</Text>
            <Text style={styles.subtitle}>active-session</Text>
          </View>
          <View testID="desktop-notification-combined-rail">
            <DesktopConnectionDisplayRail />
            <SessionNotificationsHost
              sessionSummary={{
                session_id: 'active-session',
                modified: 0,
                preview: '',
                metadata: {
                  notifications: {
                    items: [SESSION_NOTIFICATION],
                  },
                },
              }}
              inlinePresentations={['inline', 'banner', 'modal']}
              renderInline={({ notification, onDismiss, onFollowupAction }) => (
                <ActionResultInlineCard
                  display={notification.display}
                  onDismiss={onDismiss}
                  onFollowupAction={(action) => onFollowupAction(action)}
                />
              )}
            />
          </View>
          <View style={styles.messages} testID="desktop-notification-message-content">
            <Text style={styles.message}>Messages are pushed below the notification rail.</Text>
          </View>
        </View>
      </DesktopGlobalDisplayLayer>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#D1D1D6',
    backgroundColor: '#FFFFFF',
  },
  title: {
    color: '#000000',
    fontSize: 16,
    fontWeight: '700',
  },
  subtitle: {
    color: '#636366',
    fontSize: 12,
    marginTop: 2,
  },
  messages: {
    flex: 1,
    margin: 12,
    padding: 16,
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
  },
  message: {
    color: '#000000',
    fontSize: 14,
  },
});