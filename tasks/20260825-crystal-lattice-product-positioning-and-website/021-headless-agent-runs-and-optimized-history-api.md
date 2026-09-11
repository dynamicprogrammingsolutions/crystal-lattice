# Add Headless Agent Runs and Optimized History APIs

Provide supported Python, HTTP, frontend-SDK, and command-line contracts for
running configured agents without an interactive frontend, waiting for
asynchronous work, retrieving a structured outcome, and loading a bounded
history projection without transferring long tool results or heavy native
metadata.

## Requirements checklist

- [ ] A Python caller can atomically append one message and run the selected
      session request synchronously through the shared application request
      coordinator, receiving a structured outcome without processing the event
      stream.
- [ ] An asynchronous caller can use a request ID to inspect, wait for, cancel,
      and retrieve the completed structured outcome, with explicit retention
      and restart-authority semantics.
- [ ] The structured outcome distinguishes success, failure, cancellation, and
      interruption and includes redacted error information, the affected
      session, the resulting canonical message range, and final output
      messages.
- [ ] Embedding applications have a supported way to construct and close the
      same effective runtime used by the command-line application, including
      configuration dotenv resolution, application ownership, notifications,
      snapshots, and runtime path handling.
- [ ] HTTP callers can use typed, documented request and response contracts for
      headless submission, status, waiting, results, and cancellation without
      breaking the existing `/send`, `/send_message`, message, status, event,
      or cancellation routes.
- [ ] Python and HTTP callers can request a deterministic, bounded history
      summary or projection that avoids full tool output, provider-native
      history, inline binary data, and unselected heavy metadata while
      preserving canonical message indices and indicating omitted or truncated
      data.
- [ ] The optimized history contract supports the range, role, field, and
      payload-budget behavior needed by headless callers and frontends, with a
      documented way to retrieve any canonical full message on demand.
- [ ] The frontend SDK exposes the optimized history and request-outcome
      contracts, and at least one real frontend or headless controller consumes
      the shared implementation rather than duplicating its projection or wait
      logic.
- [ ] A one-shot CLI command can create or continue a persisted session, accept
      input from a safe argument, file, or stdin path, run synchronously, emit
      plain final output or a stable JSON outcome on stdout, keep diagnostics
      on stderr, and support timeout, cancellation, useful exit codes, and
      ordinary shell-level parallel execution.
- [ ] Optimized history and request-result views are derived from authoritative
      session/request state and never replace, rewrite, or become a second
      authoritative copy of canonical session history.
- [ ] Current user documentation explains Python, HTTP, CLI, synchronous,
      server-backed asynchronous, compact-history, security, persistence, and
      failure behavior using verified examples and expected output.
- [ ] Automated coverage exercises the public Python, real HTTP, frontend-SDK,
      and subprocess CLI boundaries, including long tool results, failures,
      cancellation, timeout, concurrent distinct sessions, and compatibility
      with existing clients.
