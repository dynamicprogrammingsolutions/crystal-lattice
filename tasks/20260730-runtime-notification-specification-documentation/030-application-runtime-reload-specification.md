# Cross-Package Application Runtime Reload Specification

Create the root specification for replacing `AgentApplication` while its
owning process, server listeners, frontend connections, and stable event owner
remain alive.

## Requirements checklist

- [ ] The root reload specification defines user-visible behavior, the reload
  state machine, admission/drain semantics, candidate swap/rollback, cleanup,
  events, and compatibility.
- [ ] The specification explicitly distinguishes application reconstruction
  from full CLI/server process restart.
- [ ] Stable `RLD-*` requirements link implementation and verification across
  Core, Application, plugins, server, CLI, and frontends.
- [ ] Deferred running-request, configuration-writing, credential-hardening,
  and possible refactoring stages are clearly separated from implemented
  behavior.
- [ ] Material cross-package reload decisions are recorded as root decisions.
- [ ] Downstream owner-process variations, including the local mobile runtime
  task, can conform without assuming terminal-process ownership.

Parent Task:
`tasks/20260730-runtime-notification-specification-documentation/000-main.md`

## Proposed artifacts

```text
docs/development/specifications/application-runtime-reload/
├── index.md
├── product-spec.md
├── technical-spec.md
├── requirements.md
└── decisions/
```

## Product behavior to specify

- User intent and expected feedback when configuration or plugins change.
- Reload requested, waiting/draining, completed, and failed states.
- New work being rejected while admitted work finishes.
- No automatic cancellation of admitted work in the implemented stage.
- Server, CLI, bridge, Bonjour, and frontend connections remaining alive.
- Candidate failure retaining the old application and reopening admission.
- Changed plugin revisions being valid after the old runtime is closed.
- Sessions remaining persisted and available after replacement.
- Reload notifications using the notification contract.
- Operator-visible errors and retry behavior.

## Technical behavior to specify

- Owning process, stable owner, shared event store, current replaceable
  application, and retained operations.
- Operation admission/retention boundary.
- Condition/lock and active-operation semantics at a contract level.
- Candidate construction from current config and freshly read environment.
- Validation, swap, replacement listeners, old-application closure, rollback,
  and admission reopening.
- Cleanup ordering for application plugins, async runtime, runtime stores,
  tools, and MCP servers.
- Requested/ready/completed/failed control events and notification relationship.
- HTTP `application_reload_pending` behavior.
- Idempotency/concurrent reload rejection.
- Shutdown while reload is pending.
- Owner-specific integration flexibility for terminal/server and future local
  mobile runtimes.

## Decisions to normalize

- Stable owner outlives `AgentApplication`.
- Reload waits for admitted operations and rejects new operations.
- Full process restart is not required.
- Application-global notifications and event store remain owner-scoped.
- Candidate failure rolls back to the active application.
- Completion is published only after old-runtime cleanup.

## Deferred behavior

Record but do not resolve:

- whether a future reload uses old/new config for steps of an in-flight request;
- cancel-on-reload modes;
- partial config/plugin reload while a request continues;
- deeper `AgentApplication.send_request` self-containment/refactoring;
- secure application-action credential mutation;
- device-specific secret stores for an embedded mobile owner.
- drain-safe interaction response/cancel control operations for future
  wait-only interactions;
- an owner-aware continuation scheduler for future real-suspend interactions.

## Ground-truth references

- `core/python/agent_app/application_owner.py`
- `core/python/agent_app/application_future.py`
- `application/python/agent_terminal_app/__main__.py`
- `application/python/agent_terminal_app/server.py`
- `application/python/agent_terminal_app/terminal_app.py`
- `plugins/application-config-app`
- `core/python/tests/test_application_owner.py`
- `application/python/tests/test_application_reload_owner.py`
- `application/python/tests/test_cli_e2e.py`
- `plugins/mcp-runtime-app/tests/test_application_owner_reload.py`
- `tasks/20260729-staged-application-config-and-full-reload.md`
- `tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`
