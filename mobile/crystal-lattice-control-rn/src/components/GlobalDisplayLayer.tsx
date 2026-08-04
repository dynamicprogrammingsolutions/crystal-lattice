import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { Alert, Linking, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Clipboard from '@react-native-clipboard/clipboard';

import {
  ApplicationNotificationsController,
  classifyDisplayEnvelope,
  displayEnvelopeLifecycleKey,
  displayEnvelopeRevisionKey,
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  NotificationDismissalCache,
  notificationDismissalRevisionKey,
  runApplicationAction,
  subscribeDisplayPresentation,
  type ActionDisplayFollowupAction,
  type AgentBackend,
  type ApplicationNotification,
  type DisplayEnvelope,
  type KeyValueStore,
  type NotificationDismissalCacheState,
} from '@crystal-lattice/frontend-sdk';
import {
  NotificationBannerHost,
  type NotificationBannerHostItem,
} from '@crystal-lattice/frontend-rn-components';

import { useApplicationPlugins } from '../ApplicationPluginsContext';
import ActionResultInlineCard from './ActionResultInlineCard';
import ActionResultModal from './ActionResultModal';
import { handleGeneratedFileFollowupAction } from '../utils/generatedFileActions';

interface GlobalDisplayLayerProps {
  backend: AgentBackend | null;
  connectionId: string | null;
  children: React.ReactNode;
}

interface GlobalDisplayContextValue {
  items: DisplayEnvelope[];
  dismissalCache: NotificationDismissalCache | null;
  dismissalCacheState: NotificationDismissalCacheState;
  dismiss: (envelope: DisplayEnvelope) => Promise<void>;
  followup: (
    action: ActionDisplayFollowupAction,
    envelope: DisplayEnvelope,
  ) => Promise<void>;
}

const GlobalDisplayContext = createContext<GlobalDisplayContextValue | null>(null);
const notificationDismissalStore: KeyValueStore = {
  get: (key) => AsyncStorage.getItem(key),
  set: (key, value) => AsyncStorage.setItem(key, value),
  delete: (key) => AsyncStorage.removeItem(key),
};

export function useNotificationDismissalCache(): {
  cache: NotificationDismissalCache | null;
  state: NotificationDismissalCacheState;
} {
  const context = useContext(GlobalDisplayContext);
  return {
    cache: context?.dismissalCache ?? null,
    state: context?.dismissalCacheState ?? { loaded: false, entries: [] },
  };
}

export function MobileDisplayHost({
  scope,
  sessionId,
  testID = 'global-notification-banner-rail',
}: {
  scope: 'connection' | 'session';
  sessionId?: string;
  testID?: string;
}): React.JSX.Element | null {
  const context = useContext(GlobalDisplayContext);
  const items = useMemo(() => {
    if (!context) return [];
    return context.items.filter((envelope) => {
      const ownership = classifyDisplayEnvelope(envelope);
      if (scope === 'connection') {
        return ownership.scope === 'connection';
      }
      return ownership.scope === 'session' && ownership.sessionId === sessionId;
    });
  }, [context, scope, sessionId]);
  if (!context || items.length === 0) return null;
  const banners: NotificationBannerHostItem[] = items
    .filter((item) => item.display.presentation === 'banner')
    .map((envelope) => ({ envelope }));
  const inline = items.filter((item) => item.display.presentation === 'inline');
  const modal =
    items.slice().reverse().find((item) => item.display.presentation === 'modal') ?? null;
  return (
    <>
      {banners.length > 0 ? (
        <NotificationBannerHost
          items={banners}
          layout="flow"
          horizontalInset={scope === 'connection' ? 0 : 12}
          topSpacing={scope === 'connection' ? 0 : 8}
          testID={testID}
          onDismiss={(item) => {
            void context.dismiss(item.envelope);
          }}
          onFollowupAction={(action, item) => {
            void context.followup(action, item.envelope);
          }}
        />
      ) : null}
      {inline.length > 0 ? (
        <View pointerEvents="box-none">
          {inline.map((envelope) => (
            <ActionResultInlineCard
              key={envelope.id}
              display={envelope.display}
              onDismiss={() => {
                void context.dismiss(envelope);
              }}
              onFollowupAction={(action) => {
                void context.followup(action, envelope);
              }}
            />
          ))}
        </View>
      ) : null}
      <ActionResultModal
        visible={modal !== null}
        display={modal?.display ?? null}
        testID="global-notification-modal"
        onRequestClose={() => {
          if (modal) void context.dismiss(modal);
        }}
        onFollowupAction={(action) => {
          if (modal) void context.followup(action, modal);
        }}
      />
    </>
  );
}

export default function GlobalDisplayLayer({
  backend,
  connectionId,
  children,
}: GlobalDisplayLayerProps): React.JSX.Element | null {
  const { actionsById, actionsByKey = {} } = useApplicationPlugins();
  const [transientItems, setTransientItems] = useState<DisplayEnvelope[]>([]);
  const [applicationNotifications, setApplicationNotifications] = useState<
    ApplicationNotification[]
  >([]);
  const [locallyDismissedRevisions, setLocallyDismissedRevisions] = useState<
    string[]
  >([]);
  const dismissalCache = useMemo(
    () =>
      backend && connectionId
        ? new NotificationDismissalCache({
            store: notificationDismissalStore,
          })
        : null,
    [backend, connectionId],
  );
  const [dismissalCacheState, setDismissalCacheState] =
    useState<NotificationDismissalCacheState>({
      loaded: false,
      entries: [],
    });
  const applicationControllerRef =
    useRef<ApplicationNotificationsController | null>(null);

  const upsert = useCallback((envelope: DisplayEnvelope) => {
    const key = displayEnvelopeLifecycleKey(envelope);
    setTransientItems((current) => {
      const index = current.findIndex(
        (item) => displayEnvelopeLifecycleKey(item) === key,
      );
      if (index < 0) return [...current, envelope];
      const next = current.slice();
      next[index] = envelope;
      return next;
    });
  }, []);

  useEffect(() => {
    if (!backend) {
      setTransientItems([]);
      return;
    }
    return subscribeDisplayPresentation(backend, upsert);
  }, [backend, upsert]);

  useEffect(() => {
    if (!dismissalCache) {
      setDismissalCacheState({ loaded: false, entries: [] });
      return;
    }
    const sync = () => setDismissalCacheState(dismissalCache.getSnapshot());
    const unsubscribe = dismissalCache.subscribe(sync);
    sync();
    void dismissalCache.load();
    return unsubscribe;
  }, [dismissalCache]);

  useEffect(() => {
    if (!backend) {
      setApplicationNotifications([]);
      return;
    }
    const controller = new ApplicationNotificationsController({
      backend,
      connectionId,
      hydrateSnapshot: true,
      dismissalCache: dismissalCache ?? undefined,
    });
    applicationControllerRef.current = controller;
    const sync = () => {
      setApplicationNotifications(controller.getSnapshot().notifications);
    };
    const unsubscribe = controller.subscribe(sync);
    sync();
    controller.start();
    return () => {
      if (applicationControllerRef.current === controller) {
        applicationControllerRef.current = null;
      }
      unsubscribe();
      controller.close();
    };
  }, [backend, connectionId, dismissalCache]);

  const dismissLocally = useCallback((envelope: DisplayEnvelope) => {
    const lifecycle = displayEnvelopeLifecycleKey(envelope);
    const revision = displayEnvelopeRevisionKey(envelope);
    setLocallyDismissedRevisions((current) =>
      current.includes(revision) ? current : [...current, revision],
    );
    setTransientItems((current) =>
      current.filter((item) => displayEnvelopeLifecycleKey(item) !== lifecycle),
    );
  }, []);

  const dismiss = useCallback(
    async (envelope: DisplayEnvelope) => {
      try {
        if (envelope.source === 'application_notification') {
          const controller = applicationControllerRef.current;
          if (!controller) {
            throw new Error('Application notification controller is unavailable.');
          }
          await controller.dismiss(envelope.id);
          return;
        }
        if (envelope.source === 'session_notification') {
          if (!backend?.dismissSessionNotification || !envelope.sessionId) {
            throw new Error('Backend does not support session notification dismissal.');
          }
          const revision = envelope.notificationRevision ?? envelope.updatedAt;
          if (revision == null) {
            throw new Error('Notification revision is unavailable.');
          }
          const cache = dismissalCache;
          const cachedDismissal =
            cache && connectionId
              ? {
                  cache,
                  entry: {
                    connectionId,
                    scope: 'session' as const,
                    sessionId: envelope.sessionId,
                    notificationId: envelope.id,
                    revision,
                    dismissedAt: new Date().toISOString(),
                  },
                }
              : null;
          const cacheWrite = cachedDismissal
            ? cachedDismissal.cache.record(cachedDismissal.entry)
            : null;
          dismissLocally(envelope);
          await cacheWrite;
          try {
            await backend.dismissSessionNotification(
              envelope.sessionId,
              envelope.id,
              {
                expectedRevision: revision,
                reason: 'user',
              },
            );
            if (cachedDismissal) {
              void cachedDismissal.cache.remove(cachedDismissal.entry);
            }
          } catch {
            if (!cachedDismissal) {
              throw new Error('Notification dismissal failed.');
            }
          }
          return;
        }
        dismissLocally(envelope);
      } catch (error) {
        Alert.alert(
          'Dismiss failed',
          error instanceof Error
            ? error.message || 'Notification dismissal failed.'
            : 'Notification dismissal failed.',
        );
      }
    },
    [backend, connectionId, dismissalCache, dismissLocally],
  );

  const followup = useCallback(
    async (action: ActionDisplayFollowupAction, envelope: DisplayEnvelope) => {
      if (action.kind === 'dismiss') {
        await dismiss(envelope);
        return;
      }
      if (action.kind === 'open_url') {
        await Linking.openURL(action.url);
        return;
      }
      if (action.kind === 'copy_text') {
        Clipboard.setString(action.text);
        return;
      }
      if (action.kind === 'download_attachment_asset' && backend) {
        await handleGeneratedFileFollowupAction({ backend, action });
        return;
      }
      if (action.kind !== 'run_action' || !backend) return;

      const result = await runApplicationAction({
        backend,
        element: {
          ui_type: 'display_followup',
          plugin: action.plugin,
          id: action.id,
          label: action.label,
          action_id: action.action_id,
          action_owner: action.action_owner,
          fixed_params: action.fixed_params as Record<string, any> | undefined,
          param_map: action.param_map,
        },
        actionsById,
        actionsByKey,
        context: {
          connectionId: connectionId ?? undefined,
          sessionId: envelope.sessionId ?? undefined,
        },
      });
      if (!result.ok) {
        Alert.alert('Action error', result.errorMessage || 'Action failed');
        return;
      }
      if (result.display) {
        emitDisplayPresentation(
          backend,
          normalizeDisplayEnvelope({
            source: 'action_response',
            ownershipScope: classifyDisplayEnvelope(envelope).scope,
            connectionId,
            sessionId: envelope.sessionId,
            display: result.display,
          }),
        );
      }
    },
    [actionsById, actionsByKey, backend, connectionId, dismiss],
  );

  if (!backend) return <>{children}</>;
  const applicationItems = applicationNotifications
    .filter((notification) => notification.status === 'pending')
    .map((notification) =>
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
    );
  const items = [...applicationItems, ...transientItems].filter((item) => {
    if (locallyDismissedRevisions.includes(displayEnvelopeRevisionKey(item))) {
      return false;
    }
    if (
      !connectionId ||
      (item.source !== 'application_notification' &&
        item.source !== 'session_notification')
    ) {
      return true;
    }
    const revision = item.notificationRevision ?? item.updatedAt;
    if (revision == null) return true;
    const scope =
      item.source === 'application_notification' ? 'application' : 'session';
    const revisionKey = notificationDismissalRevisionKey({
      connectionId,
      scope,
      sessionId: item.sessionId ?? undefined,
      notificationId: item.id,
      revision,
    });
    return !dismissalCacheState.entries.some(
      (entry) =>
        notificationDismissalRevisionKey({
          connectionId: entry.connectionId,
          scope: entry.scope,
          sessionId: entry.sessionId,
          notificationId: entry.notificationId,
          revision: entry.revision,
        }) === revisionKey,
    );
  });
  return (
    <GlobalDisplayContext.Provider
      value={{
        items,
        dismissalCache,
        dismissalCacheState,
        dismiss,
        followup,
      }}
    >
      {children}
    </GlobalDisplayContext.Provider>
  );
}