- [ ] The capability remains distinct from persistent model-facing subagents:
      it does not claim parent-child relationships, vendor-compatible subagent
      tools, replay recovery, or child lifecycle behavior that has not been
      implemented.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`

## Scope and relationship

This is a separately tracked application/API capability discovered while
preparing:

- `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md`.

It is not a dependency of that baseline. Task 020 may use the current
low-level HTTP workflow, record its limitations, and continue while this task
remains incomplete.

The owning implementation scopes are:

- `core/python/agent_app` for coordinated request and result primitives;
- `application/python/agent_terminal_app` for CLI-equivalent runtime
  construction and HTTP/CLI adapters;
- `packages/frontend-sdk` for portable HTTP client and headless-controller
  contracts;
- an existing mobile or desktop consumer only where needed to prove that the
  optimized projection is genuinely reusable by frontends.

## Requirement questions

- Must completed asynchronous request outcomes survive application restart in
  the first delivered version, or may the first version retain completed
  outcomes only for a documented bounded process lifetime?
  - **Recommendation:** persist a minimal bounded request outcome containing
    status, timestamps, session ID, canonical message range, and redacted error
    data, while deriving message bodies from canonical session history. This
    avoids duplicate transcripts and provides a useful foundation for later
    restart-safe subagents.
- Must the first CLI release include a detached server-backed submit/wait
  command, or is a synchronous `run` command that can be placed in the
  background with ordinary shell process control sufficient?
  - **Recommendation:** require the synchronous command plus ordinary shell
    backgrounding first; expose server-backed wait/result through HTTP and add
    a detached CLI form only if it can attach to a clearly selected running
    server without inventing hidden daemon ownership.

## Current behavior and supporting facts

- `AgentApplication.run_session_request(...)` already runs synchronously
  through the shared coordinator and returns `SessionRequestResult`.
- `AgentApplication.start_session_request_with_message(...)` already reserves
  the session, atomically appends a message, starts a background worker, and
  returns a request ID.
- `SessionRequestCoordinator` already enforces application-process
  single-flight behavior per session across terminal and HTTP callers. Distinct
  sessions can run concurrently.
- The background worker currently discards its `SessionRequestResult` after
  publishing events and cleanup. There is no request-ID lookup or wait/result
  API.
- `SessionRequestResult` currently contains the final serialized session and
  final messages but does not retain an explicit outcome state or error event.
- `POST /sessions/{session_id}/send_message` provides atomic asynchronous
  append-and-start. `POST /sessions/request-statuses` reports derived session
  states, and `GET /sessions/{session_id}/messages` supports Python-style
  negative ranges such as `start=-1`.
- The derived session status intentionally has no durable failed or cancelled
  state, and its request ID is absent after active execution ends. Reliable
  failure diagnosis therefore still requires request events.
- Fetching `start=-1` avoids transferring earlier tool results after a normal
  successful text turn, but there is no general role/field projection or
  bounded compact-history contract.
- Tool plugins may already provide concise display metadata such as a
  single-line result. A shared projection can use that data with a bounded
  fallback without changing the stored tool message.
- `TerminalApplication.send_request(...)` demonstrates that a synchronous
  caller can receive final messages without interpreting events, but
  `TerminalApplication` is a frontend façade rather than a complete supported
  embedding factory.
- Constructing `AgentApplication` or `TerminalApplication` directly does not
  automatically reproduce all CLI-owned dotenv, notification-store,
  snapshot-selection, application-owner, and cleanup behavior.
- `--no-tty` runs the interactive console lifecycle against an internal
  prompt-toolkit pipe. It is not a one-shot stdin prompt command.
- The frontend SDK exposes session creation, asynchronous send, status,
  messages, events, and cancellation, while integration helpers and
  controllers still implement their own request-completion waiting patterns.
- The current HTTP OpenAPI document uses broad dictionary payloads for several
  relevant routes, so it does not provide a sufficiently descriptive
  machine-readable external contract.
- Direct local HTTP routes currently have no application authentication
  scheme. Headless documentation must treat loopback or another explicitly
  trusted connection boundary as a prerequisite.
- The planned persistent-subagent work already calls for configured-agent
  resolution, ordinary persisted child sessions, waiting, cancellation,
  request exclusivity, and restart behavior. Its model-facing tool contracts
  and parent-child semantics remain separate from this task.
- Reconstructed Codex `spawn_agent`, `send_input`, `wait`, `close_agent`, and
  `resume_agent` schemas are present as reference material, but no corresponding
  Crystal Lattice subagent runtime was found during the initial inspection.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
   — shared program requirements, handoff rules, output boundaries, and public
   claim constraints.
2. `application/python/agent_terminal_app/AGENTS.md` — terminal, HTTP, mobile,
   bridge, and application-layer ownership and verification rules.
3. `application/python/docs/development/request-execution.md` — current
   coordinator, synchronous/background APIs, result objects, status authority,
   persistence, events, and adapter boundaries.
4. `core/python/agent_app/request_execution.py` and
   `core/python/agent_app/application_future.py` — current start, run,
   cancellation, persistence, and result implementation.
5. `application/python/agent_terminal_app/server.py` — current session,
   message, send, status, event, and cancellation HTTP routes.
6. `core/python/agent_app/session_request_status.py` — current derived status
   states and limitations.
7. `application/python/agent_terminal_app/__main__.py`,
   `application/python/agent_terminal_app/terminal_app.py`, and
   `application/python/docs/terminal.md` — runtime construction, standalone
   commands, terminal façade, and current `--no-tty` behavior.
8. `packages/frontend-sdk/src/backend/backend.ts`,
   `packages/frontend-sdk/src/backend/restBackend.ts`,
   `packages/frontend-sdk/src/chat/chatController.ts`, and
   `packages/frontend-sdk/src/integration/__tests__/README.md` — portable
   frontend contracts, current polling, and real-backend verification.
9. `tasks/20260715-persistent-plugin-subagents/000-main.md` and
   `plugins/codex-tools/reference/codex-cli-tools/README.md` — overlapping
   execution needs and distinct future model-facing subagent behavior.
10. `docs/development/standards/documentation.md`,
    `docs/development/repository/documentation.md`,
    `docs/development/standards/specifications.md`, and
    `docs/development/repository/specifications.md` — documentation,
    specification, audience, and ownership rules.

### Additional references

- `application/python/README.md` and `application/python/docs/index.md` for the
  current user-facing HTTP, CLI, and configuration routes.
- `plugins/docs/notifications-and-action-displays.md` and
  `application/python/docs/development/operations.md` if request outcomes or
  waiting interact with notifications or managed application operations.
- Existing deterministic request-coordinator, HTTP, frontend-backend, CLI
  subprocess, and large-event/message tests identified from the owning
  implementation files.

## Expected outputs

- Supported Python request/run, wait/result, runtime-construction, and
  optimized-history APIs.
- Typed backward-compatible HTTP request, status, wait/result, and optimized
  history contracts.
- Frontend SDK methods/types plus one real consumer of the shared optimized
  history or headless wait behavior.
- A one-shot `crystal-lattice run` command with stable plain-text and JSON
  output contracts.
- Package-owned current user documentation under `application/python/docs/`
  and updated package indexes.
- Updated application request-execution implementation documentation.
- A package-owned target specification and requirements only after its owning
  scope, behavior scope, overlap, and proportional file set are presented and
  approved as required by repository policy.
- Focused automated acceptance evidence at the Python, HTTP, frontend-SDK, and
  CLI subprocess boundaries.

## Scope boundaries

- Do not implement Codex-, Kimi-, Gemini-, Claude-, or other model-facing
  subagent tools in this task.
- Do not add parent-child session metadata, subagent trees, child
  notifications, tool-call replay identity, or subagent restart recovery
  unless separately approved through the persistent-subagent work.
- Do not remove or weaken the event stream; streaming frontends continue to
  use events.
- Do not rewrite canonical session messages or persist a second compact
  transcript.
- The optimized history is deterministic projection, not an LLM-generated
  conversation summary.
- Do not expose provider-native history, credentials, raw inline binary data,
  or unrestricted metadata through a compact response.
- Do not add arbitrary client-selected object traversal if a bounded named
  projection or field allowlist provides a safer stable contract.
- Do not redesign mobile or desktop presentation beyond adopting the shared
  contract in a real consumer where useful.
- Do not change provider, compatibility-tool, bridge, or cloud-agent behavior.
- Do not change `landing_page/src/content/` or publish the capability on the
  website as delivered before implementation and verification are complete.
- Do not run hosted-provider tests or use saved account credentials without
  explicit command-specific approval.
- Do not edit or depend on a developer's personal `~/.crystal` configuration
  or session data in automated tests.

## Execution plan

Status: Draft

Define one request outcome shared by synchronous Python calls, asynchronous
request lookup/wait, HTTP responses, and CLI JSON output. Extend the existing
application-owned coordinator rather than introducing adapter-local workers or
request authority.

Add an atomic synchronous append-and-run operation and a supported
CLI-equivalent runtime factory. Retain enough bounded request state to support
lookup and waiting according to the approved restart contract, deriving final
message bodies from canonical session history wherever possible.

Define a deterministic optimized-history contract with stable original
indices, role-aware concise representations, explicit omission/truncation
metadata, bounded payload behavior, and on-demand access to canonical full
messages. Expose the same semantics through Python, HTTP, and the frontend SDK.

Add a one-shot CLI command on the same application primitives. Keep stdout
machine-safe, diagnostics on stderr, persisted sessions visible, and
cancellation tied to the actual request ID. Preserve all existing HTTP and
frontend behavior while adding the new opt-in contracts.

### Implementation decisions and open questions

- **Optimized-history route:** decide between extending
  `GET /sessions/{session_id}/messages` with a named projection and adding a
  dedicated endpoint.
  - **Recommendation:** use a dedicated deterministic history-projection
    endpoint and leave the canonical full-message response unchanged. This
    gives the compact response its own typed schema, payload budget, and
    evolution path without making `IndexedMessage` conditionally incomplete.
  - Extending the existing endpoint uses fewer routes but creates a response
    union and increases the risk that old callers treat projected messages as
    canonical messages.
- **Projection selection:** decide whether clients choose individual fields or
  named projection profiles.
  - **Recommendation:** define a stable compact profile with a small,
    explicitly allowed optional field set. Avoid arbitrary nested field paths.
    Preserve original indices and include `has_full_content`,
    `content_length`, and truncation/omission reasons.
- **Tool representation:** prefer plugin-provided concise display metadata
  when safe and available; otherwise generate a deterministic bounded fallback
  from tool name, status, and normalized content. Never require loading full
  tool content merely to compute a compact list when stored metadata already
  provides the projection.
- **Range and role semantics:** canonical indices should define the requested
  range before role filtering, and every projected row should retain its
  canonical index. The final contract must make this ordering explicit.
- **Request endpoints:** decide whether to add a resource-oriented submit route
  or retain existing submit routes and add request lookup/wait/result only.
  - **Recommendation:** keep `/send` and `/send_message` as the initial submit
    paths, enrich their typed acknowledgements where backward compatible, and
    add request-ID lookup/wait/result APIs. Add another submit route only if it
    materially improves a coherent resource contract.
- **Wait behavior:** decide between bounded long-polling on request lookup and
  a dedicated wait operation. The contract must include timeout behavior,
  cancellation, stale/unknown IDs, and application-restart authority.
- **Completed outcome retention:** resolve the requirement question above
  before selecting an application-owned store. Do not use the transient event
  stream as the only completed-result authority.
- **Python ownership:** keep coordinated request primitives in `agent_app`;
  place CLI-equivalent config/dotenv/store/runtime construction in the
  terminal application package rather than making provider-neutral core code
  depend on CLI policy.
- **CLI shape:** use a built-in `run` command rather than overloading
  `--no-tty`. Persist a new session by default, allow an existing session
  explicitly, read stdin when selected, and keep plain text and JSON output
  deterministic.
- **Asynchronous CLI:** ordinary shell backgrounding of synchronous runs is
  sufficient for process-owned execution. A command that submits and exits
  must target a selected persistent server and return a handle usable by a
  separate wait/result command.
- **Specification:** this public multi-boundary capability likely justifies an
  application-owned specification. Before creating it, present the proposed
  application ownership, public behavior, relationship to request execution
  and persistent subagents, and proportional file set for approval.

### Documentation

- Add a package-user guide under `application/python/docs/` covering
  first-success Python, HTTP, and CLI examples; expected plain/JSON output;
  optimized history; parallel shell use; cancellation; errors; persistence;
  and the trusted-network boundary.
- Link the guide from `application/python/docs/index.md` and keep the package
  README concise.
- Update
  `application/python/docs/development/request-execution.md` with the current
  outcome, retention, wait, projection, and CLI adapter ownership once
  implemented.
- Update frontend SDK documentation for the new portable methods and headless
  consumer behavior.
- Keep proposed behavior in the approved specification/task until it is
  implemented; current user documentation must not describe target-only
  behavior as available.
- Task 020 may record the delivered capability and evidence after verification
  but must not become the authoritative API documentation.

### Task checklist

- [ ] Confirm request-outcome persistence and CLI asynchronous-scope
      requirement questions.
- [ ] Present and obtain approval for the package specification scope and
      proportional file set if a specification remains justified.
- [ ] Define typed request outcome, status, error, message-range, and retention
      contracts.
- [ ] Define the optimized-history schema, range/role/field semantics, payload
      budgets, omission rules, and full-message fallback.
- [ ] Add the supported CLI-equivalent application runtime factory.
- [ ] Add atomic synchronous append-and-run and asynchronous lookup/wait/result
      application APIs.
- [ ] Expose backward-compatible typed HTTP contracts.
- [ ] Implement the deterministic optimized-history projection in one shared
      owning layer.
- [ ] Add frontend SDK methods/types and migrate one real consumer or headless
      workflow to the shared contract.
- [ ] Add the one-shot CLI command and stable output/exit behavior.
- [ ] Add deterministic Python, HTTP, frontend-SDK, and CLI subprocess
      acceptance coverage.
- [ ] Verify existing event-driven frontend and request-coordinator behavior
      remains compatible.
- [ ] Add current user and implementation documentation with verified examples.
- [ ] Update requirement evidence and any factual handoff consumed by task 020.

### Requirement verification

- **Python synchronous and runtime construction:** a package-user-style test
  opens the supported runtime against a deterministic provider, atomically
  submits one message, receives a successful structured outcome without
  reading events, reloads the persisted session, and closes every owned
  resource without warnings or leaked workers.
- **Asynchronous lifecycle:** real application and HTTP tests submit distinct
  sessions concurrently, query and wait by request ID, retrieve final outcomes,
  and distinguish failure, cancellation, interruption, timeout, unknown ID,
  and same-session busy behavior.
- **Optimized history:** a persisted session containing large tool output,
  provider-native metadata, inline media, ordinary user/assistant messages,
  and plugin display metadata produces a bounded deterministic projection at
  both Python and real HTTP boundaries. Original indices and omission markers
  are correct, full messages remain retrievable, and canonical stored data is
  unchanged.
- **Frontend reuse:** a production frontend adapter/controller obtains the
  optimized projection and request outcome through the frontend SDK, with a
  real backend integration crossing FastAPI and `RestAgentBackend`.
- **CLI:** subprocess tests provide prompts through stdin and a file, verify
  plain and JSON stdout independently from stderr diagnostics, inspect exit
  codes and persisted session IDs, exercise timeout/SIGINT cancellation, and
  run two deterministic distinct-session commands concurrently.
- **Compatibility:** existing `/send`, `/send_message`, status, message, event,
  cancellation, terminal, mobile/desktop adapter, and request-coordinator
  tests continue to pass.
- **Documentation:** every documented command and representative response is
  validated by an automated example or focused acceptance test.

### Additional implementation verification

- Run the focused `core/python` or application-layer request tests selected by
  the implementation owner.
- Run `pytest application/python/tests -q` or an explicitly justified focused
  subset plus affected integration markers.
- Run `npm --workspace @crystal-lattice/frontend-sdk test` and the real-backend
  integration that exercises the new contract.
- Run affected mobile or desktop package tests when a production consumer
  changes.
- Run `git diff --check` and package documentation link validation.
- Treat hosted-provider verification as a separate explicitly authorized
  follow-up; deterministic success is required regardless of hosted access.
