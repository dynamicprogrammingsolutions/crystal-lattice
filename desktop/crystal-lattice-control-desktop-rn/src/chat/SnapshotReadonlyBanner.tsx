import React from 'react';

import { NotificationBanner } from '@crystal-lattice/frontend-rn-components';

export interface SnapshotReadonlyBannerProps {
  snapshotId: string;
  onClear: () => void | Promise<void>;
  disabled?: boolean;
}

export function SnapshotReadonlyBanner({
  snapshotId,
  onClear,
  disabled,
}: SnapshotReadonlyBannerProps): React.JSX.Element {
  return (
    <NotificationBanner
      display={{
        format: 'text',
        title: 'Viewing snapshot',
        body: `${snapshotId} · Read-only`,
        variant: 'info',
        presentation: 'inline',
        dismissible: false,
        actions: [{ kind: 'dismiss', id: 'return-to-live', label: 'Live' }],
      }}
      disabledActionIds={disabled ? ['return-to-live'] : []}
      onDismiss={() => void onClear()}
    />
  );
}