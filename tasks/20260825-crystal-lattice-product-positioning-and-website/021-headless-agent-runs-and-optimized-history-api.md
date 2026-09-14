# Add Local Headless Agent Runs and Optimized History APIs

Provide a supported local Python API and command-line workflow for discovering
configured agents, sending an initial task, observing bounded progress,
receiving a compact structured result, continuing the persisted session with
follow-up messages, and inspecting deterministic compact history without
loading long tool results.

## Requirements checklist

- [x] A package user can open and close a supported local Crystal Lattice
      runtime that discovers the same project-local or user-level
      configuration and related dotenv values needed by the command-line
      application, uses an explicit session root, and releases every resource
      it owns.
- [x] The local Python API lists configured agents and runs either a new
      persisted session selected by `agent_id` or a follow-up in an existing
      persisted session selected by `session_id` through one natural call.
- [x] Each Python run atomically admits the session request, appends its user
      message only after admission succeeds, and executes synchronously
      through the shared application request coordinator.
- [x] Python callers can observe ordered, bounded request, provider, assistant,
      and tool progress without receiving complete tool results by default or
      interpreting events merely to obtain the final answer.
- [x] Every run returns a compact structured result that distinguishes
      success, failure, cancellation, and interruption and includes the
      session ID, request ID, agent ID, final output text, final messages, and
      redacted error information without embedding the complete serialized
      session by default.
- [x] A caller can send a follow-up through the same API and session ID after a
      run completes, and the configured agent receives the persisted prior
      conversation according to the existing session-history contract.
- [x] Distinct sessions can run concurrently through ordinary Python futures
      or shell process control, while existing same-session single-flight
      behavior remains authoritative and a failed admission never appends the
      proposed message.
- [x] Python callers can retrieve a deterministic compact history projection
      with canonical indices, Python-style ranges, role selection, bounded
      content and total payload behavior, concise tool representations, and
      explicit omission or truncation information.
- [x] Python callers can retrieve any selected canonical message in full, and
      compact history remains a derived view that never rewrites or becomes a
      second authority for persisted session history.
- [x] The `crystal-lattice` command can list configured agents, run a new task
      or follow-up, accept exactly one prompt source from an argument, file, or
      stdin, and inspect compact or single-message full history.
- [x] The one-shot CLI emits bounded human-readable progress on stderr, emits
      only final text or one stable JSON result on stdout, provides useful exit
      codes, handles timeout and interrupt cancellation, and supports ordinary
      shell-level parallel execution for distinct sessions.
- [x] Current package-user documentation covers Python and CLI first success,
      configured-agent discovery, progress, results, follow-ups, compact and
      full history, parallel execution, cancellation, configuration and
      persistence, output separation, and concurrency limitations using
      verified examples.
- [x] Automated coverage exercises the public local Python API and real CLI
      subprocess boundaries with deterministic streaming and tools, including
      follow-ups, long tool output, failure, cancellation, timeout, concurrent
      distinct sessions, same-session rejection, clean JSON output, and
      compatibility with existing terminal and request APIs.
- [ ] Configured agents can optionally receive a system-message section that
      accurately tells them how a project running outside Crystal Lattice can
      invoke the Crystal Lattice command, import the supported Python API, use
      the applicable Python interpreter, and find installed documentation.
      Those values come from explicit runtime/configuration variables,
      including any additions needed alongside variables such as
      `BUILTIN_PLUGINS`, and the section is independently enabled or disabled
      in the same manner as task guidance.
- [ ] An explicitly gated real Ollama API test using
      `glm-5.3-flash:cloud` starts an outer configured agent with the access
      guidance enabled, gives it a deliberately non-procedural request to use
      a subagent, and proves that it invokes Crystal Lattice with the same
      config and session root to create and complete a separate configured
      agent session rather than merely claiming delegation.
