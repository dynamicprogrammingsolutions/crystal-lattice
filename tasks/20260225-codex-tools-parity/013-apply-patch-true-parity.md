# 013 — True `apply_patch` parity with Codex CLI

Implement real upstream Codex CLI parity for `apply_patch`, including model-aware exposure and the correct freeform-vs-function behavior, after the core prerequisite exists.

## Requirements checklist

- [ ] Match current upstream Codex CLI `apply_patch` exposure behavior by model as closely as this platform allows.
- [ ] Use the upstream JSON fallback shape only where appropriate, with `input` as the sole structured field.
- [ ] Update tests and docs to cover the final parity behavior rather than a standalone schema-only rename.

Parent Task: `tasks/20260225-codex-tools-parity/000-main.md`
Depends On: `tasks/20260225-codex-tools-parity/011-shell-selection-parity.md`, `tasks/20260225-codex-tools-parity/012-core-freeform-tool-prerequisite.md`

## Why this task exists

The original `010` scope was too small. Upstream Codex CLI does not primarily treat `apply_patch` as a function tool with an `input` parameter for GPT-5 models; it primarily uses a freeform/custom tool and only keeps the JSON/function form as a fallback.

So the real parity task must include:

- the freeform/custom tool path
- the JSON/function fallback shape with `input`
- model-aware exposure rules

## Findings to preserve

### 1) Upstream freeform is the primary GPT-5 path

Upstream factories:

- freeform/custom tool: `../codex/codex-rs/core/src/tools/handlers/apply_patch.rs:288-299`
- JSON/function fallback: `../codex/codex-rs/core/src/tools/handlers/apply_patch.rs:302-389`

The upstream comment explicitly says the JSON/function tool should only be used with `gpt-oss` models.

### 2) Upstream tool registration is model-config driven

Codex CLI registers `apply_patch` only when `config.apply_patch_tool_type` is present, and then chooses freeform vs function from that value:

- `../codex/codex-rs/core/src/tools/spec.rs:1914-1923`

Important examples from current upstream model metadata:

- `gpt-5.4` -> `apply_patch_tool_type = "freeform"` at `../codex/codex-rs/core/models.json:81-117`
- `gpt-5.2` -> `apply_patch_tool_type = "freeform"` at `../codex/codex-rs/core/models.json:359-395`
- `gpt-5.1` -> `apply_patch_tool_type = "freeform"` at `../codex/codex-rs/core/models.json:427-459`
- `gpt-5` -> `apply_patch_tool_type = null` at `../codex/codex-rs/core/models.json:555-591`

### 3) Our current implementation is still a `patch_text` function tool

Current local implementation:

- `plugins/codex-tools/src/codex_tools/apply_patch_tool.py:501-694`
- `plugins/codex-tools/tests/test_apply_patch_tool.py`

Current behavior differences:

- structured arg name is `patch_text`, not `input`
- there is no freeform/custom tool path
- the tool is not yet aligned with upstream model gating

## Desired outcome

After this task:

- models that upstream marks as freeform `apply_patch` expose a freeform/custom `apply_patch` tool here too
- any function fallback path uses `input` as the sole structured field, with no alias parameters
- plain `gpt-5` does not expose `apply_patch` if upstream still leaves it unset
- execution, previews, results, and docs all reflect the final parity behavior

## Implementation notes

This task should absorb the schema cleanup that was originally imagined for `010`.

Specifically:

- do not create a separate intermediate task just to rename `patch_text` -> `input`
- perform that rename only as part of the final parity implementation
- if both freeform and function fallback are supported, keep their descriptions and gating aligned with upstream intent

Likely implementation areas:

- `plugins/codex-tools/src/codex_tools/apply_patch_tool.py`
- `plugins/codex-tools/src/codex_tools/model_family.py`
- `plugins/codex-tools/tests/test_apply_patch_tool.py`
- `plugins/codex-tools/README.md`
- any provider/tool-interop plumbing completed in `012`

## Test expectations

- Add tests for freeform/custom `apply_patch` on the models that should expose it.
- Add tests for the function fallback shape using `input` only.
- Add tests showing plain `gpt-5` does not expose `apply_patch` when upstream metadata says `null`.
- Update docs so they describe actual parity behavior rather than the old `patch_text` schema.