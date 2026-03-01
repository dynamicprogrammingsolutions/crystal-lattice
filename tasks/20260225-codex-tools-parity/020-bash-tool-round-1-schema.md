# 020 — Shell tooling: Round 1 (Codex-accurate schemas, keep functionality)

## Problem

The current `shell` tool works, but we want to move to **Codex-accurate tool names and schemas**.

Examples:

- Codex CLI’s default “command string” tool is typically `shell_command` (especially in cookbook examples).
- On macOS/Linux, Codex CLI often exposes `exec_command` + `write_stdin` instead of `shell_command`.
- Schemas include permission/sandbox-related fields (sometimes feature-gated).

We want to **keep existing runtime functionality** in this round, but:

- rename tools to match Codex CLI
- update schemas to match Codex CLI

We will **not** add alias argument names.

## References

- Current tool implementation: `plugins/codex-tools/src/codex_tools/shell_tool.py`
- Codex CLI reconstructed schemas:
  - `docs/codex-tools/shell/schema.*.json`
  - `docs/codex-tools/shell_command/schema.*.json`
  - `docs/codex-tools/exec_command/schema.*.json`

## Plan

### A) Tool naming: implement Codex CLI tools explicitly

1) Implement a **new** tool plugin named `shell_command` with the Codex CLI schema.
2) Do not expose `shell` unless we implement Codex CLI’s `shell` argv-array schema.

Rationale: the goal is parity, and `shell_command` is what the cookbook describes. Keeping a `shell` tool with a non-Codex schema increases drift.

Optional benchmarking:

- Keep the existing tool bundle as a **separate plugin bundle** so users can switch between implementations.
- Do not attempt to ship both `shell_command` implementations simultaneously under different tool names.

### B) Schema: match Codex CLI (even if we ignore some fields in v1)

1) `shell_command` schema should match `docs/codex-tools/shell_command/schema.*.json`.
   - Accept Codex CLI field names as-is.
   - If a field cannot be honored yet (e.g. `additional_permissions`), we can initially reject with a clear error rather than accepting aliases.

2) Runtime can still execute via the existing `bash -lc` pipeline for Round 1.

### C) Preview text / display

No behavior change required, but ensure that tool call previews remain compact and deterministic.

### D) Tests

1) Add tests validating the `shell_command` schema matches the Codex CLI schema.
2) Add tests validating that unsupported-but-present Codex fields fail loudly (until Round 3 implements them).

## Acceptance criteria

- `shell_command` exists and is callable with the Codex CLI schema.
- No alias argument names are introduced.
- Old vs new comparison happens by switching plugin bundles, not by adding multiple tool names.

## Open questions / follow-ups

- Should we also implement Codex CLI’s `shell` tool (argv-array) or omit it entirely in favor of `shell_command` + `exec_command`?
- Whether our providers enforce tool-schema strictness; this impacts whether we should model “optional” params using `null` unions.