- [x] The capability remains distinct from persistent model-facing subagents:
      it does not claim parent-child relationships, input sent to a running
      child, vendor-compatible subagent tools, durable detached jobs, replay
      recovery, or child lifecycle behavior that has not been implemented.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`

## Approved scope decisions

- Required delivery is local Python and direct CLI execution. New HTTP
  request/result endpoints are not completion requirements.
- Durable asynchronous request lookup, completed-result retention, and
  restart-safe detached jobs are outside this task. Python callers use ordinary
  futures and shell callers use ordinary background processes around the
  synchronous operation.
- Deterministic compact history remains required at the Python and CLI
  boundaries.
- HTTP exposure of compact history is an optional later adapter over the same
  application-owned projection.
- TypeScript SDK and mobile/desktop changes are outside this task. They should
  be undertaken only with an HTTP projection contract and a frontend design
  for lazy full-message loading.
- The supported local runtime reproduces configuration, dotenv, runtime-path,
  session, snapshot-selection, notification, and cleanup behavior needed for
  correct local requests. It does not reproduce HTTP server, Bonjour, bridge,
  profile, or managed live-reload lifecycles.
- The approved package-owned specification scope is
  `application/python/docs/development/specifications/headless-agent-runs/`
  with `index.md`, `technical-spec.md`, and `requirements.md`.
- External-project access instructions are a required second phase. They must
  be investigated and planned separately only after direct Python API, CLI,
  and compact-history acceptance tests pass. Their implementation is not
  authorized until that follow-on plan is presented and approved.

## Scope and relationship

This is a separately tracked application capability discovered while
preparing:

- `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md`.

It is not a dependency of that baseline. Task 020 may use the current
low-level HTTP workflow, record its limitations, and continue while this task
remains incomplete.

The owning implementation scopes are:

- `core/python/agent_app` for coordinated synchronous message-and-run
  primitives, structured outcomes, progress observation, and reusable compact
  history projection;
- `application/python/agent_terminal_app` for local runtime construction,
  package-user convenience methods, CLI command parsing, progress rendering,
  output separation, signal handling, and exit behavior.

The public convenience API belongs to the `crystal-lattice-cli` application
package because it resolves product configuration and runtime paths. The
provider-neutral `agent_app` layer continues to own request and session
mechanics used by every adapter.

## Current behavior and supporting facts

- `AgentApplication.run_session_request(...)` already executes synchronously
  through `SessionRequestCoordinator`, publishes public events, persists
  checkpoints, and returns `SessionRequestResult`.
- `AgentApplication.start_session_request_with_message(...)` already reserves
  a session and atomically appends a message for background execution.
  Synchronous execution has no equivalent atomic append-and-run operation.
- `SessionRequestCoordinator` already enforces process-local single-flight
  behavior per session. Distinct sessions can run concurrently.
- The synchronous coordinator accepts an internal checkpoint callback but has
  no public progress observer. A caller that wants progress must currently run
  background work and poll the event store or use the lower-level generator.
- `SessionRequestResult` contains the complete serialized final session and
  final messages but no explicit success, failure, cancellation, interruption,
  or error fields. Fatal errors and cancellation are currently visible through
  events rather than the result.
- A direct application-layer workflow currently requires a caller to create or
  load a session, use the returned core to add a message, save it, and then run
  the request. Repeating those steps for a follow-up is functional but not a
  natural public task API, and append followed by run is not atomic.
- `TerminalApplication.send_request(...)` demonstrates direct final-result
  collection, while its mutable current-session behavior and prompt-toolkit
  concerns make it a frontend façade rather than the intended embedding API.
- `AgentApplication` can be constructed directly with a config and session
  root, but command-line-owned config search, dotenv collection, runtime
  layout, notification-store, snapshot-selection, and cleanup wiring is not a
  supported reusable factory.
- The current command has server and interactive terminal modes.
  `--no-tty` still runs the prompt-toolkit lifecycle against an internal pipe;
  it is not a one-shot task command.
- The CLI configures core logging before application startup, but current
  startup and plugin output is not guaranteed to preserve machine-clean
  stdout. The one-shot command needs an explicit stdout/stderr boundary and
  regression coverage.
- Interactive `/list short` already renders concise tool history using
  `metadata.display.single_line` when available and bounded fallbacks
  otherwise. This behavior is presentation-only and has no reusable Python
  projection contract.
- Full session serialization and the ordinary message APIs can include long
  tool content, provider-native metadata, and multipart data. A compact caller
  should not need those fields merely to identify prior turns or results.
- Existing frontend controllers load complete `IndexedMessage` records and
  collapse tool output only after transport. Using a compact HTTP response
  would also require a projected frontend type, lazy full-message retrieval,
  mixed projected/full reconciliation, and UI loading behavior; a TypeScript
  type-only change would not provide the optimization.
- The deterministic streaming provider is the appropriate local acceptance
  fixture. `config_echo_app.json` uses an echo provider whose streaming path
  does not produce a finalized assistant message and must not be treated as
  evidence for the new streaming-result contract.
- Request coordination is application-process local. Distinct direct CLI
  processes should use distinct sessions; concurrent writers to one persisted
  session across processes are not made safe by this task.
- Planned persistent-subagent work overlaps in configured-agent resolution,
  persisted sessions, waiting, and cancellation, but its model-facing tools,
  parent-child relationships, mid-run input, detached lifetime, and restart
  semantics remain separate.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
   — shared program requirements, handoff rules, output boundaries, and public
   claim constraints.
2. `application/python/agent_terminal_app/AGENTS.md` — application-layer,
   terminal, CLI, HTTP, and verification ownership.
3. `application/python/docs/development/request-execution.md` — current
   coordinator, synchronous/background APIs, result objects, persistence,
   events, and adapter boundaries.
4. `core/python/agent_app/request_execution.py` and
   `core/python/agent_app/application_future.py` — current request admission,
   execution, publication, cancellation, persistence, and cleanup.
5. `application/python/agent_terminal_app/__main__.py`,
   `application/python/agent_terminal_app/runtime_layout.py`,
   `application/python/agent_terminal_app/terminal_app.py`,
   `application/python/docs/configuration-placeholders.md`, and
   `application/python/docs/terminal.md` — config/runtime resolution,
   terminal façade, CLI lifecycle, and current progress/history behavior.
6. `application/python/agent_terminal_app/event_rendering.py`,
   `docs/api/events.md`, and `core/python/agent_app/events.py` — current event
   shapes, compact tool rendering, and transient event storage.
7. `core/python/plugins/deterministic_stream_provider.py`,
   `application/python/tests/test_session_request_coordinator.py`,
   `application/python/tests/test_terminal_compact_tool_rendering.py`, and
   CLI subprocess tests — deterministic fixtures and existing verification
   patterns.
8. `tasks/20260715-persistent-plugin-subagents/000-main.md` and
   `plugins/codex-tools/reference/codex-cli-tools/README.md` — overlapping
   execution mechanics and explicitly separate future subagent contracts.
9. `docs/development/standards/documentation.md`,
   `docs/development/repository/documentation.md`,
   `docs/development/standards/specifications.md`, and
   `docs/development/repository/specifications.md` — documentation,
   specification, audience, ownership, and evidence rules.

### Optional follow-up references

- `application/python/agent_terminal_app/server.py` for a later compact-history
  HTTP adapter.
- `packages/frontend-sdk/src/backend/backend.ts`,
  `packages/frontend-sdk/src/backend/restBackend.ts`,
  `packages/frontend-sdk/src/chat/chatController.ts`, and production message
  components for a separately approved frontend transport optimization.

## Expected outputs

- An approved application-owned specification and live requirements under
  `application/python/docs/development/specifications/headless-agent-runs/`.
- A coordinated atomic synchronous append-and-run primitive with structured
  status/error outcome and progress observation.
- A supported context-managed local runtime and natural Python methods for
  agent discovery, initial runs, follow-ups, compact history, full-message
  retrieval, and cancellation.
- One application-owned deterministic compact-history projection shared by
  the Python convenience API and CLI.
- Built-in `crystal-lattice agents`, `crystal-lattice run`, and
  `crystal-lattice history` commands with stable text/JSON and progress
  behavior.
- Package-owned current user documentation under `application/python/docs/`,
  concise package/index routes, and updated request-execution maintainer
  documentation.
- Deterministic acceptance evidence at the Python package-user and CLI
  subprocess boundaries plus compatibility evidence for existing request and
  terminal behavior.
- After the direct runtime is verified, an approved follow-on design and
  implementation for opt-in system guidance that exposes the installed CLI,
  Python API, interpreter, and documentation to agents working in external
  projects.

## Optional later work

The following work may reuse the delivered primitives but does not block this
task and must not be silently added during execution:

- an HTTP compact-history endpoint;
- typed HTTP request-result resources, long polling, or durable completed
  outcomes;
- frontend SDK projected-message methods;
- frontend lazy full-message loading and mobile/desktop adoption;
- server-backed detached CLI submit/wait/result commands.

## Scope boundaries

- Do not implement HTTP, frontend SDK, mobile, or desktop behavior in this
  task.
- Do not add a background result registry, durable request-result store,
  restart recovery, or detached job ownership.
- Do not implement Codex-, Kimi-, Gemini-, Claude-, or other model-facing
  subagent tools.
- Do not add parent-child session metadata, subagent trees, child
  notifications, mid-run input, tool-call replay identity, or child restart
  recovery.
- Do not remove or weaken the event stream; lower-level and event-driven
  frontends continue to use it.
- Do not rewrite canonical session messages or persist a second compact
  transcript.
- Compact history is deterministic projection, not an LLM-generated
  conversation summary.
- Do not expose provider-native history, credentials, raw inline binary data,
  or unrestricted metadata through compact results.
- Do not add arbitrary client-selected nested field traversal when a bounded
  named projection is sufficient.
- Do not redesign the interactive terminal beyond refactoring shared
  application/runtime or compact-rendering logic needed by the new commands.
- Do not claim cross-process same-session single-flight. Document the
  process-local boundary and require distinct sessions for ordinary parallel
  CLI execution.
- Do not change provider, compatibility-tool, bridge, cloud-agent, or website
  behavior.
- Do not change `landing_page/src/content/` or publish this capability as
  delivered before implementation and verification are complete.
- Do not run hosted-provider tests or use saved account credentials except for
  the explicitly approved `glm-5.3-flash:cloud` Ollama acceptance test, or
  another command-specific approval.
- Do not edit or depend on a developer's personal `~/.crystal`
  configuration, auth state, or sessions in automated tests.

## Execution plan

Status: Approved

First define the application-owned target and stable requirements for a local
headless runtime, compact run result, bounded progress, follow-ups, and compact
history. Keep the target at the application package because its public
convenience layer resolves Crystal Lattice config, dotenv, runtime-layout, and
session policy; link the lower-level `agent_app` request coordinator as the
shared implementation boundary.

Extend synchronous coordinated execution rather than wrapping the current
background thread API. Admission, optional message append, request execution,
event publication, persistence checkpoints, and cleanup will remain one
operation. Add structured outcome classification and an observer path while
preserving existing `run_session_request(...)` and background APIs.

Build one context-managed local runtime over those primitives. It will resolve
the selected config and session root, construct the required stores, expose
agent discovery and one `run(...)` operation for both new and existing
sessions, normalize bounded progress, provide compact result text, and own
cleanup. The CLI will call this runtime rather than reproducing request logic.

Add a deterministic compact-history projector below both Python and CLI
adapters. It will retain canonical indices, select a Python-style range before
role filtering, use a named compact schema, prefer safe plugin display
metadata for tools, enforce per-entry and total budgets, and expose full
canonical message retrieval separately.

Add built-in one-shot CLI commands using the existing command-dispatch
structure without converting the entire CLI to a new parser architecture.
Runtime construction and request execution will happen with application and
plugin diagnostics routed away from stdout. Human progress goes to stderr;
text and JSON final results go to stdout after completion. Timeout and SIGINT
will cancel the actual request through the application cancellation path and
return stable result/exit behavior.

Verify the shared mechanics first, then the local runtime, compact history,
and real subprocess commands. Update user and maintainer documentation only
with behavior established by tests. HTTP and frontend consumers remain
explicit follow-up work.

After all direct Python API, compact-history, and CLI acceptance tests pass,
stop before changing system-message configuration. Investigate the existing
runtime variable and optional section mechanisms, write a separate detailed
plan for exposing the CLI, Python API, interpreter, and installed
documentation to agents in external projects, and obtain approval for that
material configuration/system-message contract. Completion of that approved
follow-on implementation remains required for this task.

### Implementation decisions and open questions

- **Public local-runtime API:** introduce a small application-package façade
  provisionally named `LocalAgentRuntime`, opened by
  `open_runtime(...)` and re-exported lazily from `agent_terminal_app`.
  - `open_runtime(...)` is a context manager and supports explicit config and
    session paths.
  - With no explicit config, it follows the existing local-then-user config
    search. Missing config should produce a clear error rather than silently
    starting an HTTP/server lifecycle.
  - Runtime-layout defaults may still create the same default config currently
    created by the CLI when that behavior is already part of path resolution;
    the technical specification must state the selected behavior exactly.
- **Natural run method:** use one
  `run(prompt, *, agent_id=None, session_id=None, ...)` method.
  - Exactly one of `agent_id` and `session_id` is required.
  - `agent_id` creates a persisted session; `session_id` continues an existing
    session and derives its configured agent.
  - Accept optional message metadata, multipart content, request overrides,
    streaming selection, timeout, and progress callback without exposing the
    internal core/base-config tuple.
- **Coordinated primitive:** add
  `AgentApplication.run_session_request_with_message(...)` backed by a
  `SessionRequestCoordinator.run(...)` message option. Do not implement it as
  a separate append followed by the existing run call.
- **Progress representation:** expose a bounded immutable `RunProgress` record
  from the convenience runtime. Keep raw public event dictionaries available
  through lower-level application APIs.
  - Progress records should identify session/request, kind, phase, tool name,
    and bounded human text where applicable.
  - Do not include complete tool-result content, provider-native payloads, or
    binary/multipart bodies.
  - Progress callbacks execute synchronously with request observation and must
    return promptly. The technical specification will define callback-failure
    behavior before implementation; the recommendation is to cancel and
    surface callback failure rather than silently ignore it.
- **Structured outcomes:** extend the coordinated result with explicit status
  and redacted error detail while preserving its existing fields for
  compatibility. Convert it to a smaller immutable `AgentRunResult` at the
  convenience boundary.
  - `AgentRunResult` excludes `final_session`.
  - `output_text` is derived deterministically from final assistant messages;
    JSON retains all final messages.
  - A request ending without a successful final response, explicit error, or
    cancellation is `interrupted`.
- **Cancellation and timeout:** retain application request IDs as the
  cancellation authority. A timeout schedules cooperative cancellation; a
  CLI interrupt cancels the known active request and waits for bounded cleanup
  before choosing its exit code. Provider calls that cannot cooperate may
  finish their current blocking operation, which must be documented.
- **Concurrency:** do not add a task pool or async result handle. Document
  `concurrent.futures` for Python and shell background jobs for CLI.
  Same-session requests continue to reject admission; different direct CLI
  processes must use distinct sessions.
- **Compact-history schema:** use one named compact projection rather than
  arbitrary field paths.
  - Apply canonical range selection before role filtering.
  - Preserve each original message index.
  - Include role, bounded display content, original content length,
    truncation/omission indicators, and small role-specific identifiers such
    as tool name/status where available.
  - Prefer `metadata.display.single_line` for tools and use a deterministic
    whitespace-normalized fallback.
  - Enforce per-message and total character budgets with deterministic
    ordering and explicit omission counts.
  - Provide full-message lookup by canonical index.
- **CLI commands:** reserve built-in `agents`, `run`, and `history` command
  names.
  - `run` accepts exactly one of `--prompt`, `--prompt-file`, and `--stdin`.
  - `run` accepts exactly one of `--agent` and `--session`.
  - `--format text|json` defaults to text.
  - `history` supports compact ranged output and one full message by index;
    its JSON schema mirrors the Python representation.
  - Global runtime/config flags retain their existing placement unless focused
    usability tests demonstrate that command-local aliases are necessary.
- **Machine-clean output:** route application logs, direct startup prints, and
  progress away from final stdout during one-shot commands. Fix a shared
  unconditional startup print when required, and add subprocess assertions
  rather than relying on logging level alone.
- **Runtime ownership:** use the stores needed by local execution and
  compatible session inspection, including filesystem snapshot selection and
  a non-warning application notification store. Do not construct an HTTP
  server, bridge/Bonjour integrations, project profile, or managed reload
  owner.
- **Specification:** create the approved three-file package specification
  before implementation. Use stable `HLR-###` requirement IDs and link the
  active task only from development tracking contexts.
