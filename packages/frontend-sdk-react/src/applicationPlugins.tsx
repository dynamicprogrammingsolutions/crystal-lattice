import React, { createContext, useContext, useEffect, useMemo, type ReactNode } from 'react';
import type { PluginsRegistryState } from '@crystal-lattice/frontend-sdk';
import { PluginsRegistry } from '@crystal-lattice/frontend-sdk';

import { useBackend, useConnectionScopeKey } from './sdkRuntimeContext';
import { useSubscribableSnapshot } from './useSubscribable';

export type UseApplicationPluginsResult = Omit<PluginsRegistryState, 'loading' | 'error'>;

export interface ApplicationPluginsContextValue extends PluginsRegistryState {}

const defaultContext: ApplicationPluginsContextValue = {
  actionsById: {},
  sessionActions: [],
  messageActions: [],
  sessionListActions: [],
  sessionListFields: [],
  sessionListPinnedToggles: [],
  loading: false,
  error: null,
};

const ApplicationPluginsContext = createContext<ApplicationPluginsContextValue>(defaultContext);

export interface ApplicationPluginsProviderProps {
  children: ReactNode;
}

export const ApplicationPluginsProvider: React.FC<ApplicationPluginsProviderProps> = ({
  children,
}) => {
  const backend = useBackend();
  const scopeKey = useConnectionScopeKey();
  const cacheKey = useMemo(() => scopeKey || 'default', [scopeKey]);

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

  return (
    <ApplicationPluginsContext.Provider value={state}>
      {children}
    </ApplicationPluginsContext.Provider>
  );
};

export function useApplicationPluginsContext(): ApplicationPluginsContextValue {
  return useContext(ApplicationPluginsContext);
}

export function useApplicationPlugins(): UseApplicationPluginsResult {
  const {
    actionsById,
    sessionActions,
    messageActions,
    sessionListActions,
    sessionListFields,
    sessionListPinnedToggles,
  } = useApplicationPluginsContext();
  return {
    actionsById,
    sessionActions,
    messageActions,
    sessionListActions,
    sessionListFields,
    sessionListPinnedToggles,
  };
}
