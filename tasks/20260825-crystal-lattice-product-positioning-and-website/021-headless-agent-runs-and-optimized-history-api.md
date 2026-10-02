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
- [x] Configured agents can optionally receive a system-message section that
      accurately tells them how a project running outside Crystal Lattice can
      invoke the Crystal Lattice command, import the supported Python API, use
      the applicable Python interpreter, and find installed documentation.
      Those values come from explicit runtime/configuration variables,
      including any additions needed alongside variables such as
      `BUILTIN_PLUGINS`, and the section is independently enabled or disabled
      in the same manner as task guidance.
- [x] An explicitly gated real Ollama API test using
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
- [x] After the direct Python API, compact-history, and CLI acceptance tests
      pass, investigate and present a separate Draft plan for external-project
      CLI/API/interpreter/documentation variables and opt-in system guidance.
- [x] After separate approval, implement and verify the external-project
      access variables, optional system-message section, packaging behavior,
      and current documentation.
- [x] Run existing request-coordinator, terminal, config/dotenv, compact-tool,
      and CLI compatibility coverage.
- [x] Add current package-user and implementation documentation with tested
      examples and update package indexes.
- [x] Update specification requirements with implementation, verification,
      documentation, and delivery evidence.
- [x] Update this task throughout execution and add immutable completion notes
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
- 2026-09-14: Implemented runtime-owned access variables, exact same-config and
  same-session-root CLI argv, source/bundled interpreter and docs discovery,
  truthful optimized-bundle fallback, the independently disabled default
  system-message section for all maintained vendor profiles, existing-config
  adoption guidance, and distribution staging. The gated real
  `glm-5.3-flash:cloud` test passed in 87.75 seconds: the sparse outer prompt
  caused a CLI tool call and a separately persisted completed
  `subagent-worker` session containing the project marker.

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
  - `CRYSTAL_LATTICE_DOCS_URL`: stable public application documentation URL;
  - `CRYSTAL_LATTICE_SYSTEM_MESSAGES`: runtime-owned system-message resources
    used by existing configs to adopt the helper without copying source.
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

- [x] Extend the approved technical specification for `HLR-060` before code
      changes.
- [x] Define and test runtime-access derivation for source,
      bundled-Python, and optimized frozen layouts.
- [x] Add application-docs layout/staging where a local path is supported.
- [x] Add the shared opt-in access-section renderer and UI-schema helper.
- [x] Add the variable and placeholder to every maintained default vendor
      system-message configuration without changing the default compiled
      prompt.
- [x] Add deterministic default-config tests for disabled/enabled section
      behavior across configured vendor agents.
- [x] Add source, bundled-Python builder, and optimized-layout tests for
      executable, interpreter, API, docs, quoting, and unavailable-capability
      behavior.
- [x] Add and explicitly run the gated real Ollama
      `glm-5.3-flash:cloud` same-config delegation acceptance test.
- [x] Update current user, system-message configuration, runtime, and
      distribution documentation.
- [x] Run focused system-message, runtime-layout, package-builder, direct
      Python/CLI, Core, application, and documentation checks.
- [x] Complete `HLR-060`, the remaining parent requirement, task evidence, and
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

## Completion Notes

- **Outcome:** Delivered a supported context-managed local Python runtime,
  atomic synchronous initial/follow-up runs, bounded progress, structured
  outcomes, compact/full history, and one-shot `agents`, `run`, and `history`
  commands. Added an independently disabled Crystal Lattice access section
  that gives configured agents exact same-config/same-session-root CLI
  guidance plus applicable interpreter, Python API, local docs, and public
  docs information.
- **Canonical history and compatibility:** Compact results and history remain
  derived views. Existing persisted messages, event APIs, HTTP behavior,
  interactive terminal behavior, and same-session coordinator authority remain
  unchanged. HTTP, TypeScript, mobile, desktop, and persistent-subagent
  contracts were not expanded.
- **Distribution behavior:** Source and bundled-Python layouts expose an
  import-capable interpreter and local docs. Optimized frozen layouts expose
  their CLI and staged docs without falsely claiming a general Python
  interpreter. Existing configs are not rewritten and can adopt the
  runtime-owned helper explicitly. Unsupported pip/pipx installation claims
  were removed from the touched application guidance.
- **Real API evidence:** With
  `RUN_CRYSTAL_LATTICE_OLLAMA_SUBAGENT_E2E=1`, the
  `glm-5.3-flash:cloud` test passed in 87.75 seconds. Given only “Ask a
  subagent for the project marker and report its answer,” the outer agent used
  the advertised CLI, selected the same config and session root, created a
  separate `subagent-worker` session, obtained the marker in that worker's
  completed response, and reported it in the outer response. Assertions also
  verified the persisted CLI tool invocation; a textual delegation claim
  without the worker session cannot pass.
- **Automated verification:** Direct Python/coordinator/history acceptance
  passed; the real CLI subprocess suite passed with 10 tests; access,
  runtime-layout, and package-builder coverage passed; feature-system-message
  unit coverage passed with 34 tests; Core passed with 541 tests and one
  expected failure; and the final application suite exited `0` with 446
  passing tests, one skip, and 92 intentionally deselected tests.
- **Static and documentation verification:** Focused Pyright completed with no
  errors or warnings, changed-file Ruff passed, JSON and diff checks passed,
  documentation preparation passed, and a normal MkDocs build passed.
- **Known unrelated verification limits:** Strict MkDocs still aborts on ten
  repository-existing warnings involving unrelated plugin links, Core
  docstring indentation, and generated-reference cross-references. A broad
  feature-system-message package run also has seven pre-existing integration
  incompatibilities: two tests use unsaved direct sessions against current
  reconciliation, and five construct raw default agents/providers without
  their required mixins. The owning feature unit suite and the new
  application-owned compiled-message integration both pass; these failures
  were not weakened or changed.
- **Plan changes:** The user approved narrowing mandatory delivery away from
  HTTP/frontend work, then added and separately approved external-project
  access guidance and the real Ollama delegation requirement. Pip/pipx was
  removed as an unsupported product distribution assumption.
