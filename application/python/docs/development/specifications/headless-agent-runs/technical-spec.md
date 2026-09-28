# Local headless agent runs technical specification

This is a target specification. Current package-user and implementation
documentation describes the behavior only after the corresponding
requirements are implemented and verified.

## Ownership

`core/python/agent_app` owns:

- atomic synchronous message admission and request execution;
- raw public event observation during coordinated execution;
- request outcome classification;
- compact history projection and canonical full-message lookup.

`application/python/agent_terminal_app` owns:

- local configuration and runtime construction;
- the public convenience types and methods;
- bounded progress normalization;
- command parsing and rendering;
- stdout/stderr separation;
- signal, timeout, and process exit behavior.

The convenience runtime delegates to `AgentApplication`. It does not maintain
another session store, active-request map, event store, request worker, or
cancellation authority.

## Public Python surface

The application package exports these public concepts:

```python
from agent_terminal_app import (
    AgentRunResult,
    CompactHistory,
    CompactMessage,
    LocalAgentRuntime,
    RunProgress,
    open_runtime,
)
```

Exact annotations may use package type aliases, but these names and behavioral
roles are the target contract.

### Opening a runtime

`open_runtime(...)` is a context manager returning `LocalAgentRuntime`.

Supported inputs include:

```python
open_runtime(
    *,
    config_path: str | Path | None = None,
    session_root: str | Path | None = None,
)
```

When no config path is supplied, resolution searches:

1. `<working-directory>/.crystal/config.json`;
2. `~/.crystal/config.json`.

For the Python API, absence of both files is an error with an actionable
message. A library call does not silently create user files. The CLI may retain
its existing default-config creation behavior before it opens the same
resolved runtime.

An explicit missing Python `config_path` is an error. The CLI's existing
explicit-config creation behavior remains compatible unless command-specific
validation identifies a user-safety conflict.

The runtime uses the same dotenv collection and precedence as the application
command:

1. existing process environment;
2. `.env` beside the active config;
3. `<working-directory>/.crystal/.env`;
4. `~/.crystal/.env`;
5. standard working-directory parent discovery.

The runtime resolves application layout environment values, session storage,
filesystem snapshot selection, and a usable application notification store.
It owns every store it constructs and closes in reverse dependency order.

The runtime does not construct:

- `AgentApplicationOwner`;
- HTTP/FastAPI;
- Bonjour or bridge clients;
- project profile state;
- managed live reload.

### Agent discovery

```python
runtime.list_agents() -> tuple[str, ...]
```

The result contains configured agent IDs in deterministic application order.
It does not inspect provider credentials or make an API request.

### Running a task

```python
runtime.run(
    prompt: str,
    *,
    agent_id: str | None = None,
    session_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    multipart_content: Sequence[Mapping[str, Any]] | None = None,
    overrides: Mapping[str, Any] | None = None,
    stream: bool = True,
    timeout: float | None = None,
    on_progress: Callable[[RunProgress], None] | None = None,
) -> AgentRunResult
```

Rules:

- `prompt` must be a string. Empty input is rejected by the convenience API.
- Exactly one of `agent_id` and `session_id` is required.
- `agent_id` creates and persists a new session before request admission.
- `session_id` loads an existing writable session and derives its configured
  agent. It does not silently switch agents.
- The user message is admitted, appended, and run through one coordinated
  operation.
- A same-session admission conflict does not append the message.
- Request overrides remain request-scoped and follow existing merge
  precedence.
- The method blocks until success, failure, cancellation, interruption, or a
  non-cooperative timeout cleanup boundary.

The lower application API adds:

```python
AgentApplication.run_session_request_with_message(...)
```

It is implemented by allowing `SessionRequestCoordinator.run(...)` to prepare
an optional message before `_execute(...)`. It must not call a standalone
append method followed by `run_session_request(...)`.

## Outcome contract

The coordinated result gains:

```python
status: Literal["succeeded", "failed", "cancelled", "interrupted"]
error: RunError | None
```

Existing `SessionRequestResult` fields remain available for compatibility.
The public convenience layer converts it to:

```python
@dataclass(frozen=True)
class AgentRunResult:
    status: Literal["succeeded", "failed", "cancelled", "interrupted"]
    session_id: str
    request_id: str
    agent_id: str
    output_text: str
    final_messages: tuple[Mapping[str, Any], ...]
    error: RunError | None
```

