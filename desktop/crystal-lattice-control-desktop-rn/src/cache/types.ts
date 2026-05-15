import type {
  SessionScopedMessagesBySession,
  SessionScopedMessagesCache,
  SessionScopedMessagesCacheEntry,
  SessionSummary,
} from '@crystal-lattice/frontend-sdk';

export interface SessionsCacheEntry {
  connectionId: string;
  sessions: SessionSummary[];
  lastLoadedAt: number | null;
}

export type SessionsCache = Record<string, SessionsCacheEntry>;

export type MessagesCacheEntry = SessionScopedMessagesCacheEntry;
export type MessagesBySession = SessionScopedMessagesBySession;
export type MessagesCache = SessionScopedMessagesCache;
