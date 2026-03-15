# 010 - Reader Tools

Short description: Plan and implement the first compatibility tools in the new vendor-specific packages: Gemini-like reader tools in `gemini-tools`, Qwen-like reader tools in `qwen-tools`, and Grok-like `view_file` in `grok-tools`, all backed by a shared internal package.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: None

## Goal

Deliver the first vendor-compatibility tool set with extra attention to schema fidelity, truncation behavior, media/binary handling, and path validation semantics.

This is the most detailed subtask because it establishes:

1. The shared internal package shape.
2. The compatibility testing style.
3. The first concrete examples of public vendor-specific tool classes.

## Desired public package outcome

1. `plugins/gemini-tools/`
- Expose Gemini-like reader class or classes.
- Initial focus: `read_file`
2. `plugins/qwen-tools/`
- Expose Qwen-like reader class or classes.
- Initial focus: `read_file`
3. `plugins/grok-tools/`
- Expose Grok-like reader class or classes.
- Initial focus: `view_file`
4. Shared internal package.
- Not directly enabled by users as a plugin package.
- Owns reusable file-reading internals.

## Why this task should start the whole effort

The reader investigation showed large overlap in internals but meaningful differences in model-facing behavior.

That makes the reader tools the best place to prove the package split:

1. One shared engine.
2. Several thin vendor-specific wrappers.
3. Exact schema/result compatibility tests.

## Existing platform references

### Tool protocol and execution

- Tool protocol:
  - `core/python/agent_core/types.py:963`
- Tool execution and final tool-message formatting:
  - `core/python/agent_core/core.py:2593`

### Current basic file tools

- `core/python/plugins/file_reader_tool.py:13`
- `core/python/plugins/file_writer_tool.py:13`

These are much simpler than the target compatibility tools and should be treated only as rough local examples.

### Node-hosted tool option

- `core/python/agent_core/tool_hosts/node_tool_plugin.py:33`
- `docs/plugins/development.md:602`

Conclusion from investigation: do not start with Node for this subtask. A Python implementation is the best default because the external TypeScript logic is coupled to non-portable config and application services.

## Source-of-truth external references

### Gemini reader

- Tool implementation:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/read-file.ts:32`
- Path validation and truncation wrapper:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/read-file.ts:85`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/read-file.ts:120`
- Shared file logic and constants:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/utils/fileUtils.ts:56`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/utils/fileUtils.ts:407`
- Schema text:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts:36`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/gemini-3.ts:39`

### Qwen reader

- Tool implementation:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/read-file.ts:29`
- Validation logic:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/read-file.ts:174`
- Shared file logic:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/utils/fileUtils.ts:313`

### Grok reader analogue

- Tool schema:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts:5`
- Agent guidance for usage:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/agent/grok-agent.ts:93`

## Compatibility findings that should shape the implementation

### 1. Shared internals are realistic

Gemini and Qwen both support:

1. BOM-aware text reading.
2. Binary detection.
3. SVG special casing.
4. Image/PDF and related media inline payloads.
5. 20MB file-size cap.
6. Similar missing-file/directory failure modes.

This should become a shared internal read engine.

### 2. Public schemas must stay separate

Differences that matter to the model:

1. Parameter names.
2. Relative vs absolute path expectations.
3. Line numbering semantics.
4. Truncation wrapper wording.
5. Ignore-pattern behavior.
6. Directory handling for Grok.

These should be modeled as separate public tool classes, not one schema with compatibility aliases.

### 3. Grok is structurally different

Grok's `view_file` is not just another `read_file` variant. It is a combined:

1. file reader
2. partial file reader
3. directory viewer

That means `grok-tools` should expose a separate `GrokViewFileTool` rather than forcing Grok into the Gemini/Qwen reader abstraction.

## Proposed shared internal package responsibilities

The shared internal package should own reusable helpers like:

1. path normalization and safe workspace checks
2. allowlist / workspace / temp-dir policy helpers
3. BOM detection and text decoding
4. binary/media/SVG detection
5. 20MB cap enforcement
6. line slicing and truncation helpers
7. inline media payload generation
8. result-shape normalization for tests

It should not define public tool names like `read_file` or `view_file`.

## Proposed public classes

### `gemini-tools`

1. `GeminiReadFileTool`
- Tool name: `read_file`
- Parameters: `file_path`, `start_line`, `end_line`
- Match Gemini description and parameter docs exactly or as closely as practical.

### `qwen-tools`

1. `QwenReadFileTool`
- Tool name: `read_file`
- Parameters: `absolute_path`, `offset`, `limit`
- Match Qwen description and parameter docs exactly or as closely as practical.

### `grok-tools`

1. `GrokViewFileTool`
- Tool name: `view_file`
- Parameters: `path`, `start_line`, `end_line`
- Return file content or directory listing depending on target path.

## Behavior requirements

### Gemini-like behavior to match

1. `file_path` may be relative.
2. `start_line` and `end_line` are 1-based.
3. Empty `file_path` yields the Gemini-style validation error.
4. `start_line < 1`, `end_line < 1`, or `start_line > end_line` should mirror Gemini behavior.
5. Ignored files should be rejected.
6. Default text-file read window should behave like Gemini's 2000-line default.
7. Per-line truncation at 2000 chars should be preserved.
8. Truncation banner should closely match:
   `IMPORTANT: The file content has been truncated.`
