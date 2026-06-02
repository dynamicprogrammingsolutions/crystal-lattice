import React from 'react';
import type { StyleProp, ViewStyle } from 'react-native';

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
  onOpenMenu?: () => void;
  isActionDisabled?: (action: SessionActionKey) => boolean;
  extraActions?: SessionActionDefinition[];
  availableActions?: SessionActionKey[];
  isActive?: boolean;

  title?: string;
  variant?: 'modal' | 'dropdown';
  modalContentStyle?: StyleProp<ViewStyle>;
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
  onOpenMenu,
  isActionDisabled,
  extraActions,
  availableActions,
  isActive,
  title,
  variant,
  modalContentStyle,
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
      modalContentStyle={modalContentStyle}
      baseActions={ALL_SESSION_ACTIONS}
      extraActions={extraActions}
      availableActions={availableActions}
      pinned={pinned}
      onChangePinned={onChangePinned}
      onAction={onAction}
      onOpenMenu={onOpenMenu}
      isActionDisabled={isActionDisabled}
      isActive={isActive}
    />
  );
}
