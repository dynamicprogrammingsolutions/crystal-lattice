import React, { createContext, useContext, useEffect, useMemo, type ReactNode } from 'react';
import type { AgentBackend, PluginsRegistryState } from '@crystal-lattice/frontend-sdk';
import { PluginsRegistry } from '@crystal-lattice/frontend-sdk';
import { useSubscribableSnapshot } from './useSubscribable';

export type UseApplicationPluginsResult = Omit<PluginsRegistryState, 'loading' | 'error'>;

export interface ApplicationPluginsContextValue extends PluginsRegistryState {
  refresh: () => Promise<void>;
  invalidate: () => void;
}

const defaultContext: ApplicationPluginsContextValue = {
  actionsById: {},
  sessionActions: [],
  messageActions: [],
  sessionListActions: [],
  sessionListFields: [],
  sessionListPinnedToggles: [],
  sessionListDiagnostics: [],
  loading: false,
  error: null,
  refresh: async () => {},
  invalidate: () => {},
};

const ApplicationPluginsContext = createContext<ApplicationPluginsContextValue>(defaultContext);

export interface ApplicationPluginsProviderProps {
  backend: AgentBackend | null;
  connectionId: string | null;
  children: ReactNode;
}

export const ApplicationPluginsProvider: React.FC<ApplicationPluginsProviderProps> = ({
  backend,
  connectionId,
  children,
}) => {
  const cacheKey = useMemo(() => connectionId || 'default', [connectionId]);

  const registry = useMemo(
    () => new PluginsRegistry({ backend, cacheKey }),
    [backend, cacheKey],
  );

  const state = useSubscribableSnapshot(registry);

  useEffect(() => {
    registry.load().catch(() => {
      // Errors are stored in state.
    });
  }, [registry]);

  const value = useMemo(
    () => ({
      ...state,
      refresh: () => registry.refresh(),
      invalidate: () => registry.invalidate(),
    }),
    [registry, state],
  );

  return (
    <ApplicationPluginsContext.Provider value={value}>
      {children}
    </ApplicationPluginsContext.Provider>
  );
};

export function useApplicationPluginsContext(): ApplicationPluginsContextValue {
  return useContext(ApplicationPluginsContext);
}

export function selectApplicationPlugins(
  value: ApplicationPluginsContextValue,
): UseApplicationPluginsResult {
  const {
    actionsById,
    sessionActions,
    messageActions,
    sessionListActions,
    sessionListFields,
    sessionListPinnedToggles,
    sessionListDiagnostics,
  } = value;
  return {
    actionsById,
    sessionActions,
    messageActions,
    sessionListActions,
    sessionListFields,
    sessionListPinnedToggles,
    sessionListDiagnostics,
  };
}

export function useApplicationPlugins(): UseApplicationPluginsResult {
  return selectApplicationPlugins(useApplicationPluginsContext());
}
