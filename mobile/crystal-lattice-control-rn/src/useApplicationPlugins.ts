import { useEffect, useState } from 'react';
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

export function useApplicationPlugins(
  adapter: ConnectionAdapter | null,
  connectionId: string | null,
): UseApplicationPluginsResult {
  const [result, setResult] = useState<UseApplicationPluginsResult>(emptyResult);

  useEffect(() => {
    if (!adapter) {
      setResult(emptyResult);
      return;
    }

    const cacheKey = connectionId || 'default';
    const cached = APPLICATION_PLUGINS_CACHE[cacheKey];
    let cancelled = false;

    if (cached !== undefined) {
      if (!cancelled) {
        setResult(buildResultFromEntry(cached));
      }
      return;
    }

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
        APPLICATION_PLUGINS_CACHE[cacheKey] = entry;
        setResult(buildResultFromEntry(entry));
      } catch (err) {
        console.log('Failed to load application actions/ui-schema', err);
        if (!cancelled) {
          APPLICATION_PLUGINS_CACHE[cacheKey] = null;
          setResult(emptyResult);
        }
      }
    };

    load().catch(() => {
      // Error already handled above.
    });

    return () => {
      cancelled = true;
    };
  }, [adapter, connectionId]);

  return result;
}
