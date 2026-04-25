# 035 — GPT-5.4 tool-selection, workdir, and developer-message parity

Follow up on the non-sandbox Codex parity gaps found after shell output/limits work. This task focuses on matching Codex CLI behavior for `gpt-5.4` tool exposure, `workdir` handling, and the model-visible Codex prompt/developer-context shape.

**STATUS: COMPLETED**

## Requirements checklist

- [x] Align `gpt-5.4` auto-selection with current Codex CLI so the model gets `shell_command`, not the array `shell` tool.
- [x] Align `workdir` defaulting and relative-path resolution with Codex CLI turn-cwd behavior, excluding sandboxing and approval/escalation work.
- [x] Align the model-visible Codex developer/system message and cwd/AGENTS context more closely to Codex CLI, reusing the existing dynamic system-message architecture already used for other vendors.

Parent Task: `tasks/20260225-codex-tools-parity/000-main.md`
Depends On: `tasks/20260225-codex-tools-parity/030-bash-tool-round-2-output-and-limits.md`

## Scope

This task is intentionally separate from `tasks/20260225-codex-tools-parity/040-bash-tool-round-3-sandboxing.md`.

Do in this task:

- Fix which shell tool is exposed for `gpt-5.4` in our Codex-compatible provider/tool bundle.
- Fix how omitted, empty, and relative `workdir` values are interpreted.
- Fix what the model sees about cwd and AGENTS/developer instructions for the Codex provider path.

Do not do in this task:

- Sandbox policy alignment.
- Approval/escalation field behavior.
- OS-level sandbox implementation.

## Why this follow-up exists

Investigation against `/Users/ferenci84/Dev/Mine/codex` showed that our current Codex-compatible path is close in prompt text, but still diverges from Codex CLI in three important areas that affect tool use reliability:

1. `gpt-5.4` currently selects the wrong shell tool in our stack.
2. `workdir` defaults/resolution do not match Codex CLI behavior.
3. The Codex model-visible cwd/AGENTS context is assembled differently, and may diverge from the actual execution directory.

## Findings to preserve

### 1) `gpt-5.4` is `shell_command` in Codex CLI, but our auto-selection treats it like array-shell

Codex CLI currently marks `gpt-5.4` with `"shell_type": "shell_command"` in `../codex/codex-rs/core/models.json:95-117`.

Relevant references:

- `../codex/codex-rs/core/models.json:95`
- `../codex/codex-rs/core/models.json:117`
- `../codex/codex-rs/core/src/tools/spec.rs:572`

Our current app/provider config uses `openai/gpt-5.4` with `shell_tool_mode: "auto"`:

- `application/python/agent_terminal_app/default_config/config.json:4-21`

But our Codex model detection only emits `codex-variant` for names ending in `-codex`, `-codex-mini`, or `-codex-max`:

- `plugins/codex-tools/src/codex_tools/codex_variant_feature.py:53-66`

And our shell auto-selection logic depends entirely on that tag:

- `plugins/codex-tools/src/codex_tools/shell_tool.py:57-78`
- `plugins/codex-tools/src/codex_tools/shell_command_tool.py:53-74`

Current consequence:

- `openai/gpt-5.4` does not get the `codex-variant` tag.
- `shell` is enabled.
- `shell_command` is not auto-enabled.

That is inverted relative to current Codex CLI behavior for `gpt-5.4`.

### 2) Our visible schema for the chosen shell tool is narrower than Codex CLI

Codex CLI `shell_command` includes at least:

- `command`
- `workdir`
- `timeout_ms`
- `login`
- plus approval/sandbox-related fields added in tool spec construction

References:

- `../codex/codex-rs/core/src/tools/spec.rs:576-635`
- `../codex/codex-rs/protocol/src/models.rs:984-1002`

Our current `shell_command` schema only exposes:

- `command`
- `workdir`
- `timeout_ms`
- `login`

Reference:

- `plugins/codex-tools/src/codex_tools/shell_command_tool.py:76-111`

Do not pull sandboxing/approval implementation into this task, but keep this finding in mind when adjusting descriptions and model-visible guidance so we do not accidentally overstate behavior.

### 3) `workdir` defaulting/resolution differs from Codex CLI

Codex CLI behavior:

- Missing or empty `workdir` falls back to the turn cwd.
- Relative `workdir` is resolved against that turn cwd before deserialization/execution.

References:

- `../codex/codex-rs/core/src/tools/handlers/mod.rs:75-88`
- `../codex/codex-rs/core/src/tools/handlers/shell.rs:63-78`
- `../codex/codex-rs/core/src/tools/handlers/shell.rs:107-128`

Our current behavior:

- Only `None` falls back.
- Fallback target is `config["working_directory"]`.
- Explicit relative paths are passed through to subprocess `cwd` without Codex-style normalization.

References:

- `plugins/codex-tools/src/codex_tools/shell_tool.py:149-170`
- `plugins/codex-tools/src/codex_tools/shell_command_tool.py:162-187`
- `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py:201-260`

This means at least these cases differ from Codex CLI:

