# Gemini, Qwen, and Grok Tool Packages

Short description: Plan a compatibility-oriented tool-plugin effort organized into separate plugin packages `gemini-tools`, `qwen-tools`, and `grok-tools`, backed by a shared non-plugin package with common filesystem/search logic, plus application changes to allow agent/provider-specific plugin package specs.

## Goal

Build new tool plugin packages that behave like the corresponding open-source CLI tools closely enough that an agent can be configured with Gemini-like, Qwen-like, or Grok-like tool surfaces.

The user asked for:

1. Separate plugin packages grouped under:
- `gemini-tools`
- `qwen-tools`
- `grok-tools`
2. A shared package containing reusable logic, but not itself exposed as a tool plugin package.
3. Initial subtasks focused on:
- reader tools
- edit and write tools
- list, grep, and glob tools
4. A fourth subtask to extend configuration so plugin packages can be declared at the agent or provider level in addition to the current global `plugins` list.
5. A fifth subtask to extract Gemini-friendly, Qwen-friendly, and Grok-friendly system-message templates and reconstruction notes for later manual or feature-backed implementation.
6. For config-level agent/provider settings, reuse the `plugins` key with a new meaning.
- At the agent/provider config level, `plugins` should mean plugin package specs.
- No backward compatibility is required for the old agent-level meaning.
7. Keep the existing session metadata/UI-controlled `plugins` key semantics.
- Session metadata `plugins` remains the explicit enabled-plugin-id list.
8. Add a new config-level `disabled_plugins` key for less verbose plugin enablement.

## Package structure direction

Target plugin/package layout:

1. `plugins/gemini-tools/`
- Tool plugin package exposing Gemini-like tools and schemas.
2. `plugins/qwen-tools/`
- Tool plugin package exposing Qwen-like tools and schemas.
3. `plugins/grok-tools/`
- Tool plugin package exposing Grok-like tools and schemas.
4. A shared package for common logic.
- This should not be a standalone plugin package users enable directly.
- It can live either as a shared Python package under one of the plugin repos or as a separate internal helper package/repo that the three plugin packages depend on.
- The important constraint is architectural: shared helpers should not themselves define the public tool surface seen by models.

Recommended interpretation:

1. Keep each compatibility surface in its own plugin repo so the model only sees one vendor-style tool family at a time.
2. Share internals aggressively for path handling, binary/text detection, truncation, replacement logic, listing, globbing, grep formatting, and test fixtures.
3. Avoid one public mega-plugin with a runtime mode switch, because the model-facing schemas need to stay vendor-accurate.

## Why separate public tool packages are preferred

The investigation showed that Gemini, Qwen, and Grok differ in ways that are important to model behavior:

1. Different tool names.
- Gemini reader: `read_file`
- Qwen reader: `read_file`, but different parameter names and semantics
- Grok reader analogue: `view_file`
2. Different parameter names.
- Gemini: `file_path`, `start_line`, `end_line`
- Qwen: `absolute_path`, `offset`, `limit`
- Grok: `path`, `start_line`, `end_line`
3. Different truncation policies and wording.
4. Different error wording and path validation rules.
5. Different editing/write patterns.
6. Grok's search model is structurally different from Gemini/Qwen list/grep/glob.

Those differences make separate model-facing classes the cleaner choice, even if the internals are shared.

## Current repo capabilities we can build on

The host framework already supports the plugin architecture we need:

1. Python `ToolPlugin` protocol:
- `core/python/agent_core/types.py:963`
2. Tool execution and final message formatting pipeline:
- `core/python/agent_core/core.py:2593`
3. Existing simple file tools for baseline comparison:
- `core/python/plugins/file_reader_tool.py:13`
- `core/python/plugins/file_writer_tool.py:13`
4. Node-hosted JS/TS tool plugins, if we later need them:
- `core/python/agent_core/tool_hosts/node_tool_plugin.py:33`
- `docs/plugins/development.md:602`

Important implementation takeaway from the investigation:

1. The framework is flexible enough to match tool schemas and LLM-visible result content.
2. Exact parity for CLI confirmation UX, IDE diff integration, or host-managed approval flows is out of scope for pure tool plugins unless the application/core layers are extended.
3. For the first pass, Python implementations are the best default. The external TS repos are informative but not directly reusable because their logic is tightly coupled to their own config, telemetry, ignore, approval, and IDE layers.

## External investigation summary

### Gemini reader references

