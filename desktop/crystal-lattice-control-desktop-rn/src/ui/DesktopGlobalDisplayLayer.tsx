import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Clipboard, Linking, StyleSheet, View } from 'react-native';

import {
  ApplicationNotificationsController,
  displayEnvelopeLifecycleKey,
  displayEnvelopeRevisionKey,
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  normalizeDisplayEnvelopeForHost,
  subscribeDisplayPresentation,
  type ActionDisplayFollowupAction,
  type AgentBackend,
  type ApplicationNotification,
  type DisplayEnvelope,
} from '@crystal-lattice/frontend-sdk';
import {
  NotificationBannerHost,
  type NotificationBannerHostItem,
  useTheme,
} from '@crystal-lattice/frontend-rn-components';

import type { OpenConnectionsById } from '../connections/useOpenConnections';
import { ActionResultInlineCard } from './ActionResultInlineCard';

interface DesktopGlobalDisplayLayerProps {
  openConnectionsById: OpenConnectionsById;
  connectionNameById: Record<string, string>;
}

function ConnectionDisplaySubscription({
  connectionId,
  backend,
  onDisplay,
  onNotifications,
}: {
  connectionId: string;
  backend: AgentBackend;
  onDisplay: (envelope: DisplayEnvelope) => void;
  onNotifications: (
    connectionId: string,
    notifications: ApplicationNotification[],
  ) => void;
}): null {
  useEffect(() => subscribeDisplayPresentation(backend, onDisplay), [backend, onDisplay]);
  useEffect(() => {
    const controller = new ApplicationNotificationsController({ backend, connectionId });
    const sync = () => {
      onNotifications(connectionId, controller.getSnapshot().notifications);
    };
    const unsubscribe = controller.subscribe(sync);
    sync();
    controller.start();
    return () => {
      unsubscribe();
      controller.close();
      onNotifications(connectionId, []);
    };
  }, [backend, connectionId, onNotifications]);
  return null;
}

export function DesktopGlobalDisplayLayer({
  openConnectionsById,
  connectionNameById,
}: DesktopGlobalDisplayLayerProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [transientItems, setTransientItems] = useState<DisplayEnvelope[]>([]);
  const [applicationNotificationsByConnection, setApplicationNotificationsByConnection] =
    useState<Record<string, ApplicationNotification[]>>({});
  const [dismissedRevisions, setDismissedRevisions] = useState<string[]>([]);

  const upsert = useCallback((envelope: DisplayEnvelope) => {
    const normalized = normalizeDisplayEnvelopeForHost(envelope, 'desktop');
    const key = displayEnvelopeLifecycleKey(normalized);
    setTransientItems((current) => {
      const index = current.findIndex(
        (item) => displayEnvelopeLifecycleKey(item) === key,
      );
      if (index < 0) return [...current, normalized];
      const next = current.slice();
      next[index] = normalized;
      return next;
    });
  }, []);

  const updateApplicationNotifications = useCallback(
    (connectionId: string, notifications: ApplicationNotification[]) => {
      setApplicationNotificationsByConnection((current) => ({
        ...current,
        [connectionId]: notifications,
      }));
    },
    [],
  );

  const dismiss = useCallback((envelope: DisplayEnvelope) => {
    const revision = displayEnvelopeRevisionKey(envelope);
    const lifecycle = displayEnvelopeLifecycleKey(envelope);
    setDismissedRevisions((current) =>
      current.includes(revision) ? current : [...current, revision],
    );
    setTransientItems((current) =>
      current.filter((item) => displayEnvelopeLifecycleKey(item) !== lifecycle),
    );
  }, []);

  const connections = Object.entries(openConnectionsById).flatMap(([connectionId, state]) =>
    state.status === 'open' && state.backend ? [{ connectionId, backend: state.backend }] : [],
  );
  const backendFor = (envelope: DisplayEnvelope): AgentBackend | null =>
    envelope.connectionId
      ? openConnectionsById[envelope.connectionId]?.backend ?? null
      : null;

  const applicationItems = Object.entries(applicationNotificationsByConnection).flatMap(
    ([connectionId, notifications]) =>
      notifications
        .filter((notification) => notification.status === 'pending')
        .map((notification) =>
          normalizeDisplayEnvelopeForHost(
            normalizeDisplayEnvelope({
              id: notification.id,
              source: 'application_notification',
              sourceKey: notification.key,
              connectionId,
              display: notification.display,
              createdAt: notification.created_at,
              updatedAt: notification.updated_at,
            }),
            'desktop',
          ),
        ),
  );
  const items = [...applicationItems, ...transientItems].filter(
    (item) => !dismissedRevisions.includes(displayEnvelopeRevisionKey(item)),
  );

  const followup = useCallback(
    async (action: ActionDisplayFollowupAction, envelope: DisplayEnvelope) => {
      if (action.kind === 'dismiss') {
        dismiss(envelope);
      } else if (action.kind === 'open_url') {
        await Linking.openURL(action.url);
      } else if (action.kind === 'copy_text') {
        Clipboard.setString(action.text);
      } else if (action.kind === 'run_action') {
        const backend = backendFor(envelope);
        if (!backend) return;
        const response =
          envelope.sessionId && backend.executeSessionAction
            ? await backend.executeSessionAction({
                sessionId: envelope.sessionId,
                pluginId: action.plugin,
                actionId: action.action_id,
                actionOwner: action.action_owner,
                inputs: { ...(action.fixed_params ?? {}) },
              })
            : await backend.executeAction({
                pluginId: action.plugin,
                actionId: action.action_id,
                actionOwner: action.action_owner,
                inputs: { ...(action.fixed_params ?? {}) },
              });
        if (response.status === 'ok' && response.result.display) {
          emitDisplayPresentation(
            backend,
            normalizeDisplayEnvelope({
              source: 'action_response',
              connectionId: envelope.connectionId,
              sessionId: envelope.sessionId,
              display: response.result.display,
            }),
          );
        }
      }
    },
    [dismiss, openConnectionsById],
  );

  const banners: NotificationBannerHostItem[] = items
    .filter((item) => item.display.presentation === 'banner')
    .map((envelope) => ({
      envelope,
      connectionLabel: envelope.connectionId
        ? connectionNameById[envelope.connectionId]
        : null,
      sessionLabel: envelope.sessionId ?? null,
    }));
  const inline = items.filter((item) => item.display.presentation === 'inline');

  return (
    <>
      {connections.map(({ connectionId, backend }) => (
        <ConnectionDisplaySubscription
          key={connectionId}
          connectionId={connectionId}
          backend={backend}
          onDisplay={upsert}
          onNotifications={updateApplicationNotifications}
        />
      ))}
      <NotificationBannerHost
        items={banners}
        onDismiss={(item) => dismiss(item.envelope)}
        onFollowupAction={(action, item) => {
          void followup(action, item.envelope);
        }}
      />
      {inline.length > 0 ? (
        <View style={styles.inlineHost}>
          {inline.map((envelope) => (
            <ActionResultInlineCard
              key={`${envelope.connectionId ?? ''}:${envelope.id}`}
              display={envelope.display}
              onDismiss={() => dismiss(envelope)}
              onFollowupAction={(action) => {
                void followup(action, envelope);
              }}
            />
          ))}
        </View>
      ) : null}
    </>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    inlineHost: {
      position: 'absolute',
      top: 8,
      left: 12,
      right: 12,
      zIndex: 9000,
      backgroundColor: theme.background,
    },
  });
}