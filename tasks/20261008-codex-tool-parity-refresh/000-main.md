# Codex tool parity refresh

Refresh the `plugins/codex-tools` tool surface toward current upstream Codex CLI
(`../codex`). An audit on 2026-10-08 found the local plugin frozen at upstream
state as of 2026-05-05 while upstream moved on in two independent ways: tool
description wording drifted, and the entire shell tool surface was replaced by
unified exec.

## Requirements checklist

- [x] `view_image` model-facing description and parameter descriptions match
  current upstream Codex CLI wording, removing the "only use if given a full
  filepath by the user" constraint that blocks self-initiated visual feedback
  (owner: `tasks/20261008-codex-tool-parity-refresh/010-sync-view-image-apply-patch-descriptions.md`).
- [x] `view_image` accepts `detail: "high"` as valid input per the current
  upstream enum contract while preserving the existing
  `enable_view_image_detail_original` gating and rejection of other values
  (owner: 010 subtask).
- [x] `apply_patch` freeform description matches current upstream Codex CLI
  wording (owner: 010 subtask).
- [x] Reference snapshots under
  `plugins/codex-tools/reference/codex-cli-tools/` for `view_image` and the
  `apply_patch` freeform schema reflect the current upstream contract
  (owner: 010 subtask).
- [x] An `exec_command` + `write_stdin` unified exec shell surface is
  implemented for codex agents with upstream-parity schemas, interactive
  sessions, and explicitly decided rollout (plan approved 2026-10-10:
  `auto` flips for shell-command family models; approval params omitted;
  cross-request sessions)
  (owner: `tasks/20261008-codex-tool-parity-refresh/020-unified-exec-shell-tools.md`).
- [ ] Windows support for the unified exec tools is planned and tracked
  (native shell resolution, ConPTY, Windows schema variant)
  (owner: `tasks/20261008-codex-tool-parity-refresh/030-windows-unified-exec-support.md`).
- [ ] An opt-in settings plugin (separate project, not in the default
  config) exposes `shell_tool_mode` as a per-session setting, enabling the
  legacy `shell_command` for individual sessions without a restart; with
  model-based selection dropped (`auto` = unified exec for every model)
  (owner: `tasks/20261008-codex-tool-parity-refresh/040-shell-command-session-selector.md`).

## Subtasks

- [x] [010-sync-view-image-apply-patch-descriptions.md](tasks/20261008-codex-tool-parity-refresh/010-sync-view-image-apply-patch-descriptions.md) — completed 2026-10-08; unit tests, full plugin suite, and both hosted-API view_image runs passed.
- [x] [020-unified-exec-shell-tools.md](tasks/20261008-codex-tool-parity-refresh/020-unified-exec-shell-tools.md) — completed 2026-10-10; unified exec implemented and verified (full plugin suite, key-gated selection suites, hosted-API round-trip on gpt-6-luna); see its Completion Notes.
- [ ] [030-windows-unified-exec-support.md](tasks/20261008-codex-tool-parity-refresh/030-windows-unified-exec-support.md) — Windows port of the unified exec tools (ConPTY, Windows shell resolution, schema variant); planning only, `Status: Draft`; depends on 020.
- [ ] [040-shell-command-session-selector.md](tasks/20261008-codex-tool-parity-refresh/040-shell-command-session-selector.md) — opt-in settings plugin exposing `shell_tool_mode` as a per-session setting plus dropping model-based selection; plan approved 2026-10-10 (drop model-based `auto`); execution pending; depends on 020.

## Supporting details

Audit findings (verified against `../codex` working tree and git history on
2026-10-08):

- `view_image`: local description frozen at the pre-2026-05-26 upstream text
  ("only use if given a full filepath by the user..."). Upstream `675cb1af`
  (2026-05-26, #23949) replaced it with a constraint-free description. Upstream
  also changed the `detail` param to enum `["high", "original"]` with a new
  description, added an optional `environment_id` param (multi-environment
  feature, no local counterpart), and a `unified_image_budget` mode that drops
  `detail`. Source: `../codex/codex-rs/core/src/tools/handlers/view_image_spec.rs`.
- `apply_patch` freeform: upstream `f7376056` (2026-07-16, #33680) reworded
  "Use the `apply_patch` tool to edit files." to "The `apply_patch` tool can be
  used to edit files." Cosmetic only. Upstream deleted function-style
  `apply_patch` on 2026-05-08 (`e783341`, #21651); the local long
  `_FUNCTION_DESCRIPTION` is a platform fallback for chat-completions providers
  and is intentionally retained.
- Shell surface: upstream removed the array-based `shell` tool on 2026-05-13
  (`83decfa3`, #22246), removed `shell_command` on 2026-08-20 (`8a40095e`,
  #39757, "Standardize shell execution on unified exec"), and now ships
  `exec_command` + `write_stdin` (PTY/session semantics, `cmd` string,
  `yield_time_ms`, `max_output_tokens`, sandbox/approval params). Local
  `shell`/`shell_command` descriptions match upstream's final pre-removal
  wording exactly; the deviation is the tool surface itself, not the text.
  Source: `../codex/codex-rs/core/src/tools/handlers/shell_spec.rs`.
- Local `shell_tool_mode: "auto"` selects `shell_command` for shell-command
  family models (including `gpt-6.1-sol`) via
  `plugins/codex-tools/src/codex_tools/model_family.py`, so the 020 subtask
  affects exactly the models using codex agents today.
- The `gpt-6.1-sol` developer message
  (`application/python/agent_terminal_app/default_config/codex/gpt-6.1-sol/instructions_default.20260929.md`)
  already references the newer tool naming (`functions.exec`,
  `functions.request_user_input_async`), reinforcing the unified exec direction
  of 020.
- No system message in `application/python/agent_terminal_app/default_config/`
  mentions `view_image`; the tool description is the only model-facing guidance
  for it.

## Open questions

- 030 (design decisions, unresolved): ConPTY runtime approach (`pywinpty`
  vs ctypes), default Windows shell, Windows verification environment
  availability, and `tty` fallback if ConPTY is unavailable. See the 030
  subtask. The 020 design decisions were resolved with the user on
  2026-10-10 (rollout option B; approval params omitted; cross-request
  sessions via the runtime store).
