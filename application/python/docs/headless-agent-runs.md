# Run configured agents from Python or the command line

Crystal Lattice can run a configured agent without starting the interactive
terminal or HTTP server. A run creates or continues an ordinary persisted
session by default, or executes one non-retained turn when requested. Both
modes report bounded progress and return the final result directly.

Use this workflow for scripts, local automation, parallel investigations, and
follow-up prompts whose sessions should remain visible in other Crystal
Lattice frontends.

## Prerequisites

Use the supported bundled-Python command or a source checkout, and configure at
least one agent:

```bash
crystal-lattice agents
```

The command prints one configured agent ID per line:

```text
claude-openrouter
codex-openai
```

Use `--format json` for machine-readable discovery:

```bash
crystal-lattice agents --format json
```

```json
{"agents":["claude-openrouter","codex-openai"]}
```

Add `--details` to inspect safe effective defaults and configurable fields
without making a provider request:

```bash
crystal-lattice agents --details --format json
```

Python callers use `runtime.list_agent_descriptors()` or
`runtime.describe_agent(agent_id)`. Descriptors contain display metadata, the
provider route and plugin, safe effective model/reasoning values, and the
flattened plugin config schema. They do not contain credentials.

Global options precede the standalone command. For example:

```bash
crystal-lattice \
  --config ~/.crystal/config.json \
  --sessions-dir ./.crystal/sessions \
  agents
```

## Python first run

The public local API is provided by the `crystal-lattice-cli` distribution's
`agent_terminal_app` module:

```python
from agent_terminal_app import RunProgress, open_runtime


def report(progress: RunProgress) -> None:
    print(progress.message)


with open_runtime() as runtime:
    result = runtime.run(
        "Inspect this project's test strategy.",
        agent_id="claude-openrouter",
        on_progress=report,
    )

print(result.status)
print(result.session_id)
print(result.output_text)
```

`open_runtime()` searches for configuration in this order:

1. `./.crystal/config.json`;
2. `~/.crystal/config.json`.

Unlike the CLI, the Python helper does not create a missing configuration.
Pass `config_path` and `session_root` when the defaults are not appropriate:

```python
from agent_terminal_app import open_runtime


with open_runtime(
    config_path="/workspace/.crystal/config.json",
    session_root="/workspace/.crystal/sessions",
) as runtime:
    result = runtime.run("Review README.md.", agent_id="codex-openai")
```

The runtime loads dotenv values using the same config, project, user, and
working-directory precedence as the command. Existing process-environment
values continue to win.

Always close the runtime, preferably with `with`. It owns plugin processes,
the application async runtime, environment overlays, event state, and its
notification and snapshot-selection adapters.

## Results

`runtime.run(...)` returns `AgentRunResult`:

```python
result.status          # succeeded, failed, cancelled, or interrupted
result.session_id      # persisted session or ephemeral correlation identity
result.request_id      # request cancellation and diagnostic identity
result.agent_id        # configured agent used by the session
result.persistence     # persisted or ephemeral
result.output_text     # final assistant text
result.final_messages  # final response messages
result.error           # bounded RunError or None
```

The result intentionally does not contain the complete serialized session.
Earlier messages, provider-native state, and long tool output therefore do not
enter a calling script merely because it needs the final answer.

An error contains a stable category and bounded message without a traceback or
complete provider response. Use configured logs or the lower-level event API
when deeper diagnostics are necessary.

## Request-scoped settings

Python callers pass provider/plugin settings through `overrides`:

```python
result = runtime.run(
    "Inspect the project.",
    agent_id="codex-openai",
    overrides={
        "model": "gpt-5.6-luna",
        "reasoning_effort": "high",
    },
)
```

Use `runtime.describe_agent(...)` to discover the selected agent's flattened
config schema. Overrides apply only to that request and do not mutate the
source config or a persisted session's stored settings.

## Progress

Pass `on_progress` to observe request and tool activity:

```python
def report(progress: RunProgress) -> None:
    tool = f" [{progress.tool_name}]" if progress.tool_name else ""
    print(f"{progress.kind}{tool}: {progress.message}")


with open_runtime() as runtime:
    result = runtime.run(
        "Run the relevant tests and summarize failures.",
        agent_id="codex-openai",
        on_progress=report,
    )
```

