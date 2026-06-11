# Claude MCP Tools

Investigate Claude Code's MCP behavior and add Claude-compatible MCP tool support to the existing `claude-tools` package using the shared MCP runtime infrastructure already proven by Codex.

## Requirements checklist

- [x] Stage 1: Investigate real Claude Code MCP behavior with a deterministic filesystem MCP server and normalized fixtures.
- [x] Stage 1: Document the observed Claude MCP model-facing naming, schema, tool-call payload, result formatting, startup/error behavior, and transcript/debug artifacts.
- [x] Stage 2: Implement a Claude-specific MCP wrapper inside `plugins/claude-tools` without moving Claude-specific naming/schema/result logic into `mcp-shared`.
- [x] Stage 2: Wire the wrapper into Claude plugin packaging/config/docs, including local `mcp-shared` dependency metadata.
- [x] Stage 2: Add deterministic unit tests plus realistic integration coverage through a real MCP server and, where appropriate, the shipped default config.
- [x] Stage 2: Update related task status and docs after verification.

## Related Work

- `tasks/20260315-gemini-qwen-grok-tool-packages/150-mcp-tools.md`
- `tasks/20260504-claude-tools-parity/000-main.md`
- `tasks/20260504-claude-tools-parity/050-validation-and-docs.md`

## Current Worktree

This task was created for:

```text
/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/claude-mcp-tools
branch: task/claude-mcp-tools
```

The worktree was created from `develop` and installed with:

```bash
python -m pip install -e "core/python[dev]"
python -m pip install -e application/python
```

Fresh validation note from this worktree:

```bash
pytest plugins/tool-compat-shared/tests -q
```

Result:

```text
1 failed, 149 passed, 4 skipped
```

The remaining shared-suite failure is:

```text
plugins/tool-compat-shared/tests/test_search_engine.py::test_glob_search_sorts_recent_files_first_and_matches_case_insensitively
```

This failure is still present on the clean branch and should be fixed or explicitly triaged before using `050` as a fully clean validation baseline.

## Existing MCP Implementation To Reuse

The completed Codex MCP slice is the reference implementation:

- `plugins/codex-tools/src/codex_tools/mcp_tool.py`
- `plugins/codex-tools/src/codex_tools/mcp_names.py`
- `plugins/codex-tools/tests/test_mcp_tool.py`
- `application/python/tests/test_terminal_default_config_codex_mcp_real_api.py`
- `plugins/codex-tools/agent_plugin.json`
- `plugins/codex-tools/README.md`

Shared MCP runtime package:

- `plugins/mcp-shared/src/mcp_shared/runtime.py`
- `plugins/mcp-shared/src/mcp_shared/registry.py`
- `plugins/mcp-shared/tests/test_runtime.py`
- `plugins/mcp-shared/README.md`

MCP observability app plugin:

- `plugins/mcp-runtime-app/src/mcp_runtime_app/__init__.py`
- `plugins/mcp-runtime-app/tests/test_mcp_runtime_app.py`
- `plugins/mcp-runtime-app/README.md`

Important established architecture:

- `mcp-shared` is not a plugin package and must remain vendor-neutral.
- `MCPRuntimeManager` owns transports, live MCP sessions, discovery, raw calls, and cleanup.
- `MCPRegistry` is stored in the generic application `runtime_store` under `mcp_registry`.
- Vendor wrappers own all model-facing shape:
  - config parsing
  - UI toggles
  - model-visible tool naming
  - schema shaping
  - result formatting
  - error wording
- Codex currently exposes MCP tools as `mcp__server__tool`.
- The shared config keys are:
  - `mcp_enabled`
  - `mcp_fail_on_startup_error`
  - `mcp_reuse_runtime`
  - `mcp_servers`

## Claude Package State

Claude tools currently live in:

- `plugins/claude-tools/src/claude_tools/`
- `plugins/claude-tools/agent_plugin.json`
- `plugins/claude-tools/setup.py`
- `plugins/claude-tools/README.md`

Current Claude local workspace dependencies:

- `tool-compat-shared`
- `web-fetch-shared`

`plugins/claude-tools/setup.py` will need a third sibling dependency for:

- `mcp-shared`

`plugins/claude-tools/agent_plugin.json` will need:

- a new Claude MCP tool entry
- `"mcp-shared"` in `local_workspace_dependencies`

## Investigation Target

Use the official filesystem MCP server as the primary real MCP server:

```bash
npx -y @modelcontextprotocol/server-filesystem <workspace-dir>
```

Reasons:

