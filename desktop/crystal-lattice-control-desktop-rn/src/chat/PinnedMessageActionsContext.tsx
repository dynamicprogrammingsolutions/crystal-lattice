import React, { createContext, useContext } from 'react';

import type { MessageActionKey } from './messageActions';

export interface PinnedMessageActionsContextValue {
  isActive: boolean;
  getPinnedForRole: (role: string) => MessageActionKey[];
  setPinnedForRole: (role: string, pinned: MessageActionKey[]) => void;
}

const PinnedMessageActionsContext = createContext<PinnedMessageActionsContextValue | null>(null);

export function PinnedMessageActionsProvider({
  value,
  children,
}: {
  value: PinnedMessageActionsContextValue;
  children: React.ReactNode;
}): React.JSX.Element {
  return (
    <PinnedMessageActionsContext.Provider value={value}>
      {children}
    </PinnedMessageActionsContext.Provider>
  );
}

export function usePinnedMessageActions(): PinnedMessageActionsContextValue {
  const ctx = useContext(PinnedMessageActionsContext);
  if (!ctx) {
    throw new Error('usePinnedMessageActions must be used within a PinnedMessageActionsProvider');
  }
  return ctx;
}
