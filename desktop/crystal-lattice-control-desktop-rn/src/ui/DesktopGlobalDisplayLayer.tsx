import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { Clipboard, Linking, View } from 'react-native';

import {
  ApplicationNotificationsController,
  classifyDisplayEnvelope,
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
} from '@crystal-lattice/frontend-rn-components';

import type { OpenConnectionsById } from '../connections/useOpenConnections';
import { ActionResultInlineCard } from './ActionResultInlineCard';

interface DesktopGlobalDisplayLayerProps {
  openConnectionsById: OpenConnectionsById;
  connectionNameById: Record<string, string>;
  children: React.ReactNode;
}

interface DesktopDisplayContextValue {
  items: DisplayEnvelope[];
  connectionNameById: Record<string, string>;
  dismiss: (envelope: DisplayEnvelope) => Promise<void>;
  followup: (
    action: ActionDisplayFollowupAction,
    envelope: DisplayEnvelope,
  ) => Promise<void>;
}

const DesktopDisplayContext = createContext<DesktopDisplayContextValue | null>(null);

function ConnectionDisplaySubscription({
  connectionId,
  backend,
  onDisplay,
  onNotifications,
  onController,
}: {
  connectionId: string;
  backend: AgentBackend;
  onDisplay: (envelope: DisplayEnvelope) => void;
  onNotifications: (
    connectionId: string,
    notifications: ApplicationNotification[],
  ) => void;
  onController: (
    connectionId: string,
    controller: ApplicationNotificationsController | null,
  ) => void;
}): null {
  useEffect(() => subscribeDisplayPresentation(backend, onDisplay), [backend, onDisplay]);
  useEffect(() => {
    const controller = new ApplicationNotificationsController({
      backend,
      connectionId,
      hydrateSnapshot: true,
    });
    onController(connectionId, controller);
    const sync = () => {
      onNotifications(connectionId, controller.getSnapshot().notifications);
    };
    const unsubscribe = controller.subscribe(sync);
    sync();
    controller.start();
    return () => {
      unsubscribe();
      controller.close();
      onController(connectionId, null);
      onNotifications(connectionId, []);
    };
  }, [backend, connectionId, onController, onNotifications]);
  return null;
}

