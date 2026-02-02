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
  initialEventsCursorId?: string | null;
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
    initialEventsCursorId,
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
      initialEventsCursorId,
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

    if (state?.loading) {
      return;
    }

    if (controller.isEventStreaming()) {
      return;
    }

    // Avoid starting polling before we have an initial snapshot.
    // This keeps UI transitions snappier while still guaranteeing that
    // request lifecycle events will eventually clear `activeRequestId`.
    const hasInitialSnapshot =
      (state?.eventsCursorId != null) || (Array.isArray(state?.messages) && state!.messages.length > 0);
    if (!hasInitialSnapshot) {
      return;
    }

    const sinceId =
      initialSinceId ??
      state?.eventsCursorId ??
      controller.getSnapshot().eventsCursorId ??
      null;
    controller.startEventStreaming({ initialSinceId: sinceId });
  }, [controller, eventsEnabled, initialSinceId, state?.eventsCursorId, state?.messages, state?.loading]);

  return { controller, state };
}
