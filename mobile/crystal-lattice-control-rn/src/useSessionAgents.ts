import { useCallback, useState } from 'react';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';

export interface UseSessionAgentsResult {
  availableAgents: string[];
  agentLoading: boolean;
  ensureAgentsLoaded: (backend: AgentBackend | null) => Promise<string[]>;
  setAgentLoading: (value: boolean) => void;
}

export function useSessionAgents(): UseSessionAgentsResult {
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);
  const [agentLoading, setAgentLoading] = useState(false);

  const ensureAgentsLoaded = useCallback(
    async (backend: AgentBackend | null): Promise<string[]> => {
      if (!backend) {
        throw new Error('No active connection');
      }
      if (availableAgents.length > 0) {
        return availableAgents;
      }
      setAgentLoading(true);
      try {
        const agents = await backend.listAgents();
        setAvailableAgents(agents);
        return agents;
      } finally {
        setAgentLoading(false);
      }
    },
    [availableAgents],
  );

  return { availableAgents, agentLoading, ensureAgentsLoaded, setAgentLoading };
}
