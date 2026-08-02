import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import {
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  type AgentBackend,
  type IndexedMessage,
  type SessionNotification,
  type SessionSummary,
} from '@crystal-lattice/frontend-sdk';

import { ApplicationPluginsProvider } from '../ApplicationPluginsContext';
import { PinnedActionsProvider } from '../PinnedActionsContext';
import SessionChatScreen from '../SessionChatScreen';
import SessionsScreen from '../SessionsScreen';
import GlobalDisplayLayer from '../components/GlobalDisplayLayer';
import { ThemeProvider, lightTheme } from '../theme';

type VisualScenario =
  | 'sessions-banner'
  | 'sessions-modal'
  | 'sessions-session-hidden'
  | 'messages-banner'
  | 'messages-application-hidden'
  | 'messages-inline'
  | 'messages-modal';

const SESSION_ID = 'notification-visual-session';
const SESSION_SUMMARY: SessionSummary = {
  session_id: SESSION_ID,
  modified: 1,
  preview: 'Notification visual validation session',
  metadata: {},
  presentation: {
    title: 'Notification visual validation',
    subtitle: 'Detox production-screen harness',
    meta: '2 messages',
  },
};
const MESSAGES: IndexedMessage[] = [
  {
    index: 0,
    message: {
      role: 'user',
      content: 'Please demonstrate notification placement.',
    },
  },
  {
    index: 1,
    message: {
      role: 'assistant',
      content: 'The notification should not overlap this transcript.',
    },
  },
];

function createHarnessBackend(): AgentBackend {
  return {
    kind: 'inProcess',
    getCapabilities: () => ({
      featureCompletions: false,
      sessionUiSchema: false,
      sessionConfigOverrides: false,
      sessionPlugins: false,
      applicationActions: true,
      applicationConfig: false,
    }),
    listAgents: async () => ['default'],
    listSessions: async () => [SESSION_SUMMARY],
    listApplicationActions: async () => [],
    listApplicationUiSchema: async () => [],
    getLatestEventId: async () => '0',
    listEvents: async () => ({
      events: [],
      latestEventId: '0',
      cursorExpired: false,
    }),
  } as unknown as AgentBackend;
}

function sessionSummaryForScenario(scenario: VisualScenario): SessionSummary {
  if (scenario !== 'messages-inline') {
    return SESSION_SUMMARY;
  }
  const notification: SessionNotification = {
    id: 'notification-visual-inline',
    key: 'notification:visual:inline',
    kind: 'notification',
    status: 'pending',
    severity: 'warning',
    title: 'Inline session notification',
    body: 'This persistent notification is part of the Messages content flow.',
    created_at: '2026-07-30T00:00:00Z',
    updated_at: '2026-07-30T00:00:00Z',
    source: { plugin: 'notification_visual_harness' },
    display: {
      format: 'text',
      title: 'Inline session notification',
      body: 'This persistent notification is part of the Messages content flow.',
      variant: 'warning',
      presentation: 'inline',
      dismissible: true,
    },
    model_visibility: 'hidden',
  };
  return {
    ...SESSION_SUMMARY,
    metadata: {
      notifications: {
        items: [notification],
      },
    },
  };
}

export function MobileNotificationBannerHarness(): React.JSX.Element {
  const backend = useMemo(() => createHarnessBackend(), []);
  const [scenario, setScenario] = useState<VisualScenario | null>(null);

  useEffect(() => {
    if (!scenario || scenario === 'messages-inline') return;
    const timer = setTimeout(() => {
      const isSessions = scenario.startsWith('sessions');
      const presentation = scenario.endsWith('modal') ? 'modal' : 'banner';
      const source =
        scenario === 'sessions-session-hidden'
          ? 'session_notification'
          : scenario === 'messages-application-hidden'
            ? 'application_notification'
            : isSessions
              ? 'application_notification'
              : 'session_notification';
      const count = presentation === 'banner' ? 2 : 1;
      for (let index = 1; index <= count; index += 1) {
        emitDisplayPresentation(
          backend,
          normalizeDisplayEnvelope({
          id: `notification-visual-${scenario}-${index}`,
          source,
          connectionId: 'notification-visual',
          sessionId: source === 'session_notification' ? SESSION_ID : undefined,
          updatedAt: '2026-07-30T00:00:00Z',
          display: {
            format: 'text',
            title:
              presentation === 'modal'
                ? 'Notification visual modal'
                : `Notification visual banner ${index}`,
            body: isSessions
              ? 'Application notification on the Sessions screen.'
              : 'Session notification on the Messages screen.',
            variant: isSessions ? 'success' : 'warning',
            presentation,
            dismissible: true,
          },
          }),
        );
      }
    }, 100);
    return () => clearTimeout(timer);
  }, [backend, scenario]);

  return (
    <ThemeProvider theme={lightTheme}>
      <PinnedActionsProvider>
        <ApplicationPluginsProvider
          backend={backend}
          connectionId="notification-visual"
        >
          <View style={styles.root} testID="notification-banner-harness-ready">
            {scenario === null ? (
              <View style={styles.scenarioPicker}>
                <Text style={styles.title}>Notification visual scenarios</Text>
                {(
                  [
                    'sessions-banner',
                    'sessions-modal',
                    'sessions-session-hidden',
                    'messages-banner',
                    'messages-application-hidden',
                    'messages-inline',
                    'messages-modal',
                  ] as VisualScenario[]
                ).map((item) => (
                  <Pressable
                    key={item}
                    testID={`notification-scenario-${item}`}
                    style={styles.scenarioButton}
                    onPress={() => setScenario(item)}
                  >
                    <Text style={styles.scenarioButtonText}>{item}</Text>
                  </Pressable>
                ))}
              </View>
            ) : (
              <GlobalDisplayLayer
                backend={backend}
                connectionId="notification-visual"
              >
                <View style={styles.screen} testID="notification-visual-ready">
                  {scenario.startsWith('sessions') ? (
                    <SessionsScreen
                      backend={backend}
                      connectionId="notification-visual"
                      cachedSessions={[SESSION_SUMMARY]}
                      lastLoadedAt={1}
                      isActive={false}
                      onUpdateCache={() => {}}
                      onSelectSession={() => {}}
                    />
                  ) : (
                    <SessionChatScreen
                      backend={backend}
                      connectionId="notification-visual"
                      isActive={false}
                      sessionId={SESSION_ID}
                      sessionSummary={sessionSummaryForScenario(scenario)}
                      cachedMessages={MESSAGES}
                      lastLoadedAt={1}
                      cachedEventsCursorId="0"
                      cachedActiveRequestId={null}
                      onUpdateCache={() => {}}
                      onUpdateSessionSummaries={() => {}}
                      onBack={() => {}}
                      onNavigateToSession={() => {}}
                      initialComposeText=""
                      initialScrollAnchor={null}
                      initialRangeStartText="-50"
                      initialRangeEndText=""
                      onSaveComposeText={() => {}}
                      onSaveScrollAnchor={() => {}}
                      onSaveHistoryRange={() => {}}
                      debugTimeline={[]}
                      onAppendDebugTimelineEntry={() => {}}
                    />
                  )}
                </View>
              </GlobalDisplayLayer>
            )}
          </View>
        </ApplicationPluginsProvider>
      </PinnedActionsProvider>
    </ThemeProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  screen: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  scenarioPicker: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    gap: 10,
  },
  title: {
    color: '#000000',
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 10,
  },
  scenarioButton: {
    borderRadius: 8,
    backgroundColor: '#007AFF',
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  scenarioButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
    textAlign: 'center',
  },
});