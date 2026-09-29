export type DesktopEventMap = {
  sessionsReloadRequested: {
    connectionId: string;
    reason?: string;
  };

  sessionAgentSwitched: {
    connectionId: string;
    sessionId: string;
    agentId: string;
  };

  pinnedActionsChanged: {
    storageKey: string;
    pinned: string[];
    source: symbol;
  };
};

type DesktopEventKey = keyof DesktopEventMap;

type Listener<K extends DesktopEventKey> = (
  payload: DesktopEventMap[K],
) => void;

const listenersByEvent: {
  [K in DesktopEventKey]: Set<Listener<K>>;
} = {
  sessionsReloadRequested: new Set(),
  sessionAgentSwitched: new Set(),
  pinnedActionsChanged: new Set(),
};

export const desktopEventBus = {
  publish<K extends DesktopEventKey>(
    event: K,
    payload: DesktopEventMap[K],
  ): void {
    const listeners = listenersByEvent[event] as Set<Listener<K>>;
    listeners.forEach(listener => {
      try {
        listener(payload);
      } catch {}
    });
  },

  subscribe<K extends DesktopEventKey>(
    event: K,
    listener: Listener<K>,
  ): () => void {
    const listeners = listenersByEvent[event] as Set<Listener<K>>;
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },
};
