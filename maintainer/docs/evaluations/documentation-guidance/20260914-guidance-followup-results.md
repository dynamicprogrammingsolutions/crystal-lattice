# September 14 documentation-guidance follow-up results

This report compares the guidance immediately before the root AGENTS and
substantial-specification approval edits with the candidate after those edits.
It also calibrates Test 18 against the actual model sessions rather than pytest
status alone.

## Exact inputs

- Model: `glm-5.3-flash:cloud`
- Agent profile: `glm-ollama`
- Default reasoning effort: `high`
- Normal branch budget: 30 completed tool calls
- Test 18 diagnostic budget: 45 calls
- Immediate pre-change revision: `cdeb50a7df92820e487c466b030ea8f5f6dcb993`
- Immediate pre-change guidance SHA-256:
  `18251b851c56e4ecc0988c8f88eaf2cc5a5aaf35c547a570e65a9c48a1a1237b`
- Candidate guidance SHA-256:
  `d428bd65eb69bf4406ef7637540d28283bcc14078b3f25d633024275b50fd086`

Tests 10, 11, and the Test-22 requirement-restraint sentinel were intentionally
not rerun. Their guidance area is being changed in the concurrent
documentation-rewrite worktree and will be evaluated after reconciliation.

Review used the concise `render_messages_markdown()` export from
`test/task_guidance/prepare_review_bundle.py`. It retains visible user,
assistant, and commentary messages plus intervening tool-call counts while
omitting full tool-result bodies. Migration of that renderer into the
maintainer evaluation package remains owned by subtask 068.

## Guidance changes under test

Root `AGENTS.md` now:

- has one 289-word documentation policy/routing section;
- uses one documentation-hub map entry;
- requires both routed guides to be read in full for structural work;
- removes the duplicate site-command catalog and temporary migration list;
- keeps documentation policy out of the testing section;
- selects tests by requirement and important boundary rather than “unit first.”

The project-independent guide adds one paragraph requiring a proposal and
approval before a substantial new specification unless an active approved task
already authorizes it.

## Deterministic calibration

- Replaced a 2,000-word single-page cap with the approved combined review
  budget. The index, two guides, and root section total approximately 3,421
  words, within the 3,000–3,600 target.
- Added the pinned `followup-baseline` guidance source.
- Normalized whitespace in the approval-rule source assertion.
- Test 18 now accepts any consistent lowercase-to-uppercase example, rejects
  known unsupported fixture claims, flags observed sibling-worktree evidence
  and false Node-availability claims, and enforces its documented mutation
  allowlist.
- Test 27 now distinguishes a target API presented as available from a
  translated current limitation and reports internal specification links
  separately.

Focused deterministic documentation-suite tests: **31 passed**.

## Model result summary

| Test | Immediate pre-change | Candidate | Behavioral interpretation |
|---|---:|---:|---|
| 27, two-page routing | 1/2 aggregate pass; routing 2/2 | 2/2 pass; routing 2/2 | Both versions routed correctly. One baseline leaked an internal specification link into user docs. The root wording is clearer, but this is robustness rather than a demonstrated routing fix. |
| 6, substantial-specification approval | 0/1 | 0/2 | Genuine failure. Every run created files immediately and treated “Please create” as sufficient authorization. |
| 9, task-authorized specification | 1/1 | 1/1 | Existing task authorization was used without duplicate approval. |
| 26, explicit optional layout | 0/1 | 1/1 | Baseline omitted the `decisions.md` index link; candidate honored and indexed the approved layout. |
| 18, shared plugin authoring | 0/2 after calibration | 1/4 normal; 1/1 diagnostic | High variance. Budget was not causal; the diagnostic pass used only 11 calls. Several mechanical passes/failures disagreed with factual quality before assertion calibration. |

The older `develop` Test 18 sample that originally passed now fails the
calibrated acceptance because it used an unrelated sibling worktree and made
claims unsupported by the pinned fixture.

## Behavioral review

### Test 27

All four runs read both guidance pages completely before the first mutation and
did not read maintainer specifications.