- It is already used by the completed Codex MCP e2e path.
- It is deterministic with a small temporary workspace.
- It exercises stdio startup, tool discovery, tool schema exposure, tool calls, and tool result formatting.
- It requires no extra service credentials.
- It is simple enough for Claude Code to call reliably with direct prompts.

Suggested deterministic workspace:

```text
workspace/
  note.txt
  nested/
    facts.md
```

Suggested probe prompts:

```text
Use the MCP filesystem tool to read note.txt. Reply with exactly the first line.
```

```text
Use the MCP filesystem tool to read nested/facts.md. Then answer with exactly the value after "Answer:".
```

Add a minimal local MCP fixture server only if the official filesystem server does not expose enough information for error cases or non-text content.

## Stage 1 Plan: Investigation

1. Add a Claude MCP investigation script under:

   ```text
   plugins/claude-tools/investigation/scripts/investigate_mcp.py
   ```

2. Reuse the existing Claude investigation/proxy conventions:

   - run real Claude Code
   - force project settings where possible
   - use the Anthropic-compatible proxy setup already documented for Claude investigations
   - capture raw logs under ignored `investigation/raw/`
   - write normalized fixtures under `investigation/fixtures/mcp/`

3. Start the official filesystem MCP server through Claude Code MCP config rather than through test-only shortcuts.

4. Capture normalized fixtures for at least:

   - successful text read from the filesystem MCP server
   - unknown or invalid file path error
   - disabled or failing MCP server if Claude exposes useful behavior
   - at least one case with two files/tools if needed to observe naming and disambiguation

5. Normalize machine-specific values:

   - workspace paths -> `<WORKSPACE>`
   - session ids -> `<SESSION_ID>`
   - transcript paths -> `<PROJECT_TRANSCRIPT>`
   - temporary MCP config paths -> `<MCP_CONFIG>`
   - proxy/request ids and timestamps where needed

6. Document findings in:

   ```text
   plugins/claude-tools/investigation/notes/mcp.md
   ```

7. Required questions to answer before implementation:

   - What model-visible names does Claude use for MCP tools?
   - Does Claude prefix names with `mcp__server__tool`, use `server__tool`, or use another shape?
   - What does the Anthropic `tools` array look like for MCP tools?
   - How are MCP input schemas preserved or sanitized?
   - What exact payload does Claude send in a tool-use block?
   - What does Claude send back to the model as a tool result?
   - How are MCP startup failures surfaced?
   - Does Claude write MCP-specific transcript/debug artifacts worth emulating?
   - Does Claude include any MCP server status UI behavior that belongs in our existing `mcp-runtime-app` story?

8. Pause after Stage 1 and update this task with the observed implementation contract before writing production code.

## Stage 2 Plan: Implementation

Only start this stage after Stage 1 findings are recorded.

1. Add the Claude MCP wrapper:

   ```text
   plugins/claude-tools/src/claude_tools/claude_mcp_tool.py
   ```

2. Keep the wrapper architecture parallel to Codex MCP:

   - `init(config)` stores static local config state
   - `prepare_async(config, state, context=...)` builds `MCPRuntimeConfig`, uses `MCPRegistry`, discovers tools, and returns JSON-like prepared catalog data
   - `get_tool_schemas(state, prepared=...)` exposes Claude/Anthropic-shaped tool schemas
   - `can_handle_tool_call(...)` recognizes prepared Claude MCP tool names
   - `execute_tool_async(..., prepared=...)` routes raw calls through `MCPRegistry`
   - `format_tool_result(...)` emits Claude-compatible tool results based on Stage 1 fixtures

3. Reuse the common MCP config keys unless Stage 1 proves Claude requires different public config:

   ```json
   {
     "mcp_enabled": true,
     "mcp_fail_on_startup_error": false,
     "mcp_reuse_runtime": true,
     "mcp_servers": {}
   }
   ```

4. Add Claude MCP UI elements:

   - global `mcp_enabled` checkbox
   - per-server checkbox matching the existing Codex convention
   - keep full nested server editing out of scope

5. Update package wiring:

   - `plugins/claude-tools/agent_plugin.json`
   - `plugins/claude-tools/src/claude_tools/__init__.py`
   - `plugins/claude-tools/setup.py`
   - `plugins/claude-tools/README.md`

6. Update local dependency metadata:

   - add `"mcp-shared"` to `plugins/claude-tools/agent_plugin.json` `local_workspace_dependencies`
   - add the sibling `mcp-shared @ file://...` dependency in `plugins/claude-tools/setup.py`