export function DesktopGlobalDisplayLayer({
  openConnectionsById,
  connectionNameById,
  children,
}: DesktopGlobalDisplayLayerProps): React.JSX.Element {
  const [transientItems, setTransientItems] = useState<DisplayEnvelope[]>([]);
  const [applicationNotificationsByConnection, setApplicationNotificationsByConnection] =
    useState<Record<string, ApplicationNotification[]>>({});
  const [dismissedRevisions, setDismissedRevisions] = useState<string[]>([]);
  const applicationControllersRef = useRef<
    Record<string, ApplicationNotificationsController>
  >({});

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

  const dismissLocally = useCallback((envelope: DisplayEnvelope) => {
    const revision = displayEnvelopeRevisionKey(envelope);
    const lifecycle = displayEnvelopeLifecycleKey(envelope);
    setDismissedRevisions((current) =>
      current.includes(revision) ? current : [...current, revision],
    );
    setTransientItems((current) =>
      current.filter((item) => displayEnvelopeLifecycleKey(item) !== lifecycle),
    );
  }, []);

  const updateApplicationController = useCallback(
    (
      connectionId: string,
      controller: ApplicationNotificationsController | null,
    ) => {
      if (controller) {
        applicationControllersRef.current[connectionId] = controller;
      } else {
        delete applicationControllersRef.current[connectionId];
      }
    },
    [],
  );

  const dismiss = useCallback(async (envelope: DisplayEnvelope) => {
    if (
      envelope.source === 'application_notification' &&
      envelope.connectionId
    ) {
      const controller =
        applicationControllersRef.current[envelope.connectionId];
      if (!controller) return;
      try {
        await controller.dismiss(envelope.id);
      } catch {
        // Keep the server-owned notification visible when dismissal fails.
      }
      return;
    }
    dismissLocally(envelope);
  }, [dismissLocally]);

  const connections = Object.entries(openConnectionsById).flatMap(([connectionId, state]) =>
    state.status === 'open' && state.backend ? [{ connectionId, backend: state.backend }] : [],
  );
  const backendFor = useCallback(
    (envelope: DisplayEnvelope): AgentBackend | null =>
      envelope.connectionId
        ? openConnectionsById[envelope.connectionId]?.backend ?? null
        : null,
    [openConnectionsById],
  );

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
              notificationRevision:
                notification.revision ?? notification.updated_at,
            }),
            'desktop',
          ),
        ),
  );
  const openConnectionIds = new Set(connections.map((item) => item.connectionId));
  const items = [...applicationItems, ...transientItems]
    .filter(
      (item) =>
        !item.connectionId ||
        openConnectionIds.has(item.connectionId),
    )
    .filter(
      (item) => !dismissedRevisions.includes(displayEnvelopeRevisionKey(item)),
    )
    .sort((left, right) =>
      String(left.updatedAt ?? left.createdAt ?? left.id).localeCompare(
        String(right.updatedAt ?? right.createdAt ?? right.id),
      ),
    );

  const followup = useCallback(
    async (action: ActionDisplayFollowupAction, envelope: DisplayEnvelope) => {
      if (action.kind === 'dismiss') {
        await dismiss(envelope);
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
              ownershipScope: classifyDisplayEnvelope(envelope).scope,
              connectionId: envelope.connectionId,
              sessionId: envelope.sessionId,
              display: response.result.display,
            }),
          );
        }
      }
    },
    [backendFor, dismiss],
  );

  return (
    <DesktopDisplayContext.Provider
      value={{ items, connectionNameById, dismiss, followup }}
    >
      {connections.map(({ connectionId, backend }) => (
        <ConnectionDisplaySubscription
          key={connectionId}
          connectionId={connectionId}
          backend={backend}
          onDisplay={upsert}
          onNotifications={updateApplicationNotifications}
          onController={updateApplicationController}
        />
      ))}
      {children}
    </DesktopDisplayContext.Provider>
  );
}

export function DesktopConnectionDisplayRail({
  testID = 'desktop-connection-display-rail',
}: {
  testID?: string;
}): React.JSX.Element | null {
  const context = useContext(DesktopDisplayContext);
  if (!context) return null;
  const items = context.items.filter(
    (item) => classifyDisplayEnvelope(item).scope === 'connection',
  );
  if (items.length === 0) return null;
  const banners: NotificationBannerHostItem[] = items
    .filter((item) => item.display.presentation === 'banner')
    .map((envelope) => ({
      envelope,
      connectionLabel: envelope.connectionId
        ? context.connectionNameById[envelope.connectionId] ?? envelope.connectionId
        : null,
    }));
  const inline = items.filter((item) => item.display.presentation === 'inline');
  return (
    <View testID={testID}>
      {banners.length > 0 ? (
        <NotificationBannerHost
          items={banners}
          layout="flow"
          onDismiss={(item) => {
            context.dismiss(item.envelope).catch(() => {});
          }}
          onFollowupAction={(action, item) => {
            context.followup(action, item.envelope).catch(() => {});
          }}
        />
      ) : null}
      {inline.map((envelope) => (
        <ActionResultInlineCard
          key={`${envelope.connectionId ?? ''}:${envelope.id}`}
          contextLabel={
            envelope.connectionId
              ? context.connectionNameById[envelope.connectionId] ?? envelope.connectionId
              : undefined
          }
          display={envelope.display}
          onDismiss={() => {
            context.dismiss(envelope).catch(() => {});
          }}
          onFollowupAction={(action) => {
            context.followup(action, envelope).catch(() => {});
          }}
        />
      ))}
    </View>
  );
}