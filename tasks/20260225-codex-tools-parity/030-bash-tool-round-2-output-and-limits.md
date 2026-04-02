# 030 — Shell tooling: Round 2 (Codex-like output formatting + token-aware limits)

**STATUS: COMPLETED** via `tasks/20260315-gemini-qwen-grok-tool-packages/104-codex-v2-tool.md`

## Problem

Codex CLI shell outputs follow conventions that matter for GPT‑5 “agentic coding” flows:

- token-aware output truncation (`max_output_tokens` in some schemas)
- consistent headers / metadata (`exit_code`, duration, truncation notes)
- predictable formatting differences between success vs failure

Our current (non-Codex) `shell` tool:

- truncates by **lines and chars**, not tokens
- includes some headers but not Codex CLI’s conventions
- streaming emits mixed parts (`text`, then `summary`) but does not implement Codex-style structured output objects

We want the **Codex-accurate shell tools** (`shell_command`, and later `exec_command`/`write_stdin`) to follow Codex CLI conventions.

## References

- Current `shell` formatting + truncation: `plugins/codex-tools/src/codex_tools/shell_tool.py`
- Codex CLI shared formatting behavior notes:
  - `docs/codex-tools/shared/README.md`
  - `docs/codex-tools/exec_command/README.md`
  - `docs/codex-tools/shell_command/README.md`

## Plan

### A) Add token-aware truncation

1) Add Codex-style limits:
   - `max_output_tokens` (tool arg where applicable)
   - tool-level defaults in config

2) Implement a conservative approximation:
   - Use a fast heuristic (e.g. `len(text) / 4`) as a default token estimate.
   - Optionally, if `tiktoken` is available, use it (feature-detect; do not require).

3) Apply truncation policy that matches Codex CLI as closely as practical.

Note: we should remove any “line limit” concept if it does not exist in Codex CLI for the target tool.

Include explicit truncation notes that mirror Codex CLI (“Total output lines: …” and/or “... truncated …”).

### B) Standardize result shape

Codex CLI shell-like tools tend to have both:

- a **model-facing** concise content string, and
- a **UI-facing** structured payload.

In our framework, we can emulate this by:

We should treat the Codex-accurate tools as new implementations:

- Do not preserve output conventions that diverge from Codex CLI.
- Update `format_tool_result` to follow Codex CLI’s conventions.

Additionally, add these fields to the *result dict* (not necessarily in the formatted text):

- `duration_seconds`
- `timed_out: bool`
- `truncation: { stdout: {reason, ...}, stderr: {reason, ...} }` (optional)

### C) Streaming consistency

1) Ensure the first streamed chunk includes the same header as `to_display_format` (already attempted).
2) Ensure the final summary is emitted even when stdout is truncated heavily.
3) Ensure final `result` dict always appears and includes `success`.

### D) Update tests

- Add tests for the new token limit behavior.
- Add tests for the presence/consistency of new metadata fields.

## Acceptance criteria

- There is a deterministic, documented truncation policy aligned with Codex CLI.
- Users/models can reliably detect truncation.
- A `max_output_tokens` cap works even when output contains long lines.

## Open questions / follow-ups

- Should we switch to Codex CLI’s “structured JSON string output” mode? That may require provider or UI changes; likely defer.
- Should stderr have separate token caps, or share a single budget? Codex CLI effectively budgets per tool output; we can start with shared.
