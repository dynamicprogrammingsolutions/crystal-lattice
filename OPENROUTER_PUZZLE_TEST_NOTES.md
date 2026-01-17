# OpenRouter Puzzle Test Notes

This note captures why `application/python/tests/test_agent_terminal_app_openrouter_puzzle.py` can fail even when OpenRouter is configured correctly.

## Summary

The test calls `agent_terminal_app.server.send_request(...)` and then immediately asserts that the puzzle files have been edited (via `puzzle_main.run_tests()`).

However, the `send_request` endpoint in `application/python/agent_terminal_app/server.py` runs the request in a background thread and returns immediately. The test does not wait for completion, so the puzzle edits usually have not happened by the time assertions run.

## Key Behavior Mismatch

- Test behavior (`application/python/tests/test_agent_terminal_app_openrouter_puzzle.py`)
  - Creates a session.
  - Adds the user message.
  - Calls `server_mod.send_request(...)`.
  - Immediately imports `puzzle_main` and calls `puzzle_main.run_tests()`.

- Server behavior (`application/python/agent_terminal_app/server.py`)
  - `send_request` starts a daemon thread:
    - `threading.Thread(target=_run_send_request_background, ...)`
  - Returns `{}` immediately to the caller.
  - The actual tool-loop / model call and file edits happen asynchronously.

As a result, the test is effectively asserting on the filesystem before the background request has finished.

## Additional Complication: Tool Names in the Prompt

The test's system prompt tells the model:

"Use the read_file and write_file tools ..."

But the OpenRouter config (`application/python/agent_terminal_app/config_openrouter_app_layer.json`) wires `ShellTool` and `ApplyPatchTool` (tool names: `shell`, `apply_patch`).

This doesn't explain the immediate failure on its own, but it can lower the probability of the model solving the puzzle even if the test starts waiting properly.

## How to Reproduce

With `OPENROUTER_API_KEY` set:

```bash
pytest -q application/python/tests/test_agent_terminal_app_openrouter_puzzle.py
```

Typical failure: `puzzle_main.run_tests()` still sees the original buggy implementations because edits have not occurred yet.

## Potential Fix Directions (Not Implemented)

### Option A: Wait for completion via event store (preferred)

After calling `send_request`, poll the application's event store for a terminal signal (e.g., a "request_completed" / "final" marker event) tied to the session/request.

This keeps the test faithful to the production model: clients observe progress via events.

### Option B: Add a synchronous test-only send helper

Expose a helper in `agent_terminal_app.server` that runs the send loop synchronously (no thread) for tests. This avoids timing flakiness but diverges from production behavior.

### Option C: Change the endpoint behavior (not recommended)

Make `/sessions/{session_id}/send` blocking. This would change runtime behavior for the server/mobile clients.
