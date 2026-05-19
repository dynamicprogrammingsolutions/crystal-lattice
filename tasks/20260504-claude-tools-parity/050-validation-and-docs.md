# Validation And Docs

Validate Claude tool/config/compaction parity end to end and update relevant docs so future contributors understand how to investigate and maintain vendor-compatible tools.

## Requirements checklist

- [ ] Add or update unit tests for `claude-tools`, shared formatters, system-message rendering, config loading, and compaction.
- [ ] Add application-level integration tests proving the default `claude` agent lists and can execute the expected tools.
- [ ] Add gated real-provider or Ollama tests where useful and mark/report them correctly.
- [ ] Run focused test suites for touched packages.
- [ ] Update README/docs for Claude tools and the behavior-driven investigation harness.

Parent Task: tasks/20260504-claude-tools-parity/000-main.md

Depends On: tasks/20260504-claude-tools-parity/020-implement-claude-tools.md
Depends On: tasks/20260504-claude-tools-parity/030-implement-claude-system-message-and-config.md
Depends On: tasks/20260504-claude-tools-parity/040-investigate-and-implement-claude-compaction.md

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
