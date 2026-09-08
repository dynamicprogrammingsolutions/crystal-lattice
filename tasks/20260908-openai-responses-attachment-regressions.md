# OpenAI Responses Attachment Regressions

Two pre-existing attachment-area failures in the openai_responses plugin
test suites, verified failing identically on develop and in a fresh
worktree `.venv` on 2026-09-08 (so they are real regressions, not
environment noise). Recorded here for dedicated investigation; the
failing tests must stay realistic — fix the product code or update the
test only when the current behavior is confirmed intentional.

## Requirements checklist

- [ ] Adding a message with a PDF attachment while
      `attachment_upload_mode` is not `upload_before_send` either
      returns 400 from the add-message endpoint (the test's current
      expectation) or the expectation is updated to match behavior that
      was deliberately changed — with the deciding commit identified.
- [ ] `_openai_responses_uploaded_attachments` bookkeeping stays
      coherent through native history rebuild, slice, and fork: content
      indices and file ids map to the parts that are actually present
      in the rebuilt native messages.
- [ ] The three native-history regression tests pass:
      `test_uploaded_attachment_history_rebuilds_original_multipart_content`,
      `test_uploaded_attachment_history_slice_and_fork_keep_coherent_native_segments`,
      and `test_session_asset_attachment_history_rebuilds_original_asset_ref`.
- [ ] Fixes are verified without weakening the failing tests.

## Unresolved requirement questions and decisions

- **Q1 (execution approval): blocking** — this task is Draft; no
  execution is authorized yet.
- **Q2 (add-message 400):** decide which side is correct — the endpoint
  should reject PDFs without upload mode (test expectation), or the
  validation was deliberately relaxed (test stale). Needs git-history
  investigation of the add-message PDF validation path before changing
  anything.

## Supporting facts

### Failure A — PDF without upload mode accepted (200, expected 400)

- Test:
  `plugins/openai_responses/tests/test_agent_application_openai_responses_attachment_endpoints.py::test_add_message_returns_400_for_pdf_without_upload_mode`
  (moved there from
  `application/python/tests/test_openai_responses_attachment_endpoints.py`
  on 2026-09-08; the failure predates the move and reproduces at the old
  location on develop).
- Failure: `assert 200 == 400` — the add-message endpoint accepts the
  PDF instead of rejecting it.
- Investigation starting points: the server's multipart validation
  around `application/python/agent_terminal_app/server.py:1124-1146`
  and the upload-mode policy in
  `plugins/openai_responses/src/openai_responses_plugins/openai_responses_attachment_policy.py`
  (`ATTACHMENT_UPLOAD_MODE_KEY`, `resolve_attachment_upload_mode`).

### Failure B — stale uploaded-attachment metadata after history operations

- Tests: three tests in
  `plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py`
  (verified failing on develop, 2026-09-08):
  - `test_uploaded_attachment_history_rebuilds_original_multipart_content`
    (assertion at line ~423): after a rebuild, the metadata carries one
    entry `{content_index: 2, uploaded_part: {type: input_file, file_id: file_1}}`
    where two entries are expected
    (`{content_index: 1, input_image, file_1}` and
    `{content_index: 2, input_file, file_2}`).
  - `test_uploaded_attachment_history_slice_and_fork_keep_coherent_native_segments`:
    after `slice_session(remove_indices=[0, 1])`, the metadata keeps
    `file_1` at the surviving index where `file_2` is expected.
  - `test_session_asset_attachment_history_rebuilds_original_asset_ref`:
    same stale-mapping pattern after rebuild.
- Common mechanism: `_openai_responses_uploaded_attachments` entries
  are not re-indexed or re-mapped when native messages are rebuilt,
  sliced, or forked.
- Bookkeeping code:
  `plugins/openai_responses/src/openai_responses_plugins/openai_responses_attachment_policy.py`
  plus the extension code that writes the metadata.

### Environment evidence (2026-09-08)

- Both failures reproduce identically in the develop checkout venv
  (populated environment) and in a fresh `.venv` provisioned only with
  `install:venv` + `install:all` + `install:plugins` — not
  environment-related, not introduced by the test-suite moves of
  2026-09-08.

## Execution plan

### Workstream A — add-message PDF validation decision

1. Trace the git history of the add-message PDF validation (when a 400
   for PDFs without upload mode existed, and whether its removal was
   deliberate).
2. Resolve Q2: restore the validation or update the test to the
   confirmed intended behavior, with the deciding commit referenced.
3. Add/keep a regression test that fails before the fix.

### Workstream B — uploaded-attachment history bookkeeping

1. Trace where `_openai_responses_uploaded_attachments` is written and
   updated during native history rebuild, slice, and fork in the
   attachment policy and extensions.
2. Fix the re-indexing so the metadata maps to the parts actually
   present after each history operation.
3. The three regression tests are the acceptance coverage; do not
   weaken them.

### Verification

- `pytest plugins/openai_responses/tests -q` (default run)
- `pytest plugins/openai_responses/tests -m "integration and not api and not slow_integration and not manual_integration" -q`
- The specific failing test files directly.