Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`

Specification:
`maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`

Requirement IDs:
`DOCGEN-005`, `DOCGUIDE-004`, `DOCVAL-010`

# Substantial Specification Approval Guidance

Restore the concise approval boundary accidentally omitted by the two-page
rewrite: when no active approved task already authorizes a substantial new
specification, the agent presents its proposed scope, location, file shape, and
overlap and obtains approval before creating it.

## Requirements checklist

- [x] The project-independent guide requires approval before creating a
  substantial new specification unless the active approved task already
  authorizes that specification.
- [x] The approval request states why a durable specification is useful, which
  component or shared scope owns it, the intended behavior boundary, the
  smallest useful file set, and overlap with existing specifications.
- [ ] A direct user request to create a substantial specification without an
  approved task produces a concrete proposal and no repository mutation before
  approval.
- [x] An approved task that already authorizes the specification proceeds
  without duplicate approval.
- [x] Small local fixes and updates to an existing specification do not acquire
  a new approval ceremony.
- [x] Explicit approved file-layout choices remain effective and are not
  overridden by a default tree.
- [x] The rule does not add lifecycle status fields to every specification;
  approval remains task-owned by default.
- [ ] Test 6 passes without regressing Tests 9 and 26 in this branch.
- [ ] Tests 10 and 11 plus the integrated requirement-restraint sentinel are
  rerun after the concurrent guidance branch is reconciled; unresolved results
  remain visible until then.

## Coordination boundary

This task edits a different section of `docs/development/documentation.md` from
the concurrent Test-22 workstream in
`/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite`.

The approval paragraph may be implemented and reviewed now. Reconcile the
branches later and rerun Tests 10 and 11 plus the selected requirement-restraint
sentinel against the integrated guidance.

This task does not change Test 22, requirement-minimality wording, Test 13
vocabulary rules, or task decomposition.

## Supporting details

The historical `DOCGEN-005` rule required approval and previously passed Test
6 on supported models. The two-page rewrite preserved when a specification is
useful but omitted the approval sentence. Under both the previous and rewritten
GLM-5.3 matrices, Test 6 created the specification immediately instead of
requesting approval.

The current guide already distinguishes specifications, requirements, and
tasks and explains proportional file selection. The expected fix is one short
paragraph in the existing “When a specification helps” section, not a new
policy section.

Test 9 covers an approved task that already authorizes a substantial
specification. Test 26 covers an explicit safe file-layout override. Tests 10
and 11 distinguish existing-specification updates and local fixes that should
not require new durable structure.

## Implementation Notes

- September 14, 2026: Pinned the pre-change project-independent guide at
  `cdeb50a7df92820e487c466b030ea8f5f6dcb993`, SHA-256
  `d138cedf351581603b976d916a0de2e90b024df36379b8c02ec6441321f96feb`.
- Added one paragraph under “When a specification helps.” It requires a
  concrete proposal and approval only when an active approved task does not
  already authorize a substantial new specification.
- The paragraph names usefulness, owning component or shared scope, behavior
  boundary, smallest useful file set, and overlap. It does not add a
  specification status field or duplicate the rule in root/local guidance.
- The project-independent guide is now 2,055 words. Behavioral verification
  remains pending; Tests 10 and 11 and the Test-22 sentinel remain deferred
  until branch reconciliation.
- Test 6 used immediate pre-change guidance SHA-256 `18251b85...` and candidate
  `d428bd65...`. The baseline and both candidate samples created files without
  requesting approval. The paragraph does not yet distinguish a direct
  creation request from explicit approval of the proposed scope and file set.
- Tests 9 and 26 were paired. Test 9 passed under both guidance versions. Test
  26's baseline omitted the `decisions.md` index link; the candidate passed.
- Tests 10 and 11 and the Test-22 sentinel remain intentionally unresolved
  until concurrent guidance reconciliation.
- Detailed behavior review and recommended wording are recorded in
  `maintainer/docs/evaluations/documentation-guidance/20260914-guidance-followup-results.md`.
- Final local verification completed: 68 agent-evaluation tests and 15
  documentation-site preparation tests passed; Ruff, Python compilation,
  documentation preparation, MkDocs build, task structure, and `git diff
  --check` passed. Existing MkDocs warnings remain unrelated.

## Execution plan

Status: Approved

### 1. Preserve the immediate pre-change baseline

1. Record the current branch guidance revision before editing.
2. Restore the existing Test 6 failure and passing Tests 9 and 26 with exact
   guidance/model provenance.
3. Confirm the failure is the missing approval boundary rather than an
   assertion or fixture defect.

### 2. Add the shortest general rule

Add one concise paragraph to the project-independent guide:

- require approval only for a substantial new specification;
- exempt an active approved task that already authorizes it;
- name the proposal contents: usefulness, owner/location, behavior scope,
  smallest useful file set, and overlap;
- keep updates to existing specifications and straightforward local fixes
  proportional.

Do not duplicate the paragraph in the Crystal Lattice addendum or root
`AGENTS.md`.

### 3. Preserve task-owned approval

1. Confirm no mandatory approval/status field is added to specifications.
2. Keep task files as the default approval and execution record.
3. Preserve custom governance as an allowed specification-specific exception.

### 4. Run paired behavior checks

1. Run Test 6 against the immediate pre-change and candidate guidance with
   unchanged prompt, fixture, assertions, model, and effort.
2. Run Test 9 to verify approved-task execution does not ask twice.
3. Run Test 26 to preserve explicit file-layout overrides.
4. After branch reconciliation, run Tests 10 and 11 to verify existing-spec
   updates and local fixes remain proportional.
5. After branch reconciliation, run the integrated requirement-restraint
   sentinel selected by the Test-22 workstream without modifying its contract.

### 5. Verify and reconcile

1. Run deterministic guidance tests, documentation preparation, site assembly,
   MkDocs build, and `git diff --check`.
2. Update the current requirements ledger and this task's evidence.
3. Present the concise paragraph and paired results for human review before
   completion.

### Implementation decisions and open questions

- Recommendation: restore one paragraph in the project-independent guide only.
- Recommendation: treat the active approved task as sufficient authorization;
  do not ask the user to approve the same specification twice.
- Recommendation: preserve the existing Test 6 scenario rather than adding a
  new substantial behavioral test.
- Approved: implement and review the paragraph before branch reconciliation.
- Tests 10 and 11 and the selected requirement-restraint sentinel remain
  explicitly unresolved until reconciliation; they do not block this branch's
  guidance review or focused Test 6/9/26 evidence.

### Documentation

- `docs/development/documentation.md`
- This task and the documentation-standard requirements ledger
- Behavior-verification result notes only when paired evidence changes

No root AGENTS, Crystal Lattice addendum, TASKS-v7, CONTRIBUTING, or package
documentation change is planned.

### Task checklist

- [x] Pin the immediate pre-change guidance.
- [x] Confirm Test 6's causal failure.
- [x] Add the concise approval paragraph.
- [x] Run paired Test 6.
- [x] Run Tests 9 and 26.
- [ ] Reconcile the concurrent guidance branch.
- [ ] Run Tests 10 and 11 after reconciliation.
- [ ] Run the integrated requirement-restraint sentinel after reconciliation.
- [x] Run deterministic and documentation-build verification.
- [x] Update requirement/task evidence.
- [ ] Obtain human review of the final wording and behavior.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Approval boundary | Candidate Test 6 makes no mutation, presents a concrete proposal, and explicitly requests approval before creating the substantial specification. |
| Existing authorization | Test 9 proceeds from its approved task without duplicate confirmation. |
| Proportional scope | Tests 10 and 11 do not introduce unnecessary specification approval or structure. |
| File-layout flexibility | Test 26 continues to honor one approved `decisions.md` file without coercing the default tree. |
| Integration with concurrent guidance | The selected requirement-restraint sentinel retains its approved contract and passing behavior after branch reconciliation. |
| Documentation quality | The rule appears once in the project-independent guide, remains concise, and passes focused link/build checks. |

### Additional implementation verification

- Check that the approval paragraph does not push the main guide over its
  approved review-size budget without an equivalent simplification.
- Verify no competing approval rule appears in root AGENTS or the Crystal
  Lattice addendum.
