import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { AppState } from 'react-native';

import type {
  AgentBackend,
  KeyValueStore,
} from '@crystal-lattice/frontend-sdk';
import {
  HumanTimeSpanTracker,
  HumanTimeSpanUploader,
  appendHumanTimeSpan,
  emitHumanTimeTelemetryWarning,
  humanTimeDiagnosticSpanKey,
  humanTimeDiagnosticUploadStatus,
  loadHumanTimeSpans,
  type HumanTimeDiagnosticUploadStatus,
  type HumanTimeSpan,
  type HumanTimeUploadEvent,
} from '@crystal-lattice/frontend-rn-components';

import {
  desktopHumanTimeDiagnosticsBridge,
  type DesktopHumanTimeDiagnosticEntry,
  type DesktopHumanTimeDiagnosticSpan,
  type DesktopHumanTimeDiagnosticUpload,
  type DesktopHumanTimeDiagnostics,
} from './desktopHumanTimeDiagnostics';

interface DesktopHumanTimeTelemetryValue {
  recordActivity: (
    connectionId: string | null,
    sessionId: string | null,
  ) => void;
  splitForComposedMessage: (
    connectionId: string | null,
    sessionId: string | null,
  ) => void;
}

const DesktopHumanTimeTelemetryContext =
  createContext<DesktopHumanTimeTelemetryValue>({
    recordActivity: () => {},
    splitForComposedMessage: () => {},
  });

export function useDesktopHumanTimeTelemetry(): DesktopHumanTimeTelemetryValue {
  return useContext(DesktopHumanTimeTelemetryContext);
}

export interface DesktopHumanTimeTelemetryProviderProps {
  enabled: boolean;
  pluginId: string;
  inactivityMs: number;
  connectionIds: string[];
  connectedConnectionIds: string[];
  activeSurfaceKey: string;
  store: KeyValueStore;
  getBackend: (connectionId: string) => AgentBackend | null;
  children: React.ReactNode;
}

function desktopDiagnosticEntryKey(
  connectionId: string,
  span: HumanTimeSpan,
): string {
  return `${connectionId}\u0000${humanTimeDiagnosticSpanKey(span)}`;
}

function newestDesktopEntries(
  entries: DesktopHumanTimeDiagnosticEntry[],
): DesktopHumanTimeDiagnosticEntry[] {
  return [...entries]
    .sort((left, right) => right.to.localeCompare(left.to))
    .slice(0, 10);
}

function updateDesktopEntries(
  current: DesktopHumanTimeDiagnosticEntry[],
  connectionId: string,
  spans: HumanTimeSpan[],
  uploadStatus: HumanTimeDiagnosticUploadStatus,
  error: string | null,
): DesktopHumanTimeDiagnosticEntry[] {
  const entries = new Map(
    current.map(entry => [
      desktopDiagnosticEntryKey(entry.connectionId, entry),
      entry,
    ]),
  );
  for (const span of spans) {
    entries.set(desktopDiagnosticEntryKey(connectionId, span), {
      connectionId,
      ...span,
      uploadStatus,
      error,
    });
  }
  return newestDesktopEntries([...entries.values()]);
}

function mergeDesktopPendingEntries(
  current: DesktopHumanTimeDiagnosticEntry[],
  pendingByConnection: Array<{
    connectionId: string;
    spans: HumanTimeSpan[];
  }>,
): DesktopHumanTimeDiagnosticEntry[] {
  const entries = new Map(
    current.map(entry => [
      desktopDiagnosticEntryKey(entry.connectionId, entry),
      entry,
    ]),
  );
  for (const { connectionId, spans } of pendingByConnection) {
    for (const span of spans) {
      const key = desktopDiagnosticEntryKey(connectionId, span);
      if (!entries.has(key)) {
        entries.set(key, {
          connectionId,
          ...span,
          uploadStatus: 'pending',
          error: null,
        });
      }
    }
  }
  return newestDesktopEntries([...entries.values()]);
}

