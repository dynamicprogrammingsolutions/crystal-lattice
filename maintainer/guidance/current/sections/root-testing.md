## Testing Principles

**When to add tests**
- Any new public behavior or API surface.
- Any bugfix (add a regression test that fails before the fix).
- Any change in `agent_core`, `agent_app`, `agent_terminal_app`, built-in plugin projects, or core-packaged plugins visible to users.

**What to test**
- Use the least expensive test that proves the requirement without bypassing
  the important boundary. Unit and component tests suit pure functions,
  protocol implementations, local state, and rendering behavior.
- Use **integration tests** for multi-layer flows or provider-backed behavior; mark them with `integration`.
- Add `api` for hosted real-provider tests that require credentials and may incur cost.
- Add `slow_integration` for broad, high-latency, or expensive integration suites that should be run selectively.
- Keep provider selectors such as `openrouter`, `openai`, `ollama`, `gemini`, `fireworks`, `zai`, plus `docker` and `manual_integration`, so specific integration slices stay easy to target.
- Treat `not integration` as the practical quick filter for local verification; some intentionally fast local Ollama coverage may still remain in that path if it is not marked `integration`.
- Use **example / end-to-end tests** for high-level flows (`core/python/examples/tests`, `application/python/tests`).

**Test realism**
- Integration/e2e tests must exercise realistic public user/deployment flows. Do not make a test pass by adding test-only shortcuts, direct internal endpoints, special overrides, or alternate paths that hide an important product defect.
- If a realistic test exposes a real issue, keep the test realistic and fix the product code. If the fix is out of scope, report the failing test and exposed issue clearly instead of weakening the test.
- When a requested or required test is gated by markers, flags, or environment variables, run it with the appropriate marker/flag/env enabled instead of accepting a skipped result as success. The main Python suites in `core/python/tests`, `core/python/examples/tests`, `application/python/tests`, `plugins/openrouter/tests`, `plugins/openai_responses/tests`, and `plugins/reference-openai-compatible-provider/tests` bootstrap the repo-root `.env` via suite `conftest.py` without overwriting already-exported env vars, but do not assume every other suite in the repo does. Report a skipped gated test as "not run" unless you explicitly enabled the gate and verified the skip is intentional for the current task.
- Describe coverage by the boundary it actually crosses. Direct route-function calls are not HTTP integration tests, mocked frontend tests are not backend integration tests, and deterministic simulator harnesses are native UI tests rather than network/server end-to-end tests.
- Count a test run as successful only when the requested tests are collected and the command exits successfully. Collection failures, teardown errors, open handles, or background-timer errors after passing assertions still make the run incomplete or failed.
- When behavior crosses server, transport, and UI boundaries, include at least one integration test that uses the public backend/HTTP API and production frontend adapter.
- Treat shared test harnesses as production test infrastructure: keep them type-checkable, verify an existing consumer when they change, and do not count tests that fail before collection.

**Design/testing style**
- Keep code functional/immutable; avoid in-place mutation of shared data.
- Do not add shallow copies (e.g. `dict(...)`, `list(...)`) purely to "protect" returned structures; callers are expected to treat them as immutable.
- Assert on data structures (sessions, messages, events), not logs.
- For history-modifying features (`slice_session`, `modify_message`, `/delete`, `/modify`), cover both core and app/terminal behavior.
- Put stable test identifiers or accessibility labels on production entity rows, action triggers, and dialog controls. Do not create harness-only copies of production UI solely to make native tests selectable.
- Exercise shared helpers through at least one real consumer; do not replace the helper with a duplicate implementation in the consumer's test mock.
- In React Native unit/component tests, mock native host-component packages at their public package boundary while preserving the props, events, and imperative ref methods used by consumers.

**Plugin + test fixture placement**
- Keep package-specific tests and fixtures in the owning package's test directory.
- Put cross-cutting tests and fixtures used by multiple packages or runtimes under `test/`; put shared fixture files under `test/fixture/`.
- Do not add new `core/python/tests` that depend on repo-root `plugins/` (use `core/python/tests/fixtures` instead).
- Test-only plugins/fixtures live under `core/python/tests` (prefer `core/python/tests/fixtures`).
- Core-packaged plugins that still ship with `agent-core` live under `core/python/plugins`.
- First-party built-in plugin projects live under repo-root `plugins/`, and their tests live alongside them.
- Do not add new plugin projects under `core/python/plugins` without explicit user consent.

Treat applicable tests, type hints, and documentation updates as part of
“done” for substantive changes.

