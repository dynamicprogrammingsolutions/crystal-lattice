import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  loadConnections,
  saveConnections,
  type ConnectionRecord,
  type KeyValueStore,
} from '@crystal-lattice/frontend-sdk';

export interface UsePersistedConnectionsResult {
  hydrated: boolean;
  connectionRecords: ConnectionRecord[];
  sortedConnectionRecords: ConnectionRecord[];
  upsertConnection: (record: ConnectionRecord) => void;
  deleteConnection: (connectionId: string) => void;
  touchConnection: (connectionId: string) => void;
  clearConnections: () => void;
}

function sortByLastUsedDesc(records: ConnectionRecord[]): ConnectionRecord[] {
  return [...records].sort((a, b) => (b.lastUsedAt ?? 0) - (a.lastUsedAt ?? 0));
}

export function usePersistedConnections(store: KeyValueStore): UsePersistedConnectionsResult {
  const [connectionRecords, setConnectionRecords] = useState<ConnectionRecord[]>([]);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const hydrate = async () => {
      try {
        const records = await loadConnections(store);
        setConnectionRecords(records);
      } finally {
        setHydrated(true);
      }
    };
    hydrate();
  }, [store]);

  useEffect(() => {
    if (!hydrated) return;
    const save = async () => {
      try {
        await saveConnections(store, connectionRecords);
      } catch {
      }
    };
    save();
  }, [connectionRecords, hydrated, store]);

  const upsertConnection = useCallback((record: ConnectionRecord) => {
    setConnectionRecords((prev) => {
      const idx = prev.findIndex((existing) => existing.id === record.id);
      if (idx === -1) {
        return [...prev, record];
      }
      const next = [...prev];
      next[idx] = record;
      return next;
    });
  }, []);

  const deleteConnection = useCallback((connectionId: string) => {
    setConnectionRecords((prev) => prev.filter((record) => record.id !== connectionId));
  }, []);

  const touchConnection = useCallback((connectionId: string) => {
    const now = Date.now();
    setConnectionRecords((prev) =>
      prev.map((record) =>
        record.id === connectionId ? { ...record, lastUsedAt: now } : record,
      ),
    );
  }, []);

  const clearConnections = useCallback(() => {
    setConnectionRecords([]);
  }, []);

  const sortedConnectionRecords = useMemo(
    () => sortByLastUsedDesc(connectionRecords),
    [connectionRecords],
  );

  return {
    hydrated,
    connectionRecords,
    sortedConnectionRecords,
    upsertConnection,
    deleteConnection,
    touchConnection,
    clearConnections,
  };
}
