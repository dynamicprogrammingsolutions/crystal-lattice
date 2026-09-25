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
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import {
  humanTimeDiagnosticUploadStatus,
  mergePendingHumanTimeDiagnosticEntries,
  updateHumanTimeDiagnosticEntries,
  type HumanTimeDiagnosticEntry,
  type HumanTimeDiagnosticUploadStatus,
} from '@crystal-lattice/frontend-rn-components';

import { useHomeWorkspace } from '../HomeWorkspaceContext';
import { appendSpan, loadSpans } from './spanCache';
import type { HumanTimeSpan } from './spans';
import {
  HumanTimeSpanUploader,
  type FlushOutcome,
  type HumanTimeUploadEvent,
} from './uploader';
import { emitHumanTimeTelemetryWarning } from './warning';

export type { HumanTimeDiagnosticEntry, HumanTimeDiagnosticUploadStatus };

export interface HumanTimeDiagnostics {
  enabled: boolean;
  connected: boolean;
  openSpan: HumanTimeSpan | null;
  lastCollectedSpan: HumanTimeSpan | null;
  pendingCount: number;
  lastUpload: HumanTimeUploadEvent | null;
  recentEntries: HumanTimeDiagnosticEntry[];
  collectionError: string | null;
}

interface HumanTimeTelemetryValue {
  diagnostics: HumanTimeDiagnostics;
  refreshDiagnostics: () => Promise<void>;
  uploadNow: () => Promise<FlushOutcome>;
}

const defaultValue: HumanTimeTelemetryValue = {
  diagnostics: {
    enabled: false,
    connected: false,
    openSpan: null,
    lastCollectedSpan: null,
    pendingCount: 0,
    lastUpload: null,
    recentEntries: [],
    collectionError: null,
  },
  refreshDiagnostics: async () => {},
  uploadNow: async () => 'disabled',
};

const HumanTimeTelemetryContext =
  createContext<HumanTimeTelemetryValue>(defaultValue);

export function useHumanTimeTelemetry(): HumanTimeTelemetryValue {
  return useContext(HumanTimeTelemetryContext);
}

export interface HumanTimeTelemetryProviderProps {
  backend: AgentBackend | null;
  connectionId: string | null;
  activeSessionId: string | null;
  children: React.ReactNode;
}

interface ActiveSessionSpan {
  connectionId: string;
  sessionId: string;
  fromMs: number;
}

/**
 * Owns the human time telemetry pipeline: foreground session presence,
 * durable caching, and batched upload. Collection runs only when the user
 * opted in; uploads target the frontend-owned telemetry plugin id.
 */
export const HumanTimeTelemetryProvider: React.FC<
  HumanTimeTelemetryProviderProps
