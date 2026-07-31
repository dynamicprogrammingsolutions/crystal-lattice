import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { Alert, Linking, View } from 'react-native';
import Clipboard from '@react-native-clipboard/clipboard';

import {
  ApplicationNotificationsController,
  classifyDisplayEnvelope,
  displayEnvelopeLifecycleKey,
  displayEnvelopeRevisionKey,
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
  runApplicationAction,
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
  dismiss: (envelope: DisplayEnvelope) => void;
  followup: (
    action: ActionDisplayFollowupAction,
    envelope: DisplayEnvelope,
  ) => Promise<void>;
}

const GlobalDisplayContext = createContext<GlobalDisplayContextValue | null>(null);

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
          testID={testID}
          onDismiss={(item) => context.dismiss(item.envelope)}
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
              onDismiss={() => context.dismiss(envelope)}
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
        presentationMode="overlay"
        testID="global-notification-modal"
        onRequestClose={() => {
          if (modal) context.dismiss(modal);
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
  const [dismissedRevisions, setDismissedRevisions] = useState<string[]>([]);

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
    if (!backend) {
      setApplicationNotifications([]);
      return;
    }
    const controller = new ApplicationNotificationsController({
      backend,
      connectionId,
    });
    const sync = () => {
      setApplicationNotifications(controller.getSnapshot().notifications);
    };
    const unsubscribe = controller.subscribe(sync);
    sync();
    controller.start();
    return () => {
      unsubscribe();
      controller.close();
    };
  }, [backend, connectionId]);

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

  const followup = useCallback(
    async (action: ActionDisplayFollowupAction, envelope: DisplayEnvelope) => {
      if (action.kind === 'dismiss') {
        dismiss(envelope);
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
      }),
    );
  const items = [...applicationItems, ...transientItems].filter(
    (item) => !dismissedRevisions.includes(displayEnvelopeRevisionKey(item)),
  );
  return (
    <GlobalDisplayContext.Provider value={{ items, dismiss, followup }}>
      {children}
    </GlobalDisplayContext.Provider>
  );
}