`AgentRunResult` never embeds `final_session`.

`output_text` concatenates non-empty final assistant-message content in event
order, separated by one newline. Other final messages remain available in
`final_messages` and do not enter text output implicitly.

Outcome classification is deterministic:

- `cancelled` when the request emitted cancellation;
- `failed` when it emitted a fatal error;
- `succeeded` when it reached a final assistant response without later fatal
  error or cancellation;
- `interrupted` when execution ended without any of those terminal facts.

An observed cancellation event outranks failure. Otherwise an explicit fatal
error outranks an earlier intermediate final event.

`RunError` contains a stable category and bounded user-safe message. It does
not include a traceback, provider-native response, headers, configuration,
environment, or complete event. Raw details remain in configured logs and
existing low-level events according to their current contract.

## Progress contract

`RunProgress` is immutable and bounded:

```python
@dataclass(frozen=True)
class RunProgress:
    kind: Literal[
        "request_started",
        "assistant_started",
        "assistant_progress",
        "tool_started",
        "tool_progress",
        "tool_completed",
        "request_failed",
        "request_cancelled",
        "request_completed",
    ]
    session_id: str
    request_id: str
    message: str
    tool_name: str | None = None
    tool_call_id: str | None = None
```

Progress normalization consumes the public events observed by the coordinator.
It does not require polling the event store. Internal session checkpoints are
not exposed.

The normalizer:

- collapses whitespace in human text;
- enforces a fixed maximum progress-message length;
- prefers safe tool `metadata.display.single_line` content;
- omits complete tool results and tool arguments;
- omits provider-native and multipart data;
- may suppress token-level partial events that provide no useful bounded
  progress;
- preserves event order for records it emits.

The same normalization drives CLI stderr progress.

The callback runs synchronously on the request thread and must return promptly.
If it raises, the runtime requests cancellation, completes bounded cleanup,
and re-raises the callback exception. Callback failure is not converted into a
model failure result.

The existing event store and raw events remain unchanged.

## Cancellation and timeout

`AgentApplication.cancel_request(request_id)` remains the cancellation
authority.

For a finite positive timeout, coordinated synchronous execution arranges a
timer after request ID allocation. At expiry it cancels that request. The
timer is always disarmed during cleanup.

Cancellation is cooperative. A provider or tool that does not observe
cancellation may finish its current blocking operation. The Python call and
CLI wait for the coordinator to leave the session in its existing persisted
checkpoint state; they do not abandon an unowned worker.

The public result reports `cancelled`. The CLI maps a timeout-triggered
cancellation to timeout exit behavior while an interactive interrupt maps to
interrupt exit behavior.

## Concurrency

One `LocalAgentRuntime` may execute distinct sessions from ordinary Python
threads. The application coordinator remains the single-flight authority per
session.

The runtime introduces no executor and returns no durable async handle.
Callers use `concurrent.futures` when needed.

Direct CLI processes may run distinct sessions concurrently. Cross-process
same-session mutual exclusion is not guaranteed. Documentation warns against
using direct commands as simultaneous writers to one session.

## Compact history

Compact history is a deterministic derived view of a persisted `Session`.

### Python methods

```python
runtime.history(
    session_id: str,
    *,
    start: int | None = None,
    end: int | None = None,
    roles: Collection[str] | None = None,
    max_messages: int = 100,
    max_content_chars: int = 500,
    max_total_content_chars: int = 20_000,
) -> CompactHistory

runtime.get_message(session_id: str, index: int) -> Mapping[str, Any]
```

Bounds use Python slice semantics, including negative values. The projector:

1. resolves the canonical range;
2. applies role filtering;
3. retains the newest `max_messages` selected rows;
4. allocates the total content budget from newest to oldest;
5. returns retained rows in canonical chronological order.

This preserves the most recent conversation while making omission
deterministic.

### Result schema

```python
@dataclass(frozen=True)
class CompactMessage:
    index: int
    role: str
    content: str
    content_length: int
    content_truncated: bool
    content_omitted: bool
    tool_name: str | None = None
    tool_call_id: str | None = None
    tool_status: str | None = None


@dataclass(frozen=True)
class CompactHistory:
    session_id: str
    messages: tuple[CompactMessage, ...]
    selected_message_count: int
    omitted_message_count: int
    content_characters: int
    max_messages: int
    max_content_chars: int
    max_total_content_chars: int
```