> = ({ backend, connectionId, activeSessionId, children }) => {
  const { timeTrackingEnabled, timeTrackingPluginId } = useHomeWorkspace();
  const [openSpan, setOpenSpan] = useState<HumanTimeSpan | null>(null);
  const [lastCollectedSpan, setLastCollectedSpan] =
    useState<HumanTimeSpan | null>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [lastUpload, setLastUpload] = useState<HumanTimeUploadEvent | null>(
    null,
  );
  const [recentEntries, setRecentEntries] = useState<
    HumanTimeDiagnosticEntry[]
  >([]);
  const [collectionError, setCollectionError] = useState<string | null>(null);

  // The uploader reads its configuration through getters on every flush;
  // a ref keeps those getters pointed at the latest render values.
  const latestRef = useRef({
    backend,
    connectionId,
    activeSessionId,
    timeTrackingEnabled,
    timeTrackingPluginId,
  });
  latestRef.current = {
    backend,
    connectionId,
    activeSessionId,
    timeTrackingEnabled,
    timeTrackingPluginId,
  };

  const activeSessionSpanRef = useRef<ActiveSessionSpan | null>(null);
  const appStateRef = useRef(AppState.currentState);
  const uploaderRef = useRef<HumanTimeSpanUploader | null>(null);
  const pendingWritesRef = useRef<Promise<void>>(Promise.resolve());

  const refreshDiagnostics = useCallback(async () => {
    const activeConnectionId = latestRef.current.connectionId;
    if (!activeConnectionId) {
      setPendingCount(0);
      setRecentEntries([]);
      return;
    }
    const pending = await loadSpans(activeConnectionId);
    if (latestRef.current.connectionId !== activeConnectionId) return;
    setPendingCount(pending.length);
    setRecentEntries((current) =>
      mergePendingHumanTimeDiagnosticEntries(current, pending),
    );
  }, []);

  useEffect(() => {
    const uploader = new HumanTimeSpanUploader({
      getBackend: () => latestRef.current.backend,
      getConnectionId: () => latestRef.current.connectionId,
      getPluginId: () => latestRef.current.timeTrackingPluginId,
      isEnabled: () => latestRef.current.timeTrackingEnabled,
      onDefinitiveFailure: (error) => {
        const { backend: activeBackend, connectionId: activeConnectionId } =
          latestRef.current;
        if (!activeBackend) return;
        emitHumanTimeTelemetryWarning(activeBackend, activeConnectionId, error);
      },
      onUploadEvent: (event) => {
        setLastUpload(event);
        setRecentEntries((current) =>
          updateHumanTimeDiagnosticEntries(
            current,
            event.spans,
            humanTimeDiagnosticUploadStatus(event.outcome),
            event.error,
          ),
        );
        void refreshDiagnostics();
      },
    });
    uploaderRef.current = uploader;
    return () => {
      uploader.dispose();
      uploaderRef.current = null;
    };
  }, [refreshDiagnostics]);

  const closeActiveSessionSpan = useCallback(
    (atMs = Date.now()) => {
      const active = activeSessionSpanRef.current;
      if (!active) return;
      activeSessionSpanRef.current = null;
      const span: HumanTimeSpan = {
        sessionId: active.sessionId,
        from: new Date(active.fromMs).toISOString(),
        to: new Date(Math.max(active.fromMs, atMs)).toISOString(),
      };
      setOpenSpan(null);
      setLastCollectedSpan(span);
      pendingWritesRef.current = pendingWritesRef.current.then(async () => {
        const appended = await appendSpan(active.connectionId, span);
        if (!appended) {
          const error = 'The collected span could not be saved.';
          setCollectionError(error);
          setRecentEntries((current) =>
            updateHumanTimeDiagnosticEntries(
              current,
              [span],
              'failed',
              error,
            ),
          );
          return;
        }
        setCollectionError(null);
        setRecentEntries((current) =>
          updateHumanTimeDiagnosticEntries(current, [span], 'pending', null),
        );
        await refreshDiagnostics();
        uploaderRef.current?.notifySpanClosed();
      });
    },
    [refreshDiagnostics],
  );

  const reconcileActiveSessionSpan = useCallback(() => {
    const {
      activeSessionId: nextSessionId,
      connectionId: nextConnectionId,
      timeTrackingEnabled: enabled,
    } = latestRef.current;
    const shouldTrack =
      enabled &&
      appStateRef.current === 'active' &&
      !!nextConnectionId &&
      !!nextSessionId;
    const active = activeSessionSpanRef.current;
    if (
      active &&
      (!shouldTrack ||
        active.connectionId !== nextConnectionId ||
        active.sessionId !== nextSessionId)
    ) {
      closeActiveSessionSpan();
    }
    if (!shouldTrack || activeSessionSpanRef.current) return;
    const fromMs = Date.now();
    activeSessionSpanRef.current = {
      connectionId: nextConnectionId,
      sessionId: nextSessionId,
      fromMs,
    };
    setOpenSpan({
      sessionId: nextSessionId,
      from: new Date(fromMs).toISOString(),
      to: new Date(fromMs).toISOString(),
    });
  }, [closeActiveSessionSpan]);

  useEffect(() => {
    reconcileActiveSessionSpan();
  }, [
    activeSessionId,
    connectionId,
    reconcileActiveSessionSpan,
    timeTrackingEnabled,
  ]);

  // Close when the app leaves the foreground. On return, start a new span
  // for the still-open session and flush durable spans from the prior period.
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (state) => {
      appStateRef.current = state;
      if (state === 'active') {
        reconcileActiveSessionSpan();
        void pendingWritesRef.current.then(() => {
          uploaderRef.current?.notifyAppForeground();
          return refreshDiagnostics();
        });
        return;
      }
      closeActiveSessionSpan();
    });
    return () => {
      subscription?.remove?.();
    };
  }, [
    closeActiveSessionSpan,
    reconcileActiveSessionSpan,
    refreshDiagnostics,
  ]);

  // A connection became usable: flush after any pending cache write.
  const connectionKey = backend && connectionId ? connectionId : null;
  useEffect(() => {
    setRecentEntries([]);
  }, [connectionId]);

  useEffect(() => {
    void refreshDiagnostics();
    if (!connectionKey || !timeTrackingEnabled) return;
    void pendingWritesRef.current.then(() => {
      uploaderRef.current?.notifyConnectionUsable();
    });
  }, [connectionKey, refreshDiagnostics, timeTrackingEnabled]);

  // Setting changes re-arm the one-time warning.
  useEffect(() => {
    uploaderRef.current?.rearmWarning();
  }, [timeTrackingEnabled, timeTrackingPluginId]);

  const uploadNow = useCallback(async (): Promise<FlushOutcome> => {
    closeActiveSessionSpan();
    await pendingWritesRef.current;
    const outcome = await uploaderRef.current?.flush();
    await refreshDiagnostics();
    reconcileActiveSessionSpan();
    return outcome ?? 'no-connection';
  }, [
    closeActiveSessionSpan,
    reconcileActiveSessionSpan,
    refreshDiagnostics,
  ]);

  const diagnostics = useMemo<HumanTimeDiagnostics>(
    () => ({
      enabled: timeTrackingEnabled,
      connected: backend !== null && connectionId !== null,
      openSpan,
      lastCollectedSpan,
      pendingCount,
      lastUpload,
      recentEntries,
      collectionError,
    }),
    [
      backend,
      collectionError,
      connectionId,
      lastCollectedSpan,
      lastUpload,
      openSpan,
      pendingCount,
      recentEntries,
      timeTrackingEnabled,
    ],
  );

  const value = useMemo<HumanTimeTelemetryValue>(
    () => ({
      diagnostics,
      refreshDiagnostics,
      uploadNow,
    }),
    [diagnostics, refreshDiagnostics, uploadNow],
  );

  return (
    <HumanTimeTelemetryContext.Provider value={value}>
      {children}
    </HumanTimeTelemetryContext.Provider>
  );
};
