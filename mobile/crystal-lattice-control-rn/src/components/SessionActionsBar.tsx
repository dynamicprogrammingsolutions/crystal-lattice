import React from 'react';

import { ActionsMenuBar } from '@crystal-lattice/frontend-rn-components';
import Icon from 'react-native-vector-icons/Feather';

import {
  ALL_SESSION_ACTIONS,
  type SessionActionDefinition,
  type SessionActionKey,
} from '../sessionActions';

export interface SessionActionsBarProps {
  pinned: SessionActionKey[];
  onChangePinned: (pinned: SessionActionKey[]) => void;
  onAction: (action: SessionActionKey) => void;
  isActionDisabled?: (action: SessionActionKey) => boolean;
  extraActions?: SessionActionDefinition[];
  availableActions?: SessionActionKey[];
  isActive?: boolean;
}

const SessionActionsBar: React.FC<SessionActionsBarProps> = ({
  pinned,
  onChangePinned,
  onAction,
  isActionDisabled,
  extraActions,
  availableActions,
  isActive,
}) => {
  return (
    <ActionsMenuBar<SessionActionDefinition>
      title="Session actions"
      variant="modal"
      renderIcon={({ name, size, color }) => <Icon name={name} size={size} color={color} />}
      renderPinIcon={({ pinned: isPinned, size, color }) => (
        <Icon name={isPinned ? 'star' : 'star'} size={size} color={color} />
      )}
      renderCloseIcon={({ size, color, renderIcon }) =>
        renderIcon ? renderIcon({ name: 'x', size, color }) : null
      }
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
};

export default SessionActionsBar;