7. Add deterministic tests:

   ```text
   plugins/claude-tools/tests/test_claude_mcp_tool.py
   ```

   Cover:

   - global/per-server UI toggles
   - disabled global MCP behavior
   - disabled server behavior
   - name qualification and collision behavior from fake discovered tools
   - schema shaping from fake discovered tools
   - execution routing with a fake runtime manager
   - result formatting for text, structured content, and MCP errors

8. Add real integration coverage:

   - use the official filesystem MCP server
   - verify discovered tools are exposed through the Claude wrapper
   - verify a real MCP call can read a deterministic file
   - close/reconnect runtime through `mcp-runtime-app` where practical

9. Add default-config/API smoke coverage if the branch scope includes shipped config wiring:

   - load the shipped default config
   - use the real `claude` agent
   - enable MCP through session plugin/config UI paths, not shortcuts
   - use a real OpenRouter model and real filesystem MCP server
   - verify the model calls an MCP-backed tool and answers with the deterministic file content

10. Revisit MCP wrapper conflict handling:

   - If Claude MCP can coexist in default config with Codex MCP in different agents only, document that as acceptable for this task.
   - If a single agent can enable more than one MCP wrapper, add or schedule conflict-key validation as described in `tasks/20260315-gemini-qwen-grok-tool-packages/150-mcp-tools.md`.

## Test Targets

Expected focused tests after implementation:

```bash
pytest plugins/claude-tools/tests/test_claude_mcp_tool.py -q
pytest plugins/mcp-shared/tests -q
pytest plugins/mcp-runtime-app/tests -q
pytest plugins/codex-tools/tests/test_mcp_tool.py -q
```

If default-config real coverage is added:

```bash
pytest -m "integration and api and openrouter" application/python/tests/test_claude_default_config_mcp_real_api.py -q
```

If the shared glob failure is fixed in this branch, rerun:

```bash
pytest plugins/tool-compat-shared/tests -q
```

## Acceptance Criteria

- Claude MCP behavior is captured from real Claude Code before production implementation.
- Normalized Claude MCP fixtures and notes are committed under `plugins/claude-tools/investigation/`.
- `mcp-shared` remains vendor-neutral.
- `claude-tools` owns all Claude-specific naming, schema shaping, and result formatting.
- The Claude MCP wrapper uses `MCPRegistry` in application `runtime_store` for runtime reuse and cleanup.
- Package dependency metadata includes `mcp-shared`.
- Deterministic unit tests cover the wrapper.
- Real integration coverage proves at least one filesystem MCP tool can be discovered and called.
- README/config docs explain Claude MCP support and config keys.

## Stage 1 Findings

Added after the approved Stage 1 investigation.

Implemented and ran:

```text
plugins/claude-tools/investigation/scripts/investigate_mcp.py
```

Captured normalized fixtures:

```text
plugins/claude-tools/investigation/fixtures/mcp/filesystem-read-file.json
plugins/claude-tools/investigation/fixtures/mcp/filesystem-read-nested-file.json
plugins/claude-tools/investigation/fixtures/mcp/filesystem-missing-file.json
```

Documented findings:

```text
plugins/claude-tools/investigation/notes/mcp.md
```

Verification:

```bash
ruff check plugins/claude-tools/investigation/scripts/investigate_mcp.py
python -m py_compile plugins/claude-tools/investigation/scripts/investigate_mcp.py
```

Result: both passed.

Observed contract:

- Claude Code version used: `2.1.154`
- MCP config works through `--strict-mcp-config --mcp-config <mcp.json>` with a Claude-style `mcpServers` object.
- Passing `--tools ""` suppresses MCP tool schemas too; the investigation harness should not use it.
- Real MCP tool execution was captured with `--permission-mode bypassPermissions`; without it Claude attempted MCP calls but local permission handling denied them.
- Claude exposes MCP tools as `mcp__<server>__<tool>`, for example `mcp__filesystem__read_text_file`.
- Claude sends MCP tools in the Anthropic `tools` array with normal `name`, `description`, and `input_schema` fields.
- The MCP input schema was preserved substantially as provided by the filesystem server, including `$schema`.
- Claude emits normal Anthropic `tool_use` blocks with the qualified MCP tool name and forwards model arguments to the MCP server.
- Successful text results are returned as Anthropic `tool_result` blocks whose `content` is a JSON string such as `{"content":"..."}` plus `cache_control: {"type": "ephemeral"}`.
- MCP errors are returned as Anthropic `tool_result` blocks with `is_error: true` and plain error text content, plus ephemeral cache control.
- Claude starts the stdio MCP server before sending MCP schemas, calls raw MCP tools by unqualified raw names internally, and closes the process cleanly on exit.

