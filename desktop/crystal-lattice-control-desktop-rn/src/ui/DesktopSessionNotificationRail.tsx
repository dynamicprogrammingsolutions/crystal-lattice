import React, { useCallback, useEffect, useState } from 'react';
import { View } from 'react-native';

import type {
  ActionDisplayFollowupAction,
  AgentBackend,
  Event,
  SessionNotification,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';
import { SessionNotificationsHost } from '@crystal-lattice/frontend-rn-components';

import { ActionResultInlineCard } from './ActionResultInlineCard';

interface DesktopSessionNotificationRailProps {
  backend: AgentBackend | null;
  connectionId: string;
  sessionId: string;
  sessionSummary: SessionSummary | null;
  events?: readonly Event[];
  enabled?: boolean;
  activeActionId?: string | null;
  onFollowupAction?: (
    action: ActionDisplayFollowupAction,
    notification: SessionNotification,
  ) => void;
}

export function DesktopSessionNotificationRail({
  backend,
  connectionId,
  sessionId,
  sessionSummary,
  events = [],
  enabled = true,
  activeActionId,
  onFollowupAction,
}: DesktopSessionNotificationRailProps): React.JSX.Element {
  const [authoritativeSummary, setAuthoritativeSummary] =
    useState<SessionSummary | null>(sessionSummary);

  const refresh = useCallback(async () => {
    if (!backend) return null;
    const summary = await backend.getSessionSummary(sessionId);
    setAuthoritativeSummary(summary);
    return summary;
  }, [backend, sessionId]);

  useEffect(() => {
    if (!enabled || !backend) return;
    let cancelled = false;
    backend.getSessionSummary(sessionId).then(
      (summary) => {
        if (!cancelled) setAuthoritativeSummary(summary);
      },
      () => {
        // Keep the last available summary when authoritative refresh fails.
      },
    );
    return () => {
      cancelled = true;
    };
  }, [backend, enabled, sessionId]);

  const dismiss = useCallback(
    async (notification: SessionNotification) => {
      if (!backend?.dismissSessionNotification) {
        throw new Error(
          'Backend does not support session notification dismissal.',
        );
      }
      await backend.dismissSessionNotification(sessionId, notification.id, {
        expectedRevision: notification.revision ?? notification.updated_at,
        reason: 'user',
      });
      await refresh();
    },
    [backend, refresh, sessionId],
  );

  return (
    <View
      testID={`desktop-session-notification-rail-${connectionId}-${sessionId}`}
    >
      <SessionNotificationsHost
        sessionSummary={authoritativeSummary}
        events={events}
        inlinePresentations={['inline', 'banner', 'modal']}
        onDismissNotification={dismiss}
        onFollowupAction={onFollowupAction}
        renderInline={({ notification, onDismiss, onFollowupAction: followup }) => (
          <ActionResultInlineCard
            display={notification.display}
            activeActionId={activeActionId}
            onDismiss={onDismiss}
            onFollowupAction={(action) => followup(action)}
          />
        )}
      />
    </View>
  );
}