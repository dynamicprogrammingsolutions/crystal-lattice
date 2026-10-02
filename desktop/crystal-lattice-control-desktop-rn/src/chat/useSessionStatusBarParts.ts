import { useCallback, useEffect, useMemo, useState } from 'react';

import type {
  AgentBackend,
  AgentDescriptor,
  IndexedMessage,
  SessionSummary,
  StreamingRow,
  UiSchemaElement,
} from '@crystal-lattice/frontend-sdk';
import {
  deriveChatStatusBarParts,
  filterStatusBarElements,
  selectLastAssistantMessage,
} from '@crystal-lattice/frontend-sdk';
import { useAgentsController } from '@crystal-lattice/frontend-sdk-react';

import { desktopEventBus } from '../events/desktopEventBus';

export interface UseSessionStatusBarPartsOptions {
  backend: AgentBackend | null;
  connectionId: string;
  sessionId: string;
  isActive: boolean;
  uiSchemaElements: UiSchemaElement[];
  messages: IndexedMessage[];
  streamingRow: StreamingRow | null;
  sessionSummary?: SessionSummary | null;
}

export interface UseSessionStatusBarPartsResult {
  statusBarParts: string[];
  ensureAgentsLoaded: () => Promise<string[]>;
  ensureAgentDescriptorsLoaded: () => Promise<AgentDescriptor[]>;
  agentsLoading: boolean;
}

export function useSessionStatusBarParts(
  options: UseSessionStatusBarPartsOptions,
): UseSessionStatusBarPartsResult {
  const {
    backend,
    connectionId,
    sessionId,
    isActive,
    uiSchemaElements,
    messages,
    streamingRow,
    sessionSummary,
  } = options;

  const agentsEnabled = !!(backend && isActive);
  const { controller: agentsController, state: agentsState } = useAgentsController({
    backend,
    cacheKey: connectionId,
    enabled: agentsEnabled,
  });
  const availableAgents = agentsState?.agents ?? [];

  const [sessionAgentId, setSessionAgentId] = useState<string | null>(null);

  useEffect(() => {
    const md = sessionSummary?.metadata;
    const raw = (md as any)?.agent_id;
    if (typeof raw === 'string' && raw.trim()) {
      setSessionAgentId(raw.trim());
      return;
    }
    setSessionAgentId(null);
  }, [sessionId, sessionSummary]);

  useEffect(() => {
    if (!agentsEnabled) {
      return;
    }
    if (!backend) {
      return;
    }
    if (sessionAgentId != null) {
      return;
    }

    let cancelled = false;
    backend
      .getSessionAgent(sessionId)
      .then((value) => {
        if (cancelled) {
          return;
        }
        const trimmed = typeof value === 'string' ? value.trim() : '';
        setSessionAgentId(trimmed ? trimmed : null);
      })
      .catch(() => {
        // Non-fatal; status bar should still render.
      });

    return () => {
      cancelled = true;
    };
  }, [agentsEnabled, backend, sessionAgentId, sessionId]);

  useEffect(() => {
    return desktopEventBus.subscribe('sessionAgentSwitched', (payload) => {
      if (payload.connectionId !== connectionId) {
        return;
      }
      if (payload.sessionId !== sessionId) {
        return;
      }
      const next = typeof payload.agentId === 'string' ? payload.agentId.trim() : '';
      setSessionAgentId(next ? next : null);
    });
  }, [connectionId, sessionId]);

  const ensureAgentsLoaded = useCallback(async (): Promise<string[]> => {
    if (!agentsController) {
      throw new Error('Agent controller is not available.');
    }
    return agentsController.ensureLoaded();
  }, [agentsController]);

  const ensureAgentDescriptorsLoaded = useCallback(async (): Promise<
    AgentDescriptor[]
  > => {
    if (!agentsController) {
      throw new Error('Agent controller is not available.');
    }
    return agentsController.ensureDescriptorsLoaded();
  }, [agentsController]);

  const statusBarElements = useMemo((): UiSchemaElement[] => {
    return filterStatusBarElements(uiSchemaElements || []);
  }, [uiSchemaElements]);

  const lastAssistantMessage = useMemo(() => {
    return selectLastAssistantMessage({ messages, streamingRow });
  }, [messages, streamingRow]);

  const statusBarParts = useMemo(() => {
    return deriveChatStatusBarParts({
      sessionId,
      sessionAgentId,
      availableAgents,
      lastAssistantMessage,
      statusBarElements,
    });
  }, [
    availableAgents,
    lastAssistantMessage,
    sessionAgentId,
    sessionId,
    statusBarElements,
  ]);

  return {
    statusBarParts,
    ensureAgentsLoaded,
    ensureAgentDescriptorsLoaded,
    agentsLoading: agentsState?.loading ?? false,
  };
}