Progress records are ordered and bounded. They can identify request,
assistant, and tool phases, but they do not carry complete tool results,
provider-native payloads, tool arguments, or multipart bodies.

The callback runs synchronously and should return promptly. If it raises,
Crystal Lattice requests cancellation, completes request cleanup, and
re-raises the callback exception.

Raw public events remain available from the lower-level `AgentApplication`
API for applications that need the complete event contract.

## Follow up in the same session

Use the first result's `session_id`:

```python
with open_runtime() as runtime:
    first = runtime.run(
        "Compare the two provider adapters.",
        agent_id="claude-openrouter",
    )
    follow_up = runtime.run(
        "Focus only on cancellation behavior.",
        session_id=first.session_id,
    )

print(follow_up.output_text)
```

The follow-up uses the persisted conversation and the agent already attached
to the session. It does not silently switch agents.

Message append and request admission are one operation. If the session already
has an active request in this application process, the follow-up is rejected
and its proposed message is not appended.

## Non-retained runs

Use an ephemeral run when one answer is needed and no child session should
remain visible in Crystal Lattice:

```python
with open_runtime() as runtime:
    result = runtime.run(
        "Inspect these files and return a concise finding.",
        agent_id="codex-openai",
        persistence="ephemeral",
    )
```

The request uses the same configured agent, tool loop, progress, timeout,
cancellation, and result contracts. Session checkpoints remain in memory and
no canonical session file is written. `result.session_id` is a request-scoped
correlation identity, not a reusable persisted session. Ephemeral runs cannot
be continued by `session_id`.

Operational logs and separately configured provider usage/cost stores are not
session storage and may still retain their normal bounded records.

## Parallel Python runs

Use normal Python futures for distinct sessions:

```python
from concurrent.futures import ThreadPoolExecutor

from agent_terminal_app import open_runtime


assignments = [
    ("Inspect provider behavior.", "claude-openrouter"),
    ("Inspect CLI behavior.", "codex-openai"),
]

with open_runtime() as runtime:
    with ThreadPoolExecutor(max_workers=len(assignments)) as executor:
        futures = [
            executor.submit(runtime.run, task, agent_id=agent)
            for task, agent in assignments
        ]
        results = [future.result() for future in futures]
```

One runtime can run distinct sessions from different threads. Do not submit
concurrent calls to the same session.

## Compact history

Load a bounded view without full tool output:

```python
with open_runtime() as runtime:
    history = runtime.history(
        result.session_id,
        start=-50,
        roles={"user", "assistant", "tool"},
    )

for item in history.messages:
    print(item.index, item.role, item.content)
```

Compact rows contain:

- the canonical message index and role;
- bounded whitespace-normalized content;
- the canonical text length;
- explicit truncated and omitted flags;
- small tool identifiers and status when available.

Tool messages prefer a plugin-provided `metadata.display.single_line` summary.
They otherwise use a bounded deterministic fallback. Provider-native history,
unrestricted metadata, multipart content, and binary data are excluded.

Default bounds retain at most the newest 100 selected messages, at most 500
content characters per row, and at most 20,000 content characters overall.
Range selection happens before role filtering. Content budgets are allocated
from newest to oldest, and retained rows are returned in chronological order.

Retrieve one canonical message explicitly when its complete content is needed:

```python
full = runtime.get_message(result.session_id, index=7)
print(full["message"]["content"])
```

Negative indices use Python indexing. A full message may contain long or
sensitive tool, metadata, or multipart fields; request it only when needed.

Neither operation modifies session history.

For complete ranges with caller-selected fields, plugin-filtered session
enumeration, and JSON/text shell pipelines, see
[Query sessions and messages](session-data-query.md).

## Command-line runs

Run one task:

```bash
crystal-lattice run \
  --agent codex-openai \
  --prompt "Inspect the package tests."
```

Inspect agent defaults, apply request-scoped settings, and avoid retaining a
session:

```bash
crystal-lattice agents --details --format json
crystal-lattice run \
  --agent codex-openai \
  --set model=gpt-5.6-luna \
  --set reasoning_effort=high \
  --ephemeral \
  --prompt-file investigation.md \
  --format json
```

