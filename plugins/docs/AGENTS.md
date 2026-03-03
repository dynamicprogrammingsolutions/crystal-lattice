# Documentation agent guidelines (plugins/docs)

This file captures conventions for agents working on documentation under `plugins/docs/`.

The goal is to keep documentation:

- accurate to the runtime code,
- readable for first-time users,
- easy to maintain without duplication/drift.

## 1) Write for readers, not for reviewers

- Do **not** include wording that reflects an internal review or planning process.
  - Avoid headings like “where did they go?”, “tests-first (per review)”, “as requested”, etc.
- Keep titles and section headers natural and user-facing.
- If something changed compared to earlier docs, explain it as a normal design choice,
  not as an artifact of a prior conversation.

## 2) Prefer runtime-accurate claims with code pointers

- When documenting behavior, prefer **file-path references** to the actual implementation.
  - Examples:
    - protocols/docstrings: `core/python/agent_core/types.py`
    - provider wrapper: `core/python/agent_core/plugin/provider.py`
    - adapters/defaults: `core/python/agent_core/plugin/adapters.py`
    - request flow: `core/python/agent_core/core.py`
- If the code and older docs disagree, follow the code.

## 3) Include code examples everywhere they teach something

- Every concept section should have at least one concrete example.
- Prefer examples that are:
  - short,
  - copy/paste-able,
  - and representative of real usage.

### Example completeness

- Avoid examples that end in `...` when the missing part is essential to understanding.
  - If you must omit details, omit only non-essential parts and say what was omitted.
- Prefer runnable snippets for tests and configs.

## 4) Recommend an automated test loop as the default development workflow

- For provider development, recommend:
  - implement a small piece,
  - run `pytest`,
  - iterate.
- Wire-up examples (e.g., `AgentCore.register_provider`) are useful, but should not be the
  primary way you recommend validating correctness.

## 5) Document both “quick feedback” and “real app” workflows

Provider docs should include:

- a fast local workflow via tests, and
- a guide for running the provider in a real application config (terminal/desktop/mobile)
  using the app-layer plugin loader (`path:`/`git+` + `agent_plugin.json`).

Reference existing app configs when possible (for patterns):

- `application/python/agent_terminal_app/config_echo_app.json`
- `application/python/agent_terminal_app/config_openrouter_app_layer.json`

## 6) Be explicit about streaming patterns and when to deviate

When documenting provider streaming:

- Present a recommended baseline pattern (accumulator-based streaming) and explain why it works.
- Also document when it is appropriate to implement custom `process_chunk`/`finalize`:
  - unusual stream event types,
  - special delta handling,
  - multiple final messages,
  - limited control using the accumulator approach.

Avoid claiming unrealistic “wire formats” as common.

## 7) Include trial-and-error guidance without encouraging unsafe logging

- Real providers often require shape discovery.
- Recommend temporary debug logging for chunks/deltas and request/response payloads,
  but:
  - truncate large payloads,
  - never log secrets (API keys, auth headers),
  - prefer structured logging helpers where available.

## 8) Split shared topics into shared pages to avoid drift

If a section applies broadly across plugin kinds (providers/extensions/features/tools),
prefer creating or updating a shared page under `plugins/docs/` and linking to it.

Examples of shared topics:

- packaging/loading (`agent_plugin.json`, `path:`/`git+` specs)
- execution order
- UI elements and `ui_type`
- testing/validation commands

When adding a new shared doc, update `plugins/docs/index.md`.

## 9) Keep `docs/plugins/development.md` as a general overview

`docs/plugins/development.md` is readable and useful as a general plugin overview.

- Do not delete it.
- If provider-specific docs evolve, prefer adding a pointer/link rather than duplicating
  provider details there.

## 10) Template + tests guidance

When documentation references templates:

- Prefer templates that are simple and minimize “delete this example” work.
- If integration tests are included as templates:
  - allow them to be `xfail` by default,
  - keep setup/assertions close to real reference tests,
  - make it easy for developers to enable by editing a small constants file.
