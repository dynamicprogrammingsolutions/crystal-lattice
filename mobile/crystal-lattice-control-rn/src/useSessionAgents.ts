import { useCallback, useState } from 'react';
import type { ConnectionAdapter } from '../App';
import { apiListAgents } from './api';

export interface UseSessionAgentsResult {
  availableAgents: string[];
  agentLoading: boolean;
  ensureAgentsLoaded: (adapter: ConnectionAdapter | null) => Promise<string[]>;
  setAgentLoading: (value: boolean) => void;
}

export function useSessionAgents(): UseSessionAgentsResult {
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);
  const [agentLoading, setAgentLoading] = useState(false);

  const ensureAgentsLoaded = useCallback(
    async (adapter: ConnectionAdapter | null): Promise<string[]> => {
      if (!adapter) {
        throw new Error('No active connection');
      }
      if (availableAgents.length > 0) {
        return availableAgents;
      }
      setAgentLoading(true);
      try {
        const agents = await apiListAgents(adapter);
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
