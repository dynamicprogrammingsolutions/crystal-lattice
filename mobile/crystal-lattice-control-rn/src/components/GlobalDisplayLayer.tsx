import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { Alert, Linking, StyleSheet, View } from 'react-native';
import Clipboard from '@react-native-clipboard/clipboard';

import {
  ApplicationNotificationsController,
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
import { useTheme } from '../theme';
import ActionResultInlineCard from './ActionResultInlineCard';
import ActionResultModal from './ActionResultModal';
import { handleGeneratedFileFollowupAction } from '../utils/generatedFileActions';

interface GlobalDisplayLayerProps {
  backend: AgentBackend | null;
  connectionId: string | null;
  connectionName: string | null;
  children: React.ReactNode;
}

interface GlobalBannerContextValue {
  items: NotificationBannerHostItem[];
  onDismiss: (item: NotificationBannerHostItem) => void;
  onFollowupAction: (
    action: ActionDisplayFollowupAction,
    item: NotificationBannerHostItem,
  ) => void;
}

const GlobalBannerContext = createContext<GlobalBannerContextValue | null>(null);

export function GlobalNotificationBannerSlot({
  testID = 'global-notification-banner-rail',
}: {
  testID?: string;
}): React.JSX.Element | null {
  const context = useContext(GlobalBannerContext);
  if (!context || context.items.length === 0) return null;
  return (
    <NotificationBannerHost
      items={context.items}
      layout="flow"
      testID={testID}
      onDismiss={context.onDismiss}
      onFollowupAction={context.onFollowupAction}
    />
  );
}

export default function GlobalDisplayLayer({
  backend,
  connectionId,
  connectionName,
  children,
}: GlobalDisplayLayerProps): React.JSX.Element | null {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
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
  const banners: NotificationBannerHostItem[] = items
    .filter((item) => item.display.presentation === 'banner')
    .map((envelope) => ({
      envelope,
      connectionLabel: connectionName,
      sessionLabel: envelope.sessionId ?? null,
    }));
  const inline = items.filter((item) => item.display.presentation === 'inline');
  const modal =
    items.slice().reverse().find((item) => item.display.presentation === 'modal') ?? null;

  const bannerContext = {
    items: banners,
    onDismiss: (item: NotificationBannerHostItem) => dismiss(item.envelope),
    onFollowupAction: (
      action: ActionDisplayFollowupAction,
      item: NotificationBannerHostItem,
    ) => {
      void followup(action, item.envelope);
    },
  };

  return (
    <GlobalBannerContext.Provider value={bannerContext}>
      {children}
      {inline.length > 0 ? (
        <View pointerEvents="box-none" style={styles.inlineHost}>
          {inline.map((envelope) => (
            <ActionResultInlineCard
              key={envelope.id}
              display={envelope.display}
              onDismiss={() => dismiss(envelope)}
              onFollowupAction={(action) => {
                void followup(action, envelope);
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
          if (modal) dismiss(modal);
        }}
        onFollowupAction={(action) => {
          if (modal) void followup(action, modal);
        }}
      />
    </GlobalBannerContext.Provider>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    inlineHost: {
      marginHorizontal: 12,
      paddingBottom: 8,
      backgroundColor: theme.background,
    },
  });
}