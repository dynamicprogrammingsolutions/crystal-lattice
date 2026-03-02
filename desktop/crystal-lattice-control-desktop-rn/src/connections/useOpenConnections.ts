import { useCallback, useMemo, useState } from 'react';

import {
  createDefaultSdkRuntime,
  FetchTransport,
  RestAgentBackend,
  type AgentBackend,
  type ConnectionRecord,
  type SdkRuntime,
} from '@crystal-lattice/frontend-sdk';

export type OpenConnectionStatus = 'closed' | 'connecting' | 'open' | 'error';

export interface OpenConnectionState {
  status: OpenConnectionStatus;
  baseUrl: string;
  transport?: FetchTransport;
  backend?: AgentBackend;
  runtime?: SdkRuntime;
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
  openConnection: (record: ConnectionRecord) => Promise<AgentBackend | null>;
  closeConnection: (connectionId: string) => void;
  closeAllConnections: () => void;
  toggleConnection: (record: ConnectionRecord) => Promise<void>;
  getBackend: (connectionId: string) => AgentBackend | null;
  getRuntime: (connectionId: string) => SdkRuntime | null;
}

export function useOpenConnections(): UseOpenConnectionsResult {
  const [openConnectionsById, setOpenConnectionsById] = useState<OpenConnectionsById>({});

  const openConnectionIds = useMemo(() => Object.keys(openConnectionsById), [openConnectionsById]);

  const isConnectionOpen = useCallback(
    (connectionId: string) => openConnectionsById[connectionId]?.status === 'open',
    [openConnectionsById],
  );

  const openConnection = useCallback(async (record: ConnectionRecord): Promise<AgentBackend | null> => {
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
    const rawBackend = new RestAgentBackend({ transport });
    const runtime = createDefaultSdkRuntime({
      scopeKey: record.id,
      backend: rawBackend,
    });
    const backend = runtime.backend;
    if (!backend) {
      throw new Error('Failed to initialize runtime backend');
    }

    try {
      await backend.listAgents();
      setOpenConnectionsById((prev) => ({
        ...prev,
        [record.id]: {
          status: 'open',
          baseUrl,
          transport,
          backend,
          runtime,
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

  const getRuntime = useCallback(
    (connectionId: string) => openConnectionsById[connectionId]?.runtime ?? null,
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
    getRuntime,
  };
}
