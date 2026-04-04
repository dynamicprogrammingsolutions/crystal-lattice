# Tool-Loop Cancellation During Tool Execution

Short description: High-priority application/core fix to make user cancellation interrupt an in-flight tool execution instead of waiting for the current tool to finish on its own.

## Requirements checklist

- [x] Add real cancellation propagation for running tools, not just phase-boundary checks.
- [x] Ensure `cancel_request()` can interrupt a currently executing shell tool.
- [x] Preserve consistent `request_cancelled` and `request_completed` event behavior after interruption.
- [x] Add regression tests for cancellation during long-running and silent tool executions.

## Why this exists

Current cancellation is best-effort bookkeeping only:

- `core/python/agent_app/application_future.py:1258-1270` only records the cancelled request ID.
- `core/python/agent_app/tool_loop.py:71-79` exposes that as a callback.
- `core/python/agent_app/tool_loop.py:107-113`, `148-154`, `366-372`, and `403-409` only check cancellation at outer loop boundaries.
- `core/python/agent_app/tool_loop.py:257-327` does not check cancellation while iterating a running tool call.
- `core/python/agent_core/core.py:3303-3338` has no tool-cancellation contract beyond consuming `stream_tool(...)`.

As a result, a shell tool that blocks inside `stream_tool(...)` ignores user cancel until it eventually returns, which may be never.

## Fix scope

This task is about cancellation plumbing and contracts:

- how `ToolLoopRunner` reacts to cancel while a tool is running
- how the core/tool API can cooperate with cancellation
- how shell-tool runtime state is made reachable from request cancellation

Do not use this task to redesign unrelated tool schemas or prompt behavior.

## Suggested implementation outline

1. Define the smallest practical cancellation contract for tool execution.
2. Thread cancellation state into `ToolLoopRunner._apply_tool_calls(...)`.
3. Extend shell-tool execution so it can register and clear a cancel target while the subprocess is live.
4. Ensure cancellation produces a deterministic final tool result or error payload rather than hanging the iterator.
5. Verify the active request bookkeeping in the server clears once cancellation completes.

## Completion Notes

Added during completion on 2026-04-04.

Implemented a request-scoped cancellation controller in `core/python/agent_app/tool_loop.py` and `core/python/agent_app/application_future.py`. `cancel_request()` now triggers live callbacks for active requests instead of only setting a best-effort flag.

Threaded optional cancellation propagation through:

- `core/python/agent_core/types.py`
- `core/python/agent_core/plugin/tool.py`
- `core/python/agent_core/plugin/adapters.py`
- `core/python/agent_core/core.py`
- `core/python/agent_app/tool_loop.py`

`ToolLoopRunner` now passes the cancellation handle into `iter_tool_messages(...)`, stops running additional tool calls after cancellation, and still emits the expected `request_cancelled` and `request_completed` lifecycle events.

Updated Codex shell tools so their streaming subprocess paths register live cancel callbacks and return deterministic cancelled results:

- `plugins/codex-tools/src/codex_tools/base_shell_tool.py`
- `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
- `plugins/codex-tools/src/codex_tools/shell_tool.py`

Added regression coverage for:

- direct shell-tool cancellation
- cancellation during silent tool execution
- cancellation after streamed partial output
- repeated cancel calls
- fresh follow-up requests after cancellation

Test files updated:

- `core/python/tests/dummy_tool.py`
- `core/python/tests/test_application_layer_streaming.py`
- `plugins/codex-tools/tests/test_shell_command_tool.py`
- `plugins/codex-tools/tests/test_shell_tool.py`

Current limit: non-shell tools only become interruptible when they opt into the new optional `cancellation` hook. The application/core path is now ready for that, but it does not forcibly interrupt legacy tools that ignore the hook.

## Testing expectations

- Cancellation while a tool is already running.
- Cancellation while a tool has produced no output yet.
- Cancellation while streaming partial output is in progress.
- Repeated cancel requests should be idempotent.
- A fresh request after cancellation should still complete normally.

## Useful references

- `core/python/agent_app/application_future.py`
- `core/python/agent_app/tool_loop.py`
- `core/python/agent_core/core.py`
- `core/python/tests/test_application_layer_streaming.py`
- `application/python/agent_terminal_app/server.py`

## Execution plan

Added during completion on 2026-04-04.

1. Introduce a request-scoped cancellation controller in the application layer so `cancel_request()` can trigger immediate callbacks for an active request, not just set a flag.
2. Thread that controller through `ToolLoopRunner` and `AgentCore.iter_tool_messages(...)` as an optional cancellation handle that existing tools can ignore safely.
3. Update shell tool streaming paths to register live subprocess termination callbacks while the process is running and to emit a deterministic cancelled result after interruption.
4. Stop the tool loop cleanly after a cancelled tool result so no additional tool calls or follow-up LLM phases run for that request.
5. Add regression tests covering cancellation during silent tool execution, streamed tool execution, idempotent repeated cancel calls, and normal follow-up requests after cancellation.