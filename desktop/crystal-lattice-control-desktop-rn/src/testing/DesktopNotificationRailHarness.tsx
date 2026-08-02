import React, { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  type ApplicationNotification,
  type AgentBackend,
  type SessionNotification,
} from '@crystal-lattice/frontend-sdk';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import {
  DesktopConnectionDisplayRail,
  DesktopGlobalDisplayLayer,
} from '../ui/DesktopGlobalDisplayLayer';
import { DesktopSessionNotificationRail } from '../ui/DesktopSessionNotificationRail';

function createBackend(
  applicationNotification: ApplicationNotification,
): AgentBackend {
  let currentApplicationNotification = applicationNotification;
  let currentSessionNotification = SESSION_NOTIFICATION;
  return {
    kind: 'inProcess',
    getLatestEventId: async () => '0',
    listEvents: async () => ({
      events: [],
      latestEventId: '0',
      cursorExpired: false,
    }),
    listApplicationNotifications: async () =>
      currentApplicationNotification.status === 'pending'
        ? [currentApplicationNotification]
        : [],
    dismissApplicationNotification: async () => {
      currentApplicationNotification = {
        ...currentApplicationNotification,
        status: 'dismissed',
        revision: (currentApplicationNotification.revision ?? 1) + 1,
        updated_at: '2026-08-01T00:00:01Z',
        dismissal: { dismissed_at: '2026-08-01T00:00:01Z' },
      };
      return currentApplicationNotification;
    },
    getSessionSummary: async () => ({
      session_id: 'active-session',
      modified: 0,
      preview: '',
      metadata: {
        notifications: {
          items: [currentSessionNotification],
        },
      },
    }),
    dismissSessionNotification: async () => {
      currentSessionNotification = {
        ...currentSessionNotification,
        status: 'dismissed',
        revision: (currentSessionNotification.revision ?? 1) + 1,
        updated_at: '2026-08-01T00:00:01Z',
        dismissal: { dismissed_at: '2026-08-01T00:00:01Z' },
      };
      return currentSessionNotification;
    },
  } as unknown as AgentBackend;
}

const FIRST_APPLICATION_NOTIFICATION: ApplicationNotification = {
  id: 'first-connection-notification',
  key: 'desktop:first',
  kind: 'notification',
  status: 'pending',
  revision: 1,
  severity: 'success',
  title: 'First application notification',
  body: 'Banner from the first open connection.',
  created_at: '2026-08-01T00:00:00Z',
  updated_at: '2026-08-01T00:00:00Z',
  source: { plugin: 'desktop_notification_rail_harness' },
  display: {
    format: 'text',
    title: 'First application notification',
    body: 'Banner from the first open connection.',
    variant: 'success',
    presentation: 'banner',
    dismissible: true,
  },
  model_visibility: 'hidden',
};

const SECOND_APPLICATION_NOTIFICATION: ApplicationNotification = {
  ...FIRST_APPLICATION_NOTIFICATION,
  id: 'second-connection-notification',
  key: 'desktop:second',
  severity: 'info',
  title: 'Second application notification',
  body: 'Desktop modal fallback from the second connection.',
  display: {
    format: 'text',
    title: 'Second application notification',
    body: 'Desktop modal fallback from the second connection.',
    variant: 'info',
    presentation: 'modal',
    dismissible: true,
  },
};

const SESSION_NOTIFICATION: SessionNotification = {
  id: 'desktop-session-notification',
  key: 'desktop:session',
  kind: 'notification',
  status: 'pending',
  revision: 1,
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
  const first = useMemo(
    () => createBackend(FIRST_APPLICATION_NOTIFICATION),
    [],
  );
  const second = useMemo(
    () => createBackend(SECOND_APPLICATION_NOTIFICATION),
    [],
  );

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
          <View
            accessible
            accessibilityLabel="Notification rail: First connection; Second connection; Active session notification"
            testID="desktop-notification-combined-rail"
          >
            <DesktopConnectionDisplayRail />
            <DesktopSessionNotificationRail
              backend={first}
              connectionId="first"
              sessionId="active-session"
              sessionSummary={null}
            />
          </View>
          <View
            accessible
            accessibilityLabel="Desktop notification message content"
            style={styles.messages}
            testID="desktop-notification-message-content"
          >
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