- **External-project access planning gate:** add its required outcome to the
  specification and requirements now, but defer its technical contract. After
  the direct runtime and CLI acceptance suite passes, inspect configuration
  variables, runtime layout, packaged interpreter discovery, documentation
  installation paths, and optional system-message sections such as task
  guidance. Present a separate plan and return for approval before implementing
  that phase.

### Documentation

- Create
  `application/python/docs/development/specifications/headless-agent-runs/index.md`
  for target scope, ownership, relationships, user workflows, goals, and
  non-goals.
- Create
  `application/python/docs/development/specifications/headless-agent-runs/technical-spec.md`
  for Python types and methods, configuration resolution, request and progress
  flow, result/error/cancellation semantics, compact-history schema and
  budgets, CLI syntax/output/exit codes, concurrency, compatibility, security,
  and verification.
- Create
  `application/python/docs/development/specifications/headless-agent-runs/requirements.md`
  with stable `HLR-###` IDs and separate implementation, verification,
  documentation, and evidence state.
- Add `application/python/docs/headless-agent-runs.md` as the current
  package-user guide when implementation is available. Include tested first
  success for Python and CLI, progress callbacks/output, follow-ups, Python
  futures, shell background jobs, compact/full history, cancellation,
  configuration discovery, persistence, and process-local concurrency limits.
