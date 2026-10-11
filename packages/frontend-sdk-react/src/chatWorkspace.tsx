import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  useSyncExternalStore,
} from "react";
import type { ChatController } from "@crystal-lattice/frontend-sdk";

export interface ChatEditDraft {
  index: number;
  text: string;
}

export type PendingChatRequest = {
  idempotencyKey: string;
  requestedAtMs: number;
  errorMessage: string;
  configOverrides?: Record<string, any>;
} & (
  | {
      kind: "send_message";
      message: Parameters<ChatController["sendMessage"]>[0]["message"];
    }
  | { kind: "send" }
);

export interface ChatWorkspaceState {
  edit: ChatEditDraft | null;
  recovery: PendingChatRequest | null;
  actions: Readonly<Record<string, string>>;
  modifying: boolean;
  submitting: boolean;
  attachmentDrafts: { above: unknown[]; below: unknown[] };
}

const EMPTY: ChatWorkspaceState = {
  edit: null,
  recovery: null,
  actions: {},
  modifying: false,
  submitting: false,
  attachmentDrafts: { above: [], below: [] },
};

function createWorkspace() {
  const entries = new Map<string, ChatWorkspaceState>();
  const listeners = new Set<() => void>();
  return {
    get: (key: string) => entries.get(key) ?? EMPTY,
    subscribe: (listener: () => void) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    update: (
      key: string,
      updater: (state: ChatWorkspaceState) => ChatWorkspaceState
    ) => {
      entries.set(key, updater(entries.get(key) ?? EMPTY));
      listeners.forEach((listener) => listener());
    },
  };
}

const ChatWorkspaceContext = createContext<ReturnType<
  typeof createWorkspace
> | null>(null);

export function ChatWorkspaceProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [workspace] = useState(createWorkspace);
  return (
    <ChatWorkspaceContext.Provider value={workspace}>
      {children}
    </ChatWorkspaceContext.Provider>
  );
}

export function useSessionChatWorkspace(
  connectionId: string | null,
  sessionId: string
) {
  const shared = useContext(ChatWorkspaceContext);
  const local = useMemo(createWorkspace, []);
  const workspace = shared ?? local;
  const key = JSON.stringify([connectionId, sessionId]);
  const state = useSyncExternalStore(
    workspace.subscribe,
    () => workspace.get(key),
    () => workspace.get(key)
  );
  const update = useCallback(
    (updater: (state: ChatWorkspaceState) => ChatWorkspaceState) =>
      workspace.update(key, updater),
    [key, workspace]
  );
  const get = useCallback(() => workspace.get(key), [key, workspace]);
  const runAction = useCallback(
    async (actionKey: string, label: string, run: () => Promise<void>) => {
      if (workspace.get(key).actions[actionKey]) return;
      workspace.update(key, (current) => ({
        ...current,
        actions: { ...current.actions, [actionKey]: label },
      }));
      try {
        await run();
      } finally {
        workspace.update(key, (current) => ({
          ...current,
          actions: Object.fromEntries(
            Object.entries(current.actions).filter(
              ([entry]) => entry !== actionKey
            )
          ),
        }));
      }
    },
    [key, workspace]
  );
  return { state, update, get, runAction };
}