- **Deferred outside scope:** Durable detached jobs, restart-retained request
  results, HTTP compact-history/result resources, TypeScript/frontend lazy
  history, and model-facing persistent-subagent semantics remain separately
  scoped future work.

## Post-completion follow-up

On 2026-09-14, `main` at `a1cde086` was merged into this task branch in
`b51a8297`. The two documentation conflicts were resolved by keeping the new
macOS/Linux, native Windows PowerShell, and manual archive installation
guidance while retaining this task's headless API documentation. Focused
installation tests passed with 74 tests, and the direct headless CLI plus
runtime/access tests passed with 43 tests after the merge.

The user requested a follow-up for complete native-OS verification,
config-owned full and CLI-only prompt variants, explicit unavailable UI, and
real model-mediated CLI and Python SDK calls. The user approved execution on
2026-09-14, including permission to push this branch and trigger the native
GitHub Actions workflow.

### Approved follow-up requirements checklist

- [x] All supported source and bundled-Python runtimes provide one complete,
      validated access-variable set, and every public archive, Bash installer,
      PowerShell installer, and manual archive path exposes that capability on
      its native release targets.
- [x] The default system-message template contains explicit full-access and
      CLI-only placeholders, backed by config-owned Markdown definitions with
      visible named runtime placeholders and environment-value mappings rather
      than instruction prose generated by helper code.
- [x] Full-access and CLI-only predicates are mutually exclusive. A runtime
      with valid CLI and Python SDK values compiles only the full section; a
      runtime with valid CLI values but no supported Python SDK compiles only
      the CLI-only section; a runtime without valid CLI values compiles
      neither.
- [x] `include_crystal_lattice_access` remains the single user-controlled
      opt-in. Its UI element identifies whether full or CLI-only access is
      available, remains visible but disabled with a concrete reason when
      neither is available, and a saved true override cannot compile an
      invalid section.
- [x] `disabled` is an explicit documented Python and TypeScript UI-schema
      field, and terminal, mobile, and desktop behavior prevents changes while
      displaying the unavailable or CLI-only explanation.
- [x] Focused automated tests verify the access predicates, explicit config
      text, required values, compiled variants, and every supported source,
      archive/manual, Bash-installed, and PowerShell-installed runtime path.
- [x] One real tool-capable LLM follows the config-owned guidance and creates
      distinct persisted child sessions through both the CLI and Python SDK on
      every native release target. Textual claims without tool and child
      session evidence fail.
- [x] A one-off native Detox end-to-end run, without adding a permanent Detox
      test, confirms that the full, CLI-only, and unavailable options appear
      with the expected enabled/disabled state and explanatory text.
- [x] Current user, configuration, distribution, UI-schema, testing, and
      maintainer documentation describes the verified behavior without
      claiming persistent-subagent semantics.

### Investigation findings

- The merged release workflow builds and natively executes bundled-Python
  archives on Linux AMD64/ARM64, macOS AMD64/ARM64, and Windows AMD64/ARM64.
  It independently exercises direct archive use on all six targets, the Bash
  installer on five applicable targets, and native PowerShell installation on
  both Windows targets.
- Native run `34860183022` took about 26 minutes 48 seconds wall-clock. Its test
  and build jobs consumed about 53.5 raw runner-minutes in total. Individual
  build jobs ranged from 2.5 minutes on Linux ARM64 to 20.9 minutes on Windows
  ARM64.
- Before this follow-up, distribution smokes verified archive identity,
  command discovery, plugin installation, startup, and agent listing. They did
  not execute
  `crystal-lattice run`, import `open_runtime`, or verify the complete access
  environment through each installed entry point.
- The pre-follow-up real access test was source-layout-only and CLI-only. Its
  `glm-5.3-flash:cloud` run took 87.75 seconds and proved one real child
  session, but it does not cover the Python SDK or packaged native layouts.
- An existing optional optimized-bundle Ollama test uses `qwen3:0.6b` for one
  file-reading tool call, but it is not part of the bundled-Python release
  matrix. On the local macOS ARM64 machine, its underlying Core tool-call test
  passed in 5.25 seconds with the model already downloaded and warm.
  `qwen3:0.6b` occupies about 522 MB on disk and about 1 GB while loaded.
- Installing Ollama and pulling that model independently on six clean native
  runners would transfer at least about 3.1 GB before caches and add setup
  variability. Native Windows ARM64 Ollama availability is also not
  established. A 0.6B model is materially less reliable for a multi-step
  CLI-versus-SDK instruction-following gate than for one explicit file tool.
- OpenRouter currently reports `google/gemini-2.5-flash-lite` as supporting
  tools at $0.10 per million input tokens and $0.40 per million output tokens.
  It is already used by repository OpenRouter integration coverage. Two
  compact tool-loop scenarios per target should remain below roughly $0.02
  for the complete six-target matrix, including generous prompt/output
  allowance, and should add about 30–120 seconds to each parallel build job
  rather than model installation time.
- Local semantic trials showed that Gemini Flash Lite stopped after discovery
  or requested information already present in the sparse prompt. The test
  correctly rejected those runs. Switching to
  `anthropic/claude-haiku-4.5` with a minimal access-only system message and
  production Claude Bash/Write tools completed both real CLI and SDK routes,
  including two separately persisted deterministic worker sessions and secret
  isolation. Its current OpenRouter price is $1 per million input tokens and
  $5 per million output tokens; the compact six-target scenario is expected to
  remain below about $0.20 per workflow run. The first successful local pair
  cost about $0.02552, implying about $0.153 for six comparable targets.
- A real-provider secret must not be inherited by a model-controlled shell.
  The safe test shape resolves the OpenRouter credential into the already
  constructed outer provider, removes it from the process environment before
  tool execution, and uses deterministic credential-free child agents.
- UI-schema `disabled` behavior already exists functionally. The shared React
  settings logic propagates it, mobile and the primary desktop session
  settings disable controls and render descriptions, and terminal `/set`
  rejects disabled settings with their description. The Python protocol docs
  and TypeScript `UiSchemaElement` type do not declare `disabled` explicitly,
  and focused frontend tests do not yet prove the access-specific unavailable
  note.
