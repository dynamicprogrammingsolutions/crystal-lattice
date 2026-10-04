# Agent selection window

`AgentPickerWindow` is the production two-pane window used by both new-session
and switch-agent flows.

## Data flow

1. The existing agents controller loads ordered descriptors.
2. The launch surface stores the live `AgentBackend` in
   `agentPickerCoordinator`.
3. The native window receives only serializable display/selection props.
4. The window reads the coordinated backend and calls
   `AgentsController.ensurePluginsLoaded(agentId)`.
5. The SDK calls the optional `listAgentPlugins(agentId)` backend method and
   caches the safe projection by connection and agent.
6. Submission returns only the connection ID, stable agent ID, mode, and
   optional session ID through `DesktopWindowManager`.

Using the live coordinated backend preserves REST, bridge, and in-process
connections. A serialized direct URL would not represent every supported
transport.

## Compatibility and failure behavior

- Descriptor-less backends retain ID-only fallback rows.
- Backends without `listAgentPlugins` show an unavailable message.
- Preview loading and errors never disable Create or Switch.
- Closing, cancelling, or submitting the native window clears the coordinated
  backend reference.
- Plugin configuration values are never rendered because the public endpoint
  and SDK type contain only identity and state metadata.

The native macOS window opens at 900×620 with a 720×480 minimum so both panes
remain usable.