`--set` may be repeated. JSON values such as `true`, `42`, arrays, and objects
are decoded; other values remain strings. Settings use the same generic config
keys exposed by the selected agent's schema.

For multiline or sensitive input, prefer a file or stdin over a shell argument:

```bash
crystal-lattice run \
  --agent codex-openai \
  --prompt-file investigation.md
```

```bash
crystal-lattice run \
  --agent codex-openai \
  --stdin < investigation.md
```

Exactly one of `--agent` and `--session`, and exactly one of `--prompt`,
`--prompt-file`, and `--stdin`, is required.

Continue a completed session:

```bash
crystal-lattice run \
  --session "<session-id>" \
  --prompt "Now verify the documentation."
```

Text mode prints only final assistant text to stdout. Progress and the
session/request identity go to stderr. An ephemeral text run labels the
identity as request-scoped and does not advertise it for follow-up.

## JSON output

Use JSON for orchestration:

```bash
crystal-lattice run \
  --agent codex-openai \
  --prompt-file investigation.md \
  --format json \
  > result.json \
  2> progress.log
```

Stdout contains exactly one JSON document:

```json
{
  "status": "succeeded",
  "session_id": "<session-id>",
  "request_id": "<request-id>",
  "agent_id": "codex-openai",
  "persistence": "persisted",
  "output_text": "<assistant response>",
  "final_messages": [
    {
      "role": "assistant",
      "content": "<assistant response>"
    }
  ],
  "error": null
}
```

Application logs, startup output, and progress are kept away from stdout.
`--no-progress` suppresses ordinary progress but not errors.

## Command-line history

Inspect compact history:

```bash
crystal-lattice history \
  --session "<session-id>" \
  --start -50
```

Filter roles and use JSON:

```bash
crystal-lattice history \
  --session "<session-id>" \
  --start -50 \
  --role user \
  --role assistant \
  --format json
```

Retrieve one full message:

```bash
crystal-lattice history \
  --session "<session-id>" \
  --index 7 \
  --format json
```

`--index` cannot be combined with range or role options.

## Parallel shell runs

Use ordinary shell process control and distinct sessions:

```bash
crystal-lattice run --agent codex-openai --prompt-file code.md \
  --format json > code.json 2> code.progress &
code_pid=$!

crystal-lattice run --agent claude-openrouter --prompt-file docs.md \
  --format json > docs.json 2> docs.progress &
docs_pid=$!

wait "$code_pid" "$docs_pid"
```

The direct commands do not provide cross-process same-session locking. Do not
use separate CLI processes as simultaneous writers to one session. Use a
distinct session for each parallel assignment.

## Let a configured agent delegate from another project

Newly generated default configurations include an optional system-message
section that tells an agent how to use this exact Crystal Lattice runtime from
the current project, even when that project was not launched by Crystal
Lattice.

Enable it for one session:

```text
/set include_crystal_lattice_access true
```

Mobile and desktop session settings expose the access checkbox through the
normal configuration schema. The setting defaults to off and is independent
from **Include TASKS Guidance**.

Source checkouts and bundled-Python distributions show **Include Crystal
Lattice Access Guidance**. When enabled, the agent receives:

- an authoritative CLI argument vector rendered as a correctly quoted command;
- the active `--config` and `--sessions-dir`, so delegated calls cannot select
  an unrelated project config or session store;
- examples for agent discovery, initial runs, completed-session follow-ups,
  compact history, session enumeration, and projected canonical messages;
- the applicable Python interpreter and
  `from agent_terminal_app import open_runtime` when a general Python runtime
  is available;
- local application documentation when included in the runtime and the public
  documentation URL.

Optimized frozen executables show **Include Crystal Lattice Access Guidance
(CLI only)**. Their separately authored section includes CLI and documentation
instructions, explicitly says that no supported general Python SDK is
available, and never emits an SDK import or interpreter claim.

If the CLI/config/session/documentation values are absent or invalid, the
setting remains visible as **Include Crystal Lattice Access Guidance
(unavailable)**. It is disabled and its description names the missing or
invalid values. A previously stored true override cannot compile either
section in that state.

