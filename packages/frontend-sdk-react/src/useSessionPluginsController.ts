import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { AgentBackend, SessionPluginEntry } from '@crystal-lattice/frontend-sdk';

import { computeNextEnabledIds } from './sessionPlugins/logic';

export interface SessionPluginsState {
  loading: boolean;
  error: string | null;
  plugins: SessionPluginEntry[];
  lastLoadedAt?: number | null;
}

export interface UseSessionPluginsControllerOptions {
  backend: AgentBackend | null;
  sessionId: string | null;
  enabled?: boolean;
}

export interface UseSessionPluginsControllerResult {
  state: SessionPluginsState;
  reload: (opts?: { force?: boolean }) => Promise<void>;
  setEnabled: (pluginId: string, enabled: boolean) => Promise<void>;
  resetToDefaults: () => Promise<void>;
}

function formatErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message || 'Request failed.';
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'Request failed.';
}

function isSupported(backend: AgentBackend | null): boolean {
  try {
    return Boolean(backend?.getCapabilities()?.sessionPlugins);
  } catch {
    return false;
  }
}

const EMPTY_PLUGINS: SessionPluginEntry[] = [];

export function useSessionPluginsController(
  options: UseSessionPluginsControllerOptions,
): UseSessionPluginsControllerResult {
  const { backend, sessionId, enabled = true } = options;

  const [state, setState] = useState<SessionPluginsState>(() => ({
    loading: false,
    error: null,
    plugins: EMPTY_PLUGINS,
    lastLoadedAt: null,
  }));

  const requestSeqRef = useRef(0);

  const canLoad = useMemo(() => {
    return Boolean(enabled && backend && sessionId);
  }, [backend, enabled, sessionId]);

  const reload = useCallback(
    async (opts?: { force?: boolean }) => {
      if (!backend || !sessionId) {
        return;
      }
      if (!enabled && !opts?.force) {
        return;
      }

      if (!isSupported(backend)) {
        setState((prev) => ({
          ...prev,
          loading: false,
          error: 'Session plugins are not supported by this server.',
        }));
        return;
      }

      const seq = ++requestSeqRef.current;
      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const plugins = await backend.listSessionPlugins(sessionId);
        if (requestSeqRef.current !== seq) {
          return;
        }
        setState({
          loading: false,
          error: null,
          plugins: Array.isArray(plugins) ? plugins : EMPTY_PLUGINS,
          lastLoadedAt: Date.now(),
        });
      } catch (error) {
        if (requestSeqRef.current !== seq) {
          return;
        }
        setState((prev) => ({
          ...prev,
          loading: false,
          error: formatErrorMessage(error),
        }));
      }
    },
    [backend, enabled, sessionId],
  );

  const setEnabled = useCallback(
    async (pluginId: string, nextEnabled: boolean) => {
      if (!backend || !sessionId) {
        return;
      }
      if (!isSupported(backend)) {
        setState((prev) => ({
          ...prev,
          error: 'Session plugins are not supported by this server.',
        }));
        return;
      }

      let plugins = state.plugins;
      if (!Array.isArray(plugins) || plugins.length === 0) {
        try {
          plugins = await backend.listSessionPlugins(sessionId);
        } catch (error) {
          setState((prev) => ({
            ...prev,
            error: formatErrorMessage(error),
          }));
          return;
        }
      }

      try {
        const enabledIds = computeNextEnabledIds({
          plugins: Array.isArray(plugins) ? plugins : EMPTY_PLUGINS,
          pluginId,
          nextEnabled,
        });
        await backend.setSessionPlugins(sessionId, enabledIds);
      } catch (error) {
        setState((prev) => ({
          ...prev,
          error: formatErrorMessage(error),
        }));
        return;
      }

      await reload({ force: true });
    },
    [backend, reload, sessionId, state.plugins],
  );

  const resetToDefaults = useCallback(async () => {
    if (!backend || !sessionId) {
      return;
    }
    if (!isSupported(backend)) {
      setState((prev) => ({
        ...prev,
        error: 'Session plugins are not supported by this server.',
      }));
      return;
    }

    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      await backend.clearSessionPlugins(sessionId);
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: formatErrorMessage(error),
      }));
      return;
    }

    await reload({ force: true });
  }, [backend, reload, sessionId]);

  useEffect(() => {
    setState((prev) => {
      if (prev.plugins === EMPTY_PLUGINS && prev.error === null && prev.lastLoadedAt === null) {
        return prev;
      }
      return {
        loading: false,
        error: null,
        plugins: EMPTY_PLUGINS,
        lastLoadedAt: null,
      };
    });
    requestSeqRef.current += 1;
  }, [backend, sessionId]);

  useEffect(() => {
    if (!canLoad) {
      return;
    }
    reload().catch(() => {
      // State captures errors.
    });
  }, [canLoad, reload]);

  return {
    state,
    reload,
    setEnabled,
    resetToDefaults,
  };
}
