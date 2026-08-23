# Claude Tools Guidelines

This package implements Claude Code-compatible tools and supporting system-message assets.

The main goal in this directory is Claude parity at the LLM-facing boundary:

- match Claude Code tool names
- match Claude Code schemas
- match Claude Code result formatting
- preserve Anthropic-native tool schema/call/result handling

Internal implementation does not need to copy Claude Code literally, but the public tool shape should stay Claude-compatible unless a deliberate divergence is documented and discussed.

## What Lives Here

- `src/claude_tools/`
  - Claude-compatible tool implementations
  - Anthropic-native interop helpers in `interop.py`
  - cross-tool helpers such as read/write/edit activity tracking
- `tests/`
  - deterministic fixture-driven unit tests
  - real-provider integration tests for selected tool paths
- `investigation/scripts/`
  - repeatable Claude CLI harnesses used to capture real behavior
- `investigation/fixtures/`
  - normalized committed source-of-truth files for schemas and result formatting
- `investigation/notes/`
  - human-readable implementation notes derived from fixtures
- `system_messages/claude/`
  - Claude system-message sections used by default config

## Working Model

Use the same loop that built this package:

1. Investigate real Claude behavior.
2. Normalize the captured behavior into committed fixtures.
3. Implement the tool or behavior.
4. Add fixture-driven tests.
5. Run focused validation.

Avoid implementing new Claude-facing behavior from memory when a real investigation can be run.

## Shared Building Blocks

Prefer reusing existing engines before adding new logic here:

- `plugins/tool-compat-shared`
  - filesystem readers/editors/search
  - shell execution
  - background process runtime
  - Gemini and Tavily web-search providers
- `plugins/web-fetch-shared`
  - HTTP fetch
  - content extraction
  - truncation
  - prompt-driven summarization helper

Keep Claude-specific formatting in `claude-tools` unless it is genuinely reusable by multiple vendor packages and covered by tests.

## Investigation Harness

The investigation scripts use the local Claude CLI, Ollama, and the sibling proxy repo.

Expected setup:

- Claude CLI available as `claude`
- Ollama reachable at `http://localhost:11434`
- proxy repo available at `../openai-proxy`

Important harness rules:

- use `--tools <ToolName>` to restrict the advertised tool set
- use `--setting-sources project` plus explicit `--settings` so user-level Claude settings do not leak into the run
- use `--verbose` with `--output-format stream-json`
- pin both:
  - `ANTHROPIC_SMALL_FAST_MODEL`
  - `ANTHROPIC_DEFAULT_HAIKU_MODEL`

The scripts commit normalized fixtures, not raw logs. Raw logs are only for local inspection.

Normalized fixtures should be produced by the investigation scripts. Do not treat manual fixture normalization or hand-edited committed fixtures as the normal workflow.

If manual transcription or hand-editing is ever used as a temporary debugging step, it should be replaced with script-generated fixtures before the work is considered complete.

## Licensing And Provenance

This subtree is licensed under Apache-2.0. Its compatibility implementation,
investigation scripts and notes, tests, system-message compatibility assets,
and AI-generated normalized behavior fixtures are Crystal Lattice project
materials covered by the subtree `LICENSE`.

Do not claim that Anthropic's license applies to a Crystal Lattice file merely
because publicly visible Claude Code behavior was observed. User-facing
documentation must clearly state that Crystal Lattice is an independent
compatibility implementation and is not affiliated with or endorsed by
Anthropic.

Claude and Claude Code names and observed literal strings may remain where
factually or behaviorally necessary for compatibility. Preserve those
LLM-facing contracts unless an investigation and tests support changing them.

Raw logs, credentials, local settings, real user-home paths, and other
run-specific private data must not be committed. Explicit workspace and raw
directory replacements take precedence, after which normalizers must replace
macOS, Linux, and Windows user-home prefixes with stable placeholders.

See `PROVENANCE.md` for the public provenance and non-affiliation statement.

## Implemented Surface

Currently implemented:

- `Read`
- `Write`
- `Edit`
- `Glob`
- `Grep`
- `Bash`
- `TaskStop`
- `WebFetch`
- `WebSearch`

Also included:

- Claude system-message assets used by the default `claude` agent

Not yet covered here:

- Claude compaction support lives in separate work and should be treated as a distinct area

## Testing Pattern

Run focused package tests first:

```bash
pytest plugins/claude-tools/tests -q
ruff check plugins/claude-tools/src/claude_tools plugins/claude-tools/tests
```

Useful adjacent validation:

```bash
pytest application/python/tests/test_claude_system_message_helpers.py -q
pytest application/python/tests/test_claude_default_config_openrouter_tool_smoke_integration.py -q
pytest plugins/claude-tools/tests/test_claude_web_search_integration.py -q
```

When changing investigation-backed behavior, rerun the relevant investigation script and update fixtures if the real behavior changed:

```bash
python plugins/claude-tools/investigation/scripts/investigate_read_tool.py --case all --discard-raw
python plugins/claude-tools/investigation/scripts/investigate_bash_tool.py --case all --discard-raw
python plugins/claude-tools/investigation/scripts/investigate_web_fetch_tool.py --case all --discard-raw
python plugins/claude-tools/investigation/scripts/investigate_web_search_tool.py --case all --discard-raw
```

## App-Level Validation Notes

For the default `claude` agent, app-level smoke tests should use real provider/network paths, not mocked tool internals.

Important detail:

- set `CONFIG_DIR` to the repo default-config directory when building `AgentApplication` from default config in tests

Without that, unrelated default-config plugins such as cloud-agent profile resolution may look in the wrong place and fail before Claude tests even start.

## Common Pitfalls

- Do not silently change Claude-facing schema text or result strings without checking fixtures.
- Do not assume weakly observed server behavior is a desired product contract. For example, domain filtering in captured `WebSearch` results appeared inconsistent; if enforcing stricter behavior locally, do it intentionally and test it.
- Keep sibling shared-package dependencies explicit in packaging. This package depends on both:
  - `tool-compat-shared`
  - `web-fetch-shared`
- Be careful with async execution inside tool implementations. If a tool may run under an existing event loop, use the same safe bridging pattern already used in Claude tools rather than raw `asyncio.run(...)`.

## AGENTS.md Maintenance

This file should stay current when the package changes enough to make guidance stale or incomplete.

If you notice stale details or new important package knowledge while working here:

- do not wait for an explicit user request to realize it should be updated
- but always confirm with the user before actually editing this file
- when asking, say briefly what would be updated so the user can approve the scope