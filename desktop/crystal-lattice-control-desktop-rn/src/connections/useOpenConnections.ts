import { useCallback, useMemo, useState } from 'react';

import {
  FetchTransport,
  RestAgentBackend,
  type ConnectionRecord,
} from '@crystal-lattice/frontend-sdk';

export type OpenConnectionStatus = 'closed' | 'connecting' | 'open' | 'error';

export interface OpenConnectionState {
  status: OpenConnectionStatus;
  baseUrl: string;
  transport?: FetchTransport;
  backend?: RestAgentBackend;
  errorMessage?: string;
  lastOpenedAt?: number;
}

export type OpenConnectionsById = Record<string, OpenConnectionState>;

function getBaseUrl(record: ConnectionRecord): string | null {
  if (record.kind !== 'manual') {
    return null;
  }
  const host = record.host?.trim();
  const port = record.port;
  if (!host || typeof port !== 'number') {
    return null;
  }
  return `http://${host}:${port}`;
}

export interface UseOpenConnectionsResult {
  openConnectionsById: OpenConnectionsById;
  openConnectionIds: string[];
  isConnectionOpen: (connectionId: string) => boolean;
  openConnection: (record: ConnectionRecord) => Promise<RestAgentBackend | null>;
  closeConnection: (connectionId: string) => void;
  closeAllConnections: () => void;
  toggleConnection: (record: ConnectionRecord) => Promise<void>;
  getBackend: (connectionId: string) => RestAgentBackend | null;
}

export function useOpenConnections(): UseOpenConnectionsResult {
  const [openConnectionsById, setOpenConnectionsById] = useState<OpenConnectionsById>({});

  const openConnectionIds = useMemo(() => Object.keys(openConnectionsById), [openConnectionsById]);

  const isConnectionOpen = useCallback(
    (connectionId: string) => openConnectionsById[connectionId]?.status === 'open',
    [openConnectionsById],
  );

  const openConnection = useCallback(async (record: ConnectionRecord): Promise<RestAgentBackend | null> => {
    const baseUrl = getBaseUrl(record);
    if (!baseUrl) {
      setOpenConnectionsById((prev) => ({
        ...prev,
        [record.id]: {
          status: 'error',
          baseUrl: '',
          errorMessage: 'Unsupported connection record',
        },
      }));
      return null;
    }

    setOpenConnectionsById((prev) => ({
      ...prev,
      [record.id]: { status: 'connecting', baseUrl },
    }));

    const transport = new FetchTransport({ baseUrl });
    const backend = new RestAgentBackend({ transport });

    try {
      await backend.listAgents();
      setOpenConnectionsById((prev) => ({
        ...prev,
        [record.id]: {
          status: 'open',
          baseUrl,
          transport,
          backend,
          lastOpenedAt: Date.now(),
        },
      }));
      return backend;
    } catch (err: any) {
      setOpenConnectionsById((prev) => ({
        ...prev,
        [record.id]: {
          status: 'error',
          baseUrl,
          errorMessage: err?.message || 'Failed to open connection',
        },
      }));
      return null;
    }
  }, []);

  const closeConnection = useCallback((connectionId: string) => {
    setOpenConnectionsById((prev) => {
      if (!(connectionId in prev)) {
        return prev;
      }
      const next = { ...prev };
      delete next[connectionId];
      return next;
    });
  }, []);

  const closeAllConnections = useCallback(() => {
    setOpenConnectionsById({});
  }, []);

  const toggleConnection = useCallback(
    async (record: ConnectionRecord) => {
      const existing = openConnectionsById[record.id];
      if (existing && existing.status !== 'closed') {
        closeConnection(record.id);
        return;
      }
      await openConnection(record);
    },
    [closeConnection, openConnection, openConnectionsById],
  );

  const getBackend = useCallback(
    (connectionId: string) => openConnectionsById[connectionId]?.backend ?? null,
    [openConnectionsById],
  );

  return {
    openConnectionsById,
    openConnectionIds,
    isConnectionOpen,
    openConnection,
    closeConnection,
    closeAllConnections,
    toggleConnection,
    getBackend,
  };
}
