export function bridgeConnectionErrorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  if (message.includes('does not support HTTP transport protocol v1')) {
    return `${message}. Update the bridge, or select WebSocket in Home → Development Settings for legacy diagnostics.`;
  }
  return message;
}