- Link the user guide from `application/python/docs/index.md` and keep
  `application/python/README.md` to a concise introduction and link.
- Link the specification from
  `application/python/docs/development/index.md`.
- Update `application/python/docs/development/request-execution.md` to map
  atomic synchronous message execution, progress observation, structured
  outcome classification, local runtime ownership, and compact projection to
  current code without redefining the specification.
- Update `application/python/docs/terminal.md` only where the new one-shot
  commands need a concise command reference or a link to the focused guide.
- Keep all proposed behavior out of current package-user and implementation
  pages until the corresponding code and verification exist. Do not add
  frontend, HTTP, or website claims in this task.

### Task checklist

- [x] Create the approved application-owned specification, technical
      specification, and `HLR-###` requirements before implementation.
- [x] Define compatible coordinated status, error, progress-observer, and
      atomic synchronous message-and-run contracts.
- [x] Implement and unit-test atomic synchronous message admission,
      event/progress observation, outcome classification, timeout
      cancellation, and cleanup.
- [x] Define and unit-test the named compact-history schema, range/role
      semantics, budgets, tool previews, omission metadata, and full-message
      lookup.
- [x] Extract supported local config/dotenv/runtime-path construction and
      implement the context-managed local runtime.
- [x] Implement and test natural Python agent discovery, new runs, follow-ups,
      compact results, progress callbacks, cancellation, history, and ordinary
      concurrent distinct-session use.
