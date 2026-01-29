import { useEffect, useMemo, useSyncExternalStore } from 'react';
import type {
  AgentBackend,
  ChatControllerState,
  Event,
  IndexedMessage,
} from '@crystal-lattice/frontend-sdk';
import { ChatController } from '@crystal-lattice/frontend-sdk';

export interface UseChatControllerOptions {
  backend: AgentBackend | null;
  sessionId: string | null;
  initialMessages?: IndexedMessage[];
  initialCursorEventId?: string | null;
  initialActiveRequestId?: string | null;
  onEvents?: ((events: Event[]) => void) | null;
  eventsEnabled?: boolean;
  initialSinceId?: string | null;
}

export interface UseChatControllerResult {
  controller: ChatController | null;
  state: ChatControllerState | null;
}

export function useChatController(options: UseChatControllerOptions): UseChatControllerResult {
  const {
    backend,
    sessionId,
    initialMessages,
    initialCursorEventId,
    initialActiveRequestId,
    onEvents,
    eventsEnabled,
    initialSinceId,
  } = options;

  const controller = useMemo(() => {
    if (!backend || !sessionId) {
      return null;
    }
    return new ChatController({
      backend,
      sessionId,
      initialMessages,
      initialCursorEventId,
      initialActiveRequestId,
    });
  }, [backend, sessionId]);

  useEffect(() => {
    return () => {
      controller?.dispose();
    };
  }, [controller]);

  useEffect(() => {
    controller?.setEventsListener(onEvents ?? null);
    return () => {
      controller?.setEventsListener(null);
    };
  }, [controller, onEvents]);

  useEffect(() => {
    if (!controller) return;
    if (eventsEnabled) {
      controller.startEventStreaming({ initialSinceId: initialSinceId ?? null });
    } else {
      controller.stopEventStreaming();
    }
  }, [controller, eventsEnabled, initialSinceId]);

  const state = useSyncExternalStore(
    (onStoreChange) => (controller ? controller.subscribe(onStoreChange) : () => {}),
    () => (controller ? controller.getSnapshot() : null),
    () => (controller ? controller.getSnapshot() : null),
  );
  return { controller, state };
}
