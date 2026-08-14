# Terminal-Bench Option B Adapter

Implement a custom `BaseAgent` adapter that wraps our `AgentApplication` so
Harbor runs Terminal-Bench 2.1 task containers and verifiers while our agent
stack (providers, plugins, tools, sessions) drives the terminal.

Parent Task: `tasks/20260623-terminal-bench-evaluation/000-main.md`

Depends On: `tasks/20260623-terminal-bench-evaluation/010-evaluations-restructure.md`

## Requirements checklist

- [ ] `agent_evaluations.evaluations.terminal_bench.adapter.agent.OurTerminalBenchAgent`
  subclasses `harbor.agents.base.BaseAgent` and implements `name()`,
  `version()`, `setup(environment)`, and `run(instruction, environment,
  context)`.
- [ ] The adapter constructs an `AgentApplication` from a config directory
  passed via `--agent-kwarg config_dir=...` (or an env var fallback) during
  `setup()`.
- [ ] A single `bash` tool plugin is registered in the `AgentApplication`
  config; its `execute_tool` calls back into the adapter, which calls
  `await environment.exec(command)` and returns stdout/stderr/exit_code in
  our tool-result format.
- [ ] The adapter drives `AgentApplication.send_request_stream(...)` in a
  loop, translating each assistant tool call into an `environment.exec`
  call and feeding the result back as a tool result, until the model stops
  calling tools or harbor cancels the trial.
- [ ] The adapter populates harbor's `AgentContext` with a minimal
  `Trajectory` (one `Step` per agent turn) and `FinalMetrics` with token
  usage from our `usage` events, so harbor's viewer and verifier see the
  run.
- [ ] The adapter raises `harbor.agents.installed.base.ApiRateLimitError`
  when our provider returns a rate-limit signal, so harbor's
  `--max-retries --retry-include ApiRateLimitError` works.
- [ ] The adapter honors harbor cancellation (checks a flag in the event
  loop) and exits `run()` cleanly on cancel.
- [ ] Offline unit tests exist for the adapter that exercise the
  event→trajectory mapping and the bash-tool→`environment.exec` bridge
  without Docker or harbor (using fakes/mocks for `BaseEnvironment`).

## Scope and intent

This is the core of Option B. The adapter is the bridge between Harbor's
task environment (Docker container with `environment.exec`) and our
`AgentApplication` (LLM provider, tool loop, plugin stack).

**In scope:**
- `BaseAgent` subclass (external agent flavor).
- `BashToolPlugin` that calls `environment.exec` via a closure.
- Event-stream → harbor `Trajectory` mapping (minimal ATIF).
- Rate-limit and cancellation error mapping.
- Offline unit tests.

**Out of scope (deferred):**
- Full ATIF trajectory fidelity (tool call IDs, observation results, full
  multimodal content) — only needed for leaderboard submission.
- `BaseJobPlugin` rate limiter — only if the test-run shows we need it.
- Cloud sandbox (Daytona/Modal) wiring.

## Execution plan

Status: Approved

### Files to create

```
evaluations/src/agent_evaluations/evaluations/terminal_bench/adapter/
  __init__.py          # exports OurTerminalBenchAgent
  agent.py             # OurTerminalBenchAgent(BaseAgent)
  env_bridge.py        # BashToolPlugin + HarborBashExecutor closure
  context_writer.py    # our events -> harbor Trajectory/Step/FinalMetrics
```

### Adapter design

**`agent.py` — `OurTerminalBenchAgent(BaseAgent)`:**

```python
class OurTerminalBenchAgent(BaseAgent):
    SUPPORTS_ATIF: bool = True

    def __init__(self, *, config_dir: str | None = None, **kwargs):
        self._config_dir = config_dir or os.environ.get("AGENT_EVALUATIONS_CONFIG_DIR")
        if not self._config_dir:
            raise ValueError("config_dir kwarg or AGENT_EVALUATIONS_CONFIG_DIR env required")

    @staticmethod
    def name() -> str:
        return "our-agent-platform"

    def version(self) -> str | None:
        from agent_evaluations import __version__  # or package metadata
        return __version__

    async def setup(self, environment: BaseEnvironment) -> None:
        from agent_evaluations.config_dir import load_evaluation_environment
        self._eval_env = load_evaluation_environment(self._config_dir)
        self._app = self._eval_env.build_application()
        self._agent_id = ...  # from config or kwarg
        self._executor = HarborBashExecutor(environment)
        # Register the bash tool plugin with the executor
        self._app.register_tool(BashToolPlugin(executor=self._executor))

    async def run(self, instruction, environment, context):
        # Drive AgentApplication.send_request_stream in a loop
        # Map events to Trajectory steps via context_writer
        # Raise ApiRateLimitError on rate-limit signals
        # Check cancellation flag between turns
        ...
```

