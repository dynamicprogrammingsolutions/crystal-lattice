# Development documentation

This section contains guidance for documentation, specifications, requirements,
testing, and Crystal Lattice repository conventions. Package-specific user and
developer documentation remains with its package.

## Documentation guidance

- [Documentation and specification guide](documentation.md): choose a useful
  structure and write documentation, specifications, requirements, testing
  strategies, and verification.
- [Crystal Lattice documentation conventions](crystal-lattice-documentation.md):
  apply the guide to package paths, plugins, tasks, publication, and migration
  in this repository.

## Repository operations

- [Release quick reference](releases.md): CLI, desktop, and mobile release
  commands, publication sequences, and matching VS Code tasks.

## Cross-package specifications

- [Notifications](specifications/notifications/index.md)
- [Action displays](specifications/action-display/index.md)
- [Application runtime reload](specifications/application-runtime-reload/index.md)
- [Sessions actions](specifications/sessions-actions/index.md)
- [Chat transcript navigation](specifications/chat-transcript-navigation/index.md)
- [Bridge connectivity](specifications/bridge-connectivity/index.md)
- [Frontend connection lifecycle and offline continuity](specifications/frontend-connection-lifecycle/index.md)
- [Portable provider implementation](specifications/portable-provider-implementation/index.md)

These specifications define cross-package targets. Their requirements track
implementation and verification, while package developer pages describe the
current implementations.