Implementation contract for Stage 2:

- Implement `plugins/claude-tools/src/claude_tools/claude_mcp_tool.py`.
- Reuse `mcp-shared` and `MCPRegistry` for runtime management.
- Keep name qualification, Anthropic schema exposure, and Anthropic result formatting in `claude-tools`.
- Use `mcp__server__tool` naming.
- Preserve discovered MCP input schemas as Anthropic `input_schema`.
- Format successful text MCP content as a JSON string `{"content": "<text>"}` in the tool result.
- Format MCP errors with `is_error: true` and the raw error text.

## Out Of Scope

- MCP prompts
- MCP resources beyond whatever appears in normal tool results
- OAuth/browser login for remote MCP servers
- full nested UI editing of MCP server definitions
- dynamic tool-list change notifications
- implementing Kimi/Gemini MCP wrappers
- fixing the unrelated `tool-compat-shared` glob failure unless this branch explicitly expands to include validation cleanup

## Completion Notes

Added during completion after the approved Stage 1 checkpoint.

Implemented:

- `plugins/claude-tools/src/claude_tools/claude_mcp_tool.py`
- `plugins/claude-tools/tests/test_claude_mcp_tool.py`
- `application/python/tests/test_terminal_default_config_claude_mcp_real_api.py`

Updated:

- `plugins/claude-tools/src/claude_tools/__init__.py`
- `plugins/claude-tools/agent_plugin.json`
- `plugins/claude-tools/setup.py`
- `plugins/claude-tools/README.md`
- `application/python/agent_terminal_app/default_config/config.json`
- `application/python/tests/test_claude_system_message_helpers.py`
- `application/python/tests/test_default_config_effective_agent_configs.py`

Behavior implemented:

- Claude MCP wrapper uses `mcp-shared` for runtime lifecycle, discovery, raw MCP calls, and app-owned `MCPRegistry` reuse.
- Claude-specific logic remains in `claude-tools`.
- MCP tools are exposed as Anthropic schemas named `mcp__server__tool`.
- Discovered MCP input schemas are preserved as Anthropic `input_schema`.
- Successful text MCP results format as Anthropic-native `tool_result` blocks containing a JSON string `{"content":"..."}` with ephemeral cache control.
- MCP errors format as Anthropic-native `tool_result` blocks with `is_error: true`, raw error text, and ephemeral cache control.
- The shipped `claude` default agent now includes disabled-by-default `claude_mcp_defaults` with a filesystem MCP server definition matching the existing Codex MCP default shape.
- `claude-tools` now declares `mcp-shared` in both package setup and local workspace dependency metadata.

Verification run:

```bash
ruff check plugins/claude-tools/src/claude_tools/claude_mcp_tool.py plugins/claude-tools/tests/test_claude_mcp_tool.py plugins/claude-tools/investigation/scripts/investigate_mcp.py
pytest plugins/claude-tools/tests/test_claude_mcp_tool.py -q
pytest plugins/mcp-shared/tests plugins/mcp-runtime-app/tests plugins/codex-tools/tests/test_mcp_tool.py -q
pytest plugins/claude-tools/tests -q
pytest application/python/tests/test_claude_system_message_helpers.py -q
pytest -m integration application/python/tests/test_default_config_effective_agent_configs.py -q
```

Results:

- `ruff`: passed
- Claude MCP tests: `7 passed`
- shared MCP/Codex MCP regression tests: `14 passed`
- full `plugins/claude-tools/tests`: `92 passed, 3 skipped`
- Claude default-config/system-message tests: `4 passed`
- default-config effective agent configs: `1 passed`

Real API/default-config smoke:

```bash
set -a
source /Users/ferenci84/Dev/Mine/ai-agent-platform/.env
set +a
pytest -m "integration and api and openrouter" application/python/tests/test_terminal_default_config_claude_mcp_real_api.py -q
```

Result:

- `1 passed`

Notes:

- The new worktree does not have its own `.env`; the real API test initially skipped until the original checkout `.env` was sourced.
- The first real API attempt proved the model called `mcp__filesystem__read_text_file`, but failed because the default MCP server root came from the sourced `WORKING_DIR`. The final test overrides `mcp_servers` at the session level instead, which exercises the realistic UI/config override path without disturbing app-level default config.
- `tasks/20260504-claude-tools-parity/050-validation-and-docs.md` still records the unrelated `tool-compat-shared` glob sorting failure as the remaining clean-baseline issue outside this task.