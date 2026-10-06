# Local headless agent runs

This application-owned specification defines a supported local Python and
command-line workflow for running configured Crystal Lattice agents without an
interactive frontend or HTTP server.

It covers:

- discovery of the same configured agents used by the application;
- safe discovery of effective agent defaults and configurable fields;
- context-managed local runtime construction;
- atomic synchronous persisted, non-retained, and follow-up execution;
- generic request-scoped provider/plugin settings;
- bounded progress observation;
- compact structured outcomes;
- deterministic compact history and explicit full-message retrieval;
- one-shot `crystal-lattice agents`, `run`, and `history` commands;
- direct Python and shell concurrency for distinct sessions;
- cooperative timeout and interrupt cancellation;
- later opt-in guidance that lets configured agents locate Crystal Lattice
  capabilities while working in projects launched outside Crystal Lattice.

The application package owns the public convenience API and command because
it owns product configuration, dotenv and runtime-layout resolution, session
paths, and command-line behavior. The provider-neutral `agent_app` package
owns the coordinated request and history-projection primitives used by those
adapters.

## User workflows

### Python

A package user can open the local runtime, run an initial task, consume
optional progress, inspect the result, and continue the same persisted
session:

```python
from agent_terminal_app import RunProgress, open_runtime


def show_progress(progress: RunProgress) -> None:
    print(progress.message)


with open_runtime() as runtime:
    first = runtime.run(
        "Inspect the provider implementation.",
        agent_id="configured-agent",
        on_progress=show_progress,
    )
    follow_up = runtime.run(
        "Now inspect its tests.",
        session_id=first.session_id,
        on_progress=show_progress,
    )
```

The final result is returned directly. Reading or replaying the event stream is
not required to obtain the answer.

### Command line

A shell user can list configured agents, execute a task, retain a machine-safe
result, and continue the returned session:

```text
crystal-lattice agents
crystal-lattice run --agent configured-agent --prompt-file task.md --format json
crystal-lattice run --session <session-id> --prompt "Check one more case."
```

Progress is written to stderr. Text or one JSON document is written to stdout.

### Compact history

Python and CLI callers can inspect bounded history without carrying complete
tool results or provider-native state. Every projected row retains its
canonical message index. A caller explicitly selects a full message when
needed.

## Goals

- Make a configured Crystal Lattice agent naturally callable from Python and
  ordinary shell automation.
- Let callers inspect safe agent defaults, select generic request settings,
  and choose explicitly between persisted and non-retained execution.
- Keep message append and request admission atomic.
- Use the existing application request coordinator, persistence checkpoints,
  cancellation, and event publication.
- Return a useful final result even when the caller does not consume events.
- Preserve enough bounded progress for humans and orchestration code to
  observe request and tool activity.
- Make follow-ups an ordinary call against a persisted run's returned session
  ID while keeping non-retained identities explicitly non-resumable.
- Permit simple parallel investigations through Python futures or shell jobs
  on distinct sessions.
- Keep compact views derived from canonical persisted history.
- Preserve compatibility with interactive terminal and HTTP/event adapters.

## Non-goals

- Durable detached jobs or result lookup after the owning process exits.
- A new HTTP request/result protocol.
- TypeScript SDK or mobile/desktop adoption.
- Cross-process same-session request locking.
- Sending input to a request that is already running.
- Parent-child session relationships or model-facing subagent tools.
- LLM-generated conversation summaries.
- Replacing or rewriting canonical session history.
- Exposing complete tool output, provider-native messages, credentials, or
  inline binary data through progress or compact history.

## Delivery sequence

The direct local runtime, compact-history API, and one-shot commands are
implemented and verified first.

After their Python and CLI acceptance tests pass, work pauses before changing
configuration or system messages. A separate approved plan will define the
runtime variables and independently enabled system-message section through
which agents working in external projects can locate:

- the installed Crystal Lattice command;
- the supported Python API;
- the applicable Python interpreter;
- installed Crystal Lattice documentation.

Requirement `HLR-060` records this required later outcome. Requirement
`HLR-061` additionally requires an explicitly gated real Ollama
`glm-5.3-flash:cloud` acceptance test that proves the guidance creates and
completes a separate configured-agent session through the same config and
session root. A textual claim of delegation is not sufficient evidence.

The approved post-completion extension adds:

- explicit, mutually exclusive full CLI+SDK and CLI-only config-owned
  sections;
- visible disabled UI when no valid CLI capability exists;
- deterministic CLI and SDK execution through every supported native
  installation path;
- a real model-mediated CLI and SDK scenario on all six native release
  targets;
- one-off native Detox evidence for the three availability presentations.

The
[session and message data query specification](../session-data-query/index.md)
refines this surface with local-runtime session listing, full canonical message
ranges, and one-shot `sessions` and `messages` commands. It leaves compact
history and task execution unchanged.

## Specification documents

- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)

## Related current documentation

- [Application request execution](../../request-execution.md)
- [Terminal guide](../../../terminal.md)
- [Application configuration](../../../configuration.md)
- [Configuration placeholders](../../../configuration-placeholders.md)
