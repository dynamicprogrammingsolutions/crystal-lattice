import { useState } from "react";
import { Alert } from "react-native";
import type {
  ConnectionRecord,
  Transport,
} from "@crystal-lattice/frontend-sdk";
import { usePersistentPinnedActions } from "../usePersistentPinnedActions";

export interface ConnectionActionsProps {
  activeConnectionId: string | null;
  transport: Transport | null;
  onOpenConnection: (record: ConnectionRecord) => void | Promise<void>;
  onNewSession: (record: ConnectionRecord) => void | Promise<void>;
  onOpenServerSettings: () => void;
  onDisconnect: () => void;
  onDeleteConnection: (record: ConnectionRecord) => void;
}

export function useConnectionActions(props: ConnectionActionsProps) {
  const { pinned, setPinned } = usePersistentPinnedActions<string>(
    "clc_pinned_connection_card_actions_v1",
    ["open", "disconnect", "healthCheck", "serverSettings"]
  );
  const [busyConnectionId, setBusyConnectionId] = useState<string | null>(null);
  const [healthResult, setHealthResult] = useState<{
    title: string;
    body: string;
    error: boolean;
  } | null>(null);

  async function healthCheck(record: ConnectionRecord) {
    if (!props.transport || record.id !== props.activeConnectionId) return;
    setBusyConnectionId(record.id);
    try {
      const response = await props.transport.request({
        method: "GET",
        path: "/api/hello",
      });
      const body =
        typeof response.data === "object"
          ? JSON.stringify(response.data, null, 2)
          : String(response.data);
      setHealthResult({
        title: "Health Check",
        body: `OK: ${body}`,
        error: false,
      });
    } catch (error) {
      setHealthResult({
        title: "Health Check",
        body: error instanceof Error ? error.message : "Health check failed",
        error: true,
      });
    } finally {
      setBusyConnectionId(null);
    }
  }

  function execute(record: ConnectionRecord, key: string) {
    if (key === "open") void props.onOpenConnection(record);
    if (key === "newSession") void props.onNewSession(record);
    if (key === "disconnect") props.onDisconnect();
    if (key === "serverSettings") props.onOpenServerSettings();
    if (key === "healthCheck") void healthCheck(record);
    if (key === "delete") {
      Alert.alert(
        "Delete Connection",
        "Remove this saved connection from the list? This does not delete any data on the server.",
        [
          { text: "Cancel", style: "cancel" },
          {
            text: "Delete",
            style: "destructive",
            onPress: () => props.onDeleteConnection(record),
          },
        ]
      );
    }
  }

  return {
    pinned,
    setPinned,
    busyConnectionId,
    healthResult,
    setHealthResult,
    execute,
  };
}
