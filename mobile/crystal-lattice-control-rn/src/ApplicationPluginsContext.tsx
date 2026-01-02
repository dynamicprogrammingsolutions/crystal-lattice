import React, { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { ConnectionAdapter } from '../App';
import {
  apiListApplicationActions,
  apiListApplicationUiSchema,
  type ActionUiElement,
  type ApplicationActionDefinition,
  type ApplicationUiElement,
} from './api';

export interface UseApplicationPluginsResult {
  actionsById: Record<string, ApplicationActionDefinition>;
  sessionActions: ActionUiElement[];
  messageActions: ActionUiElement[];
  sessionListActions: ActionUiElement[];
}

export interface ApplicationPluginsContextValue extends UseApplicationPluginsResult {
  loading: boolean;
  error: string | null;
}

interface CacheEntry {
  actions: ApplicationActionDefinition[];
  elements: ApplicationUiElement[];
}

const APPLICATION_PLUGINS_CACHE: Record<string, CacheEntry | null | undefined> = {};

const emptyResult: UseApplicationPluginsResult = {
  actionsById: {},
  sessionActions: [],
  messageActions: [],
  sessionListActions: [],
};

const defaultContext: ApplicationPluginsContextValue = {
  ...emptyResult,
  loading: false,
  error: null,
};

const ApplicationPluginsContext = createContext<ApplicationPluginsContextValue>(defaultContext);

function buildResultFromEntry(entry: CacheEntry | null | undefined): UseApplicationPluginsResult {
  if (!entry) {
    return emptyResult;
  }

  const actionsById: Record<string, ApplicationActionDefinition> = {};
  (entry.actions || []).forEach((a) => {
    if (a && typeof a.id === 'string') {
      actionsById[a.id] = a;
    }
  });

  const elements = Array.isArray(entry.elements) ? entry.elements : [];
  const sessionActions = elements.filter(
    (el) => el && (el as any).ui_type === 'session_action',
  ) as ActionUiElement[];
  const messageActions = elements.filter(
    (el) => el && (el as any).ui_type === 'message_action',
  ) as ActionUiElement[];
  const sessionListActions = elements.filter(
    (el) => el && (el as any).ui_type === 'session_list_action',
  ) as ActionUiElement[];

  return {
    actionsById,
    sessionActions,
    messageActions,
    sessionListActions,
  };
}

export interface ApplicationPluginsProviderProps {
  adapter: ConnectionAdapter | null;
  connectionId: string | null;
  children: ReactNode;
}

export const ApplicationPluginsProvider: React.FC<ApplicationPluginsProviderProps> = ({
  adapter,
  connectionId,
  children,
}) => {
  const cacheKey = useMemo(() => connectionId || 'default', [connectionId]);
  const cached = APPLICATION_PLUGINS_CACHE[cacheKey];

  const [state, setState] = useState<ApplicationPluginsContextValue>(() => ({
    ...buildResultFromEntry(cached),
    loading: false,
    error: null,
  }));

  useEffect(() => {
    if (!adapter || !connectionId) {
      setState({ ...emptyResult, loading: false, error: null });
      return;
    }

    const cacheKeyLocal = connectionId || 'default';
    const cachedEntry = APPLICATION_PLUGINS_CACHE[cacheKeyLocal];
    let cancelled = false;

    if (cachedEntry !== undefined) {
      const next = buildResultFromEntry(cachedEntry);
      setState({ ...next, loading: false, error: null });
      return;
    }

    setState((prev) => ({ ...prev, loading: true, error: null }));

    const load = async () => {
      try {
        const [actions, elements] = await Promise.all([
          apiListApplicationActions(adapter),
          apiListApplicationUiSchema(adapter),
        ]);

        if (cancelled) {
          return;
        }

        const entry: CacheEntry = {
          actions: Array.isArray(actions) ? actions : [],
          elements: Array.isArray(elements) ? elements : [],
        };
        APPLICATION_PLUGINS_CACHE[cacheKeyLocal] = entry;
        const next = buildResultFromEntry(entry);
        setState({ ...next, loading: false, error: null });
      } catch (err: any) {
        console.log('Failed to load application actions/ui-schema', err);
        if (!cancelled) {
          APPLICATION_PLUGINS_CACHE[cacheKeyLocal] = null;
          setState({ ...emptyResult, loading: false, error: err?.message || 'Failed to load' });
        }
      }
    };

    load().catch(() => {
      // Error already handled.
    });

    return () => {
      cancelled = true;
    };
  }, [adapter, connectionId]);

  return (
    <ApplicationPluginsContext.Provider value={state}>
      {children}
    </ApplicationPluginsContext.Provider>
  );
};

export function useApplicationPluginsContext(): ApplicationPluginsContextValue {
  return useContext(ApplicationPluginsContext);
}

// Convenience hook matching the old "useApplicationPlugins" return
// shape, without exposing loading/error flags.
export function useApplicationPlugins(): UseApplicationPluginsResult {
  const { actionsById, sessionActions, messageActions, sessionListActions } =
    useApplicationPluginsContext();
  return { actionsById, sessionActions, messageActions, sessionListActions };
}