**`env_bridge.py` — `BashToolPlugin` + `HarborBashExecutor`:**

The `BashToolPlugin` is a `ToolPlugin` that our `AgentApplication` registers.
Its `execute_tool` delegates to an injected `executor` callable that calls
`await environment.exec(command)`. The `HarborBashExecutor` closes over the
harbor `BaseEnvironment` instance and provides a sync interface (our tool
loop is sync; harbor's `exec` is async — bridge via `asyncio.run` or an
event loop reference).

**`context_writer.py` — event → trajectory mapping:**

Walk our event stream (`assistant`, `tool_call`, `tool_result`, `usage`
events) and build harbor `Step` entries. For the first version, each step
has:
- `message`: the assistant message text
- `tool_calls`: list of `ToolCall` (name="bash", arguments={"command": ...})
- `observation`: `ObservationResult` with the bash stdout/stderr
- `FinalMetrics`: token counts from `usage` events

Skip ATIF-specific fields we don't have yet (multimodal content, tool call
IDs beyond a synthetic counter).

### Key design decisions

1. **Sync/async bridge**: our `AgentApplication` tool loop is synchronous;
   harbor's `environment.exec` is async. The adapter runs our agent in a
   thread or uses `asyncio.run` per tool call. Simplest: the adapter's
   `run()` is async (harbor calls it with `await`), and it calls our sync
   agent loop via `asyncio.to_thread(...)`. Tool calls from within the loop
   use `asyncio.run_coroutine_threadsafe(exec(...), loop)` to get back to
   the harbor event loop.

2. **Config injection**: harbor passes `--agent-kwarg config_dir=...` to
   the adapter's `__init__`. The adapter loads our evaluation environment
   from that path. Harbor's `--model` flag is accepted but ignored — our
   config has the real model.

3. **Working directory**: harbor runs each task in a container-side working
   dir. The adapter reads it from `AgentContext` / task config in `setup()`
   and ensures the `bash` tool `cd`s there before running commands.

### Implementation decisions and open questions

**Decided:**
- External agent flavor (not installed) — our agent runs in the harbor host
  process.
- Single `bash` tool surface.
- Minimal ATIF trajectory (enough for viewer + verifier).
- `ApiRateLimitError` for rate-limit mapping.

**Open:**
- How to detect rate-limit signals from our provider events — need to
  inspect the Ollama provider's error/retry behavior. Will resolve during
  implementation by checking `agent_core` provider error types.
- Whether `AgentApplication` needs a new hook to register a tool plugin
  post-construction, or if we do it via config. Will check
  `AgentApplication` API during implementation.

### Documentation

- `evaluations/evaluations/terminal_bench/AGENTS.md` (in subtask 060).

### Task checklist

- [ ] Create `adapter/__init__.py` exporting `OurTerminalBenchAgent`
- [ ] Implement `agent.py` — `OurTerminalBenchAgent(BaseAgent)`
- [ ] Implement `env_bridge.py` — `BashToolPlugin` + `HarborBashExecutor`
- [ ] Implement `context_writer.py` — event → `Trajectory` mapping
- [ ] Add offline unit tests for the adapter
- [ ] Verify `import agent_evaluations.evaluations.terminal_bench.adapter` works
- [ ] Verify harbor can import the agent class via `--agent` flag (dry run
      with `harbor run --help` or a no-op task)

### Requirement verification

| Requirement | Evidence |
|---|---|
| `OurTerminalBenchAgent` subclasses `BaseAgent` | `issubclass(OurTerminalBenchAgent, BaseAgent)` is True |
| Constructs `AgentApplication` from `config_dir` | Unit test passes a temp config dir and asserts `self._app` is an `AgentApplication` |
| `bash` tool calls `environment.exec` | Unit test fakes `BaseEnvironment.exec` and asserts the tool calls it |
| Event → trajectory mapping | Unit test feeds sample events and asserts `Trajectory` has expected `Step` entries |
| `ApiRateLimitError` on rate limit | Unit test fakes a rate-limit event and asserts the error is raised |
| Cancellation honored | Unit test sets cancel flag and asserts `run()` exits within one turn |
| Offline tests pass | `pytest evaluations/src/agent_evaluations/evaluations/terminal_bench/ -q` exits 0 |