For tool messages, display content is selected in this order:

1. non-empty `metadata.display.single_line`;
2. supported text display fallback;
3. normalized canonical content.

All selected content is whitespace-normalized and bounded. Tool-call
arguments, unrestricted metadata, complete native messages, and multipart
content are excluded.

For non-tool messages, compact content is the normalized canonical `content`.
Metadata is excluded except for explicitly normalized role-specific scalar
identifiers.

`get_message(...)` returns a newly serialized canonical message for one
explicit index, including its full supported fields. Negative indices follow
Python indexing. An invalid index raises a public range error.

Projection never mutates the `Session`, persists a projection, or updates a
cursor.

## CLI contract

The existing top-level parser retains global runtime flags before its command
name. Built-in commands reserve `agents`, `run`, and `history`.

### `agents`

```text
crystal-lattice [global options] agents [--format text|json]
```

Text prints one agent ID per line. JSON prints:

```json
{"agents": ["agent-a", "agent-b"]}
```

### `run`

```text
crystal-lattice [global options] run
  (--agent ID | --session ID)
  (--prompt TEXT | --prompt-file PATH | --stdin)
  [--format text|json]
  [--timeout SECONDS]
  [--no-progress]
```

Prompt-source and session-selector groups are mutually exclusive and required.
Prompt files and stdin are decoded as UTF-8. Empty prompts and invalid finite
timeouts are usage errors.

Default progress is bounded human text on stderr. `--no-progress` suppresses
normal progress but not errors.

Text stdout contains only `AgentRunResult.output_text`, followed by one final
newline when non-empty. JSON stdout contains one compact result object and one
final newline.

Application logs, startup summaries, direct initialization prints, plugin
diagnostics, and progress are routed away from stdout during these one-shot
commands. JSON is parsed in subprocess acceptance tests.

### `history`

Compact form:

```text
crystal-lattice [global options] history
  --session ID
  [--start INDEX]
  [--end INDEX]
  [--role ROLE ...]
  [--format text|json]
```

Full-message form:

```text
crystal-lattice [global options] history
  --session ID
  --index INDEX
  [--format text|json]
```

`--index` cannot be combined with range or role selection. Text compact output
uses canonical indices and bounded one-line content. Full text clearly labels
the selected index and may contain long or sensitive canonical content because
the user explicitly requested it. JSON mirrors the Python compact/full
schemas.

### Exit behavior

| Exit code | Meaning |
|---|---|
| `0` | Successful command or successful agent run |
| `1` | Agent/application failure or interrupted run |
| `2` | Argument, configuration, agent, session, or input error |
| `124` | Timeout-triggered cancellation |
| `130` | User interrupt |

Failure diagnostics go to stderr. JSON stdout remains either one complete
result document or empty when execution fails before a run result exists.

## Compatibility

- Existing `AgentApplication.run_session_request(...)` call sites retain their
  behavior.
- Existing background request start objects and event routes remain unchanged.
- New fields on `SessionRequestResult` have compatible defaults where direct
  fixture construction requires them.
- Existing terminal progress and `/list short` remain supported.
- The compact projector may share pure display-selection helpers with terminal
  rendering, but terminal rendering does not become the data authority.
- HTTP and frontend contracts do not change.

The separately specified
[session and message data query](../session-data-query/index.md) is a future
refinement of the local runtime and one-shot CLI. It adds complete
session/message enumeration and projection through new methods and commands;
it does not change the existing `agents`, `run`, compact `history`, or
full-message `history --index` behavior. Its HTTP and frontend changes are
owned by that specification rather than this specification's original
compatibility boundary.

## External-project access

The direct Python and CLI requirements were verified before this contract was
selected. Requirements `HLR-060` and `HLR-061` define the follow-on capability.

### Runtime access values

The application derives these runtime-owned values after resolving the active
config and session root:

