# Phase 6 — VS Code extension frontend (future)

Parent Task: `tasks/20260129-frontend-sdk/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/030-phase-2-agentbackend-restbackend.md`

Build a Node-targeted frontend (VS Code extension) that uses the same SDK `AgentBackend` + controller patterns.

The key requirement is future flexibility:

- Today: `RestAgentBackend` talks to the Python REST server.
- Future: an `InProcessAgentBackend` (TypeScript `agent-core`/`agent-app`) can be swapped in without changing UI logic.

## Status

- [ ] Not started

## Work checklist

- [ ] Create VS Code extension scaffolding (Node runtime)
- [ ] Use `@crystal-lattice/frontend-sdk` core (no React) or `frontend-sdk-react` if using React webviews
- [ ] Implement `RestAgentBackend` wiring for the extension
- [ ] Identify required REST parity endpoints (feature completions, application config)
- [ ] Add an `InProcessAgentBackend` interface stub (TypeScript) for future port

## Parity notes

- `RestAgentBackend.getCapabilities()` currently reports:
  - `featureCompletions: false`
  - `applicationConfig: false`
- The server parity plan is documented in:
  - `plans/frontend-sdk/05-terminal-and-vscode-alignment.md`
  - `application/python/agent_terminal_app/server_endpoints_parity.md`

## References

- High-level stage definition: `plans/frontend-sdk/04-migration-phases.md`
- Alignment doc: `plans/frontend-sdk/05-terminal-and-vscode-alignment.md`
