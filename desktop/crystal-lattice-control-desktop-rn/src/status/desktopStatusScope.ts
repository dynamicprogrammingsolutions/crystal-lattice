import type { HomeSessionCollections } from '@crystal-lattice/frontend-rn-components';

import type { DesktopSessionTab } from '../tabs/desktopWorkspaceState';

export interface VisibleSessionsStatusScope {
  connectionId: string | null;
  sessionIds: readonly string[];
}

export function deriveDesktopStatusSessionIds(options: {
  tabs: readonly DesktopSessionTab[];
  homeActive: boolean;
  homeCollections: HomeSessionCollections;
  lowerPanel: 'sessions' | 'history';
  focusedConnectionId: string | null;
  visibleSessions: VisibleSessionsStatusScope;
}): Record<string, string[]> {
  const ids = new Map<string, Set<string>>();
  const add = (connectionId: string, sessionId: string) => {
    const group = ids.get(connectionId) ?? new Set<string>();
    group.add(sessionId);
    ids.set(connectionId, group);
  };

  options.tabs.forEach(tab => add(tab.connectionId, tab.sessionId));
  if (options.homeActive) {
    options.homeCollections.watchlist.forEach(item =>
      add(item.connectionId, item.sessionId),
    );
    options.homeCollections.recent.forEach(item =>
      add(item.connectionId, item.sessionId),
    );
  }
  if (options.lowerPanel === 'history') {
    options.homeCollections.recent.forEach(item =>
      add(item.connectionId, item.sessionId),
    );
  } else if (
    options.visibleSessions.connectionId &&
    options.visibleSessions.connectionId === options.focusedConnectionId
  ) {
    options.visibleSessions.sessionIds.forEach(sessionId =>
      add(options.visibleSessions.connectionId!, sessionId),
    );
  }

  return Object.fromEntries(
    [...ids.entries()].map(([connectionId, values]) => [
      connectionId,
      [...values],
    ]),
  );
}