| Variable | Value |
|---|---|
| `CRYSTAL_LATTICE_CLI_ARGV_JSON` | JSON string array containing the authoritative CLI prefix, active `--config`, and active `--sessions-dir` |
| `CRYSTAL_LATTICE_CLI_COMMAND` | Platform-shell-rendered form of the same authoritative CLI prefix |
| `CRYSTAL_LATTICE_CONFIG` | Absolute active config path |
| `CRYSTAL_LATTICE_SESSIONS` | Absolute active session root |
| `CRYSTAL_LATTICE_PYTHON` | Absolute general Python interpreter when available |
| `CRYSTAL_LATTICE_PYTHON_API_MODULE` | `agent_terminal_app` when that interpreter can import the supported API |
| `CRYSTAL_LATTICE_DOCS` | Absolute local application-documentation directory when available |
| `CRYSTAL_LATTICE_DOCS_URL` | `https://docs.crystallattice.dev/packages/application-python/headless-agent-runs/` |
| `CRYSTAL_LATTICE_SYSTEM_MESSAGES` | Absolute runtime-owned system-message resource directory, including the reusable access helper |

These values are explicit `env_overrides` installed by the application's
runtime environment overlay, like `BUILTIN_PLUGINS`. A known runtime identity
outranks inherited values with the same names. They contain no provider
credentials or auth/cache paths.

The canonical execution value remains JSON argv. The application additionally
renders `CRYSTAL_LATTICE_CLI_COMMAND` for config-owned prompt text, using
`shlex.join` on POSIX and a PowerShell-compatible invocation on Windows.
Programmatic consumers should prefer the argv value.

Including the config and session root is mandatory. A child command inherits
the external project's current directory for tool behavior while continuing
to use the exact Crystal Lattice configuration and session store advertised by
the parent runtime.

### Runtime layouts

Source checkouts use:

```text
[sys.executable, "-m", "agent_terminal_app",
 "--config", <active-config>,
 "--sessions-dir", <active-session-root>]
```

The source interpreter is advertised for Python API use. Local docs resolve to
`application/python/docs` when present.

Bundled-Python archives use their manifest-selected packaged interpreter with
the same module/config/session arguments. They advertise the staged
`application/python/docs` directory. Both executable and docs paths remain
relative to the relocated runtime manifest before being resolved to absolute
values.

Optimized PyInstaller layouts use the frozen executable followed by the
config/session arguments. They advertise staged local docs and the public URL,
but omit `CRYSTAL_LATTICE_PYTHON` and
`CRYSTAL_LATTICE_PYTHON_API_MODULE`: the frozen executable is not a general
Python interpreter or import host. This is a valid CLI-only capability rather
than a full capability or an unavailable runtime.

Pip and pipx installation are not supported product layouts and do not define
fallback behavior in this contract.

### Opt-in system-message section

Maintained default Codex, Qwen, Gemini, Grok, Kimi, and Claude templates expose
both `CRYSTAL_LATTICE_ACCESS` and `CRYSTAL_LATTICE_CLI_ACCESS` at the end of
the template. One shared config mixin owns both complete Markdown values with
explicit named runtime placeholders and mappings to the corresponding
environment values. Helper Python contains no operational instruction prose.

The variable-level runtime helper contributes:

```text
include_crystal_lattice_access: bool = false
```

and one config checkbox. It is independent from `include_tasks`.

The predicates are mutually exclusive:

- `include_crystal_lattice_access()` requires the user opt-in and valid CLI,
  interpreter, API module, config, session, and docs values;
- `include_crystal_lattice_cli_access()` requires the same user opt-in, valid
  CLI/config/session/docs values, and the absence of a valid full capability;
- invalid CLI capability makes both predicates false, even when a true
  override was previously persisted.

When disabled by the user, both variables render empty and do not change the
prior compiled prompt after surrounding trailing whitespace is stripped.

The full bounded section:

- identifies the authoritative CLI command;
- shows agent discovery, initial run, follow-up, and compact-history forms;
- identifies the general interpreter and `agent_terminal_app` import;
- provides a complete `open_runtime(config_path=..., session_root=...)`
  example;
- identifies local docs when present and always supplies the public docs URL;
- says that these commands create ordinary persisted synchronous sessions;
- does not claim persistent subagent, parent-child, mid-run input, or detached
  lifetime semantics.

