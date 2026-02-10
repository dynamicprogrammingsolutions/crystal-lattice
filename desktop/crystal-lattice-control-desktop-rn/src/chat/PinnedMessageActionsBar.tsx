import React, { useCallback } from 'react';

import MessageActionsBar from './MessageActionsBar';
import type { MessageActionDefinition, MessageActionKey } from './messageActions';
import { usePinnedMessageActions } from './PinnedMessageActionsContext';

export function PinnedMessageActionsBar({
  role,
  onAction,
  availableActions,
  extraActions,
  isActionDisabled,
}: {
  role: string;
  onAction: (action: MessageActionKey) => void;
  availableActions?: MessageActionKey[];
  extraActions?: MessageActionDefinition[];
  isActionDisabled?: (action: MessageActionKey) => boolean;
}): React.JSX.Element {
  const { isActive, getPinnedForRole, setPinnedForRole } = usePinnedMessageActions();
  const pinned = getPinnedForRole(role);

  const handleChangePinned = useCallback(
    (next: MessageActionKey[]) => {
      setPinnedForRole(role, next);
    },
    [role, setPinnedForRole],
  );

  return (
    <MessageActionsBar
      pinned={pinned}
      onChangePinned={handleChangePinned}
      onAction={onAction}
      availableActions={availableActions}
      extraActions={extraActions}
      isActionDisabled={isActionDisabled}
      isActive={isActive}
    />
  );
}