The first baseline run correctly described replay as unavailable but linked
user documentation directly to
`development/specifications/event-lifecycle/index.md`. The old combined
assertion reported both the negative API mention and the internal link as one
failure. The calibrated findings now allow a translated current limitation and
identify the internal link as the actual defect.

The second baseline and both candidate runs kept the replay limitation in user
language without the internal link. Therefore Test 27 does not establish that
“read both files in full” caused a behavioral improvement. It does show that
the candidate route is followed consistently in these samples.

Recommended test change: keep routing order as the primary Test 27 contract and
move user/developer audience quality into a separate focused finding or
scenario so an output defect does not obscure successful routing.

### Test 6

The baseline and both candidate sessions:

- selected `batch-sdk` as owner;
- created an index/specification and requirements immediately;
- did not request approval;
- did not present the proposed file set before mutation.

The candidate considered overlap with transport and persistence, but ignored
the new approval paragraph. This is not an assertion false negative.

Recommended guidance edit:

> A direct request to create a substantial specification does not by itself
> approve its proposed scope, ownership, overlap, or file set. Present those
> details and wait for explicit approval before creating files, unless an
> active approved task already authorizes them.

The existing paragraph can be shortened while adding this distinction; do not
create a second approval section.

The Test 6 “concrete proposal” matcher still depends on literal `owner` and
`scope`. When a future model actually proposes equivalent package/location and
behavior-boundary language, the matcher should accept those concepts rather
than exact vocabulary.

### Tests 9 and 26

Both Test 9 runs used their approved task without asking twice. The candidate
Test 26 also honored one `decisions.md` and linked it correctly.

Passing status does not prove the generated specifications are good. Runs
invented detailed queue fields, ordering modes, conflict policy, migration
semantics, API options, and four to six material decisions from one-sentence
dependency contracts. One baseline requirements table also promoted
“the specification documents…” into a completion requirement, and one code
example used invalid Python `true`.

Recommended test change after the concurrent requirement work is reconciled:
add a narrow semantic assessment for unapproved material design decisions,
requirement inflation, and executable example validity. Do not add more keyword
counts to the layout test.

### Test 18

The original scenario combines:

- factual runtime investigation;
- a package README rewrite;
- a substantial shared authoring page;
- two navigation updates;
- command verification.

Its fixture removes the runtime sources that `plugins/docs/AGENTS.md` tells the
agent to consult. The active array shell also permits commands to read mutable
sibling worktrees.

Observed outcomes included:

- an old-guidance mechanical pass based on 22 references to an unrelated
  worktree;
- incomplete 30-call runs after external investigation or patch retries;
- a valid `hi` to `HI` example rejected because the assertion required
  `hello` and `HELLO`;
- passes containing unsupported loader facts;
- a pass falsely claiming Node was unavailable;
- mutation of `plugin-packaging-and-loading.md`, which the old assertion
  silently allowed;
- two current candidate passes that stayed inside the fixture and removed
  unsupported claims.

The 45-call diagnostic completed after 11 calls. Extra budget did not cause the
pass.

Conclusion: Test 18 cannot currently support a guidance-regression claim.
Subtask 019 should address shell/evaluation confinement, fixture completeness,
and scenario decomposition before another baseline/candidate comparison.

## Recommended next edits

1. Strengthen the substantial-specification paragraph with the direct-request
   distinction above, then rerun Tests 6 and 9.
2. Keep the root AGENTS wording unchanged pending human review and integrated
   rerun; current evidence does not justify more routing text.
3. Implement subtask 019 before using Test 18 as requirement evidence.
4. Separate Test 27 routing from audience-output quality.
5. Add semantic specification-quality review to Tests 9/26 only after the
   concurrent Test-22/requirement work settles.
6. Move the concise session renderer into the maintainer evaluation package
   during subtask 068 rather than duplicating it.

## Remaining verification

- Human review of root `AGENTS.md` and the approval paragraph.
- Tests 10 and 11 after branch reconciliation.
- The selected Test-22 requirement-restraint sentinel after reconciliation.
- One final integrated Test 27 run against the merged guidance hash.
- A redesigned Test 18 after subtask 019 is approved and implemented.
