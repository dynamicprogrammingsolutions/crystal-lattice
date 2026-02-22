import React from 'react';

import { ActionsMenuBar } from '@crystal-lattice/frontend-rn-components';
import Icon from 'react-native-vector-icons/Feather';

import {
  ALL_MESSAGE_ACTIONS,
  type MessageActionDefinition,
  type MessageActionKey,
} from './messageActions';

export interface MessageActionsBarProps {
  pinned: MessageActionKey[];
  onChangePinned: (pinned: MessageActionKey[]) => void;
  onAction: (action: MessageActionKey) => void;
  isActionDisabled?: (action: MessageActionKey) => boolean;
  availableActions?: MessageActionKey[];
  extraActions?: MessageActionDefinition[];
  isActive?: boolean;
}

const MessageActionsBar: React.FC<MessageActionsBarProps> = ({
  pinned,
  onChangePinned,
  onAction,
  isActionDisabled,
  availableActions,
  extraActions,
  isActive,
}) => {
  return (
    <ActionsMenuBar<MessageActionDefinition>
      title="Message actions"
      variant="dropdown"
      renderIcon={({ name, size, color }) => <Icon name={name} size={size} color={color} />}
      renderPinIcon={({ pinned: isPinned, size, color }) => (
        <Icon name={isPinned ? 'star' : 'star'} size={size} color={color} />
      )}
      renderCloseIcon={({ size, color, renderIcon }) =>
        renderIcon ? renderIcon({ name: 'x', size, color }) : null
      }
      baseActions={ALL_MESSAGE_ACTIONS}
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

export default MessageActionsBar;
