import { useEffect, useRef } from "react";
import type {
  AgentBackend,
  ConnectionRecord,
  Transport,
} from "@crystal-lattice/frontend-sdk";

export function disconnectTransport(candidate: unknown): void {
  if (
    candidate &&
    typeof candidate === "object" &&
    "disconnect" in candidate &&
    typeof candidate.disconnect === "function"
  ) {
    candidate.disconnect();
  }
}

interface ConnectionSetupOptions {
  transport: Transport | null;
  onConnected: (
    transport: Transport,
    record: ConnectionRecord,
    backend?: AgentBackend
  ) => void;
}

export function useConnectionSetup(options: ConnectionSetupOptions) {
  const current = useRef(options);
  current.current = options;
  const generation = useRef(0);
  const candidate = useRef<Transport | null>(null);

  function cancel() {
    generation.current += 1;
    if (candidate.current !== current.current.transport) {
      disconnectTransport(candidate.current);
    }
    candidate.current = null;
  }

  useEffect(
    () => () => {
      generation.current += 1;
      disconnectTransport(candidate.current);
    },
    []
  );

  function isCurrent(ticket: number) {
    return ticket === generation.current;
  }

  function track(ticket: number, next: Transport): boolean {
    if (!isCurrent(ticket)) {
      disconnectTransport(next);
      return false;
    }
    candidate.current = next;
    return true;
  }

  function complete(
    ticket: number,
    next: Transport,
    record: ConnectionRecord,
    backend?: AgentBackend
  ): boolean {
    if (!isCurrent(ticket)) {
      disconnectTransport(next);
      return false;
    }
    const previous = current.current.transport;
    candidate.current = null;
    generation.current += 1;
    current.current.onConnected(next, record, backend);
    if (previous !== next) disconnectTransport(previous);
    return true;
  }

  function fail(ticket: number) {
    if (!isCurrent(ticket)) return;
    disconnectTransport(candidate.current);
    candidate.current = null;
  }

  return {
    start: cancel,
    cancel,
    ticket: () => generation.current,
    isCurrent,
    track,
    complete,
    fail,
  };
}
