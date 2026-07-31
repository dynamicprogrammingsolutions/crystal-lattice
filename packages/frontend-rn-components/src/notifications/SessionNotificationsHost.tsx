import React, { useEffect, useMemo, useRef, useState } from 'react';
import { View } from 'react-native';

import type {
  ActionDisplayFollowupAction,
  DisplayPresentation,
  Event,
  SessionNotification,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import {
  mergeSessionNotificationEvents,
  normalizeDisplayEnvelope,
  selectPendingSessionNotifications,
} from '@crystal-lattice/frontend-sdk';

import { NotificationBanner } from './NotificationBanner';

export interface SessionNotificationsHostProps {
  sessionSummary: SessionSummary | null;
  events?: readonly Event[];
  onBanner?: (notification: SessionNotification) => void;
  onModal?: (notification: SessionNotification) => void;
  onFollowupAction?: (
    action: ActionDisplayFollowupAction,
    notification: SessionNotification,
  ) => void;
  renderInline?: (options: {
    notification: SessionNotification;
    onDismiss: () => void;
    onFollowupAction: (action: ActionDisplayFollowupAction) => void;
  }) => React.ReactNode;
  inlinePresentations?: DisplayPresentation[];
}

export function SessionNotificationsHost({
  sessionSummary,
  events = [],
  onBanner,
  onModal,
  onFollowupAction,
  renderInline,
  inlinePresentations = ['inline'],
}: SessionNotificationsHostProps): React.JSX.Element | null {
  const [dismissedRevisions, setDismissedRevisions] = useState<string[]>([]);
  const routed = useRef<Record<string, string>>({});
  const inlinePresentationSet = useMemo(
    () => new Set(inlinePresentations),
    [inlinePresentations],
  );
  const notifications = useMemo(
    () =>
      mergeSessionNotificationEvents(
        selectPendingSessionNotifications(sessionSummary),
        events,
      ).filter(
        (notification) => {
          const revision = `${notification.id}:${notification.updated_at}`;
          return (
            notification.status === 'pending' &&
            !dismissedRevisions.includes(revision)
          );
        },
      ),
    [dismissedRevisions, events, sessionSummary],
  );

  useEffect(() => {
    for (const notification of notifications) {
      const envelope = normalizeDisplayEnvelope({
        id: notification.id,
        source: 'session_notification',
        sessionId: sessionSummary?.session_id,
        display: notification.display,
      });
      const presentation = envelope.display.presentation ?? 'inline';
      const revision = `${notification.updated_at}:${presentation}`;
      if (routed.current[notification.id] === revision) continue;
      routed.current[notification.id] = revision;
      if (inlinePresentationSet.has(presentation)) continue;
      if (presentation === 'banner') onBanner?.(notification);
      if (presentation === 'modal') onModal?.(notification);
    }
  }, [
    inlinePresentationSet,
    notifications,
    onBanner,
    onModal,
    sessionSummary?.session_id,
  ]);

  const inline = notifications.filter(
    (notification) =>
      inlinePresentationSet.has(notification.display.presentation ?? 'inline'),
  );
  if (inline.length === 0) return null;

  return (
    <View>
      {inline.map((notification) => (
        <React.Fragment key={notification.id}>
          {renderInline ? (
            renderInline({
              notification,
              onDismiss: () =>
                setDismissedRevisions((current) => [
                  ...current,
                  `${notification.id}:${notification.updated_at}`,
                ]),
              onFollowupAction: (action) =>
                onFollowupAction?.(action, notification),
            })
          ) : (
            <NotificationBanner
              display={notification.display}
              severity={notification.severity}
              onDismiss={() =>
                setDismissedRevisions((current) => [
                  ...current,
                  `${notification.id}:${notification.updated_at}`,
                ])
              }
              onFollowupAction={(action) =>
                onFollowupAction?.(action, notification)
              }
            />
          )}
        </React.Fragment>
      ))}
    </View>
  );
}