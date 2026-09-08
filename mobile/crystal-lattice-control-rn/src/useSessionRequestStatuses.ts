import { useEffect, useState } from 'react';
import { AppState } from 'react-native';

import {
  useSessionRequestStatuses as useSharedSessionRequestStatuses,
  type SessionStatusesByConnection,
} from '@crystal-lattice/frontend-sdk-react';
import type {
  ConnectionRecord,
  ConnectionSessionStatusReader,
} from '@crystal-lattice/frontend-sdk';

export type { SessionStatusesByConnection };

export function useSessionRequestStatuses(options: {
  enabled: boolean;
  connections: readonly ConnectionRecord[];
  sessionIdsByConnection: Readonly<Record<string, readonly string[]>>;
  reader: ConnectionSessionStatusReader;
  intervalMs?: number;
  maxBackoffMs?: number;
  onMissingSessionIds?: (
    connectionId: string,
    sessionIds: readonly string[],
  ) => void;
}): SessionStatusesByConnection {
  const [foreground, setForeground] = useState(
    AppState.currentState === 'active',
  );

  useEffect(() => {
    const subscription = AppState.addEventListener('change', state => {
      setForeground(state === 'active');
    });
    return () => subscription.remove();
  }, []);

  return useSharedSessionRequestStatuses({
    active: options.enabled && foreground,
    connections: options.connections,
    sessionIdsByConnection: options.sessionIdsByConnection,
    reader: options.reader,
    intervalMs: options.intervalMs,
    maxBackoffMs: options.maxBackoffMs,
    onMissingSessionIds: options.onMissingSessionIds,
  });
}
