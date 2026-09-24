import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
} from 'react';
import { AppState } from 'react-native';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

import { useHomeWorkspace } from '../HomeWorkspaceContext';
import { appendSpan } from './spanCache';
import { HumanTimeSpanTracker } from './spanTracker';
import { HumanTimeSpanUploader } from './uploader';
import { emitHumanTimeTelemetryWarning } from './warning';

interface HumanTimeTelemetryValue {
  /** Report user activity on a surface; null for session-less surfaces. */
  recordActivity: (sessionId: string | null) => void;
}

const defaultValue: HumanTimeTelemetryValue = {
  recordActivity: () => {},
};

const HumanTimeTelemetryContext =
  createContext<HumanTimeTelemetryValue>(defaultValue);

export function useHumanTimeTelemetry(): HumanTimeTelemetryValue {
  return useContext(HumanTimeTelemetryContext);
}

export interface HumanTimeTelemetryProviderProps {
  backend: AgentBackend | null;
  connectionId: string | null;
  /** Whether the app reports in-flight request work on this connection. */
  isBusy: boolean;
  children: React.ReactNode;
}

/**
 * Owns the human time telemetry pipeline: the span tracker (activity →
 * spans), the durable cache, and the batched uploader. Collection runs only
 * when the user opted in; uploads target the frontend-owned telemetry plugin
 * id and defer while the app is busy.
 */
export const HumanTimeTelemetryProvider: React.FC<
  HumanTimeTelemetryProviderProps
> = ({ backend, connectionId, isBusy, children }) => {
  const { timeTrackingEnabled, timeTrackingPluginId } = useHomeWorkspace();

  // The uploader reads its configuration through getters on every flush;
  // a ref keeps those getters pointed at the latest render values.
  const latestRef = useRef({
    backend,
    connectionId,
    isBusy,
    timeTrackingEnabled,
    timeTrackingPluginId,
  });
  latestRef.current = {
    backend,
    connectionId,
    isBusy,
    timeTrackingEnabled,
    timeTrackingPluginId,
  };

  const trackerRef = useRef<HumanTimeSpanTracker | null>(null);
  const uploaderRef = useRef<HumanTimeSpanUploader | null>(null);

  useEffect(() => {
    const tracker = new HumanTimeSpanTracker({
      onSpanClosed: (span) => {
        const { connectionId: activeConnectionId, timeTrackingEnabled: enabled } =
          latestRef.current;
        if (!activeConnectionId || !enabled) return;
        void appendSpan(activeConnectionId, span).then((appended) => {
          if (appended) {
            uploaderRef.current?.notifySpanClosed();
          }
        });
      },
    });
    const uploader = new HumanTimeSpanUploader({
      getBackend: () => latestRef.current.backend,
      getConnectionId: () => latestRef.current.connectionId,
      getPluginId: () => latestRef.current.timeTrackingPluginId,
      isEnabled: () => latestRef.current.timeTrackingEnabled,
      isBusy: () => latestRef.current.isBusy,
      onDefinitiveFailure: (error) => {
        const { backend: activeBackend, connectionId: activeConnectionId } =
          latestRef.current;
        if (!activeBackend) return;
        emitHumanTimeTelemetryWarning(activeBackend, activeConnectionId, error);
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
  }, []);

  // Close the open span when the app leaves the foreground; the user
  // stopped being active.
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (state) => {
      if (state !== 'active') {
        trackerRef.current?.close();
      }
    });
    return () => {
      subscription.remove();
    };
  }, []);

  // Start/stop the periodic scheduling with the opt-in setting.
  useEffect(() => {
    const uploader = uploaderRef.current;
    if (!uploader) return;
    if (timeTrackingEnabled) {
      uploader.start();
    } else {
      trackerRef.current?.close();
    }
    return () => {
      uploader.dispose();
    };
  }, [timeTrackingEnabled]);

  // A connection became usable: flush, deferring while busy.
  const connectionKey = backend && connectionId ? connectionId : null;
  useEffect(() => {
    if (!connectionKey || !timeTrackingEnabled) return;
    uploaderRef.current?.notifyConnectionUsable();
  }, [connectionKey, timeTrackingEnabled]);

  // Setting changes re-arm the one-time warning.
  useEffect(() => {
    uploaderRef.current?.rearmWarning();
  }, [timeTrackingEnabled, timeTrackingPluginId]);

  const recordActivity = useCallback((sessionId: string | null) => {
    if (!latestRef.current.timeTrackingEnabled) return;
    trackerRef.current?.recordActivity(sessionId);
  }, []);

  const value = useMemo<HumanTimeTelemetryValue>(
    () => ({ recordActivity }),
    [recordActivity],
  );

  return (
    <HumanTimeTelemetryContext.Provider value={value}>
      {children}
    </HumanTimeTelemetryContext.Provider>
  );
};