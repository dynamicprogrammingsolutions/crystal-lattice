# Local headless agent runs technical specification

This is a target specification. Current package-user and implementation
documentation describes the behavior only after the corresponding
requirements are implemented and verified.

## Ownership

`core/python/agent_core` owns the public configured-model discovery wrapper
over the existing plugin hooks, descriptor normalization, and cache.

`core/python/agent_app` owns:

- model discovery through a selected agent's effective configuration;
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
    RunPersistence,
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
runtime.list_agent_descriptors() -> tuple[Mapping[str, Any], ...]
runtime.describe_agent(agent_id) -> Mapping[str, Any]
```

The ID result is deterministic. Detailed descriptors add display metadata,
provider route/plugin identity, safe effective model/reasoning values, and the
flattened plugin config schema. Discovery does not inspect provider
credentials or make an API request.

### Model discovery

```python
runtime.list_models(agent_id: str) -> tuple[Mapping[str, Any], ...]
```

The application resolves the selected agent's effective configured defaults
and enabled plugin catalog, builds a core sharing the application model cache,
and calls public `AgentCore.get_models(config)`. This delegates to the existing
provider, extension, and feature discovery pipeline.

Every descriptor retains a non-empty `id` and all additional plugin metadata,
in plugin-defined order. The convenience method does not create or save a
session or send an inference request. Catalog discovery retains existing
plugin I/O, failure, empty-result, and cache behavior; it does not introduce
an offline mode or another catalog source.

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
    persistence: Literal["persisted", "ephemeral"] = "persisted",
) -> AgentRunResult
```

Rules:

- `prompt` must be a string. Empty input is rejected by the convenience API.
- Exactly one of `agent_id` and `session_id` is required.
- `agent_id` creates a persisted session by default. Ephemeral mode creates
  only an in-memory request session and never writes it to the configured
  session store.
- `session_id` loads an existing writable session and derives its configured
  agent. It does not silently switch agents.
- Ephemeral mode cannot be combined with `session_id`; non-retained runs
  cannot be followed up after the call returns.
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
AgentApplication.run_ephemeral_request_with_message(...)
```

Both paths use `SessionRequestCoordinator` to prepare an optional message
before `_execute(...)`. The prepared request records whether checkpoints
persist. The ephemeral path keeps checkpoint sessions in memory while sharing
the ordinary tool loop, events, timeout, cancellation, and outcome
classification. It must not create and later delete a normal session.

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
    persistence: Literal["persisted", "ephemeral"]
    output_text: str
    final_messages: tuple[Mapping[str, Any], ...]
    error: RunError | None
```

`AgentRunResult` never embeds `final_session`.

`session_id` remains a request-scoped correlation identity in ephemeral mode,
but it does not identify stored history and cannot be used for a follow-up.

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
name. Built-in commands reserve `agents`, `models`, `run`, and `history`,
alongside the session-query commands defined in their owning specification.

### `agents`

```text
crystal-lattice [global options] agents [--details] [--format text|json]
```

Text prints one agent ID per line. JSON prints:

```json
{"agents": ["agent-a", "agent-b"]}
```

With `--details`, JSON also includes `agent_descriptors`; text emits
tab-separated ID, provider route, model, and reasoning effort.

### `models`

```text
crystal-lattice [global options] models --agent ID [--format text|json]
```

The agent selector is required. The command delegates to
`runtime.list_models(agent_id)`. JSON prints one document containing
`agent_id` and the complete `models` array. Default text prints tab-separated
ID, name, and description with one model per line. Missing display fields
produce empty columns; embedded tabs and newlines become spaces.

Initialization, plugin diagnostics, and logs go to stderr. Empty catalogs
are successful empty results under the existing plugin contract. Invalid or
unknown agent selectors use the existing usage-error behavior.

### `run`

```text
crystal-lattice [global options] run
  (--agent ID | --session ID)
  (--prompt TEXT | --prompt-file PATH | --stdin)
  [--set KEY=VALUE ...]
  [--ephemeral]
  [--format text|json]
  [--timeout SECONDS]
  [--no-progress]
```

Prompt-source and session-selector groups are mutually exclusive and required.
Prompt files and stdin are decoded as UTF-8. Empty prompts and invalid finite
timeouts are usage errors.

Repeated `--set` assignments decode valid JSON values and otherwise retain
string values before passing one request-scoped override mapping.
`--ephemeral` is valid only with `--agent`; it preserves progress and result
behavior without writing a canonical session.

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
[session and message data query](../session-data-query/index.md) refines the
local runtime and one-shot CLI. It adds complete
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
`CRYSTAL_LATTICE_ACCESS` and `CRYSTAL_LATTICE_CLI_ACCESS` at the end of the
template. One shared config mixin owns both complete access values plus a
separate `CRYSTAL_LATTICE_DELEGATION_GUIDANCE` value for parent behavior, with
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
- `include_crystal_lattice_delegation_guidance()` requires the user opt-in and
  a valid CLI capability, so it accompanies either access variant;
