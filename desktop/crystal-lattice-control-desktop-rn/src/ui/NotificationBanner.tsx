import React from 'react';

import { NotificationBanner as SharedNotificationBanner } from '@crystal-lattice/frontend-rn-components';

export type NotificationVariant = 'info' | 'success' | 'warning' | 'error';

export interface NotificationBannerProps {
  variant: NotificationVariant;
  title?: string;
  message?: string;
  onDismiss?: () => void | Promise<void>;
  dismissLabel?: string;
}

export function NotificationBanner({
  variant,
  title,
  message,
  onDismiss,
  dismissLabel = 'Dismiss',
}: NotificationBannerProps): React.JSX.Element {
  return (
    <SharedNotificationBanner
      display={{
        format: 'text',
        title,
        body: message ?? '',
        variant,
        presentation: 'banner',
        dismissible: false,
        actions: onDismiss
          ? [{ kind: 'dismiss', id: 'dismiss', label: dismissLabel }]
          : [],
      }}
      onDismiss={onDismiss ? () => void onDismiss() : undefined}
    />
  );
}