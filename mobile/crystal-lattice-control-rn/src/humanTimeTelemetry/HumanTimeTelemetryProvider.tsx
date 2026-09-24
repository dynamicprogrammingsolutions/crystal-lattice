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

import { useHomeWorkspace } from '../HomeWorkspaceContext';
import { appendSpan, loadSpans } from './spanCache';
import { HumanTimeSpanTracker, type HumanTimeSpan } from './spanTracker';
import {
  HumanTimeSpanUploader,
  type FlushOutcome,
  type HumanTimeUploadEvent,
} from './uploader';
import { emitHumanTimeTelemetryWarning } from './warning';

export type HumanTimeDiagnosticUploadStatus =
  | 'pending'
  | 'uploading'
  | 'uploaded'
  | 'retrying'
  | 'failed';

export interface HumanTimeDiagnosticEntry extends HumanTimeSpan {
  uploadStatus: HumanTimeDiagnosticUploadStatus;
  error: string | null;
}

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
  /** Report user activity on a surface; null for session-less surfaces. */
  recordActivity: (sessionId: string | null) => void;
  diagnostics: HumanTimeDiagnostics;
  refreshDiagnostics: () => Promise<void>;
  uploadNow: () => Promise<FlushOutcome>;
}

const defaultValue: HumanTimeTelemetryValue = {
  recordActivity: () => {},
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

const RECENT_DIAGNOSTIC_ENTRY_LIMIT = 10;

function diagnosticSpanKey(span: HumanTimeSpan): string {
  return `${span.sessionId ?? ''}\u0000${span.from}\u0000${span.to}`;
}

function newestDiagnosticEntries(
  entries: HumanTimeDiagnosticEntry[],
): HumanTimeDiagnosticEntry[] {
  return [...entries]
    .sort((left, right) => right.to.localeCompare(left.to))
    .slice(0, RECENT_DIAGNOSTIC_ENTRY_LIMIT);
}

function mergePendingDiagnosticEntries(
  current: HumanTimeDiagnosticEntry[],
  pending: HumanTimeSpan[],
): HumanTimeDiagnosticEntry[] {
  const entries = new Map(
    current.map((entry) => [diagnosticSpanKey(entry), entry]),
  );
  for (const span of pending) {
    const key = diagnosticSpanKey(span);
    if (!entries.has(key)) {
      entries.set(key, { ...span, uploadStatus: 'pending', error: null });
    }
  }
  return newestDiagnosticEntries([...entries.values()]);
}

function updateDiagnosticEntries(
  current: HumanTimeDiagnosticEntry[],
  spans: HumanTimeSpan[],
  uploadStatus: HumanTimeDiagnosticUploadStatus,
  error: string | null,
): HumanTimeDiagnosticEntry[] {
  const entries = new Map(
    current.map((entry) => [diagnosticSpanKey(entry), entry]),
  );
  for (const span of spans) {
    entries.set(diagnosticSpanKey(span), { ...span, uploadStatus, error });
  }
  return newestDiagnosticEntries([...entries.values()]);
}

function diagnosticUploadStatus(
  outcome: HumanTimeUploadEvent['outcome'],
): HumanTimeDiagnosticUploadStatus {
  switch (outcome) {
    case 'uploading':
      return 'uploading';
    case 'flushed':
      return 'uploaded';
    case 'partial-failure':
      return 'failed';
    case 'transient-failure':
      return 'retrying';
    case 'definitive-failure':
      return 'failed';
  }
}

export function useHumanTimeTelemetry(): HumanTimeTelemetryValue {
  return useContext(HumanTimeTelemetryContext);
}

export interface HumanTimeTelemetryProviderProps {
  backend: AgentBackend | null;
  connectionId: string | null;
  children: React.ReactNode;
}

/**
 * Owns the human time telemetry pipeline: the span tracker (activity →
 * spans), the durable cache, and the batched uploader. Collection runs only
 * when the user opted in; uploads target the frontend-owned telemetry plugin
 * id.
 */
export const HumanTimeTelemetryProvider: React.FC<
  HumanTimeTelemetryProviderProps
> = ({ backend, connectionId, children }) => {
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
    timeTrackingEnabled,
    timeTrackingPluginId,
  });
  latestRef.current = {
    backend,
    connectionId,
    timeTrackingEnabled,
    timeTrackingPluginId,
  };

  const trackerRef = useRef<HumanTimeSpanTracker | null>(null);
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
      mergePendingDiagnosticEntries(current, pending),
    );
  }, []);

  useEffect(() => {
    const tracker = new HumanTimeSpanTracker({
      onSpanClosed: (span) => {
        setOpenSpan(null);
        setLastCollectedSpan(span);
        const {
          connectionId: activeConnectionId,
          timeTrackingEnabled: enabled,
        } = latestRef.current;
        if (!activeConnectionId || !enabled) return;
        pendingWritesRef.current = pendingWritesRef.current.then(async () => {
          const appended = await appendSpan(activeConnectionId, span);
          if (!appended) {
            setCollectionError('The collected span could not be saved.');
            setRecentEntries((current) =>
              updateDiagnosticEntries(
                current,
                [span],
                'failed',
                'The collected span could not be saved.',
              ),
            );
            return;
          }
          setCollectionError(null);
          setRecentEntries((current) =>
            updateDiagnosticEntries(current, [span], 'pending', null),
          );
          await refreshDiagnostics();
          uploaderRef.current?.notifySpanClosed();
        });
      },
    });
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
          updateDiagnosticEntries(
            current,
            event.spans,
            diagnosticUploadStatus(event.outcome),
            event.error,
          ),
        );
        void refreshDiagnostics();
      },
    });
    trackerRef.current = tracker;
    uploaderRef.current = uploader;
    return () => {
      tracker.dispose();
      uploader.dispose();
      trackerRef.current = null;
      uploaderRef.current = null;
    };
  }, [refreshDiagnostics]);

  // Close the open span when the app leaves the foreground; the user
  // stopped being active. On return, wait for that durable write before
  // flushing because mobile runtimes commonly suspend the close debounce.
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') {
        void pendingWritesRef.current.then(() => {
          uploaderRef.current?.notifyAppForeground();
          return refreshDiagnostics();
        });
        return;
      }
      trackerRef.current?.close();
    });
    return () => {
      subscription?.remove?.();
    };
  }, [refreshDiagnostics]);

  // Close the current span when collection is disabled.
  useEffect(() => {
    if (!timeTrackingEnabled) {
      trackerRef.current?.close();
    }
  }, [timeTrackingEnabled]);

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

  const recordActivity = useCallback((sessionId: string | null) => {
    if (!latestRef.current.timeTrackingEnabled) return;
    const tracker = trackerRef.current;
    tracker?.recordActivity(sessionId);
    setOpenSpan(tracker?.getOpenSpan() ?? null);
  }, []);

  const uploadNow = useCallback(async (): Promise<FlushOutcome> => {
    trackerRef.current?.close();
    await pendingWritesRef.current;
    const outcome = await uploaderRef.current?.flush();
    await refreshDiagnostics();
    return outcome ?? 'no-connection';
  }, [refreshDiagnostics]);

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
      recordActivity,
      diagnostics,
      refreshDiagnostics,
      uploadNow,
    }),
    [diagnostics, recordActivity, refreshDiagnostics, uploadNow],
  );

  return (
    <HumanTimeTelemetryContext.Provider value={value}>
      {children}
    </HumanTimeTelemetryContext.Provider>
  );
};
