# 011 — Shell selection parity for Codex GPT-5 models

Align `plugins/codex-tools` shell auto-selection with current upstream Codex CLI model metadata, without bundling in workdir or prompt-context changes.

## Requirements checklist

- [ ] Match current Codex CLI shell-family selection for the GPT-5 models we expose through `plugins/codex-tools`.
- [ ] Stop relying on stale regex assumptions that keep plain `gpt-5.1` and `gpt-5.2` on array-shell.
- [ ] Update tests and docs so they describe the current upstream model behavior.

Parent Task: `tasks/20260225-codex-tools-parity/000-main.md`

## Scope

This task isolates only model-to-shell-tool selection.

Do in this task:

- Fix which shell tool auto-enables for the relevant GPT-5 and Codex model names.
- Update model-family detection and related tests/docs.

Do not do in this task:

- `apply_patch` implementation work
- freeform/custom tool plumbing
- workdir semantics
- developer-message / cwd prompt parity

Those concerns remain in other tasks, especially:

- `tasks/20260225-codex-tools-parity/012-core-freeform-tool-prerequisite.md`
- `tasks/20260225-codex-tools-parity/013-apply-patch-true-parity.md`
- `tasks/20260225-codex-tools-parity/035-gpt-5-4-tool-selection-workdir-and-developer-message.md`

## Findings to preserve

### 1) Our shell model heuristic is stale compared with upstream Codex CLI

Current local logic:

- `plugins/codex-tools/src/codex_tools/model_family.py:8-29`
- `plugins/codex-tools/src/codex_tools/codex_variant_feature.py:45-53`
- `plugins/codex-tools/src/codex_tools/shell_tool.py:58-79`
- `plugins/codex-tools/src/codex_tools/shell_command_tool.py:54-75`

This currently keeps plain `gpt-5`, `gpt-5.1`, and `gpt-5.2` on array-shell and routes only `*-codex` plus `gpt-5.4+` to `shell_command`.

### 2) Upstream Codex CLI now routes more plain GPT-5 models to `shell_command`

Current upstream examples from `../codex/codex-rs/core/models.json`:

- `gpt-5.4` -> `shell_type = "shell_command"` at `:95-117`
- `gpt-5.2` -> `shell_type = "shell_command"` at `:373-395`
- `gpt-5.1` -> `shell_type = "shell_command"` at `:441-459`
- `gpt-5` -> `shell_type = "default"` at `:569-591`
- `gpt-5.3-codex`, `gpt-5.2-codex`, `gpt-5.1-codex`, `gpt-5-codex`, and codex-mini/max variants also use `shell_command`

Implication:

- plain `gpt-5.1` and `gpt-5.2` should no longer be auto-routed to `shell`
- plain `gpt-5` still should not be treated the same way as the newer plain GPT-5 releases

### 3) README text is also stale

Current README still claims `gpt-5`, `gpt-5.1`, and `gpt-5.2` use `shell` in auto mode:

- `plugins/codex-tools/README.md`

That needs to move with the implementation so docs and behavior do not drift further.

## Desired outcome

After this task:

- plain `gpt-5.1` and `gpt-5.2` auto-select `shell_command`
- plain `gpt-5` remains on the non-shell-command path unless/until upstream changes again
- codex-suffixed variants continue to auto-select `shell_command`
- tests lock this behavior down
- README and any user-facing parity notes match the actual logic

## Implementation notes

Prefer a data-driven source of truth over regex growth if practical.

At minimum, cover these model families explicitly:

- `gpt-5`
- `gpt-5.1`
- `gpt-5.2`
- `gpt-5.4`
- `*-codex`
- `*-codex-mini`
- `*-codex-max`

If a local metadata table is introduced, keep it narrow and focused on shell/tool exposure rather than copying all of upstream `models.json` into the repo.

## Test expectations

- Add focused tests for `uses_shell_command_model(...)` or the equivalent replacement.
- Add plugin-level enablement tests proving which tool is visible in `auto` mode for representative model names.
- Update docs/tests that still describe `gpt-5.1` and `gpt-5.2` as array-shell models.