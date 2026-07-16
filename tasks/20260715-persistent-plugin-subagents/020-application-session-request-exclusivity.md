# Application-Level Session Request Exclusivity

Move per-session request single-flight coordination into the application layer so HTTP, terminal, and internal subagent requests cannot concurrently modify the same session.

## Requirements checklist

- [ ] Add an application-owned mechanism that reserves a session for one active request and reliably releases it on completion, cancellation, error, or generator close.
- [ ] Make internal subagent requests participate in the same reservation mechanism.
- [ ] Migrate HTTP request coordination from its server-local guard to the application-owned behavior.
- [ ] Make terminal request execution use the same behavior.
- [ ] Return a clear, stable busy/conflict outcome before a competing request starts modifying session history.
- [ ] Preserve existing cancellation and checkpoint behavior.
- [ ] Add tests covering concurrent HTTP/internal, terminal/internal, and internal/internal requests.
- [ ] Add a regression test for a user attempting to continue a visible child while its internal run is active.
- [ ] Resolve or replace the known append-and-send race expectation in `test_application_tool_loop_session_concurrency.py` as appropriate.
- [ ] Avoid introducing unrelated request APIs or UI changes.

Parent Task: `tasks/20260715-persistent-plugin-subagents/000-main.md`

Depends On: `tasks/20260715-persistent-plugin-subagents/010-codex-vertical-slice-and-shared-runtime.md`

## Why this framework change is mandatory

Current request single-flight protection is process-local to the HTTP server:

- `application/python/agent_terminal_app/server.py`

`AgentApplication.send_request(...)` does not itself reserve the session for the whole logical request. An internal background child can therefore run without being visible to the server guard. A user request against that visible child may begin concurrently and encounter checkpoint conflicts or malformed append-and-send behavior.

The repository already records a known unresolved append-and-send concurrency race:

- `core/python/tests/test_application_tool_loop_session_concurrency.py`

Central application ownership is required for safe visible child sessions. It is not a subagent-specific UI convenience.

## Scope constraints

- Keep the API minimal and usable by all current request entry points.
- Do not add queuing; a busy response is sufficient.
- Do not add special subagent interruption semantics.
- Do not hold the existing short-lived session persistence lock for the entire provider request unless testing proves that is the correct general solution.
- Keep cross-process guarantees limited to existing session conflict handling unless broader locking is explicitly approved.

## Verification

- Core application concurrency tests.
- Terminal application tests.
- HTTP server request tests.
- Subagent integration test demonstrating that user continuation is rejected while the child is active and succeeds after the child becomes idle.