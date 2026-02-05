import React from 'react';

import type {
  SessionActionDefinition,
  SessionActionKey,
} from '../sessionActions';
import { ALL_SESSION_ACTIONS } from '../sessionActions';

import type { MenuIconRenderer } from './ActionsMenuContent';
import { ActionsMenuBar } from './ActionsMenuBar';

export interface SessionActionsBarProps {
  pinned: SessionActionKey[];
  onChangePinned: (pinned: SessionActionKey[]) => void;
  onAction: (action: SessionActionKey) => void;
  isActionDisabled?: (action: SessionActionKey) => boolean;
  extraActions?: SessionActionDefinition[];
  availableActions?: SessionActionKey[];
  isActive?: boolean;

  title?: string;
  variant?: 'modal' | 'dropdown';
  renderIcon?: MenuIconRenderer;
  renderPinIcon?: (params: { pinned: boolean; size: number; color: string }) => React.ReactNode;
  renderCloseIcon?: (params: {
    size: number;
    color: string;
    renderIcon?: MenuIconRenderer;
  }) => React.ReactNode;
}

export function SessionActionsBar({
  pinned,
  onChangePinned,
  onAction,
  isActionDisabled,
  extraActions,
  availableActions,
  isActive,
  title,
  variant,
  renderIcon,
  renderPinIcon,
  renderCloseIcon,
}: SessionActionsBarProps): React.JSX.Element {
  return (
    <ActionsMenuBar<SessionActionDefinition>
      title={title ?? 'Session actions'}
      variant={variant ?? 'modal'}
      renderIcon={renderIcon}
      renderPinIcon={renderPinIcon}
      renderCloseIcon={renderCloseIcon}
      baseActions={ALL_SESSION_ACTIONS}
      extraActions={extraActions}
      availableActions={availableActions}
      pinned={pinned}
      onChangePinned={onChangePinned}
      onAction={onAction}
      isActionDisabled={isActionDisabled}
      isActive={isActive}
    />
  );
}