- [x] Add built-in `agents`, `run`, and `history` CLI commands as thin runtime
      adapters.
- [x] Implement and test stdin/file/argument validation, compact stderr
      progress, clean text/JSON stdout, exit codes, timeout, and SIGINT.
- [x] Add real subprocess tests for initial runs, follow-ups, history,
      long-tool-output bounds, failures, cancellation, and two concurrent
      distinct sessions.
- [ ] After the direct Python API, compact-history, and CLI acceptance tests
      pass, investigate and present a separate Draft plan for external-project
      CLI/API/interpreter/documentation variables and opt-in system guidance.
- [ ] After separate approval, implement and verify the external-project
      access variables, optional system-message section, packaging behavior,
      and current documentation.
- [x] Run existing request-coordinator, terminal, config/dotenv, compact-tool,
      and CLI compatibility coverage.
- [x] Add current package-user and implementation documentation with tested
      examples and update package indexes.
- [x] Update specification requirements with implementation, verification,
      documentation, and delivery evidence.
- [ ] Update this task throughout execution and add immutable completion notes
      only after all required evidence is available.

### Requirement verification

- **Local runtime and agent discovery:** a package-user test opens the public
  runtime with isolated local and user config layouts, verifies config and
  dotenv precedence plus the listed agents, confirms the chosen session root,
  and closes without leaked application, plugin, async-runtime, notification,
  or environment-overlay resources.
- **Atomic Python run and structured result:** a deterministic streaming
  provider test creates a new persisted session through `run(...)`, observes
  bounded progress, receives a successful compact result without reading raw
  events, and confirms the stored assistant result. Deterministic failure,
  cancellation, and incomplete generators produce the specified statuses and
  redacted error shape.