- The access helper currently owns both the gate/UI element and the entire
  rendered message. The system-message feature supports a config-owned
  `text` variable with a `runtime_code` helper and condition, so only
  availability and gating need remain in Python. Recursive mixins can hold one
  shared full/CLI-only definition while vendor templates retain explicit
  `{{CRYSTAL_LATTICE_ACCESS}}` and
  `{{CRYSTAL_LATTICE_CLI_ACCESS}}` placeholders.

### Proposed requirements

- All supported source and bundled-Python runtimes provide one complete,
  validated access-variable set. The public bundled-Python archive, Bash
  installer, PowerShell installer, and manual archive paths expose the same
  capability on every native release target.
- Full-access and CLI-only sections have separate config-owned Markdown
  definitions with explicit named runtime placeholders and value mappings.
  Helper code owns only availability validation, mutually exclusive predicates, the
  `include_crystal_lattice_access` gate, and its UI element.
- If full values are present, only the full CLI+SDK section compiles. If only
  CLI values are present, only the CLI-only section compiles and the UI names
  that mode. If CLI values are absent or invalid, neither section compiles and
  the setting remains visible but disabled with a concrete reason.
- `disabled` becomes an explicit documented Python/TypeScript UI-schema field,
  and terminal, mobile, and desktop acceptance proves that a disabled setting
  cannot be changed and displays its reason.
- Every supported installation scenario deterministically invokes both the
  CLI and Python SDK using its actual installed/archive runtime and verifies
  every required access value without a provider credential.
- A separately gated native-matrix test uses one real tool-capable LLM to
  follow the config-owned guidance and create distinct persisted child
  sessions through both the CLI and Python SDK. Textual claims without the
  corresponding child sessions and tool evidence fail.
- A one-off Detox run confirms the full, CLI-only, and unavailable
  presentations without adding a permanent Detox test.

### Follow-up implementation notes

- Runtime layout now supplies a shell-rendered command alongside the
  authoritative JSON argv. POSIX uses shell-safe argument joining; Windows
  emits an explicit PowerShell call expression. The application now overrides
  inherited `CONFIG_DIR` with the active config directory, fixing a real case
  where an outer shell's `~/.crystal` value silently suppressed access
  guidance for a project config.
- Direct packaged-Python SDK execution exposed and fixed a distribution bug:
  without the CLI launcher, the installed `site-packages` copy of
  `runtime_layout.json` resolved plugins under `python/lib/plugins`. Runtime
  discovery now locates the archive manifest from POSIX and Windows packaged
  interpreter layouts. The rebuilt macOS archive passed both direct archive
  and public Bash-installer CLI/SDK smokes.
- One shared config mixin now owns both complete access variants and all named
  runtime-value mappings. Every maintained vendor template includes both
  placeholders. The helper contains only named-value access, validation,
  mutually exclusive predicates, and the dynamic UI element.
- Python and TypeScript now document/type `disabled`; focused terminal, mobile,
  and desktop tests prove the reason remains visible and disabled controls do
  not patch state. A temporary production-component Detox harness displayed
  full, CLI-only, and unavailable rows on an iPhone 17 Pro simulator; the test
  passed in 38.311 seconds and every temporary harness/test change was then
  removed.
- Gemini Flash Lite trials correctly failed because the model stopped after
  discovery or requested an already supplied worker ID. Claude Haiku 4.5 then
  passed both sparse source-layout prompts. The rebuilt macOS archive also
  passed both routes, creating separate `cli-worker` and `sdk-worker` sessions
  while the test verified that the OpenRouter key was absent from
  model-controlled and child state.
- Local verification passed for clean source installation, extracted archive,
  public Bash installation, all focused suites, complete Core/application and
  shared frontend suites, mobile typechecking, changed-file Python
  typechecking, documentation build, workflow security validation, and
  whitespace checks. Repository-wide Pyright and existing desktop
  lint/typecheck remain red on unrelated baseline findings; scoped changed
  Python and TypeScript files pass.
- Windows deterministic rerun evidence and all-target real-provider evidence
  remain pending. GitHub currently exposes no `OPENROUTER_API_KEY` repository,
  organization, or `cli-release` environment secret; the local key has not
  been uploaded.
