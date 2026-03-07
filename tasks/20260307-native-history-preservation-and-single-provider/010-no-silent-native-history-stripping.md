# Stop silent native-history stripping in normal message operations

Short description: Change core mutating operations so they never silently strip provider-native history during normal use. They must preserve native history or raise an explicit error unless the caller explicitly opts into a core-only operation.

Parent Task: tasks/20260307-native-history-preservation-and-single-provider/000-main.md
Depends On: none

## Problem statement

The current core behavior allows normal message operations to silently fall back to a core-only rewrite that removes:

- `session.metadata["native_messages"]`
- `session.metadata["native_messages_integrity"]`
- per-message `metadata["native_indices"]`

That behavior is no longer acceptable for normal operations. The desired new policy is:

- Default behavior: **preserve native history or fail explicitly**.
- Explicit escape hatch: a config/keyword such as `core_only_operation=True` may allow the old core-only path when a caller intentionally requests it.
- Automatic fallback based on constraints is no longer allowed.

The user specifically wants behavior like this:

- If two providers are registered and `core_only_operation` is false/default, the operation should raise an explicit error.
- If `core_only_operation` is true, it should always use the core-only path.

## Current affected operations

### 1. `slice_session()`
Primary source of delete/fork stripping.

Relevant code:
- Public method: `core/python/agent_core/core.py:775-986`
- Core-only helper: `core/python/agent_core/core.py:721-773`

Current silent fallback cases in `slice_session()` include:
- missing config / non-dict metadata / multiple providers: `core.py:842-847`
- no `native_messages`: `core.py:849-855`
- integrity verification failure: `core.py:857-864`
- malformed or out-of-range `native_indices`: `core.py:871-910`
- rebuild failure: `core.py:945-957`

### 2. `fork_session()`
Thin wrapper over `slice_session()`.

Relevant code:
- `core/python/agent_core/core.py:988-1009`

### 3. `modify_message()`
Contains its own core-only branch that drops native history.

Relevant code:
- Public method: `core/python/agent_core/core.py:694-719`
- Internal implementation: `core/python/agent_core/core.py:405-528`
- Core-only branch: `core/python/agent_core/core.py:431-476`

### 4. `join_sessions()`
Silently downgrades to a core-only join when config or native history is incomplete.

Relevant code:
- `core/python/agent_core/core.py:1011-1083`

### 5. `add_message()` / insertion path
Insertion is affected because `_insert_single_message_with_native()` depends on `slice_session()` and `join_sessions()`.

Relevant code:
- `add_message()`: `core/python/agent_core/core.py:609-692`
- append helper: `core/python/agent_core/core.py:179-314`
- insert helper: `core/python/agent_core/core.py:316-403`

Notes:
- End-of-session append is less about stripping existing native history and more about how native history is created/maintained.
- Middle insertion may now fail explicitly where it previously degraded into core-only behavior through slice/join.

## User-facing call sites impacted by this core contract change

### Terminal app
- Fork: `application/python/agent_terminal_app/terminal_app.py:317-378`
- Delete: `application/python/agent_terminal_app/terminal_app.py:380-436`
- Modify: `application/python/agent_terminal_app/terminal_app.py:566-610`

### HTTP server
- Modify endpoint: `application/python/agent_terminal_app/server.py:1562-1614`
- Delete endpoint: `application/python/agent_terminal_app/server.py:1760-1902`
- Fork endpoint: `application/python/agent_terminal_app/server.py:2280-2350`

### Session actions app
- Copy/fork/delete message actions: `plugins/session-actions-app/src/session_actions_app/__init__.py:330-625`

### Other plugin flows that use slice/modify
- Generate title: `plugins/generate-title-app/src/generate_title_app/__init__.py:353-428`
- Summarize range: `plugins/summarize-range-app/src/summarize_range_app/__init__.py:378-519`

## Recommended implementation outline

1. Introduce an explicit core exception for preservation failures.
   - Example name: `NativeHistoryPreservationError`
   - Goal: let adapters distinguish “cannot preserve native history under current constraints” from generic runtime failures.

2. Add an explicit opt-in parameter to relevant mutators.
   - Candidate signature additions:
     - `slice_session(..., core_only_operation: bool = False)`
     - `fork_session(..., core_only_operation: bool = False)`
     - `modify_message(..., core_only_operation: bool = False)`
     - `join_sessions(..., core_only_operation: bool = False)`
     - potentially `add_message(..., core_only_operation: bool = False)` so insertion can thread it through

3. Refactor current silent fallback branches.
   - If `core_only_operation=True`, take the current core-only helper path intentionally.
   - If `core_only_operation=False` and the session already has native history, raise explicit preservation errors instead of silently stripping.

4. Define the error conditions clearly.
   When native history is present and the operation cannot preserve it, raise instead of stripping for cases such as:
   - multiple providers registered
   - missing config when config is required
   - missing `native_messages`
   - integrity mismatch
   - missing / malformed / out-of-range `native_indices`
   - rebuild failure
   - `join_sessions()` where one side has native history and the other does not

5. Decide and document how to treat sessions with no native history.
   Recommended default based on current architecture:
   - If the session has no native history to preserve, normal core-only editing may still be allowed without forcing `core_only_operation=True`, because nothing is being stripped.
   - If the product decision is stricter, document and implement that stricter rule explicitly.

6. Update adapter layers so these become user-visible validation errors rather than internal errors.
   - Terminal should surface these as `TerminalUserError`.
   - HTTP should return 400s for expected preservation failures.
   - Application action plugins should convert them to `ValueError` or another consistent user-facing action failure.

7. Update docstrings and comments.
   Remove wording like “preserved when possible” / “otherwise dropped” and replace with the new contract.

## Test work expected

### Core tests to update
Relevant existing tests:
- `core/python/tests/test_core.py:362-370` currently expects stripping when `native_indices` are missing.
- `core/python/tests/test_core.py:481-492` currently tests core-only modify behavior without provider/native history.
- `core/python/tests/test_core_insert_message_with_native.py` exercises slice/join-based insertion and should be checked for new explicit failures.

Recommended test changes:

1. Replace fallback-stripping expectations with explicit failure expectations.
   - Example: sessions with native history but missing `native_indices` should raise by default.

2. Add opt-in core-only tests.
   - For each key mutator, add a test showing `core_only_operation=True` still performs the old stripping behavior intentionally.

3. Add explicit multi-provider failure tests.
   - `slice_session()` with native history and more than one provider should fail by default.
   - `fork_session()` and `modify_message()` should also fail in equivalent conditions if they cannot preserve native history.

4. Keep / clarify tests for sessions with no native history.
   - These may still be allowed to operate core-only, depending on the final decision.

5. Verify application adapters surface readable user errors.
   - Terminal tests should assert user-facing errors, not silent mutation.
   - HTTP tests should assert 400 responses.
   - Session action tests should assert action failure rather than changed session state.

## Acceptance criteria

- No normal message operation silently strips native history from a session that already has it.
- The old stripping behavior is only reachable via an explicit opt-in such as `core_only_operation=True`.
- Delete, fork, modify, and any slice/join-backed insertion paths follow the new contract.
- Tests are updated to encode the new “preserve or fail” rule.