- **Follow-up:** a second `run(...)` using the first result's `session_id`
  atomically appends its prompt, sees the prior turn through the configured
  provider history, persists its response, and returns the same session and
  agent identity.
- **Concurrency and admission:** two deterministic distinct-session calls
  overlap through `ThreadPoolExecutor` and complete successfully. Two calls to
  one session demonstrate existing single-flight rejection and prove that the
  losing message was not appended.
- **Bounded progress and results:** a deterministic tool emits long and
  streaming output. Progress and `AgentRunResult` stay within their documented
  contracts, use concise tool display metadata when present, omit full tool
  output and native/binary payloads, and leave full canonical state persisted.
- **Compact and full history:** a session containing user, assistant, system,
  long tool, provider-native metadata, inline multipart, and display metadata
  produces deterministic compact rows with correct indices, range-before-role
  semantics, per-row and total budgets, truncation/omission markers, and no
  restricted fields. Full lookup returns the unchanged selected canonical
  message.
- **CLI first run and follow-up:** real subprocess tests invoke the installed
  source entry point with prompt argument, file, and stdin; parse clean text
  and JSON stdout; observe bounded stderr progress; reuse the returned session
  for a follow-up; and inspect compact plus one full history message.
- **CLI control and parallelism:** subprocess tests verify success, usage,
  provider/application failure, timeout, and SIGINT exit behavior. Two
  commands against distinct sessions overlap through shell/process control and
  finish with independent parseable results.
- **External-project access:** after its separately approved plan is
  implemented, source-install and bundled-layout tests verify that an enabled
  system-message section supplies accurate executable, import, interpreter,
  and documentation guidance from configured runtime variables, that the
  section can be disabled independently like task guidance, and that no
  developer-specific absolute paths or unavailable commands are advertised.
- **Compatibility:** existing coordinated background start, synchronous run,
  event publication, terminal rendering, interactive `/list short`, config
  resolution, session persistence, and application-close tests continue to
  pass without HTTP or frontend contract changes.
- **Documentation:** Python and CLI examples are exercised by focused tests or
  equivalent subprocess fixtures; package and development indexes link every
  new authored page; current docs contain no target-only claims or internal
  task vocabulary.

### Additional implementation verification

- Run focused coordinator and application tests while implementing:
  `pytest application/python/tests/test_session_request_coordinator.py -q`
  plus new local-runtime and compact-history test modules.
- Run focused terminal/CLI compatibility tests, including
  `test_terminal_application.py`, `test_terminal_compact_tool_rendering.py`,
  `test_cli_environment_isolation.py`, and the new one-shot subprocess suite.
- Run the application package default suite:
  `pytest application/python/tests -q`.
- Run the relevant non-API integration subset with its marker explicitly
  enabled so subprocess tests are collected rather than reported as skipped.
- Run focused core application-layer tests if shared `agent_app` contracts or
  exports change.
- Run Ruff on changed Python sources and tests, and use the repository's
  existing type-check command where the changed public types are covered.
- Run `python docs_site/scripts/prepare_mkdocs_site.py` and the appropriate
  MkDocs link/build validation for new authored documentation without editing
  generated output.
- Run `git diff --check` and inspect the final diff for accidental HTTP,
  frontend, generated-output, personal-config, credential, or unrelated
  changes.
- Hosted-provider verification remains a separate, command-specific,
  user-authorized follow-up and is not required for deterministic acceptance.

## Implementation Notes

- 2026-09-14: The user approved the local Python/CLI and compact-history plan
  and authorized implementation. The user also added the required
  external-project access outcome. That outcome is sequenced after direct
  Python/CLI acceptance and remains behind its separately approved follow-on
  planning gate.
- 2026-09-14: Created the approved three-file application-owned specification
  with `HLR-001` through `HLR-070` and linked it from the application
  development index. `HLR-060` records the required external-project guidance
  outcome without preempting its later planning gate.
- 2026-09-14: Implemented and documented the direct local runtime, atomic
  synchronous message-and-run operation, bounded progress and structured
  outcome, compact/full history, and `agents`, `run`, and `history` commands.
  Dedicated Python tests passed, dedicated real subprocess tests passed, the
  Core default suite passed with 541 tests and one expected failure, and the
  application default suite passed with 442 tests and one skip. Pyright and
  changed-file Ruff checks passed.
- 2026-09-14: Documentation preparation and a normal MkDocs build passed. A
  strict MkDocs build remains blocked by ten repository-existing warnings in
  unrelated plugin links, Core docstring indentation, and generated-reference
  cross-references; no warning identified the new application pages or links.
  The direct implementation and acceptance gate is complete, so the required
  `HLR-060` follow-on may now be investigated and planned.
- 2026-09-14: The user approved the external-project access follow-on plan,
  corrected the unsupported pip/pipx assumption to source and bundled-Python
  distribution paths, and added `HLR-061`: a gated real Ollama
  `glm-5.3-flash:cloud` same-config delegation test that requires evidence of
  an actual separately persisted worker session.

## External-project access follow-on plan

Status: Approved