export function DesktopHumanTimeTelemetryProvider({
  enabled,
  pluginId,
  inactivityMs,
  connectionIds,
  connectedConnectionIds,
  activeSurfaceKey,
  store,
  getBackend,
  children,
}: DesktopHumanTimeTelemetryProviderProps): React.JSX.Element {
  const [openSpan, setOpenSpan] =
    useState<DesktopHumanTimeDiagnosticSpan | null>(null);
  const [activityEventCount, setActivityEventCount] = useState(0);
  const [lastCollectedSpan, setLastCollectedSpan] =
    useState<DesktopHumanTimeDiagnosticSpan | null>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [lastUpload, setLastUpload] =
    useState<DesktopHumanTimeDiagnosticUpload | null>(null);
  const [recentEntries, setRecentEntries] = useState<
    DesktopHumanTimeDiagnosticEntry[]
  >([]);
  const [collectionError, setCollectionError] = useState<string | null>(null);

  const latestRef = useRef({
    enabled,
    pluginId,
    connectionIds,
    connectedConnectionIds,
    getBackend,
  });
  latestRef.current = {
    enabled,
    pluginId,
    connectionIds,
    connectedConnectionIds,
    getBackend,
  };

  const trackerRef = useRef<HumanTimeSpanTracker | null>(null);
  const activeConnectionIdRef = useRef<string | null>(null);
  const uploadersRef = useRef(new Map<string, HumanTimeSpanUploader>());
  const pendingWritesRef = useRef<Promise<void>>(Promise.resolve());

  const refreshDiagnostics = useCallback(async () => {
    const ids = latestRef.current.connectionIds;
    const pendingByConnection = await Promise.all(
      ids.map(async connectionId => ({
        connectionId,
        spans: await loadHumanTimeSpans(connectionId, store),
      })),
    );
    if (latestRef.current.connectionIds !== ids) return;
    setPendingCount(
      pendingByConnection.reduce(
        (total, connection) => total + connection.spans.length,
        0,
      ),
    );
    setRecentEntries(current =>
      mergeDesktopPendingEntries(current, pendingByConnection),
    );
  }, [store]);

  const getUploader = useCallback(
    (connectionId: string): HumanTimeSpanUploader => {
      const existing = uploadersRef.current.get(connectionId);
      if (existing) return existing;
      const uploader = new HumanTimeSpanUploader({
        getBackend: () => latestRef.current.getBackend(connectionId),
        getConnectionId: () => connectionId,
        getPluginId: () => latestRef.current.pluginId,
        isEnabled: () => latestRef.current.enabled,
        store,
        onDefinitiveFailure: error => {
          const backend = latestRef.current.getBackend(connectionId);
          if (!backend) return;
          emitHumanTimeTelemetryWarning(backend, connectionId, error);
        },
        onUploadEvent: (event: HumanTimeUploadEvent) => {
          setLastUpload({ connectionId, event });
          setRecentEntries(current =>
            updateDesktopEntries(
              current,
              connectionId,
              event.spans,
              humanTimeDiagnosticUploadStatus(event.outcome),
              event.error,
            ),
          );
          void refreshDiagnostics();
        },
      });
      uploadersRef.current.set(connectionId, uploader);
      return uploader;
    },
    [refreshDiagnostics, store],
  );

  const flushConnected = useCallback(async () => {
    const ids = latestRef.current.connectedConnectionIds;
    await Promise.all(ids.map(id => getUploader(id).flush()));
    await refreshDiagnostics();
  }, [getUploader, refreshDiagnostics]);

  useEffect(() => {
    const tracker = new HumanTimeSpanTracker({
      inactivityMs,
      onSpanClosed: span => {
        const connectionId = activeConnectionIdRef.current;
        activeConnectionIdRef.current = null;
        setOpenSpan(null);
        if (!connectionId) return;
        setLastCollectedSpan({ connectionId, span });
        pendingWritesRef.current = pendingWritesRef.current.then(async () => {
          const appended = await appendHumanTimeSpan(connectionId, span, store);
          if (!appended) {
            const error = 'The collected span could not be saved.';
            setCollectionError(error);
            setRecentEntries(current =>
              updateDesktopEntries(
                current,
                connectionId,
                [span],
                'failed',
                error,
              ),
            );
            return;
          }
          setCollectionError(null);
          setRecentEntries(current =>
            updateDesktopEntries(
              current,
              connectionId,
              [span],
              'pending',
              null,
            ),
          );
          await refreshDiagnostics();
          getUploader(connectionId).notifySpanClosed();
        });
      },
    });
    trackerRef.current = tracker;
    return () => {
      tracker.dispose();
      trackerRef.current = null;
      uploadersRef.current.forEach(uploader => uploader.dispose());
      uploadersRef.current.clear();
    };
  }, [getUploader, refreshDiagnostics, store]);

  useEffect(() => {
    trackerRef.current?.setInactivityMs(inactivityMs);
  }, [inactivityMs]);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', state => {
      if (state === 'active') {
        void pendingWritesRef.current.then(flushConnected);
        return;
      }
      trackerRef.current?.close();
    });
    return () => subscription?.remove?.();
  }, [flushConnected]);

  useEffect(() => {
    if (!enabled) {
      trackerRef.current?.close();
    }
    uploadersRef.current.forEach(uploader => uploader.rearmWarning());
  }, [enabled, pluginId]);

  useEffect(() => {
    trackerRef.current?.close();
  }, [activeSurfaceKey]);

  const connectedKey = [...connectedConnectionIds].sort().join('\u0000');
  useEffect(() => {
    void refreshDiagnostics();
    if (!enabled) return;
    void pendingWritesRef.current.then(async () => {
      for (const connectionId of latestRef.current.connectedConnectionIds) {
        getUploader(connectionId).notifyConnectionUsable();
      }
    });
  }, [connectedKey, enabled, getUploader, refreshDiagnostics]);

  const recordActivity = useCallback(
    (connectionId: string | null, sessionId: string | null) => {
      if (!connectionId || !sessionId || !latestRef.current.enabled) return;
      setActivityEventCount(current => current + 1);
      if (
        activeConnectionIdRef.current &&
        activeConnectionIdRef.current !== connectionId
      ) {
        trackerRef.current?.close();
      }
      activeConnectionIdRef.current = connectionId;
      trackerRef.current?.recordActivity(sessionId);
      const span = trackerRef.current?.getOpenSpan() ?? null;
      setOpenSpan(span ? { connectionId, span } : null);
    },
    [],
  );

  const splitForComposedMessage = useCallback(
    (connectionId: string | null, sessionId: string | null) => {
      if (!connectionId || !sessionId || !latestRef.current.enabled) return;
      const atMs = Date.now();
      trackerRef.current?.close(atMs);
      activeConnectionIdRef.current = connectionId;
      trackerRef.current?.recordActivity(sessionId, atMs);
      const span = trackerRef.current?.getOpenSpan() ?? null;
      setOpenSpan(span ? { connectionId, span } : null);
    },
    [],
  );

  const uploadNow = useCallback(async () => {
    trackerRef.current?.close();
    await pendingWritesRef.current;
    await flushConnected();
  }, [flushConnected]);

  useEffect(
    () =>
      desktopHumanTimeDiagnosticsBridge.registerController({
        refresh: refreshDiagnostics,
        uploadNow,
      }),
    [refreshDiagnostics, uploadNow],
  );

  const diagnostics = useMemo<DesktopHumanTimeDiagnostics>(
    () => ({
      enabled,
      connectedConnectionCount: connectedConnectionIds.length,
      activityEventCount,
      openSpan,
      lastCollectedSpan,
      pendingCount,
      lastUpload,
      recentEntries,
      collectionError,
    }),
    [
      collectionError,
      connectedConnectionIds.length,
      activityEventCount,
      enabled,
      lastCollectedSpan,
      lastUpload,
      openSpan,
      pendingCount,
      recentEntries,
    ],
  );

  useEffect(() => {
    desktopHumanTimeDiagnosticsBridge.publish(diagnostics);
  }, [diagnostics]);

  const value = useMemo(
    () => ({ recordActivity, splitForComposedMessage }),
    [recordActivity, splitForComposedMessage],
  );
  return (
    <DesktopHumanTimeTelemetryContext.Provider value={value}>
      {children}
    </DesktopHumanTimeTelemetryContext.Provider>
  );
}
