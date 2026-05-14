import type { SessionScopedMessagesCacheEntry } from '@crystal-lattice/frontend-sdk';

import type { ChatScrollAnchor } from '../chatScroll';

export interface MessagesCacheEntry
  extends SessionScopedMessagesCacheEntry<ChatScrollAnchor> {
  eventsCursorId?: string | null;
}

export type MessagesBySession = Record<string, MessagesCacheEntry>;
export type MessagesCache = Record<string, MessagesBySession>;