The direct Python API and CLI acceptance gate is complete. This follow-on
implements `HLR-060`: an independently enabled system-message section that
gives configured agents an accurate, portable way to call Crystal Lattice from
a project that was launched outside Crystal Lattice.

Extend `RuntimeLayout` with an application-documentation path and derived
runtime-access values. Expose those values through the same explicit
application environment overlay used for `BUILTIN_PLUGINS`, so config
placeholder resolution and request-time system-message helpers see one
authoritative runtime identity.

Use a JSON argument-vector value as the canonical CLI invocation rather than a
prequoted shell string. It includes the active config and session root so an
agent launched from another project cannot accidentally select that project's
config or a different session store. A request-time helper can render the
vector with platform-appropriate quoting for the system message. Source
checkouts use the active interpreter with `-m agent_terminal_app`;
bundled-Python archives use their packaged interpreter. Optimized frozen
binaries expose their executable for CLI use but must not falsely advertise an
importable Python SDK.

Add a `CRYSTAL_LATTICE_ACCESS` variable to each maintained default system
message template. Its variable-level runtime helper will both render the
section and contribute an **Include Crystal Lattice Access Guidance** checkbox
backed by `include_crystal_lattice_access`, defaulting to false. The section
will identify the CLI command, configured-agent discovery, initial/follow-up
commands, interpreter and `agent_terminal_app` import when available, local
documentation when packaged, and the stable public documentation URL.

Keep existing user configuration immutable. New default configurations gain
the opt-in section; existing configs can adopt the documented variable and
template entry explicitly. Do not inject a hidden prompt section from
application code or enable it globally.

Stage current application user documentation into supported runtime layouts.
Fall back to the public documentation URL when no stable local docs directory
exists. Verify source, bundled-Python, and optimized-layout capability
reporting deterministically, then run the separately gated real Ollama
delegation test.

### Implementation decisions and open questions

- **Canonical runtime variables:** add:
  - `CRYSTAL_LATTICE_CLI_ARGV_JSON`: JSON array for the authoritative command
    prefix, including `--config` and `--sessions-dir` for the active runtime;
  - `CRYSTAL_LATTICE_CONFIG`: absolute active config path;
  - `CRYSTAL_LATTICE_SESSIONS`: absolute active session root;
  - `CRYSTAL_LATTICE_PYTHON`: absolute interpreter path only when arbitrary
    Python and the installed API are available;
  - `CRYSTAL_LATTICE_PYTHON_API_MODULE`: `agent_terminal_app` only when that
    interpreter can import it;
  - `CRYSTAL_LATTICE_DOCS`: absolute local application-docs directory when it
    exists;
  - `CRYSTAL_LATTICE_DOCS_URL`: stable public application documentation URL.
  These values are runtime-owned overrides like `BUILTIN_PLUGINS`; inherited
  process values do not replace a known current runtime identity.
- **Command representation:** JSON argv is recommended over one shell command
  string because paths may contain spaces and quoting differs across POSIX and
  Windows. The system-message helper uses `shlex.join` on POSIX and
  `subprocess.list2cmdline` on Windows.
- **Source checkout:** use `[sys.executable, "-m", "agent_terminal_app",
  "--config", <active-config>, "--sessions-dir", <active-session-root>]`.
  This invokes the same source/importable application as the current process
  even when a `crystal-lattice` wrapper on `PATH` belongs to another
  environment.
- **Bundled-Python archive:** use the manifest's packaged interpreter and
  module invocation. Point local docs at the staged
  `application/python/docs` directory already copied into the archive.
- **Optimized PyInstaller bundle:** expose `[sys.executable]` as the CLI
  command and stage readable application docs, but omit Python/API variables
  because the frozen executable is not a general Python interpreter.
  - **Recommendation:** report this limitation accurately in the optional
    section rather than expanding the optimized bundle into a second
    bundled-Python distribution. Approval of this plan accepts that
    layout-specific fallback.
- **Distribution boundary:** pip and pipx installation are not supported
  product paths. Source checkouts and bundled-Python distributions expose
  their applicable local docs; the public docs URL remains available as a
  portable fallback.
- **Toggle:** use `include_crystal_lattice_access`, label it **Include Crystal
  Lattice Access Guidance**, and default it to false. It remains independent
  from `include_tasks`.
- **Prompt ownership:** add one named `CRYSTAL_LATTICE_ACCESS` variable and
  placeholder to maintained Codex, Qwen, Gemini, Grok, Kimi, and Claude
  templates and their default-config mixins. Use one shared helper rather than
  embedding vendor-specific command prose.
- **Section content:** keep it operational and bounded. It may show list/run/
  follow-up/history examples and Python import syntax, but must state that
  these are local synchronous runs, not persistent model-facing subagents.
- **Existing configs:** do not mutate already created
  `~/.crystal/config.json` or project configs. Document the explicit opt-in
  configuration needed to adopt the section.
- **Security:** expose executable/module/docs locations only. Do not include
  credentials, resolved provider keys, arbitrary environment values, plugin
  cache contents, or writable auth paths.
