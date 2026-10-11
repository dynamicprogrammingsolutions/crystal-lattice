# Sync view_image and apply_patch descriptions to current upstream Codex CLI

Update the model-facing `view_image` tool description, parameter descriptions,
and `detail` contract, plus the `apply_patch` freeform description, to match
the current upstream Codex CLI wording. This removes the "only use if given a
full filepath by the user" constraint that prevents codex agents from using
`view_image` for self-initiated visual feedback (for example inspecting their
own screenshots).

Parent Task: `tasks/20261008-codex-tool-parity-refresh/000-main.md`

## Requirements checklist

- [x] `view_image` tool description is exactly the current upstream Codex CLI
  text: "View a local image file from the filesystem when visual inspection is
  needed. Use this for images already available on disk."
- [x] `view_image` `path` parameter description matches upstream exactly
  ("Local filesystem path to an image file." including the trailing period).
- [x] `view_image` `detail` parameter, when exposed, is a string enum of
  `["high", "original"]` with the upstream description "Image detail level.
  Defaults to `high`; use `original` to preserve exact resolution."
- [x] `execute_tool` accepts `detail: "high"` as valid input behaving like the
  default resized path, keeps accepting `"original"` and omitted values, and
  rejects any other value with an error naming both supported values.
- [x] The existing `enable_view_image_detail_original` gating is preserved:
  when false, `detail` is absent from the schema and `"original"` is rejected.
- [x] `apply_patch` freeform description is exactly the current upstream text:
  "The `apply_patch` tool can be used to edit files. This is a FREEFORM tool,
  so do not wrap the patch in JSON."
- [x] Reference snapshots `reference/codex-cli-tools/view_image/schema.json`
  and `reference/codex-cli-tools/apply_patch/schema.freeform.json` reflect the
  current upstream contract, with the variant notes updated.
- [x] `plugins/codex-tools/README.md` documents the new `detail` contract.
- [x] Unit tests pin the new description texts, the `detail` enum schema, and
  acceptance/rejection of `detail` values; existing tests asserting the old
  wording or old error message are updated.

## Supporting details

