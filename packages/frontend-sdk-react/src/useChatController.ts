import { useEffect, useMemo } from 'react';
import type { AgentBackend, ChatControllerState } from '@crystal-lattice/frontend-sdk';
import { ChatController } from '@crystal-lattice/frontend-sdk';
import { useSubscribableSnapshot } from './useSubscribable';

export interface UseChatControllerOptions {
  backend: AgentBackend | null;
  sessionId: string | null;
  eventsEnabled?: boolean;
  initialSinceId?: string | null;
}

export interface UseChatControllerResult {
  controller: ChatController | null;
  state: ChatControllerState | null;
}

export function useChatController(options: UseChatControllerOptions): UseChatControllerResult {
  const { backend, sessionId, eventsEnabled, initialSinceId } = options;

  const controller = useMemo(() => {
    if (!backend || !sessionId) {
      return null;
    }
    return new ChatController({ backend, sessionId });
  }, [backend, sessionId]);

  useEffect(() => {
    return () => {
      controller?.dispose();
    };
  }, [controller]);

  useEffect(() => {
    if (!controller) return;
    if (eventsEnabled) {
      controller.startEventStreaming({ initialSinceId: initialSinceId ?? null });
    } else {
      controller.stopEventStreaming();
    }
  }, [controller, eventsEnabled, initialSinceId]);

  const state = controller ? useSubscribableSnapshot(controller) : null;
  return { controller, state };
}