- invalid CLI capability makes both predicates false, even when a true
  override was previously persisted.

When disabled by the user, both variables render empty and do not change the
prior compiled prompt after surrounding trailing whitespace is stripped.

The full bounded section:

- identifies the authoritative CLI command;
- shows agent and model discovery, initial run, follow-up, and compact-history forms;
- identifies the general interpreter and `agent_terminal_app` import;
- provides a complete `open_runtime(config_path=..., session_root=...)`
  example;
- identifies local docs when present and always supplies the public docs URL;
- explains persisted and non-retained synchronous sessions;
- does not claim persistent subagent, parent-child, mid-run input, or detached
  lifetime semantics.

The CLI-only section contains the same CLI and documentation guidance and
limitations, explicitly identifies itself as CLI-only, and contains no Python
SDK instruction or import claim.

The separate delegation section is addressed only to the parent agent. It
states that a child receives the selected configured agent's own
system/developer message and a self-contained user prompt constructed by the
parent. It prohibits copying the parent's system message, hidden reasoning, or
conversation transcript into the child prompt and explains agent/setting
selection, progress, result validation, persistence, and follow-up behavior.

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

A second independently gated behavior scenario gives the parent a sparse,
read-only roadmap/task-status review request. The parent must construct a
self-contained child user prompt and invoke either the CLI or Python SDK in
ephemeral mode. Acceptance requires the correct review finding, production
tool-call evidence containing the child scope, and exactly one retained
session: the parent.

Run it explicitly from the repository root:

```bash
RUN_CRYSTAL_LATTICE_OLLAMA_SUBAGENT_E2E=1 \
PYTHONPATH="$PWD/core/python:$PWD/application/python" \
pytest application/python/tests/test_crystal_lattice_access_ollama_api.py \
  -m "integration and api and ollama" -q
```

For only the ephemeral review scenario, select its test and use:

```bash
RUN_CRYSTAL_LATTICE_OLLAMA_EPHEMERAL_REVIEW_E2E=1 \
PYTHONPATH="$PWD/core/python:$PWD/application/python" \
pytest application/python/tests/test_crystal_lattice_access_ollama_api.py \
  -m "integration and api and ollama" \
  -k ephemeral_self_contained_review -q
```

A separately gated OpenAI acceptance scenario uses `gpt-5.6-luna` as the parent
and asks it to delegate a short document-status review to `gpt-6-luna`, without
retaining the child session. Both calls use the same configured Codex agent,
whose default model is the parent's model, so the child model requires a real
request-scoped override. The parent receives the shipped model-specific
instructions and config-owned access/delegation guidance; its user prompt
supplies no CLI or SDK invocation recipe. It can choose either route through
the standard Codex shell tools.

Test-only observers forward the production provider calls and streamed events
unchanged. They record the actual outbound model, bounded initial child user
prompt, instruction fingerprints, and completed answer. A session-store
observer detects saves and snapshots throughout the run, including a child
that might otherwise be persisted and subsequently deleted. No credentials or
reasoning are included in these evidence records. Acceptance also checks the
child's own GPT-6 instructions without the parent's delegation section, the
self-contained scope and read-only constraint, the planted discrepancy in both
answers, production tool-call evidence, and unchanged input files.

This scenario requires saved ChatGPT credentials. An explicitly enabled run
fails if prerequisites or the requested model are unavailable; it does not
substitute another model or turn that failure into a skipped success.

```bash
RUN_CRYSTAL_LATTICE_OPENAI_EPHEMERAL_REVIEW_E2E=1 \
PYTHONPATH="$PWD/core/python:$PWD/application/python" \
pytest application/python/tests/test_crystal_lattice_access_openai_api.py \
  -m "integration and api and openai" -q -s
```

Set `CHATGPT_CREDENTIALS` to select another saved login; otherwise the test uses
`~/.crystal/auth/chatgpt-auth.json`. The review fixture, isolated config, parent
session, bounded delegation evidence, and stderr log live under pytest's
temporary directory.

A separate model-discovery scenario gives the same real `gpt-5.6-luna`
parent a short request to discover the available models and identify Luna
models. The prompt contains no command or SDK recipe. A forwarding observer
on `LocalAgentRuntime.list_models` records the discovered public model fields,
proving that a production tool used the advertised CLI or SDK surface. The
final answer must contain the discovered Luna IDs, and enumeration must not
create additional sessions.

```bash
RUN_CRYSTAL_LATTICE_OPENAI_MODEL_DISCOVERY_E2E=1 \
PYTHONPATH="$PWD/core/python:$PWD/application/python" \
pytest application/python/tests/test_crystal_lattice_access_openai_api.py::test_luna_parent_discovers_models_from_access_guidance \
  -m "integration and api and openai" -q -s
```

It uses the same saved-login prerequisite and explicit-gate failure behavior
as the review scenario.

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