- Upstream texts (source of truth: `../codex/codex-rs/core/src/tools/handlers/`):
  - `view_image_spec.rs:44` — description, reworded in `675cb1af` (2026-05-26,
    #23949).
  - `view_image_spec.rs:19` — `path` description with trailing period.
  - `view_image_spec.rs:24-29` — `detail` as `string_enum(["high", "original"])`
    with the exact description text, exposed when
    `can_request_original_image_detail && !unified_image_budget`.
  - `apply_patch_spec.rs:20` — freeform description, reworded in `f7376056`
    (2026-07-16, #33680).
- Local code: `VIEW_IMAGE_DESCRIPTION`, `PATH_DESCRIPTION`,
  `DETAIL_DESCRIPTION`, `_parameters_schema`, and `execute_tool` validation in
  `plugins/codex-tools/src/codex_tools/view_image_tool.py`;
  `_FREEFORM_DESCRIPTION` in `plugins/codex-tools/src/codex_tools/apply_patch_runtime.py`.
- The local `detail` semantics already default results to `"high"`
  (`DEFAULT_IMAGE_DETAIL = "high"`), so accepting `"high"` as explicit input is
  consistent with existing result behavior and upstream.
- Out of scope (documented decisions):
  - Upstream's optional `environment_id` parameter and `unified_image_budget`
    mode for `view_image` are not adopted; the platform has no multi-environment
    tool concept.
  - The long `_FUNCTION_DESCRIPTION` apply_patch fallback for chat-completions
    providers is retained unchanged; upstream deleted function-style
    apply_patch, so there is no current upstream text to sync to.
- Prior task `tasks/20260701-correct-view-image-output-schema.md` pinned the
  output behavior (no `output_schema`, image-only success output, plain-text
  failures); this task must not change that.
- The `view_image` reference README handler notes remain accurate; only the
  schema snapshot and a variant note need updating.

## Execution plan

Status: Approved

Approved by the user on 2026-10-08 following the investigation in this
conversation ("the wording change of view image and apply patch ... You can
then do the first task according to the plan above").

Approach: mirror the exact upstream strings into the plugin source, adopt the
`detail` enum contract (schema plus runtime acceptance of `"high"`), refresh
the two reference snapshots to the current upstream default variant, and pin
everything with unit tests at the plugin's public `get_tool_schemas` /
`execute_tool` boundary — the same boundary the model-facing schema is served
through.

Ordered steps:

1. Update `plugins/codex-tools/src/codex_tools/view_image_tool.py`:
   description constants, `_parameters_schema` enum, and `execute_tool`
   validation/error message for `detail`.
2. Update `_FREEFORM_DESCRIPTION` in
   `plugins/codex-tools/src/codex_tools/apply_patch_runtime.py`.
3. Refresh `plugins/codex-tools/reference/codex-cli-tools/view_image/schema.json`
   and `apply_patch/schema.freeform.json`; update the `view_image` reference
   README variant note (environment_id / unified_image_budget gated upstream).
4. Update `plugins/codex-tools/README.md` View Image section.
5. Update/extend `plugins/codex-tools/tests/test_view_image_tool.py` and
   `test_apply_patch_tool.py`.
6. Run `pytest plugins/codex-tools/tests -m 'not integration' -q`, then
   `ruff check` and `black` on the changed files.

### Implementation decisions and open questions

- Adopt the enum (not just the description): accepting `"high"` is a strict
  superset of current behavior (previously an error) and matches upstream;
  decided during planning and covered by the requirements above.
- Reference `view_image` snapshot documents the default upstream variant
  (`can_request_original_image_detail=true`, `unified_image_budget=false`,
  `include_environment_id=false`); gated variants are described in prose in the
  tool's reference README, mirroring how the shell snapshot documents variants.
- No open requirement questions remain for this subtask.

### Documentation

- `plugins/codex-tools/README.md` — View Image parameter line.
- `plugins/codex-tools/reference/codex-cli-tools/view_image/schema.json`,
  `.../apply_patch/schema.freeform.json`, and the `view_image` reference README
  variant note.

### Task checklist

- [x] Update `view_image_tool.py` constants, schema, and validation.
- [x] Update `apply_patch_runtime.py` freeform description.
- [x] Refresh reference snapshots and variant note.
- [x] Update plugin README.
- [x] Update unit tests.
- [x] Run plugin unit tests and lint/format checks.

### Requirement verification

- Description/param text and enum parity, gating, and `apply_patch` freeform
  text: focused unit tests in `plugins/codex-tools/tests/test_view_image_tool.py`
  and `test_apply_patch_tool.py` asserting the exact strings and schema shapes
  returned by `get_tool_schemas` (the public plugin boundary that produces the
  model-facing schema).
- `detail` runtime acceptance (`high`, `original`, omitted) and rejection with
  the new error: unit tests calling `execute_tool` through `ToolWrapper`.
- Existing behavior preserved: full default plugin test run
  `pytest plugins/codex-tools/tests -m 'not integration' -q` plus ruff/black as
  supporting checks.

### Additional implementation verification

- Grep the repo for the removed old wording to confirm no stale copies remain
  outside the intentionally historical material.

## Implementation Notes

- The served `apply_patch` freeform description is the upstream text plus a
  pre-existing platform suffix ("Files are resolved relative to <workdir>.
  Paths are sandboxed to allowed_paths.") appended by the patch runtime. The
  upstream wording requirement is satisfied as the exact prefix; the suffix is
  unchanged platform behavior and the test asserts both.
- The reference `apply_patch/format.lark` was a stale older-era reconstruction,
  different in rule naming from both the current upstream grammar and the
  grammar embedded in `apply_patch_runtime.py` (`APPLY_PATCH_GRAMMAR`, already
  identical to current upstream). Refreshed `format.lark` to the current
  upstream grammar with a provenance header. No product code change was
  needed for the grammar.
- The reference `apply_patch/README.md` now marks `schema.function.json` as
  historical (upstream removed function-style apply_patch 2026-05-08); the
  snapshot itself is retained because the platform still serves the
  function-style fallback.

## Completion Notes

- Outcome: `view_image` and `apply_patch` model-facing wording now match
  current upstream Codex CLI. The `view_image` description no longer carries
  the user-supplied-path constraint, restoring self-initiated visual feedback
  (e.g. inspecting agent-generated screenshots) for codex agents. `detail` is
  an upstream-parity `high | original` enum and `"high"` is accepted input.
- Changed files: `plugins/codex-tools/src/codex_tools/view_image_tool.py`
  (descriptions, `DETAIL_VALUES`, enum schema, validation and error message),
  `plugins/codex-tools/src/codex_tools/apply_patch_runtime.py`
  (`_FREEFORM_DESCRIPTION`), `plugins/codex-tools/README.md`,
  `reference/codex-cli-tools/view_image/{schema.json,README.md}`,
  `reference/codex-cli-tools/apply_patch/{schema.freeform.json,format.lark,README.md}`,
  `plugins/codex-tools/tests/{test_view_image_tool.py,test_apply_patch_tool.py}`.
- Requirement evidence:
  - Description/param/enum parity and gating: unit tests
    `test_view_image_descriptions_match_current_codex_cli`,
    `test_view_image_schema_detail_can_be_disabled`,
    `test_view_image_rejects_original_when_disabled`, and the strengthened
    `test_apply_patch_exposes_custom_schema_for_responses_targets` assert the
    exact upstream texts and schema at the public `get_tool_schemas` boundary.
  - `detail` runtime acceptance/rejection:
    `test_view_image_accepts_high_detail`, `test_view_image_accepts_original_by_default`,
    `test_view_image_rejects_invalid_detail` (updated error text).
  - End-to-end through the default codex agent config against hosted OpenAI
    and OpenRouter APIs:
    `pytest application/python/tests/test_terminal_default_config_codex_view_image_real_api.py`
    with `-m 'integration and api and openai'` and `... and openrouter'` —
    both passed, proving the updated schema is accepted by the APIs and
    `view_image` still reads image content.
- Verification performed: `pytest plugins/codex-tools/tests -m 'not
  integration' -q` → 182 passed, 22 skipped (pre-existing
  `OPENROUTER_API_KEY not set` gates on shell-tool tests unrelated to this
  change), 19 integration deselected. `ruff check` passed on all changed
  files. `black` is not a repo target for `plugins/` (documented repo lint
  scope is `core/python` paths); the changed files were already
  non-conforming under a newer local black at HEAD, so no reformatting was
  done.
- Findings/deviations: none material. One extra snapshot refresh
  (`format.lark`) beyond the planned file list, covered by the reference
  snapshot requirement.
- Unresolved/deferred: the pinned gpt-5.x developer messages under
  `application/python/agent_terminal_app/default_config/codex/gpt-5.x/` still
  quote the old inline apply_patch wording; they are dated per-model snapshots
  and do not conflict with the new tool text (same instruction, older
  phrasing). Left unchanged deliberately.
