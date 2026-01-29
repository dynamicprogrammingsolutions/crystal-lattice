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
    eventsEnabled = false,
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

  const state = useSyncExternalStore(
    (onStoreChange) => (controller ? controller.subscribe(onStoreChange) : () => {}),
    () => (controller ? controller.getSnapshot() : null),
    () => (controller ? controller.getSnapshot() : null),
  );

  useEffect(() => {
    if (!controller) return;
    if (!eventsEnabled) {
      controller.stopEventStreaming();
      return;
    }

    if (controller.isEventStreaming()) {
      return;
    }

    // Avoid starting polling before we have an initial snapshot.
    // This keeps UI transitions snappier while still guaranteeing that
    // request lifecycle events will eventually clear `activeRequestId`.
    const hasInitialSnapshot =
      (state?.cursorEventId != null) || (Array.isArray(state?.messages) && state!.messages.length > 0);
    if (!hasInitialSnapshot) {
      return;
    }

    const sinceId = initialSinceId ?? state?.cursorEventId ?? controller.getSnapshot().cursorEventId ?? null;
    controller.startEventStreaming({ initialSinceId: sinceId });
  }, [controller, eventsEnabled, initialSinceId, state?.cursorEventId, state?.messages]);

  return { controller, state };
}