The config owns a separate parent-only delegation section after the access
mechanics. It tells the parent agent that a child receives the selected
agent's own configured system/developer message while the parent supplies a
self-contained child user prompt. The parent is told not to copy its system
message, hidden reasoning, or transcript into that prompt. It also explains
request-scoped settings, persisted follow-ups, and non-retained one-shot runs.

The guidance does not turn ordinary runs into parent-linked persistent
subagents and does not add mid-run input, detached lifetime, or restart
recovery.

### Adopt the section in an existing config

Crystal Lattice does not rewrite an existing user or project config. Add both
placeholders at the end of the applicable `system_message.template`:

```text
{{CRYSTAL_LATTICE_ACCESS}}

{{CRYSTAL_LATTICE_CLI_ACCESS}}
```

Copy the bundled default config's `mixins.crystal_lattice_access` definition
and its `system_messages/helpers/crystal_lattice_access.py` file into the
corresponding active config directory, then add `"crystal_lattice_access"` as
the last `mixin_refs` entry for the agent. That one mixin contains the complete
inspectable Markdown for both access variants and the separate parent-only
delegation section, plus the named runtime-value placeholders and conditions.

The runtime owns `CRYSTAL_LATTICE_SYSTEM_MESSAGES` in the same way it owns
`BUILTIN_PLUGINS`. The helper contributes availability, conditions, and the
session checkbox; the configuration owns every line of agent guidance.

The other runtime-owned values are:

- `CRYSTAL_LATTICE_CLI_ARGV_JSON`;
- `CRYSTAL_LATTICE_CLI_COMMAND`;
- `CRYSTAL_LATTICE_CONFIG`;
- `CRYSTAL_LATTICE_SESSIONS`;
- `CRYSTAL_LATTICE_PYTHON` when available;
- `CRYSTAL_LATTICE_PYTHON_API_MODULE` when available;
- `CRYSTAL_LATTICE_DOCS` when local docs are available;
- `CRYSTAL_LATTICE_DOCS_URL`.

These values describe runtime locations only. They do not expose provider
credentials, auth state, plugin-cache contents, or arbitrary environment
variables.

## Cancellation, timeout, and exit codes

Set a positive finite timeout:

```bash
crystal-lattice run \
  --agent codex-openai \
  --prompt-file investigation.md \
  --timeout 600
```

`Ctrl-C` requests cancellation and exits with interrupt status. Cancellation
is cooperative: a provider or tool that is blocked in an operation without
cancellation support may finish that operation first.

| Exit code | Meaning |
|---|---|
| `0` | Command or agent run succeeded |
| `1` | Agent/application failure or interrupted run |
| `2` | Invalid input, configuration, agent, session, or message index |
| `124` | Timeout-triggered cancellation |
| `130` | User interrupt |

Failed and cancelled runs still produce a structured JSON result when request
execution progressed far enough to create one. Failures before a request
result exists leave JSON stdout empty and write diagnostics to stderr.

## Persistence and security

Persisted runs use ordinary filesystem sessions. They remain available to
terminal, HTTP, mobile, and desktop frontends that use the same session root.
Ephemeral runs do not write a canonical session and cannot be resumed after
the call returns.

Direct execution loads provider credentials and tools from the selected
configuration. Apply the same trust and plugin-policy rules as an interactive
run. Compact history limits transfer but is not an authorization boundary.
Full-message retrieval can expose everything intentionally stored on that
message.

The local API and command do not start a network listener.

## Troubleshooting

`Crystal Lattice config not found`
: Create `./.crystal/config.json` or `~/.crystal/config.json`, or pass
  `config_path` in Python. The CLI can create its normal default configuration
  through its existing config options.

`Unknown agent_id`
: Run `crystal-lattice agents` and use one of the returned IDs.

`Session ... not found`
: Verify `--sessions-dir` or the Python `session_root`. A session ID is scoped
  to that store.

`Session ... already has active request`
: Wait for the current in-process request to finish. The rejected message was
  not appended.

No immediate cancellation
: The active provider or tool may be inside a blocking operation that does not
  yet observe cooperative cancellation.