- Tool implementation:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/read-file.ts:32`
- Shared file-reading logic:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/utils/fileUtils.ts:56`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/utils/fileUtils.ts:407`
- Schema/description source:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts:36`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/gemini-3.ts:39`

Key reader behavior:

1. Accepts `file_path`, optional `start_line`, optional `end_line`.
2. Relative paths are resolved from target dir.
3. Enforces workspace path validation.
4. Rejects ignored files.
5. Supports text, SVG-as-text, image/audio/video/PDF inline payloads.
6. Uses a 20MB file cap.
7. Text read defaults to 2000 lines with per-line truncation at 2000 chars.
8. Emits a very specific truncation banner when content is truncated.

### Qwen reader references

- Tool implementation:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/read-file.ts:29`
- Shared file-reading logic:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/utils/fileUtils.ts:313`
- Tool names and migration notes:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/tool-names.ts:8`

Key reader behavior:

1. Accepts `absolute_path`, optional `offset`, optional `limit`.
2. Requires absolute paths.
3. Restricts reads to workspace dirs plus temp/user-skill locations.
4. Rejects `.qwenignore`-ignored files.
5. Uses a 20MB file cap.
6. Trims trailing whitespace from each line before output.
7. Uses config-driven line and char truncation.
8. Emits a shorter truncation wrapper than Gemini.

### Grok reader/search/edit references

- Tool schema bundle:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts:5`
- Agent instructions showing intended use:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/agent/grok-agent.ts:80`

Key observations:

1. Grok's read analogue is `view_file`, not `read_file`.
2. `view_file` also lists directories.
3. Grok edit tool is `str_replace_editor`, not Gemini/Qwen `replace`/`edit`.
4. Grok search is a unified `search` tool, not simply `list_directory` + `grep_search` + `glob`.

## Subtasks

1. `tasks/20260315-gemini-qwen-grok-tool-packages/010-reader-tools.md`
2. `tasks/20260315-gemini-qwen-grok-tool-packages/020-edit-and-write-tools.md`
3. `tasks/20260315-gemini-qwen-grok-tool-packages/030-list-grep-glob-tools.md`
4. `tasks/20260315-gemini-qwen-grok-tool-packages/040-agent-and-provider-plugin-package-config.md`
5. `tasks/20260315-gemini-qwen-grok-tool-packages/050-vendor-friendly-system-messages.md`
6. `tasks/20260315-gemini-qwen-grok-tool-packages/060-simplified-system-message-configs-and-minimal-dynamics.md`
7. `tasks/20260315-gemini-qwen-grok-tool-packages/070-core-rebuild-after-native-initialize-changes.md`
8. `tasks/20260315-gemini-qwen-grok-tool-packages/080-portable-default-config-and-compiled-system-message-ui.md`

## Cross-cutting decisions to preserve throughout implementation

1. Public tool classes should be vendor-specific.
- Example: `GeminiReadFileTool`, `QwenReadFileTool`, `GrokViewFileTool`
2. Shared internals should live outside the public plugin surface.
3. No alias parameters unless a subtask explicitly decides a backward-compat alias is necessary.
4. Tests should assert exact schema names, parameter names, and important truncation/error strings.
5. Session metadata `plugins` should remain a list of enabled plugin ids/class-style identities, not a place to store plugin package specs.
6. At the agent/provider config level, `plugins` should mean plugin package specs rather than enabled plugin ids.
7. No backward compatibility is required for the old agent-level `plugins` meaning.
8. Add config-level `disabled_plugins` support as a concise alternative to an explicit enabled list.

## Open design questions to resolve during execution

1. Where exactly should the shared internal package live?
- Options include a dedicated internal package repo under `plugins/` or shared code duplicated minimally per plugin package.
2. Whether vendor-specific packages should each vendor-copy a tiny compatibility layer or depend on a common installable local package.
3. For the fourth subtask, whether provider-level plugin package specs should be allowed only on provider configs, only on agent configs, or on both with a documented merge order.
4. Exact precedence between session metadata `plugins`, config-level `disabled_plugins`, and implicit all-enabled behavior.

## Recommended execution order

1. Reader tools first, including the shared internal read engine and package structure decisions.
2. Edit/write tools second, reusing the same shared package.
3. List/grep/glob third, after the shared filesystem/search helpers are in place.
4. Agent/provider plugin package config support either before tool-package rollout or in parallel, because it enables cleaner configuration of the new vendor bundles.
5. Vendor-friendly system messages after the vendor tool surfaces are stable enough to reference accurately.
6. Simplified runtime system-message configs and minimal dynamic-section support after the extracted vendor instructions exist and the package-loading model is stable.