- Native run
  [34977742639](https://github.com/dynamicprogrammingsolutions/crystal-lattice/actions/runs/34977742639)
  passed Linux and macOS on both architectures. Both Windows architectures
  completed their SDK requests but rejected stdout because one info log
  preceded the JSON. The same logs also exposed that Python lookup of a bare
  installer command skipped the intended extensionless/`.cmd` launcher and
  found the repository venv executable. Imports now occur inside stdout
  redirection, and installer headless probes invoke the exact installed
  launcher after the independent by-name checks.
- Follow-up run
  [34996853430](https://github.com/dynamicprogrammingsolutions/crystal-lattice/actions/runs/34996853430)
  confirmed both Linux and both macOS targets again, plus Windows AMD64 direct
  archive and Git-Bash installation. Its PowerShell-installed command reached
  an existing Windows batch quoting edge when the absolute `.cmd` path
  contained spaces. The smoke now generates a temporary PowerShell forwarding
  script that invokes that exact command with `@args` and preserves
  `$LASTEXITCODE`; a focused test locks down the wrapper.
- Final deterministic run
  [34999315316](https://github.com/dynamicprogrammingsolutions/crystal-lattice/actions/runs/34999315316)
  passed on Linux AMD64/ARM64, macOS AMD64/ARM64, and Windows AMD64/ARM64.
  Every direct archive passed, every applicable Bash installer passed, and
  both native PowerShell installers passed the deterministic CLI and packaged
  Python SDK requests with complete access-value checks. The local clean
  source smoke also passed after the final corrections. From the test job's
  start through Windows ARM64 completion, the run took 27 minutes 10 seconds
  and about 57.2 aggregate test/build runner-minutes, versus the 26 minutes
  48 seconds and roughly 53.5 runner-minutes observed before adding these
  probes. The approximately 3.7 runner-minute delta includes normal build
  variance and requires no model installation or provider call.
- The post-change sparse Ollama
  `glm-5.3-flash:cloud` delegation test passed in 94.45 seconds. Complete
  mobile and desktop Jest suites passed with 181 and 144 tests respectively;
  the final application suite passed 481 tests with one intentional skip.
- A project-local secret updater and its dedicated dotenv live under the
  ignored `.crystal/github-actions-secrets/` directory. The simple shell
  wrapper passes the complete colocated dotenv to `gh secret set --env-file`,
  so additional repository secrets require only another dotenv entry and a
  rerun. It enforces file mode `0600`, and the repository Actions secrets are
  populated without adding worktree changes.
- Secret-enabled run
  [35061039335](https://github.com/dynamicprogrammingsolutions/crystal-lattice/actions/runs/35061039335)
  passed the real CLI+SDK gate on both Linux and both macOS targets. Windows
  AMD64 copied the correct advertised PowerShell CLI command but exposed a
  production Claude Bash defect: shell detection selected PowerShell while
  foreground execution still wrapped every command in POSIX `eval`, `$?`, and
  `printf` syntax. The superseded run was cancelled before Windows ARM64 made
  another hosted call. Claude Bash now emits native PowerShell or `cmd`
  wrappers and parses CRLF sentinels, with focused package coverage; native
  rerun evidence remained pending at that point.
- Corrected secret-enabled run
  [35062591328](https://github.com/dynamicprogrammingsolutions/crystal-lattice/actions/runs/35062591328)
  passed the real CLI and Python SDK routes on Linux AMD64/ARM64, macOS
  AMD64/ARM64, and Windows AMD64/ARM64. Every target recorded production Bash
  tool-call evidence, two distinct completed worker sessions, expected worker
  markers, exact packaged runtime/config/session identity, and no provider
  credential in model-controlled or child state.

### Draft execution plan

Status: Approved

First extend the package-owned headless-run specification and requirements,
and cross-reference the existing CLI-distribution specification. Define one
full capability plus one explicit CLI-only variation, sharing one user opt-in
but using mutually exclusive compilation predicates.

Add a small immutable runtime-access value object or equivalent pure
derivation helper. Retain `CRYSTAL_LATTICE_CLI_ARGV_JSON` as the
language-neutral authority and add a platform-shell-rendered
`CRYSTAL_LATTICE_CLI_COMMAND` for prompt text. Require and validate:

- `CRYSTAL_LATTICE_CLI_ARGV_JSON`;
- `CRYSTAL_LATTICE_CLI_COMMAND`;
- `CRYSTAL_LATTICE_CONFIG`;
- `CRYSTAL_LATTICE_SESSIONS`;
- `CRYSTAL_LATTICE_PYTHON`;
- `CRYSTAL_LATTICE_PYTHON_API_MODULE`;
- `CRYSTAL_LATTICE_DOCS`;
- `CRYSTAL_LATTICE_DOCS_URL`.

Continue exposing `CRYSTAL_LATTICE_SYSTEM_MESSAGES` as the bootstrap resource
path and verify it for every layout, but do not make a helper responsible for
diagnosing its own missing source path. Validate JSON shape, required path
existence, import-capable Python, and documentation availability. Source and
bundled-Python layouts must be complete. An optimized frozen layout with valid
CLI values but no general Python SDK uses the explicit CLI-only variant. A
runtime with invalid CLI values is unavailable.

Move both complete Markdown variants into one shared mixin in the default
config. `CRYSTAL_LATTICE_ACCESS` contains full CLI+SDK text and
`CRYSTAL_LATTICE_CLI_ACCESS` contains CLI-only text. Both use `text`, explicit
named runtime placeholders, and the same small runtime helper, but their
conditions call separate mutually exclusive predicates. Apply that mixin
after each maintained vendor system-message mixin so the variables are
deep-merged once. Every Codex, Qwen, Gemini, Grok, Kimi, and Claude template
contains both final placeholders. The explicit full text includes:

- the authoritative CLI base command;
- discovery, initial run, follow-up, and compact-history commands;
- a complete `open_runtime(config_path=..., session_root=...)` example;
- guidance to write a short Python file and execute it with the advertised
  interpreter, avoiding shell-specific Python one-liner quoting;
- the local and public documentation locations;
- the existing synchronous-session versus persistent-subagent limitation.

The CLI-only text contains the same CLI discovery, run, follow-up, history,
docs, and synchronous-session limitations, but explicitly states that no
general Python SDK is available and omits all SDK instructions.

Reduce `crystal_lattice_access.py` to pure availability checks,
`include_crystal_lattice_access()`,
`include_crystal_lattice_cli_access()`, and `get_ui_elements()`.
`include_crystal_lattice_access()` is true only when the user opt-in and all
full values are valid. `include_crystal_lattice_cli_access()` is true only
when the same opt-in is true, CLI values are valid, and full values are not.
The UI description and label identify full or CLI-only mode. When CLI values
are unavailable, the element returns `disabled: true`, `default: false`, and
an explicit description naming the missing or invalid values. A previously
saved true override therefore cannot compile partial guidance.

Formalize the existing UI behavior by documenting `disabled` in
`FeaturePlugin.get_ui_elements` and adding `disabled?: boolean` to
`UiSchemaElement`. Reuse `description` for the visible unavailable reason
rather than adding a second reason field. Add focused shared-logic, terminal,
mobile, and desktop session-settings tests. Change frontend production code
only where a focused test shows that the primary session setting can still be
edited or its description is not visible.

Add one credential-free access-contract helper to the distribution smoke
infrastructure. For source installation, extracted archives, Bash-installed
commands, and PowerShell-installed commands, it uses the deterministic
streaming provider worker to:

1. run a task through the real `crystal-lattice run` command;
2. invoke the packaged interpreter and `open_runtime(...)` for a second task;
3. compile the enabled access text and assert every required value;
4. use config/session/docs paths containing spaces;
5. assert both results and persisted sessions came from the scenario's own
   runtime and isolated state.

This deterministic probe runs in every applicable existing smoke scenario and
therefore covers manual archive use through the extracted-archive path without
adding provider time or secrets.

Add one real-provider `agent-access` scenario per native release target,
against the extracted bundled-Python archive rather than repeating it for
every installer transformation. Its isolated config contains:

- an outer `anthropic/claude-haiku-4.5` OpenRouter agent with the production
  cross-platform Claude Bash/Write tools, a minimal access-only system message,
  and access guidance enabled;
- a deterministic `cli-worker`;
- a deterministic `sdk-worker`;
- no provider credential needed by either child.

Use two sparse, method-specific prompts: one asks the outer agent to use the
CLI route in its guidance, and one asks it to use the Python SDK route. Do not
include commands, flags, Python code, or paths in those prompts. After outer
application construction, remove `OPENROUTER_API_KEY` from the environment
before any model-controlled tool runs. For each method, require the expected
tool calls, exact runtime/config/session identity, a distinct completed child
session with the expected worker agent, and the child result in the outer
response.

Run this real scenario:

- on all six native targets for release tags;
- on explicit workflow dispatch when enabled;
- never in public pull-request jobs or fork contexts;
- with a missing required release secret treated as a release failure, not a
  skipped success;
- with transport-level retry for provider throttling only, not semantic retry
  for a model that failed to use the requested method.

Retain an optional local Ollama profile for developer comparison, but do not
make Ollama installation/model download part of the six-target release gate.
The local macOS acceptance must run both methods against source and a built or
reused matching bundled-Python archive. It may additionally run the
`qwen3:0.6b` profile to record local resource/time data, but OpenRouter remains
the cross-platform release authority. After deterministic UI tests, create a
temporary one-off Detox scenario or fixture that exposes full, CLI-only, and
unavailable schema elements, run it against the native app, record the
evidence, and remove the temporary Detox test before completion.

#### Implementation decisions and open questions

- **Provider decision:** Use OpenRouter
  `anthropic/claude-haiku-4.5` for the six-target release gate. Direct local
  trials proved both routes; Gemini Flash Lite repeatedly failed semantic
  execution even when the correct method and worker ID were present.
  Keep local Ollama optional because clean-runner installation, 522 MB per
  target model transfer, Windows ARM64 availability, and 0.6B multi-step
  reliability make it a poor universal release gate.
- **Secret boundary recommendation:** Resolve the key into the outer provider,
  then remove it from the environment before enabling model-controlled tools.
  Child sessions use the deterministic streaming provider. Add an assertion
  that the shell environment and child config contain no real key.
- **Matrix recommendation:** Run deterministic CLI+SDK probes through every
  installation scenario, but run the real LLM only once per native target
  against the archive. Repeating the real model for archive, Bash, and
  PowerShell paths would increase flakiness without testing a different
  runtime.
- **Availability decision:** Full and CLI-only are explicit config-visible
  variations with mutually exclusive predicates. Optimized frozen bundles
  remain useful through CLI-only guidance, and their UI identifies that mode.
- **UI recommendation:** Standardize the already implemented `disabled`
  property and use `description` for the reason. Do not introduce `readonly`
  or `disabled_reason` unless a focused frontend test demonstrates that
  `description` cannot meet the visible-note requirement.
- **Prompt ownership recommendation:** Keep all operational prose and
  placeholders in one shared config mixin. Helper Python contains no rendered
  instruction text.
- **CI frequency decision:** Real-provider coverage is mandatory on release
  tags and opt-in on workflow dispatch, with deterministic contract tests in
  ordinary CI. No nightly six-target provider schedule is added initially.

#### Documentation

- Update the headless-run specification and requirements with full,
  CLI-only, and unavailable behavior, explicit config ownership, disabled UI,
  native installation, and real CLI/SDK evidence.
- Cross-reference the native matrix and scenario ownership from the
  CLI-distribution specification without duplicating its installation
  contract.
- Update system-message configuration docs with the single shared mixin and
  explain that helper code owns only gating/availability.
- Update the headless user guide with full, CLI-only, and unavailable UI
  examples, complete CLI/SDK snippets, and optimized-layout behavior.
- Document the deterministic and real-provider smoke commands, credential
  isolation, release/workflow-dispatch policy, expected runtime, and optional
  local Ollama profile.
- Update Python and TypeScript UI-schema reference text for `disabled`.

#### Task checklist

- [x] Obtain approval for full/CLI-only behavior, OpenRouter provider, CI
      frequency, disabled UI semantics, one-off Detox evidence, branch push,
      and native workflow execution.
- [x] Update specifications and live requirement IDs before implementation.
- [x] Define and test the complete runtime-access value contract and
      platform-rendered CLI command.
- [x] Move full and CLI-only instruction text to one shared config mixin and
      reduce helper code to gating, validation, and UI schema.
- [x] Formalize and verify disabled config controls across Python, TypeScript,
      terminal, mobile, and desktop boundaries.
- [x] Add deterministic CLI+SDK probes to every supported source/archive/
      installer scenario.
- [x] Add the secret-isolated OpenRouter CLI+SDK model-mediated scenario and
      native release-matrix wiring.
- [x] Run a temporary one-off Detox native UI scenario for full, CLI-only, and
      unavailable presentation, record evidence, and remove the temporary
      test.
- [x] Run source and packaged local macOS CLI+SDK acceptance, plus optional
      Ollama timing comparison.
- [x] Run focused, package, native-distribution, documentation, and security
      verification.
- [x] Update requirement evidence and add immutable post-follow-up completion
      evidence.

#### Requirement verification

- **Complete capability:** Source and every bundled-Python installation path
  produce a validated full set whose JSON argv round-trips, rendered command
  is executable in the platform shell, paths exist, advertised Python imports
  the SDK, docs are readable, and only the full section compiles.
- **CLI-only capability:** A valid CLI without Python/API values keeps the
  setting enabled, labels/describes CLI-only mode, compiles only the CLI-only
  section, and never emits an SDK command or import claim.
- **Unavailable capability:** Removing each required CLI value in turn leaves
  the UI element visible with `disabled: true` and a precise description,
  rejects UI/terminal edits, and prevents either section from compiling even
  when a true override was previously stored.
- **Config ownership:** Inspection and compilation tests find one shared
  config-owned Markdown definition with explicit runtime placeholders and
  named environment-value mappings; helper code contains no CLI, SDK, history,
  docs, or subagent instruction prose.
- **All installation methods:** Source, extracted archive/manual use, Bash
  installation, and native PowerShell installation each execute a
  deterministic CLI request and Python SDK request from paths containing
  spaces and persist the expected isolated sessions.
- **Real model on all OSes:** Every native release target records one real
  outer provider request with production tool calls for the CLI route and one
  for the SDK route, with corresponding distinct persisted child sessions.
  The actual provider key is absent from tool and child environments.
- **macOS local:** The current Mac executes both routes through source and a
  matching bundled-Python archive; measured time and any Ollama comparison are
  recorded as evidence rather than inferred.
- **Native UI:** A one-off Detox run visibly distinguishes full, CLI-only, and
  unavailable controls, including disabled behavior and explanation text; no
  permanent Detox test remains.

#### Additional implementation verification

- Run focused runtime-layout, config-resolution, system-message, UI-schema,
  terminal, frontend SDK/React, mobile, and desktop tests.
- Run all four existing distribution smoke entry points on applicable local
  platforms and their package-script/workflow contract tests.
- Build or reuse a matching macOS archive, then run the deterministic and real
  agent-access scenarios against its launcher and installed command.
- Run Core, application, frontend SDK, frontend SDK React, and shared React
  Native component default suites.
- Run changed-file Ruff, Pyright, frontend typechecks, JSON validation,
  documentation preparation/build, workflow security checks, and
  `git diff --check`.
- Execute the real provider gate with the required environment flag and key;
  a skip is not acceptance. Report provider outages separately without
  replacing the real scenario with a mock.

### Follow-up completion notes

- **Outcome:** The approved follow-up is complete. External projects receive
  validated full CLI+SDK or CLI-only access guidance from explicit config;
  unavailable controls remain visible and disabled. Deterministic requests
  pass through every supported source/archive/installer path, and real
  model-mediated CLI and SDK delegation passes on all six native release
  targets.
- **Native evidence:** Deterministic run
  [34999315316](https://github.com/dynamicprogrammingsolutions/crystal-lattice/actions/runs/34999315316)
  passed every native archive and applicable Bash/PowerShell installer.
  Secret-backed run
  [35062591328](https://github.com/dynamicprogrammingsolutions/crystal-lattice/actions/runs/35062591328)
  passed both real delegation methods on all six targets. The real scenario
  enforces persisted child sessions, production tool-call arguments, worker
  markers, packaged runtime identity, and credential isolation.
- **Windows finding and correction:** The first secret-backed run exposed that
  Claude Bash selected PowerShell but wrapped foreground commands with POSIX
  syntax. The tool now emits native PowerShell or `cmd` wrappers and parses
  CRLF sentinels. The complete Claude tools suite passed 142 tests, focused
  adjacent application coverage passed 20 tests, and the corrected native
  run proves both Windows architectures.
- **Local and UI evidence:** Clean source, direct macOS archive, and public
  Bash installer CLI+SDK smokes passed. Real source and packaged OpenRouter
  runs passed, as did the sparse `glm-5.3-flash:cloud` delegation test. The
  one-off Detox run proved full, CLI-only, and unavailable controls and left
  no permanent test harness.
- **Secret handling:** A local updater and dedicated dotenv are stored under
  ignored `.crystal/github-actions-secrets/`, with modes `0700` and `0600`.
  The updater passes every entry in that file to repository Actions secrets
  through `gh secret set --env-file`; adding another secret requires no script
  change. No credential appears in tracked changes. The repository secret
  remains configured for release and explicitly enabled dispatch runs.
- **Verification:** Core, application, Claude tools, frontend SDK/React/shared
  RN, complete mobile and desktop Jest suites, focused distribution/config/UI
  tests, documentation build, workflow security, Ruff, Black, original
  access-surface typechecks, JSON validation, and whitespace checks passed.
  Targeted Claude package Pyright, repository-wide Pyright, and desktop
  lint/typecheck retain unrelated pre-existing baseline failures recorded
  above.
- **Scope boundary:** This delivers natural synchronous CLI and Python SDK
  delegation with persisted sessions and compact history. Persistent parent-
  child orchestration, detached lifetime, recovery semantics, and HTTP/TS
  compact-history expansion remain outside this follow-up.

### Further gaps recorded for separate delegation (2026-09-29)

These findings do not reopen the completed requirements or authorize changes
to the delivered APIs. Define and approve the resulting behavior separately
before implementing it.

- **Current agent context:** The access guidance shows how to list and select
  agents but does not identify the current session's effective agent ID, model,
  or reasoning effort. Show those values from the active session/request and
  tell the agent to use the current agent and model for a delegated run by
  default, unless the user requests another. Preserve the effective values
  after session overrides and plugin/model variants. In the session prompting
  this finding, the user identified `codex-openai`, `gpt-6-sol`, and `high`;
  these are session facts, not repository-wide defaults.
- **Instructions for child runs:** The default `feature-system-message`
  plugin already provides a non-mutating **Show compiled system message**
  session action in terminal, mobile, and desktop. Make that effective
  system/developer message available naturally to a headless CLI/Python
  caller before delegation, and provide a clear way to append to or modify
  child-run instructions without editing the parent or losing the provider-
  and plugin-assembled base message. Expose the effective child result and
  make changes explicit for each run. During the task-020 trials, an
  `include_crystal_lattice_access: false` request override did not remove
  access guidance from the initially logged compiled message; verify
  configuration timing and the actual provider prompt before assuming a
  child-only request override changes the compiled message.
- **Child model controls:** Let a delegated run select or inherit the model
  and reasoning effort through the owning provider/plugin configuration.
  Make the effective child values inspectable, with no implicit parent
  mutation. The exact option and validation contracts are left for the
  separate work.
- **Delegation examples:** The access section currently shows `--prompt` and
  prints SDK `output_text` directly. Add a file/stdin example for multiline
  instructions, and show how a caller checks CLI exit/JSON status or SDK
  `status`/`error` before trusting a child's answer. The local two-marker
  smoke used direct CLI and SDK calls, so it did not test an outer model
  choosing to invoke these instructions. The earlier completed native
  model-mediated acceptance remains separate evidence.
- **Cross-session search ergonomics:** `crystal-lattice sessions` followed by
  ten `crystal-lattice messages` invocations initialized the runtime eleven
  times to search assistant text in ten recent sessions. The same local
  search used one SDK runtime and the existing server API successfully.
  Add a bounded, one-runtime CLI search over recent sessions and assistant
  content with session ID, canonical message index, and concise matches;
  keep role/field selection and full-message retrieval available. A local
  timing sample measured 6.75 seconds to open the configured runtime, 0.22
  seconds to list ten sessions, 0.54 seconds to query their assistant messages,
  and 0.79 seconds for equivalent queries through the already-running local
  HTTP server. These timings are observations, not performance targets.
- **Projection cost:** Current canonical-message projection materializes
  complete session messages before selecting requested fields. A caller can
  avoid receiving long tool output but still pays that in-process loading
  cost. Investigate bounded storage/query work for long histories separately
  from the CLI convenience change; do not equate a smaller response with a
  cheaper storage read.

### Approved further-development outline (2026-10-02)

The user approved this outline for addition to the post-completion follow-up.
It does not reopen the completed requirements, authorize implementation, or
move persistent parent-child subagent behavior into this task. Define and
approve concrete implementation requirements and plans before executing any
item below.

The outline was derived from direct use of the delivered headless APIs during
the accepted current-product and compatibility audit. That work used bounded
CLI and Python runs, shared-runtime parallel investigation, model/effort
calibration, phased evidence packets, cost/time guards, cross-session queries,
and direct read-only inspection of immutable session snapshots.

#### Priority 1: direct delegation ergonomics

- **Effective run context:** Expose the current effective agent ID, provider
  route, model, reasoning settings, and authentication mode where safe.
  Delegated runs inherit the current agent/model/reasoning configuration
  unless explicitly overridden. Preserve values after session overrides,
  provider composition, model variants, and plugin-owned normalization.
- **Instruction inspection:** Provide CLI and Python APIs for reading the
  effective compiled system/developer instructions without sending a model
  request.
- **Child instruction composition:** Support explicit child-only instruction
  modes such as `append`, replacement of a task-specific section, and, where
  separately authorized, full replacement. Preserve the provider/plugin-
  assembled base by default, avoid mutating the parent session, and report the
  effective child instructions or a bounded identity/digest in the result.
- **Model/plugin settings:** Let callers inspect and override model, reasoning
  effort, and other provider/plugin settings through the same schema used by
  session settings. Do not hardcode provider-specific option vocabularies in
  the generic runtime or CLI. Report the effective child values.
- **Result telemetry:** Add optional effective model/provider/reasoning,
  start/end time, duration, tool-call counts, usage, and cost provenance to
  Python and JSON run results. Provider-reported, locally estimated, and
  unavailable values remain distinct.
- **Config overlay:** Allow a temporary, non-mutating config overlay for one
  runtime or run, including agent overrides, model/reasoning values,
  instruction append, tool policy, cache location, and output metadata. Make
  the overlay inspectable and never mutate the source config or parent
  session.

The audit required copied configs to reproduce one agent/model/effort
combination. That process exposed plugin-path drift, mixin ordering and
replacement behavior, stale worktree contents, cache/session/workspace
ambiguity, and confusion between product defaults and investigator tooling.

#### Priority 2: bounded orchestration

- **Batch runner:** Add a reusable one-runtime API for a bounded collection of
  independent assignments, with maximum concurrency, per-run timeout,
  distinct sessions, progress, cancellation, and aggregated results.
- **Batch budget:** Allow optional stop conditions based on elapsed time,
  completed/failed runs, and provider-reported or estimated cost. Preserve
  cost provenance and never imply that an estimate is billing truth.
- **Run metadata:** Allow callers to attach a batch ID, assignment ID,
  purpose, source revision, output directory, and bounded tags to each
  delegated session.
- **Early checkpoint:** Support a progress/checkpoint callback suitable for
  requirements such as “a claim map must exist within eight minutes.”
- **Durable status:** Distinguish running, timed out, cancelled,
  completed-with-required-output, completed-without-required-output,
  partial-artifact, and failed-before-request states.
- **Cross-session search:** Add the already-recorded bounded, one-runtime CLI
  search over recent sessions and selected roles/fields. Return session ID,
  canonical message index, and concise matches while retaining role/field
  selection and explicit full-message retrieval.

The compatibility audit wrote custom `ThreadPoolExecutor` runners for
calibration and the broader investigation. Reusing one runtime worked well;
repeated CLI startup did not. Several runs timed out after substantial work,
and partial evidence files were useful even when no successful final response
was produced.

This batch runner remains distinct from persistent model-facing subagents.
Persistent parent-child relationships, mid-run input, restart recovery,
detached lifetime, and child-session ownership remain with the dedicated
subagent work.

#### Priority 3: evidence and safety controls

- **Tool/mutation policy:** Let a run apply an explicit tool allowlist,
  denylist, or named policy such as read-only investigation. Prompt-only
  mutation guidance is useful but is not enforcement.
- **Verification policy:** Let an assignment state whether focused local
  tests, dependency installation, network calls, hosted providers, Docker,
  native devices, external search, and writes outside an assigned output
  directory are allowed.
- **Snapshot reads:** Add read-only snapshot enumeration and projected
  history/message retrieval by `snapshot_id` to the local Python and CLI APIs,
  without selecting or restoring the snapshot. Reading a snapshot must not
  affect active-session write eligibility or selected-snapshot state.
- **Storage-level projections:** Continue the already-recorded investigation
  into avoiding complete message/tool-result materialization before
  projection. A smaller response is not necessarily a cheaper storage read.
- **Environment diagnosis:** Add a concise redacted runtime/config diagnostic
  showing interpreter, config, config directory, session root, workspace,
  cache root, plugin-path failures, documentation path, and access-guidance
  mode.

The verification process encountered a base-Python path instead of the venv,
missing plugins after branch drift, inherited `CONFIG_DIR`, separate cache and
session roots, template replacement through later mixins, and a bridge TLS
certificate-bundle requirement. Diagnostics must not expose credentials,
provider auth state, private session content, or cache contents.

#### Advanced delegated-investigation documentation

Add one advanced **Delegated investigations** recipe to the headless-run guide
rather than expanding the basic first-run example.

The recipe should cover:

1. **Keep one runtime open**
   - Open one `open_runtime()` context.
   - Use distinct sessions for independent work.
   - Limit concurrency.
   - Never write to one session concurrently from multiple processes.
2. **Record the effective context**
   - Agent ID.
   - Provider route.
   - Model.
   - Reasoning settings.
   - Compiled instruction identity or digest.
   - Source config and session root.
   - Working directory and source revision.
3. **Write a bounded assignment**
   - Purpose and intended reader.
   - Exact scope and decision questions.
   - Named sources or packages.
   - Non-goals.
   - Mutation, network, credential, and test permissions.
   - Timeout and stop conditions.
   - Required deliverables.
   - Unknowns that must remain unknown rather than inferred.
4. **Use incremental evidence**
   - Write an early claim map or work plan.
   - Record verification commands as they finish.
   - Start machine-readable claims before final synthesis when required.
   - Do not make all useful output depend on the final assistant response.
5. **Handle results safely**
   - Check `status` and `error` before consuming `output_text`.
   - Record partial artifacts after timeout or cancellation.
   - Treat delegated findings as proposals.
   - Independently verify decision-bearing claims.
6. **Describe verification honestly**
   - Test presence is not a test run.
   - A skipped gate is not a pass.
   - A timeout is not a pass.
   - Mocked component coverage is not HTTP or native-client integration.
   - Provider entitlement and hosted behavior remain unknown without a dated
     real-provider check.
7. **Use projected history**
   - Read assistant/user fields without long tool results.
   - Retrieve a full message only when needed.
   - Use a single runtime for broad searches.
   - Explain that response projection is not necessarily storage-read
     optimization.
8. **Troubleshoot configuration portability**
   - Existing configs are not automatically rewritten.
   - Config-directory-relative prompt files and mixins must remain
     resolvable.
   - Later mixins or variants may replace an entire nested template.
   - A config copied into an older worktree may reference plugins that do not
     exist there.
   - Confirm that the advertised interpreter imports the same installed
     runtime.

The basic documentation already covers multiline prompt files/stdin, JSON
`status` and `error`, compact history, parallel futures, timeout behavior, and
process-local concurrency. Connect those delivered primitives to the advanced
recipe rather than redefining them.

#### Provider-agnostic developer-message outline

The existing access section continues to describe commands and runtime
locations. A separate optional delegation section governs behavior.

Proposed provider/model-agnostic structure:

```text
# Delegated Crystal Lattice work

Current effective context:
- Agent: {{CURRENT_AGENT_ID}}
- Provider: {{CURRENT_PROVIDER_ID}}
- Model: {{CURRENT_MODEL}}
- Reasoning settings: {{CURRENT_REASONING_SETTINGS}}

Use the current effective agent, model, and reasoning settings by default.
Change them only when the user or assignment explicitly requests a different
tradeoff. Report the effective child settings in the result.

When delegating:
- Create a distinct persisted session for each independent assignment.
- Reuse one runtime for several runs when possible.
- Do not issue concurrent requests to the same session.
- Do not treat ordinary delegated sessions as persistent parent-linked
  subagents.
- Check run status and bounded error information before trusting output text.
- Treat a delegated answer as proposed evidence, not automatically as fact.
- Independently verify consequential conclusions.

For a nontrivial investigation, give the child:
- the objective and intended reader;
- exact scope, questions, and source revision;
- mutation, network, credential, and test permissions;
- required evidence and output format;
- timeout, checkpoint, and stop conditions;
- explicit unknowns and non-goals.

Prefer incremental output for long work. Require an early claim map or plan,
record verification as it occurs, and leave a concise final result identifying
completed, partial, blocked, and unverified work.
```

Do not require audit-specific files such as `claims.jsonl` for every delegated
task. Add those only through a task-role block when the work is an audit or
another workflow with a defined evidence packet.

#### Task-specific instruction template

For investigations like the completed compatibility audit, append a separate
role block containing:

- audit purpose and downstream use;
- pinned source revision;
- assigned rows, packages, or decision questions;
- the distinction between product defaults and investigator config;
- exact evidence standard;
- allowed tests and prohibited operations;
- assigned output directory;
- early checkpoint deadline;
- required packet files;
- final readiness status such as `review_ready`, `partial`, or `blocked`.

The successful calibration showed that this system-level role block mattered
substantially more than making the user prompt longer by itself. The access
section should teach mechanics; the task-role section should own evidence,
mutation, verification, and deliverable policy.

#### Optional provider-specific guidance

Do not place model names such as Luna, Terra, or Sol in the generic developer
message. Model behavior, availability, and pricing can change.

A provider-specific optional operational section may instead say:

- use the configured/default variant for ordinary delegation;
- use a faster or lower-cost variant for deterministic broad sweeps;
- increase reasoning only for narrow contradiction resolution or difficult
  synthesis;
- calibrate with one representative assignment before launching a large
  batch;
- enforce time and cost limits;
- do not assume that more tool calls or longer reasoning produces a better
  result.

The observed GPT-5.6 compatibility-audit calibration—Terra/high as the best
default, Luna/high as broad and inexpensive but slower, and xhigh as a
targeted challenge mode—is workload-specific calibration evidence, not a
permanent provider contract.

#### Recommended follow-up decomposition

When this outline is converted into executable follow-up work, group it as:

1. **Direct context and run controls**
   - effective context;
   - instruction inspection and composition;
   - plugin-driven model/reasoning overrides;
   - result telemetry;
   - config overlays and diagnostics.
2. **Batch investigation workflow**
   - one-runtime orchestration;
   - budgets, timeouts, and checkpoints;
   - output/run metadata;
   - cross-session search;
   - safe snapshot projection.
3. **Guidance and documentation**
   - provider-agnostic delegation section;
   - advanced investigation recipe;
   - verification and evidence standards;
   - optional provider-specific calibration guidance.

Persistent child relationships and restart recovery remain owned by the
separate persistent-subagent work. Storage-level projection optimization may
remain a separate performance workstream.