- omitted `workdir`
- `workdir: ""`
- relative `workdir` values such as `"subdir"`

### 4) What the model sees about cwd differs from Codex CLI

Codex CLI gives the model explicit contextual user content containing:

- project/AGENTS instructions tied to the session cwd
- a serialized `<environment_context>` with `<cwd>` and `<shell>`

References:

- `../codex/codex-rs/core/src/codex.rs:3141-3258`
- `../codex/codex-rs/core/src/environment_context.rs:156-197`
- `../codex/codex-rs/core/src/instructions/user_instructions.rs:9-29`
- `../codex/codex-rs/core/src/project_doc.rs:3-16`

Our current Codex provider path builds a system message from:

- selected Codex developer message text
- optional TASKS section
- AGENTS section

References:

- `application/python/agent_terminal_app/default_config/config.json:89-107`
- `application/python/agent_terminal_app/default_config/system_messages/helpers/select_codex_developer_message.py:44-56`
- `application/python/agent_terminal_app/default_config/system_messages/helpers/render_agents_context_section.py:11-49`

Important current difference:

- the helper runtime sets `cwd = Path.cwd().resolve()` from the Python process, not from tool/session `working_directory`

Reference:

- `application/python/agent_terminal_app/default_config/system_messages/helpers/runtime.py:5-39`

Because our tool fallback directory comes from config `working_directory`, the model-visible cwd and the actual tool execution cwd can diverge.

## Desired outcome

After this task:

- `openai/gpt-5.4` follows the same shell-tool family that current Codex CLI uses.
- A missing or empty `workdir` means the effective session/turn cwd.
- Relative `workdir` values are resolved in a Codex-like way before execution.
- The Codex system/developer message path exposes cwd and AGENTS context in a way that is consistent with the actual execution context.
- The implementation uses the existing dynamic system-message/template approach already present under `application/python/agent_terminal_app/default_config/system_messages/`, rather than inventing a special one-off path.

## Implementation plan

### A) Fix `gpt-5.4` shell tool selection

1. Decide where the source of truth lives for Codex-family tool selection in our stack.
2. Update the `codex-variant`/selection logic so `gpt-5.4` selects `shell_command` in auto mode.
3. Update README/tests so the docs no longer claim `gpt-5.4` is a plain non-Codex array-shell model.

Notes:

- Keep this surgical: do not expand into sandboxing.
- Be careful not to break older `-codex` models or forced `shell_tool_mode` overrides.

### B) Fix `workdir` semantics

1. Define the effective cwd source in our app/provider path.
2. Normalize omitted, empty, and relative `workdir` values before invoking subprocess execution.
3. Ensure both `shell` and `shell_command` use the same resolution rules.

Notes:

- The target behavior should mirror Codex CLI’s turn-cwd semantics as closely as our architecture allows.
- If session/turn cwd does not currently exist as first-class state in this path, introduce the smallest practical bridging layer.

### C) Fix the model-visible Codex prompt/context path

1. Keep using the existing `system_message` templating/runtime infrastructure.
2. Add a Codex-specific dynamic cwd/context section, analogous to how other vendor prompt templates already assemble dynamic sections under `application/python/agent_terminal_app/default_config/system_messages/`.
3. Ensure AGENTS loading and cwd presentation are based on the same effective working directory used by the shell tools.

Notes:

- Prefer reusing the existing helper/template conventions over embedding a giant static prompt blob.
- The exact representation does not need to be byte-for-byte identical to Codex CLI, but it should remove the current mismatch where the model may see one cwd while tools execute in another.

## Test expectations

- Add regression tests showing `openai/gpt-5.4` auto-selects `shell_command`.
- Add tests for omitted `workdir`, empty-string `workdir`, and relative `workdir` resolution.
- Add tests for system-message rendering/runtime helpers so the displayed cwd/AGENTS context tracks the same effective working directory used by the tools.

## Completion notes placeholder

When this task is implemented, append a `## Completion Notes` section describing:

- the final selection rule used for `gpt-5.4`
- the final source of effective cwd
- how the Codex developer/system message now exposes cwd and AGENTS context

## Completion Notes

- Auto-selection now uses explicit model-family rules in `plugins/codex-tools/src/codex_tools/model_family.py`: `gpt-5`, `gpt-5.1`, `gpt-5.2`, and their `-mini` variants stay on array `shell`; any `*-codex` model and plain/minified `gpt-5.4` and later GPT families use `shell_command`.
- The effective turn cwd now comes from provider/agent config `working_directory`, resolved relative to the Python process cwd when needed, with process cwd as the fallback when `working_directory` is missing or empty. Both shell tools then treat omitted and empty-string `workdir` as that turn cwd, and resolve relative `workdir` values against it before execution.
- The Codex system/developer message path still uses `feature_system_message`, but now renders through the Codex template plus new dynamic helpers: `render_codex_project_instructions.py` loads `AGENTS.md` content from the effective cwd and git root, and `render_codex_environment_context.py` emits a serialized `<environment_context>` block with the same effective cwd and detected shell that the tools use.