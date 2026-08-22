# Development documentation

This section contains reusable development standards, Crystal Lattice
repository policy, and target specifications for behavior that spans multiple
independently owned packages.

## Standards

- [Reusable standards](standards/index.md): package-neutral documentation and
  specification rules.
- [Crystal Lattice repository policy](repository/index.md): local paths,
  package profiles, plugin documentation, task workflow, publication, and
  validation.

Package implementation and maintenance documentation belongs under the owning
package's `docs/development/`.

## Cross-package specifications

- [Notifications](specifications/notifications/index.md)
- [Action displays](specifications/action-display/index.md)
- [Application runtime reload](specifications/application-runtime-reload/index.md)
- [Sessions actions](specifications/sessions-actions/index.md)
- [Chat transcript navigation](specifications/chat-transcript-navigation/index.md)
- [Bridge connectivity](specifications/bridge-connectivity/index.md)
- [Bridge access control](specifications/bridge-access-control/index.md)
- [Bridge end-to-end encryption](specifications/bridge-e2ee/index.md)
- [Hosted bridge client experience](specifications/hosted-bridge-client-experience/index.md)

These specifications define targets for portable behavior. Their requirements
track implementation and verification, while package development pages
describe current implementations without redefining the shared contracts.