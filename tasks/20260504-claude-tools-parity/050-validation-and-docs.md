# Validation And Docs

Validate Claude tool/config/compaction parity end to end and update relevant docs so future contributors understand how to investigate and maintain vendor-compatible tools.

## Requirements checklist

- [ ] Add or update unit tests for `claude-tools`, shared formatters, system-message rendering, config loading, and compaction.
- [x] Add application-level integration tests proving the default `claude` agent lists and can execute the expected tools.
- [x] Add gated real-provider or Ollama tests where useful and mark/report them correctly.
- [x] Run focused test suites for touched packages.
- [x] Update README/docs for Claude tools and the behavior-driven investigation harness.

Parent Task: tasks/20260504-claude-tools-parity/000-main.md

Depends On: tasks/20260504-claude-tools-parity/020-implement-claude-tools.md
Depends On: tasks/20260504-claude-tools-parity/030-implement-claude-system-message-and-config.md
Depends On: tasks/20260504-claude-tools-parity/040-investigate-and-implement-claude-compaction.md

## Execution plan

Added during completion after user approval.

Because Claude compaction is still open in `040`, this pass will validate and document the implemented Claude tool/config/system-message surface now, and leave compaction-specific validation explicitly blocked.

Planned steps:

1. Add an application-level default-config test that creates the `claude` agent through `AgentApplication`, verifies the expected Claude tool ids, and executes at least one Claude web tool through the app-created core/config.
2. Add gated real-provider `ClaudeWebSearchTool` integration tests for both `gemini_api` and `tavily`, using env-loaded credentials and marking them as integration tests.
3. Expand the Claude investigation README with the practical harness requirements and caveats now that all standard tools are covered.
4. Run focused suites for:
   - `plugins/claude-tools/tests`
   - `plugins/tool-compat-shared/tests`
   - `plugins/web-fetch-shared/tests`
   - focused Claude default-config/system-message tests in `application/python/tests`
5. Record what is completed now versus what remains blocked on compaction in completion notes and keep the checklist status accurate.

## Test Targets

Expected focused tests after implementation:

```bash
pytest plugins/claude-tools/tests -q
pytest plugins/tool-compat-shared/tests -q
pytest plugins/web-fetch-shared/tests -q
pytest plugins/gemini-compaction-app/tests -q
pytest plugins/gemini-compaction-feature/tests -q
pytest plugins/claude-compaction-app/tests -q
pytest plugins/claude-compaction-feature/tests -q
pytest core/python/tests/test_default_system_instructions_docs.py -q
pytest application/python/tests/test_terminal_application_default_config_openrouter_integration.py -q
```

Adjust the compaction package test paths based on the final implementation choice.

For broader confidence:

```bash
pytest core/python/tests -q -m "not integration"
pytest application/python/tests -q -m "not integration and not docker"
```

## Documentation Targets

Potential docs to update:

- `plugins/claude-tools/README.md`
- `plugins/docs/tool-plugins.md`
- `plugins/docs/tool-interop.md`
- `application/python/README.md`
- Default config notes if there is a suitable existing section

Document the Claude Code investigation harness:

- proxy setup
- Ollama Anthropic compatibility setup
- required Claude flags
- normalization strategy
- known caveats around settings precedence and telemetry/bootstrap calls

## Acceptance Criteria

- `claude` default agent uses `claude-tools`, not `codex-tools`.
- Standard Claude tools are visible through app/plugin listing.
- At least `Read`, `Write`, `Edit`, `Bash`, `Glob`, and `Grep` are covered by deterministic unit tests.
- `WebFetch` and `WebSearch` have deterministic tests for schema and non-network behavior, with gated integration tests if external services are required.
- System-message rendering is tested and includes Claude sections, Tasks, and AGENTS context.
- Compaction support has tests or, if deferred, the reason and captured investigation status are documented in the task completion notes.

## Progress Notes

Added during completion.

Completed the pre-compaction validation/docs slice for the implemented Claude tool surface:

- Added a real default-config Claude smoke suite in `application/python/tests/test_claude_default_config_openrouter_tool_smoke_integration.py`.
  - Uses the shipped default `claude` agent with the real OpenRouter provider and real network access.
  - Loads required credentials from the repo-root `.env`.
  - Covers all implemented Claude tools across combined happy-path scenarios:
    - `Write` + `Read` + `Edit`
    - `Glob` + `Grep`
    - `Bash` + `Read` + `TaskStop`
    - `WebFetch`
    - `WebSearch`
- Added gated real-provider integration coverage in `plugins/claude-tools/tests/test_claude_web_search_integration.py`.
  - Real Gemini-backed `WebSearch`
  - Real Tavily-backed `WebSearch`
- Expanded `plugins/claude-tools/investigation/README.md` with:
  - proxy setup
  - Ollama/Anthropic compatibility environment
  - required Claude flags
  - normalization caveats and bootstrap/telemetry notes
- Tightened deterministic unit coverage for the Claude web tools:
  - `plugins/claude-tools/tests/test_claude_web_fetch_tool.py`
  - `plugins/claude-tools/tests/test_claude_web_search_tool.py`

Focused validation runs during completion:

```bash
pytest application/python/tests/test_claude_default_config_openrouter_tool_smoke_integration.py -q
```

Result: `5 passed`

```bash
pytest application/python/tests/test_claude_system_message_helpers.py plugins/claude-tools/tests/test_claude_web_fetch_tool.py plugins/claude-tools/tests/test_claude_web_search_tool.py plugins/claude-tools/tests/test_claude_web_search_integration.py -q
```

Result: `19 passed`

```bash
pytest plugins/claude-tools/tests -q
```

Result: `66 passed`

```bash
pytest plugins/web-fetch-shared/tests -q
```

Result: `85 passed`

```bash
pytest plugins/tool-compat-shared/tests -q
```

Result: `1 failed, 152 passed, 1 skipped`

The `tool-compat-shared` failure is outside the Claude work completed here:

- `plugins/tool-compat-shared/tests/test_search_engine.py::test_glob_search_sorts_recent_files_first_and_matches_case_insensitively`

That suite was still run and recorded for `050`, but the failure does not come from the Claude-specific changes in this task.

## Completion Notes

Added during completion.

What is complete now, before `040`:

- Claude tool/config/system-message validation for the implemented non-compaction surface
- application-level execution proof for the default `claude` agent
- real-provider `WebSearch` validation for both Gemini and Tavily
- investigation-harness docs update

What remains blocked or deferred:

- the compaction portion of `050`, because `tasks/20260504-claude-tools-parity/040-investigate-and-implement-claude-compaction.md` is still open
- the first checklist item stays open because it explicitly includes compaction coverage

Recommended next step after this partial `050` pass:

- either fix or explicitly triage the unrelated `tool-compat-shared` glob test failure if we want a clean shared-suite baseline
- then move to `040` Claude compaction, after which the remaining `050` checklist item can be closed
