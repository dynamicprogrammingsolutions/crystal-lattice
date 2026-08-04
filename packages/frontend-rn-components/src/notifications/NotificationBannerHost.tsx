import React from 'react';
import { StyleSheet, View } from 'react-native';

import type {
  ActionDisplayFollowupAction,
  DisplayEnvelope,
  NotificationSeverity,
} from '@crystal-lattice/frontend-sdk';

import { NotificationBanner } from './NotificationBanner';

export interface NotificationBannerHostItem {
  envelope: DisplayEnvelope;
  severity?: NotificationSeverity;
  connectionLabel?: string | null;
  sessionLabel?: string | null;
}

export interface NotificationBannerHostProps {
  items: readonly NotificationBannerHostItem[];
  maxVisible?: number;
  topInset?: number;
  layout?: 'overlay' | 'flow';
  horizontalInset?: number;
  topSpacing?: number;
  testID?: string;
  onDismiss: (item: NotificationBannerHostItem) => void;
  onFollowupAction?: (
    action: ActionDisplayFollowupAction,
    item: NotificationBannerHostItem,
  ) => void;
}

export function NotificationBannerHost({
  items,
  maxVisible = 3,
  topInset = 0,
  layout = 'overlay',
  horizontalInset = 12,
  topSpacing = 8,
  testID,
  onDismiss,
  onFollowupAction,
}: NotificationBannerHostProps): React.JSX.Element | null {
  const limit = Math.max(1, maxVisible);
  const counts = new Map<string, number>();
  const visible = items
    .slice()
    .reverse()
    .filter((item) => {
      const connection = item.envelope.connectionId ?? 'default';
      const count = counts.get(connection) ?? 0;
      if (count >= limit) return false;
      counts.set(connection, count + 1);
      return true;
    })
    .reverse();
  if (visible.length === 0) return null;

  return (
    <View
      pointerEvents="box-none"
      testID={testID}
      style={[
        layout === 'overlay' ? styles.overlayHost : styles.flowHost,
        { left: layout === 'overlay' ? horizontalInset : undefined,
          right: layout === 'overlay' ? horizontalInset : undefined,
          marginHorizontal: layout === 'flow' ? horizontalInset : undefined },
        layout === 'overlay'
          ? { top: topInset + topSpacing }
          : { paddingTop: topInset + topSpacing },
      ]}
    >
      {visible.map((item) => (
        <NotificationBanner
          key={`${item.envelope.connectionId ?? ''}:${item.envelope.id}`}
          testID={`notification-banner-${item.envelope.id}`}
          display={item.envelope.display}
          severity={item.severity}
          connectionLabel={item.connectionLabel}
          sessionLabel={item.sessionLabel}
          onDismiss={() => onDismiss(item)}
          onFollowupAction={(action) => onFollowupAction?.(action, item)}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  overlayHost: {
    position: 'absolute',
    zIndex: 10000,
    elevation: 10000,
    gap: 8,
  },
  flowHost: {
    paddingBottom: 8,
    gap: 8,
  },
});