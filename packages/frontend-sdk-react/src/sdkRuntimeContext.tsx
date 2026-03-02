import React, { createContext, useContext, useMemo, type ReactNode } from 'react';

import type { AgentBackend, SdkRuntime } from '@crystal-lattice/frontend-sdk';

export interface SdkRuntimeContextValue {
  runtime: SdkRuntime | null;
  backend: AgentBackend | null;
  scopeKey: string | null;
}

const SdkRuntimeContext = createContext<SdkRuntimeContextValue | undefined>(undefined);

export interface SdkRuntimeProviderProps {
  runtime: SdkRuntime | null;
  children: ReactNode;
}

export const SdkRuntimeProvider: React.FC<SdkRuntimeProviderProps> = ({ runtime, children }) => {
  const value = useMemo<SdkRuntimeContextValue>(() => {
    return {
      runtime,
      backend: runtime?.backend ?? null,
      scopeKey: runtime?.scopeKey ?? null,
    };
  }, [runtime]);

  return <SdkRuntimeContext.Provider value={value}>{children}</SdkRuntimeContext.Provider>;
};

export function useSdkRuntimeContext(): SdkRuntimeContextValue {
  const context = useContext(SdkRuntimeContext);
  if (!context) {
    throw new Error('SDK runtime context is missing. Wrap the tree with <SdkRuntimeProvider runtime={...}>.');
  }
  return context;
}

export function useRuntime(): SdkRuntime | null {
  return useSdkRuntimeContext().runtime;
}

export function useBackend(): AgentBackend | null {
  return useSdkRuntimeContext().backend;
}

export function useConnectionScopeKey(): string | null {
  return useSdkRuntimeContext().scopeKey;
}
