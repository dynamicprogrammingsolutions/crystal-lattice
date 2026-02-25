# `apply_patch`

Codex supports two distinct `apply_patch` tool shapes.

## JSON tool specs

1. `schema.freeform.json` (`type: "custom"`)
   - Used by GPT-5.* Codex-style models.
   - Input is validated by a grammar (see `format.lark`).

2. `schema.function.json` (`type: "function"`)
   - Used by “JSON tool only” configurations (Codex mentions gpt-oss models as the intended target).
   - Accepts a single JSON argument: `{ "input": "...full patch text..." }`.

## Model/feature variants

- In the stock Codex model catalog, most `gpt-5.*-codex` models set `apply_patch_tool_type = freeform`.
- Some models may omit `apply_patch_tool_type`; Codex can still include `apply_patch` if the `ApplyPatchFreeform` feature is enabled.

## Handler behavior (implementation notes)

High-level flow:

1. Parse/verify the patch input.
2. Assess safety (auto-approve, ask user, or reject).
3. If approved, execute the patch application via a dedicated runtime.
4. Emit patch events and return formatted output.

Output formatting and error behavior:

- Under the hood, Codex often executes patch application by invoking its own executable with `--codex-run-as-apply-patch` and the patch payload.
- Output returned to the model uses the same exec formatting rules as shell tools (see `docs/codex-tools/shared/README.md`).
- Rejections are surfaced as tool errors (e.g. `patch rejected: <reason>`).
- If `apply_patch` is invoked *via* a shell tool (for example `bash -lc "apply_patch <<'EOF' ..."`), Codex intercepts that and records a model warning telling the model to call `apply_patch` directly.