The CLI-only section contains the same CLI and documentation guidance and
limitations, explicitly identifies itself as CLI-only, and contains no Python
SDK instruction or import claim.

The one UI element:

- identifies full CLI+SDK mode when full values are valid;
- identifies CLI-only mode when only CLI values are valid;
- remains visible with `disabled: true`, `default: false`, and a concrete
  description of missing or invalid CLI values when unavailable.

The helper reads only the named runtime access variables to validate
availability and return predicates/UI. It does not enumerate the environment
or include provider configuration values.

New generated default configs contain the disabled section. Existing user and
project configs are not rewritten; current documentation provides an explicit
adoption example.

### Real Ollama delegation acceptance

An opt-in integration test marked `integration`, `api`, and `ollama` uses
`glm-5.3-flash:cloud` through the local Ollama OpenAI-compatible endpoint.

The test:

1. requires an explicit environment gate;
2. creates an external temporary project with a non-guessable marker;
3. creates one isolated config and session root containing an outer
   orchestrator and separate worker agent;
4. enables `include_crystal_lattice_access` only for the outer request;
5. gives the outer model a sparse prompt that requests a subagent result but
   names no command, flags, agent ID, file, or procedure;
6. requires the outer model to invoke the advertised Crystal Lattice CLI;
7. verifies a new worker session in the same session root, with a completed
   response containing the marker;
8. verifies the outer tool/session history records delegation and its final
   response reports the worker result.

A textual statement that delegation occurred does not pass without the
separate persisted worker session. The worker's access section remains
disabled to prevent recursive delegation.

Unavailable Ollama service or cloud authentication is reported as a skipped or
blocked gated test, not converted to a deterministic fake. The test is excluded
from default credential-free suites.

Run it explicitly from the repository root:

```bash
RUN_CRYSTAL_LATTICE_OLLAMA_SUBAGENT_E2E=1 \
PYTHONPATH="$PWD/core/python:$PWD/application/python" \
pytest application/python/tests/test_crystal_lattice_access_ollama_api.py \
  -m "integration and api and ollama" -q
```

### Native installation and model-mediated acceptance

Credential-free distribution probes execute one deterministic task through
the actual `crystal-lattice run` entry point and another through the packaged
interpreter plus `open_runtime(...)`. Source installation, direct
archive/manual use, Bash installation, and PowerShell installation each verify
the complete access values with isolated paths containing spaces.

A separate release-gated scenario runs once per native target against the
extracted bundled-Python archive. Its outer
`anthropic/claude-haiku-4.5` OpenRouter agent receives one sparse CLI-route
request and one sparse SDK-route request. Deterministic child agents avoid
additional hosted calls. Acceptance requires production tool-call evidence,
the exact config/session identity, and separately persisted completed child
sessions; text-only claims fail.

The OpenRouter credential is resolved into the constructed outer provider and
removed from the process environment before model-controlled tools execute.
Child configs and environments must not contain it. The real scenario is
mandatory for release tags, opt-in for workflow dispatch, and absent from
public pull-request/fork execution.

Run the current-platform archive scenario explicitly with:

```bash
RUN_CRYSTAL_LATTICE_OPENROUTER_ACCESS_E2E=1 \
OPENROUTER_API_KEY=... \
CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE=/path/to/current-platform-archive \
npm run test:cli:agent-access
```

One-off Detox evidence confirms that full, CLI-only, and unavailable UI
elements render with the expected labels, descriptions, and disabled state.
The temporary Detox scenario is removed after the run; deterministic
component tests retain the permanent protocol coverage.

## Verification boundaries

- Unit tests own coordinator classification, progress normalization, history
  projection, and argument validation.
- Package-user tests own runtime construction, initial runs, follow-ups,
  concurrency, and cleanup.
- Real subprocess tests own CLI I/O, progress, signals, timeout, exit codes,
  and parseable JSON.
- Existing application tests own terminal and background-request compatibility.
- The explicitly gated Ollama `glm-5.3-flash:cloud` test owns real
  source CLI delegation evidence.
- Native distribution probes own per-installation CLI/SDK and access-value
  evidence.
- The release-gated OpenRouter scenario owns real model-mediated CLI and SDK
  evidence on all six native targets.
- One-off Detox owns final native presentation evidence; component tests own
  permanent disabled-state regression coverage.