9. Missing file, directory, binary file, large SVG, and >20MB cases should match Gemini wording as closely as practical.

### Qwen-like behavior to match

1. `absolute_path` must be absolute.
2. `offset` is 0-based.
3. `limit` is a line count.
4. Relative path inputs should fail with Qwen-style wording.
5. Reads are restricted to workspace dirs plus temp/user-skill exceptions.
6. `.qwenignore` behavior should be mirrored as closely as practical.
7. Trailing whitespace should be trimmed per output line.
8. Config-driven line and char truncation should be mirrored.
9. Truncation wrapper should closely match:
   `Showing lines X-Y of Z total lines.`

### Grok-like behavior to match

1. `path` may point to a file or a directory.
2. Directories should produce a listing rather than a file-read error.
3. Partial file view uses `start_line` and `end_line`.
4. Schema description should match the Grok wording:
   `View contents of a file or list directory contents`

## Important gap to document explicitly

The tool plugin can match the model-visible schema and result content, but not every host-side behavior from the source repos.

Examples of non-goals for this subtask:

1. Gemini/Qwen telemetry events.
2. IDE integration.
3. Their exact internal config/service object structure.
4. Grok's full host-side confirmation flow.

## Test plan

Tests for this subtask should be more detailed than later subtasks.

### Schema tests

1. Assert exact tool names.
2. Assert exact parameter names.
3. Assert required fields.
4. Assert important description text or stable snapshots.

### Reader behavior tests

1. missing file
2. path is directory
3. file too large (>20MB)
4. binary file
5. SVG <= 1MB as text
6. SVG > 1MB skipped
7. image/PDF/media inline payload cases
8. BOM handling for UTF-8/16/32
9. Gemini line slicing and truncation banner
10. Qwen offset/limit slicing and char-limit truncation
11. Grok directory listing mode

### Integration tests

1. Plugin package can be loaded through the application plugin manager.
2. A tool call produces the expected final `tool` message content through the normal tool pipeline.

## Deliverables

1. New package structure for the three vendor plugin repos.
2. Shared internal package with reusable read helpers.
3. Vendor-specific reader tool classes.
4. Tests for schema and behavior parity.
5. README notes in each plugin package describing what level of compatibility is intended.

## Execution Plan Added During Completion

Added during completion on 2026-03-15.

1. Make the minimal plugin-manager change needed for sibling Python package dependencies.
- Update local-path plugin installation so it installs from the original project directory instead of an isolated temp copy.
- Rely on the existing `plugin_policy.install_deps` support so local plugin repos can pull in sibling package dependencies through normal packaging metadata.

2. Introduce a shared internal Python package under `plugins/` that is installable but not a public plugin package.
- It will contain reusable reader internals only: path policy helpers, decoding/BOM handling, media and binary detection, size limits, slicing, truncation, and shared formatting helpers.
- It will not expose `agent_plugin.json` or any public tool plugin entries.

3. Create three vendor-specific plugin repos with thin wrappers.
- `plugins/gemini-tools/` with `GeminiReadFileTool`
- `plugins/qwen-tools/` with `QwenReadFileTool`
- `plugins/grok-tools/` with `GrokViewFileTool`
- Each wrapper will emit OpenAI chat-completions tool schemas and adapt shared reader internals to vendor-specific validation and result wording.

4. Use the locally checked-out upstream Gemini/Qwen/Grok sources as the wording and schema reference.
- Match stable schema descriptions, parameter names, validation text, and truncation banners as closely as practical.

5. Add tests in the same change.
- Unit and behavior tests for the shared reader engine and each vendor package.
- Plugin-loading coverage through the application/plugin-manager path.
- End-to-end tool-pipeline coverage for final tool message formatting.
- OpenRouter integration tests using low-cost Qwen, Gemini, and Grok models for one real tool call per vendor package.

6. Run the relevant tests, append completion notes to this task file, and stop after this subtask only.

## Completion Notes Added During Completion

Added during completion on 2026-03-15.

### What changed

1. Minimal plugin-manager support for sibling Python package dependencies.
- Updated `core/python/agent_app/plugin_sources/local_path.py` so local-path plugin installs use the original project directory instead of a copied temp subtree.
- This preserves sibling package layout for install-time path resolution.
- Added regression coverage in `core/python/tests/test_plugin_manager_localpath.py` for a local plugin repo that depends on a sibling Python package.

2. Shared internal package created under `plugins/tool-compat-shared/`.
- Added reusable reader helpers for BOM-aware decoding, binary/media detection, 20MB and SVG size caps, ignore-file matching, Gemini/Qwen text slicing/truncation, Grok directory listing, and tool-result formatting.
- This package intentionally does not expose `agent_plugin.json` entries.

