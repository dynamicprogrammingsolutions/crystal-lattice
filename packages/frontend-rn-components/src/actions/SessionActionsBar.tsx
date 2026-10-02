import React from 'react';
import type { StyleProp, ViewStyle } from 'react-native';

import type {
  SessionActionDefinition,
  SessionActionKey,
} from '../sessionActions';
import { ALL_SESSION_ACTIONS } from '../sessionActions';

import type { MenuIconRenderer } from './ActionsMenuContent';
import { ActionsMenuBar } from './ActionsMenuBar';
import type { ActionsMenuPinnedRenderParams } from './types';

export interface SessionActionsBarProps {
  pinned: SessionActionKey[];
  onChangePinned: (pinned: SessionActionKey[]) => void;
  onAction: (action: SessionActionKey) => void;
  onOpenMenu?: () => void;
  menuButtonTestID?: string;
  isActionDisabled?: (action: SessionActionKey) => boolean;
  baseActions?: readonly SessionActionDefinition[];
  extraActions?: readonly SessionActionDefinition[];
  availableActions?: SessionActionKey[];
  pinnedKeysForBar?: SessionActionKey[];
  maxPinnedActionsForBar?: number;
  pinnedRows?: 1 | 2;
  secondPinnedRowPlacement?: 'above' | 'below';
  isActive?: boolean;

  title?: string;
  variant?: 'modal' | 'dropdown';
  modalContentStyle?: StyleProp<ViewStyle>;
  renderIcon?: MenuIconRenderer;
  renderPinIcon?: (params: {
    pinned: boolean;
    size: number;
    color: string;
  }) => React.ReactNode;
  renderCloseIcon?: (params: {
    size: number;
    color: string;
    renderIcon?: MenuIconRenderer;
  }) => React.ReactNode;
  renderPinnedAction?: (
    params: ActionsMenuPinnedRenderParams<SessionActionDefinition>,
  ) => React.ReactNode | undefined;
}

export function SessionActionsBar({
  pinned,
  onChangePinned,
  onAction,
  onOpenMenu,
  menuButtonTestID,
  isActionDisabled,
  baseActions,
  extraActions,
  availableActions,
  pinnedKeysForBar,
  maxPinnedActionsForBar,
  pinnedRows,
  secondPinnedRowPlacement,
  isActive,
  title,
  variant,
  modalContentStyle,
  renderIcon,
  renderPinIcon,
  renderCloseIcon,
  renderPinnedAction,
}: SessionActionsBarProps): React.JSX.Element {
  return (
    <ActionsMenuBar<SessionActionDefinition>
      title={title ?? 'Session actions'}
      variant={variant ?? 'modal'}
      renderIcon={renderIcon}
      renderPinIcon={renderPinIcon}
      renderCloseIcon={renderCloseIcon}
      modalContentStyle={modalContentStyle}
      baseActions={baseActions ?? ALL_SESSION_ACTIONS}
      extraActions={extraActions}
      availableActions={availableActions}
      pinnedKeysForBar={pinnedKeysForBar}
      maxPinnedActionsForBar={maxPinnedActionsForBar}
      pinnedRows={pinnedRows}
      secondPinnedRowPlacement={secondPinnedRowPlacement}
      pinned={pinned}
      onChangePinned={onChangePinned}
      onAction={onAction}
      onOpenMenu={onOpenMenu}
      menuButtonTestID={menuButtonTestID}
      isActionDisabled={isActionDisabled}
      isActive={isActive}
      renderPinnedAction={renderPinnedAction}
    />
  );
}
