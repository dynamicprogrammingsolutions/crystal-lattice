# Gemini, Qwen, Grok, and Kimi Tool Packages

Short description: Plan a compatibility-oriented tool-plugin effort organized into separate plugin packages `gemini-tools`, `qwen-tools`, `grok-tools`, and `kimi-tools`, backed by shared non-plugin packages with common filesystem/search/web/logic, plus application changes to allow agent/provider-specific plugin package specs.

## Goal

Build new tool plugin packages that behave like the corresponding open-source CLI tools closely enough that an agent can be configured with Gemini-like, Qwen-like, or Grok-like tool surfaces.

The user asked for:

1. Separate plugin packages grouped under:
- `gemini-tools`
- `qwen-tools`
- `grok-tools`
- `kimi-tools`
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

### Phase 1: Core file tools (Gemini, Qwen, Grok)

- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/010-reader-tools.md`
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/020-edit-and-write-tools.md`
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/030-list-grep-glob-tools.md`

### Phase 1.5: Application and config support

- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/040-agent-and-provider-plugin-package-config.md`
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/050-vendor-friendly-system-messages.md`
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/060-simplified-system-message-configs-and-minimal-dynamics.md`
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/070-core-rebuild-after-native-initialize-changes.md`
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/080-portable-default-config-and-compiled-system-message-ui.md`

### Phase 2: Kimi + cross-vendor tools

- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/090-kimi-tools.md` — Kimi core file tools
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/095-kimi-system-message.md` — Kimi default system message extraction
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/100-shell-tools.md` — Shell tools planning (all four vendors)
  - [x] `tasks/20260315-gemini-qwen-grok-tool-packages/101-shell-engine-core.md` — Core engine with asyncio
  - [x] `tasks/20260315-gemini-qwen-grok-tool-packages/102-shell-engine-truncation.md` — Generic truncation
  - [x] `tasks/20260315-gemini-qwen-grok-tool-packages/103-shell-engine-background.md` — Background process support
  - [x] `tasks/20260315-gemini-qwen-grok-tool-packages/104-codex-v2-tool.md` — Codex V2 tool
  - [x] `tasks/20260315-gemini-qwen-grok-tool-packages/105-vendor-tools.md` — Vendor wrappers
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/110-web-fetch-tools.md` — Web fetch tools
  - [x] `tasks/20260315-gemini-qwen-grok-tool-packages/111-tool-plugin-context.md`
  - [x] `tasks/20260315-gemini-qwen-grok-tool-packages/112-web-fetch-shared.md`
  - [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/113-gemini-web-fetch.md`
  - [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/114-qwen-web-fetch.md`
  - [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/115-kimi-fetch-url.md`
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/120-web-search-tools.md` — Web search tools
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/130-todo-tools.md` — Todo tools (all four vendors)
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/135-background-process-management.md` — Background process management (application layer, Tier 2)

### Phase 2.5: Context compaction

- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/220-gemini-compaction-plugin.md` — Stage 1: Application-level manual compaction plugin
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/221-feature-plugin-context.md` — Stage 2: Feature plugin with layered context (core/app/terminal)
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/222-lifecycle-auto-compaction.md` — Stage 3: Lifecycle-triggered auto-compaction
- [x] `tasks/20260315-gemini-qwen-grok-tool-packages/223-session-aware-application-plugin-ui.md` — Session-aware application plugin UI (completes tasks 20260128/040 and 20260130/010)
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/230-qwen-compaction-and-checkpoint-replay.md` — Implement Qwen-like compaction and checkpoint replay behavior
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/240-kimi-compaction-and-checkpoints.md` — Implement Kimi-like compaction, checkpoints, and D-Mail-adjacent context management behavior where applicable
- [ ] `tasks/20260315-gemini-qwen-grok-tool-packages/250-shared-compaction-helpers.md` — Shared compaction helpers and cross-vendor implementation notes

### Phase 2 shared packages

- `plugins/tool-compat-shared/` — shared filesystem, search, shell, and todo internals (stdlib-only deps)
- `plugins/web-fetch-shared/` — shared HTTP fetch and trafilatura extraction (heavy deps: `trafilatura`, `aiohttp`); LLM summarization handled via tool context access to core/app

## Roadmap: Deferred tools

The following tools are deferred to future subtasks. Each has prerequisites from the deferred list and from completed work. High-priority items are listed first.

### High priority

#### 140 — Ask User Question (all vendors)

Structured question/response tool allowing the LLM to present options to the user and receive structured answers.

**Vendor coverage**:
- Gemini: `ask_user` — free-form text question.
- Kimi: `AskUserQuestion` — structured questions (1-4) with options (2-4 each), multi-select, recommended labels.
- Qwen: no equivalent in current codebase.
- Grok: no equivalent in current codebase.

**Why deferred**: Requires core/app-layer changes for a question/response protocol between the tool plugin and the application's UI layer. The current `ToolPlugin` protocol only supports request/response tool calls — it does not have a mechanism for the tool to pause execution and wait for user interaction mid-turn.

**Prerequisites**:
- Core: extend `ToolPlugin` protocol or application layer with a question/response interaction model (e.g., `ToolQuestion` return type that the app/terminal can render as an interactive prompt).
- Core or app: session-level state to track pending questions and their resolutions.
- Terminal/HTTP app: UI support for rendering structured question prompts and collecting answers.
- 040 (agent/provider plugin config) — for per-agent tool availability.

**Source references**:
- Kimi: `../kimi-cli/src/kimi_cli/tools/ask_user/__init__.py`, `../kimi-cli/src/kimi_cli/tools/ask_user/description.md`
- Gemini: `../gemini-cli/packages/core/src/tools/ask-user.ts`, `../gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts` (ask_user schema)

#### 150 — Task / Subagent Delegation (all vendors)

Tool for delegating work to specialized subagents from within a tool call.

**Vendor coverage**:
- Gemini: `SubagentTool` — agents-as-tools pattern; built-in subagents (`codebase_investigator`, `cli_help`, `generalist`) registered as tools.
- Qwen: `Task` — delegates to subagents with `subagent_name` + `prompt` params.
- Kimi: `Task` — delegates to subagents with `subagent_name` + `prompt` params; `CreateSubagent` — dynamically creates new subagent configurations at runtime.
- Grok: no equivalent in current codebase.

**Why deferred**: Requires core/app-layer subagent/labor market infrastructure. The current framework has no concept of subagent isolation, subagent toolsets, or subagent context management. This is a significant architectural extension.

**Prerequisites**:
- Core: subagent isolation model (separate toolset, separate context/history, separate session scope).
- Core: labor market / subagent registry for managing available subagents.
- Core: tool-call-level subagent execution within the existing tool pipeline.
- App: per-agent subagent configuration wiring.
- 040 (agent/provider plugin config) — for per-agent subagent specs.
- 140 (ask user question) — subagents may need to ask questions during execution.

**Source references**:
- Gemini: `../gemini-cli/packages/core/src/agents/subagent-tool.ts`, `../gemini-cli/packages/core/src/agents/codebase-investigator.ts`, `../gemini-cli/packages/core/src/agents/cli-help-agent.ts`, `../gemini-cli/packages/core/src/agents/generalist-agent.ts`
- Qwen: `../qwen-code/packages/core/src/tools/task.ts`
- Kimi: `../kimi-cli/src/kimi_cli/tools/multiagent/task.py`, `../kimi-cli/src/kimi_cli/tools/multiagent/create.py`, `../kimi-cli/src/kimi_cli/soul/agent.py` (LaborMarket, Agent)

#### 160 — Memory / Save Memory (Gemini, Qwen, Kimi)

Persistent memory tool for saving and retrieving cross-session user context, preferences, and facts.

**Vendor coverage**:
- Gemini: `save_memory` — saves global user context (preferences, facts) for use across all workspaces. Param: `fact` (string).
- Qwen: `MemoryTool` — similar concept, with potential `scope` (`global` | `project`) support.
- Kimi: no equivalent in current codebase (but has `Think` tool for scratchpad reasoning).
- Grok: no equivalent in current codebase.

**Why deferred**: Only 2-3 of 4 vendors have this tool. Requires a persistent storage layer (file-based or database) for cross-session memory, plus scoping rules (global vs project-level). The current framework has no memory store abstraction.

**Prerequisites**:
- Core: memory store abstraction (persistent key-value or structured storage).
- Core: per-session or per-workspace memory scoping.
- App: memory store configuration and lifecycle management.
- 040 (agent/provider plugin config) — for per-agent memory availability.

**Source references**:
- Gemini: `../gemini-cli/packages/core/src/tools/memoryTool.ts`
- Qwen: `../qwen-code/packages/core/src/tools/memoryTool.ts`

### Medium priority

#### 170 — Read Media File (Gemini, Kimi)

Tool for reading image and video files and returning them as inline media payloads for multimodal models.

**Vendor coverage**:
- Gemini: handled within `read_file` — the same tool reads text, images, audio, video, and PDF files, returning base64 inline data for non-text types.
- Kimi: `ReadMediaFile` — dedicated tool for reading images and videos. Returns base64 data URLs or provider-specific upload results. Conditional on model capabilities (`image_in`, `video_in`).
- Qwen: no dedicated tool; may handle media within `read_file`.
- Grok: no dedicated tool.

**Why deferred**: Requires extending the tool result pipeline to support non-text content parts (base64 images, video uploads). The current `ToolPlugin` protocol returns text-oriented results. Multimodal payloads need a way to flow through the tool message and into the model's input without being serialized as plain text.

**Prerequisites**:
- Core: tool result pipeline extension for non-text content parts (image/video/PDF inline data).
- Core: model capability detection (whether the current model supports `image_in`, `video_in`).
- Provider plugins: support for multimodal content parts in tool results.
- 090 (Kimi core file tools) — for Kimi's `ReadMediaFile` integration.

**Source references**:
- Gemini: `../gemini-cli/packages/core/src/tools/read-file.ts` (media handling within reader)
- Kimi: `../kimi-cli/src/kimi_cli/tools/file/read_media.py`, `../kimi-cli/src/kimi_cli/tools/file/utils.py` (media type detection)

#### 180 — Plan Mode (Gemini, Kimi)

Tools for entering and exiting plan mode, where the agent can explore and design an approach before executing.

**Vendor coverage**:
- Gemini: `enter_plan_mode` + `exit_plan_mode` — conditional on settings. Agent restricted to read-only tools during planning.
- Kimi: `EnterPlanMode` + `ExitPlanMode` — presents Yes/No dialog to user. Plan file written to hero-name-slug path in `~/.kimi/plans/`. Agent restricted to read-only tools during planning. `ExitPlanMode` presents Approve/Reject/Revise dialog with plan content.
- Qwen: `exit_plan_mode` only (enters plan mode via agent-level config, not a tool).
- Grok: no equivalent.

**Why deferred**: Requires core/app-layer plan state management (plan mode flag, restricted toolset, plan file lifecycle, user approval workflow). The current framework has no plan mode concept.

**Prerequisites**:
- Core: plan mode state management (per-session flag, toolset restriction).
- Core: plan file lifecycle (create, read, write, approve/reject workflow).
- 140 (ask user question) — for the Approve/Reject/Revise dialog in `ExitPlanMode`.
- 090 (Kimi core file tools) — for plan file writing via `WriteFile`.

**Source references**:
- Gemini: `../gemini-cli/packages/core/src/tools/enter-plan-mode.ts`, `../gemini-cli/packages/core/src/tools/exitPlanMode.ts`
- Kimi: `../kimi-cli/src/kimi_cli/tools/plan/enter.py`, `../kimi-cli/src/kimi_cli/tools/plan/__init__.py`, `../kimi-cli/src/kimi_cli/tools/plan/heroes.py` (plan file slug generation)

### Low priority

#### 190 — Think / Scratchpad (Kimi)

Tool for explicit reasoning scratchpad where the model can write out step-by-step thinking.

**Vendor coverage**:
- Kimi: `Think` — param: `thought` (string). Commented out in Kimi's own default config.
- Gemini, Qwen, Grok: no equivalent (reasoning is handled natively by reasoning-capable models).

**Why deferred**: Low-value across vendors. Only Kimi has this tool, and it's disabled by default in Kimi's own config. Reasoning models handle this natively.

**Prerequisites**:
- 090 (Kimi core file tools) — for Kimi package structure.

**Source references**:
- Kimi: `../kimi-cli/src/kimi_cli/tools/think/__init__.py`, `../kimi-cli/src/kimi_cli/tools/think/think.md`

#### 200 — Create Subagent (Kimi)

Tool for dynamically creating new subagent configurations at runtime with custom system prompts.

**Vendor coverage**:
- Kimi: `CreateSubagent` — params: `name`, `system_prompt`. Commented out in Kimi's default config.
- Gemini, Qwen: no equivalent (subagents are pre-configured).
- Grok: no equivalent.

**Why deferred**: Depends on 150 (Task / Subagent Delegation) for the subagent infrastructure. Only useful once subagent isolation and management exist.

**Prerequisites**:
- 150 (Task / Subagent Delegation) — subagent infrastructure must exist first.
- 040 (agent/provider plugin config) — for per-agent subagent specs.

**Source references**:
- Kimi: `../kimi-cli/src/kimi_cli/tools/multiagent/create.py`

#### 210 — Grok Unified Search (Grok)

Grok's unified `search` tool combining text search, file name search, and pattern matching in one interface.

**Vendor coverage**:
- Grok: `search` — params: `query`, `search_type` (`text`/`files`/`both`), `include_pattern`, `exclude_pattern`, `case_sensitive`, `whole_word`, `regex`, `max_results`, `file_types`, `include_hidden`.
- Gemini, Qwen, Kimi: separate `grep_search` + `glob` + `list_directory` tools.

**Why deferred**: Grok's search is structurally different from the other vendors' separate list/grep/glob tools. It deserves its own dedicated subtask with careful attention to the unified interface.

**Prerequisites**:
- 030 (list/grep/glob tools) — for comparison and shared helper reuse.

**Source references**:
- Grok: `../grok-cli/src/grok/tools.ts` (search tool schema, line ~140)

## Cross-cutting decisions to preserve throughout implementation

1. Public tool classes should be vendor-specific.
- Example: `GeminiReadFileTool`, `QwenReadFileTool`, `GrokViewFileTool`, `KimiReadFileTool`
2. Shared internals should live outside the public plugin surface.
3. No alias parameters unless a subtask explicitly decides a backward-compat alias is necessary.
4. Tests should assert exact schema names, parameter names, and important truncation/error strings.
5. Session metadata `plugins` should remain a list of enabled plugin ids/class-style identities, not a place to store plugin package specs.
6. At the agent/provider config level, `plugins` should mean plugin package specs rather than enabled plugin ids.
7. No backward compatibility is required for the old agent-level `plugins` meaning.
8. Add config-level `disabled_plugins` support as a concise alternative to an explicit enabled list.
9. **Response formatting is a first-class requirement for every tool.** Every tool must match the original CLI's LLM-visible output as closely as practical, including truncation banners, line numbering, per-line truncation markers, content/character/byte limits, success/error message wording, and result metadata structure. Shared helpers produce vendor-neutral intermediate dicts; vendor wrappers apply vendor-specific formatting. Formatting should be verified against upstream source during implementation and captured in snapshot tests.
10. **Heavy dependencies should be isolated.** Shared helpers that require non-stdlib dependencies (e.g., `trafilatura`, `aiohttp`) should live in dedicated shared packages (e.g., `web-fetch-shared`) rather than in `tool-compat-shared`.

## Open design questions to resolve during execution

1. Where exactly should the shared internal packages live?
- Options include a dedicated internal package repo under `plugins/` or shared code duplicated minimally per plugin package.
- Resolved for Phase 1: `plugins/tool-compat-shared/` with stdlib-only deps.
- Phase 2 adds: `plugins/web-fetch-shared/` for heavy HTTP/extraction deps.
2. Whether vendor-specific packages should each vendor-copy a tiny compatibility layer or depend on a common installable local package.
- Resolved: depend on a common installable local package.
3. For the fourth subtask, whether provider-level plugin package specs should be allowed only on provider configs, only on agent configs, or on both with a documented merge order.
- Resolved in 040.
4. Exact precedence between session metadata `plugins`, config-level `disabled_plugins`, and implicit all-enabled behavior.
- Resolved in 040.
5. How to handle Gemini API key gating for web search and web fetch tools.
- Proposed: raise `SkipThisTool` in `init()` when no API key is available. Verify feasibility during 110/120 implementation.
6. How to provide LLM provider for web fetch summarization.
- Proposed: configurable via plugin config, defaulting to the agent's current provider. Falls back to raw content if no provider available. Verify during 110 implementation.

## Recommended execution order

1. Reader tools first, including the shared internal read engine and package structure decisions. [done]
2. Edit/write tools second, reusing the same shared package. [done]
3. List/grep/glob third, after the shared filesystem/search helpers are in place. [done]
4. Agent/provider plugin package config support either before tool-package rollout or in parallel, because it enables cleaner configuration of the new vendor bundles. [done]
5. Vendor-friendly system messages after the vendor tool surfaces are stable enough to reference accurately. [done]
6. Simplified runtime system-message configs and minimal dynamic-section support after the extracted vendor instructions exist and the package-loading model is stable. [done]
7. Kimi core file tools to establish the fourth vendor package and extend shared helpers. (090)
8. Shell tools across all vendors, using Kimi's Python-native implementation as the shared helper seed. (100)
9. Web fetch tools with Gemini SDK integration, API key gating, and LLM summarization support. (110)
10. Web search tools with Gemini SDK grounding, citation formatting, and multi-provider support. (120)
11. Todo tools across all vendors, including Grok's unique two-tool create/update pattern. (130)
12. Deferred high-priority tools: ask user question, task/subagent, memory. (140-160)
13. Deferred medium-priority tools: read media file, plan mode. (170-180)
