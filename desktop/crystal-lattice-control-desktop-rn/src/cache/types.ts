import type { IndexedMessage } from '@crystal-lattice/frontend-sdk';
import type { SessionSummary } from '@crystal-lattice/frontend-sdk';

export interface SessionsCacheEntry {
  connectionId: string;
  sessions: SessionSummary[];
  lastLoadedAt: number | null;
}

export type SessionsCache = Record<string, SessionsCacheEntry>;

export interface MessagesCacheEntry {
  connectionId: string;
  sessionId: string;
  messages: IndexedMessage[];
  lastLoadedAt: number | null;
  cursorEventId?: string | null;
  activeRequestId?: string | null;
  rangeStartText?: string | null;
  rangeEndText?: string | null;
  composeText?: string;
  scrollAnchor?: any;
}

export type MessagesBySession = Record<string, MessagesCacheEntry>;
export type MessagesCache = Record<string, MessagesBySession>;