3. Vendor-specific public plugin packages created.
- `plugins/gemini-tools/` exposing `GeminiReadFileTool` with Gemini-style `read_file` schema, relative-path support, `.geminiignore` handling, and Gemini truncation wording.
- `plugins/qwen-tools/` exposing `QwenReadFileTool` with Qwen-style `read_file` schema, absolute-path validation, workspace/temp/user-skills allowlist handling, `.qwenignore` handling, trimmed output lines, and Qwen truncation wording.
- `plugins/grok-tools/` exposing `GrokViewFileTool` with Grok-style `view_file` schema and directory-listing behavior.

4. Package metadata and install wiring.
- Added README files, `agent_plugin.json` descriptors, and package exports for all three public plugin repos.
- Added sibling shared-package dependency wiring through package metadata so these repos can be loaded through the application plugin manager when dependency installation is enabled.

5. Tests added for this subtask.
- Shared helper tests in `plugins/tool-compat-shared/tests/test_reader_engine.py`.
- Vendor package behavior and plugin-manager loading tests in:
  - `plugins/gemini-tools/tests/test_gemini_read_file_tool.py`
  - `plugins/qwen-tools/tests/test_qwen_read_file_tool.py`
  - `plugins/grok-tools/tests/test_grok_view_file_tool.py`
- Real OpenRouter integration tests in:
  - `plugins/gemini-tools/tests/test_gemini_read_file_tool_openrouter_integration.py`
  - `plugins/qwen-tools/tests/test_qwen_read_file_tool_openrouter_integration.py`
  - `plugins/grok-tools/tests/test_grok_view_file_tool_openrouter_integration.py`

### Files touched

1. `core/python/agent_app/plugin_sources/local_path.py`
2. `core/python/tests/test_plugin_manager_localpath.py`
3. `plugins/tool-compat-shared/README.md`
4. `plugins/tool-compat-shared/pyproject.toml`
5. `plugins/tool-compat-shared/src/tool_compat_shared/__init__.py`
6. `plugins/tool-compat-shared/src/tool_compat_shared/reader_engine.py`
7. `plugins/tool-compat-shared/tests/test_reader_engine.py`
8. `plugins/gemini-tools/README.md`
9. `plugins/gemini-tools/pyproject.toml`
10. `plugins/gemini-tools/setup.py`
11. `plugins/gemini-tools/agent_plugin.json`
12. `plugins/gemini-tools/src/gemini_tools/__init__.py`
13. `plugins/gemini-tools/src/gemini_tools/gemini_read_file_tool.py`
14. `plugins/gemini-tools/tests/test_gemini_read_file_tool.py`
15. `plugins/gemini-tools/tests/test_gemini_read_file_tool_openrouter_integration.py`
16. `plugins/qwen-tools/README.md`
17. `plugins/qwen-tools/pyproject.toml`
18. `plugins/qwen-tools/setup.py`
19. `plugins/qwen-tools/agent_plugin.json`
20. `plugins/qwen-tools/src/qwen_tools/__init__.py`
21. `plugins/qwen-tools/src/qwen_tools/qwen_read_file_tool.py`
22. `plugins/qwen-tools/tests/test_qwen_read_file_tool.py`
23. `plugins/qwen-tools/tests/test_qwen_read_file_tool_openrouter_integration.py`
24. `plugins/grok-tools/README.md`
25. `plugins/grok-tools/pyproject.toml`
26. `plugins/grok-tools/setup.py`
27. `plugins/grok-tools/agent_plugin.json`
28. `plugins/grok-tools/src/grok_tools/__init__.py`
29. `plugins/grok-tools/src/grok_tools/grok_view_file_tool.py`
30. `plugins/grok-tools/tests/test_grok_view_file_tool.py`
31. `plugins/grok-tools/tests/test_grok_view_file_tool_openrouter_integration.py`

### Tests run

1. `python -m pip install -e core/python -e plugins/tool-compat-shared -e 'plugins/gemini-tools[dev]' -e 'plugins/qwen-tools[dev]' -e 'plugins/grok-tools[dev]' -e 'plugins/openrouter[dev]'`
2. `python -m pytest core/python/tests/test_plugin_manager_localpath.py plugins/tool-compat-shared/tests/test_reader_engine.py plugins/gemini-tools/tests/test_gemini_read_file_tool.py plugins/qwen-tools/tests/test_qwen_read_file_tool.py plugins/grok-tools/tests/test_grok_view_file_tool.py -q`
3. `python -m pytest -o addopts='' plugins/gemini-tools/tests/test_gemini_read_file_tool_openrouter_integration.py plugins/qwen-tools/tests/test_qwen_read_file_tool_openrouter_integration.py plugins/grok-tools/tests/test_grok_view_file_tool_openrouter_integration.py -q`
4. Re-ran step 3 after registering plugin-local pytest markers.

### Outcomes

1. Focused unit and behavior test slice passed: `23 passed`.
2. OpenRouter integration slice passed: `3 passed`.

### Open issues / follow-ups

1. Media results are preserved structurally in the tool result payload, but the current normal tool-message pipeline remains text-first; this subtask did not extend the core/application layers to pass true non-text tool result parts back to the model.
2. This subtask only covers reader tools and the minimal local-path plugin-manager support needed for sibling package installation. Edit/write and list/grep/glob compatibility remain for later subtasks.