- **Real Ollama delegation acceptance:** add an opt-in test marked
  `integration`, `api`, and `ollama` using `glm-5.3-flash:cloud`.
  - Build one isolated config containing an outer orchestrator and a separate
    worker agent, both using the real Ollama provider path.
  - Enable `include_crystal_lattice_access` only for the outer request so the
    worker does not recursively delegate.
  - Run from an external temporary project containing a unique marker and give
    the outer model a deliberately sparse prompt such as “Ask a subagent for
    the project marker and report its answer.” Do not name commands, flags,
    agent IDs, files, or implementation steps in the prompt.
  - Verify an additional persisted worker session appears in the same
    configured session root, completes, contains the marker in its result, and
    is reflected in the outer response/tool history. A textual claim without a
    child session fails.
  - Gate the test with an explicit environment opt-in and local Ollama/cloud
    authentication availability so default and credential-free suites never
    invoke it.

### Documentation

- Update the headless-agent-runs technical specification with the approved
  runtime variable, layout fallback, toggle, section, and compatibility
  contract.
- Update `HLR-060` implementation/evidence state only after all source and
  packaged-layout checks pass.
- Add a focused section to
  `application/python/docs/headless-agent-runs.md` explaining how users enable
  the guidance, what an agent receives, layout limitations, and how existing
  configs adopt it.
- Update `application/python/docs/configuration-system-messages.md` with the
  reusable variable-level helper/toggle pattern.
- Update application runtime/distribution maintainer documentation only where
  local docs and access-variable staging become current behavior.
- Do not add website, HTTP, TypeScript, mobile, desktop, or subagent claims.

### Task checklist

- [ ] Extend the approved technical specification for `HLR-060` before code
      changes.
- [ ] Define and test runtime-access derivation for source,
      Python-install/bundled-Python, and optimized frozen layouts.
- [ ] Add application-docs layout/staging where a local path is supported.
- [ ] Add the shared opt-in access-section renderer and UI-schema helper.
- [ ] Add the variable and placeholder to every maintained default vendor
      system-message configuration without changing the default compiled
      prompt.
- [ ] Add deterministic default-config tests for disabled/enabled section
      behavior across configured vendor agents.
- [ ] Add source, bundled-Python builder, and optimized-layout tests for
      executable, interpreter, API, docs, quoting, and unavailable-capability
      behavior.
- [ ] Add and explicitly run the gated real Ollama
      `glm-5.3-flash:cloud` same-config delegation acceptance test.
- [ ] Update current user, system-message configuration, runtime, and
      distribution documentation.
- [ ] Run focused system-message, runtime-layout, package-builder, direct
      Python/CLI, Core, application, and documentation checks.
- [ ] Complete `HLR-060`, the remaining parent requirement, task evidence, and
      immutable completion notes.

### Requirement verification

- **Source runtime:** an isolated source-layout test resolves an argv vector
  whose interpreter imports `agent_terminal_app`, points at existing local
  application docs, and renders a correctly quoted command without personal
  paths in fixture expectations.
- **Bundled-Python runtime:** package-builder tests resolve the staged launcher
  identity, packaged interpreter, import module, and staged docs relative to a
  relocated package root. The command remains valid after relocation.
- **Optimized runtime:** staged-layout tests expose the frozen executable and
  local/public docs while omitting claims that the executable is a general
  Python interpreter or import host.
- **Toggle and compiled prompts:** default-config integration tests find the
  new checkbox, prove it defaults off independently from task guidance, and
  compile the bounded access section for Codex, Qwen, Gemini, Grok, Kimi, and
  Claude when enabled.
- **Accuracy and safety:** the compiled section's CLI argv round-trips through
  JSON, its referenced local paths exist for layouts that advertise them, its
  interpreter imports the public API where advertised, and it contains no
  credential values or unrestricted environment dump.
- **Real delegation:** with the explicit API gate enabled, the outer
  `glm-5.3-flash:cloud` agent receives only a sparse delegation request and the
  opt-in guidance, invokes the advertised CLI against the same config/session
  root, and leaves a separately persisted completed worker session containing
  the external project's marker. The outer session also records the tool
  invocation and reports the worker's result.
- **Compatibility:** disabled compiled prompts retain their previous content;
  existing direct Python/CLI, default-system-message, runtime-layout,
  distribution, and config UI tests continue to pass.
- **Documentation:** enabled/disabled examples and layout limitations match
  deterministic tests, and documentation preparation/build finds no new broken
  links.

### Additional implementation verification

- Run the feature-system-message unit and default-config integration suites.
- Run `application/python/tests/test_runtime_layout.py`,
  `test_python_runtime_package_builder.py`, optimized-bundle staging tests, and
  the direct local runtime/headless CLI suites.
- Run the application and Core default suites after config/template changes.
- Run the real Ollama acceptance with its API gate and
  `glm-5.3-flash:cloud`; report unavailable local Ollama authentication or
  model access as blocked rather than weakening the test.
- Run changed-file Ruff and focused Pyright checks.
- Run documentation preparation and a normal MkDocs build; separately report
  the known unrelated strict-build warnings if they remain.
- Run `git diff --check` and inspect that no existing user config, credential,
  generated docs output, HTTP/frontend code, or website content changed.