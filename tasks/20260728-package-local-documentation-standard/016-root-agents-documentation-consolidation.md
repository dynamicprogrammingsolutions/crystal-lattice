Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`

Specification:
`maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`

Requirement IDs:
`DOCAGENT-001`, `DOCLOCAL-001`, `DOCVAL-010`

# Root AGENTS Documentation Consolidation

Consolidate the root documentation instructions into one short policy and
routing section, remove duplicated commands and temporary migration details,
align root testing language with the risk-based documentation guide, and
re-evaluate the two-page routing behavior without changing the documentation
pages owned by the concurrent Test-22 workstream.

## Requirements checklist

- [x] Root `AGENTS.md` has one clearly identifiable documentation policy and
  routing section of approximately 200–300 words.
- [x] The repository map uses one concise development-documentation entry
  instead of repeating both detailed guidance paths.
- [x] Documentation-site commands are owned by the Crystal Lattice conventions
  and are not repeated as a second command catalog in root guidance.
- [x] The testing section no longer presents itself as a second documentation
  policy and uses the same risk/boundary principle as the documentation guide.
- [x] Documentation-change triggers are concise and route to the maintained
  guide rather than repeating file-role rules.
- [x] Temporary first-wave migration exceptions are removed from permanent
  root instructions.
- [x] Structural documentation work explicitly tells agents to read both
  routed guidance pages in full.
- [x] Existing commit authorization, package architecture, plugin, testing
  realism, and unrelated development guidance remain unchanged.
- [x] Deterministic checks detect reintroduction of multiple documentation
  policy sections, temporary migration inventories, or duplicated site command
  catalogs.
- [x] Test 27 compares the exact pre-change and candidate root guidance with
  unchanged prompt, fixture, assertions, model, and reasoning effort.
- [x] Mixed or failing real-model evidence remains visible and is not converted
  into a passing claim by weakening the routing assertion.

## Scope

In scope:

- root `AGENTS.md`;
- deterministic documentation-guidance structure checks;
- Test 27 guidance-source setup and focused repeated evaluation;
- task/specification evidence for this subtask.

Out of scope:

- `docs/development/documentation.md` and
  `docs/development/crystal-lattice-documentation.md`;
- Test 13 vocabulary rules;
- Test 22 and requirement-minimality guidance;
- `TASKS-v7` content or synchronization;
- `CONTRIBUTING.md`;
- package documentation migration.

## Supporting details

Root `AGENTS.md` currently has four documentation-related blocks:

| Block | Approximate words | Current role |
|---|---:|---|
| `Docs & scripts` | 50 | repository map |
| `Documentation ownership and workflow` | 231 | policy and routing |
| `Docs` under development workflow | 54 | site commands |
| `When to update docs` | 96 | update triggers and migration exceptions |

The blocks are mostly compatible but make policy appear distributed. Site
commands duplicate the Crystal Lattice conventions, and the permanent root
message still carries a temporary legacy-page inventory.

The root testing section says to prefer unit tests first. The maintained guide
instead selects the least expensive test that proves the requirement without
mocking away the important boundary. Root instructions should use that same
principle.

Test 27 failed its first candidate run because only the project-independent
guide was read, then passed a fresh repeat after both pages were read. This is
mixed evidence. The shortest clarification to evaluate is “read both files in
full.”

The concurrent Test-22 work may change the documentation guide. This task does
not edit those pages. Final routing verification is repeated after branch
reconciliation so the evaluated guidance hash matches the integrated result.

## Implementation Notes

- September 14, 2026: Pinned the pre-change source at
  `cdeb50a7df92820e487c466b030ea8f5f6dcb993`; root `AGENTS.md` SHA-256 was
  `eb43c17f863671842b73580299ab4b5badf34a2381ab5b05e5b42085cae41d6c`.
- Consolidated the four documentation-related blocks into one 289-word policy
  and routing section plus one short repository-map entry.
- Removed the duplicated site command catalog and temporary migration
  inventory, required both guidance pages to be read in full for structural
  work, and aligned testing language with the maintained risk/boundary rule.
- Removed the lone residual numbered section heading so the root outline uses
  one consistent heading convention.
- Source-level diff inspection found no changes to commit authorization,
  package ownership, plugin behavior, task handling, or unrelated testing
  realism. Deterministic and real-model verification remain pending.
- Deterministic suite support now checks the 3,000–3,600-word combined review
  budget, one root policy section, the full-read route, and removed duplicate
  blocks; 31 focused tests pass.
- Test 27 used immediate pre-change guidance SHA-256 `18251b85...` and
  candidate `d428bd65...`. Both baseline runs and both candidate runs read the
  two pages completely before mutation. One baseline failed only because user
  documentation linked an internal specification; the other baseline and both
  candidates passed.
- The detailed model and assertion review is recorded in
  `maintainer/docs/evaluations/documentation-guidance/20260914-guidance-followup-results.md`.
- Final local verification completed: 68 agent-evaluation tests and 15
  documentation-site preparation tests passed; Ruff, Python compilation,
  documentation preparation, MkDocs build, task structure, and `git diff
  --check` passed. MkDocs retained existing navigation, link, Material, and
  Griffe warnings unrelated to this change.
- September 17, 2026: Reconciled the completed Core documentation migration,
  v3 requirement/testing guidance, and this root consolidation through merge
  commits `8c26812e` and `9c30e16c`. The integrated root section is 289 words
  and routes to current Core and development documentation.
- September 17, 2026: The final integrated Test 27 passed with injected
  guidance hash
  `b8b890674fb4ce964ae011615eec547383a81ddb03c95eefbb707021e7d40242`.
  It read both guidance pages completely before mutation and did not read
  maintainer specifications. The run remains routing evidence rather than
  independent validation of every generated documentation claim.

## Execution plan

Status: Approved

### 1. Pin the pre-change root guidance

1. Record the current `develop` revision and hashes of root `AGENTS.md` and the
   two routed guidance pages.
2. Preserve the existing Test 27 prompt, event ordering, mutation allowlist,
   model, and reasoning effort.
3. Add an explicit pre-change guidance source when needed so the comparison
   does not use the older `f81f3632` documentation baseline.

### 2. Consolidate root documentation guidance

1. Reduce `Docs & scripts` to one development-documentation hub entry.
2. Keep `Documentation ownership and workflow` as the sole policy section.
3. Change the structural-work route to require both guidance pages in full.
4. Remove the duplicated root documentation-site command list and point to the
   Crystal Lattice publication section.
5. Rename `Testing & Documentation Principles` to `Testing Principles`.
6. Replace `When to update docs` with one compact applicability rule and
   remove the temporary migration inventory.
7. Align “unit first” and the final “done” sentence with risk-based,
   applicable verification and documentation work.

### 3. Add deterministic protection

1. Assert the documentation policy section remains within the approved word
   range.
2. Assert root guidance contains the two-page full-read route exactly once.
3. Assert the temporary migration file list and duplicate MkDocs command
   catalog are absent.
4. Assert commit guidance and unrelated high-value root instructions remain.

### 4. Run focused behavioral comparison

1. Run Test 27 at least twice against the pinned pre-change root guidance.
2. Run the unchanged Test 27 at least twice against the candidate.
3. Use `glm-5.3-flash:cloud` with the same supported reasoning effort for all
   paired runs.
4. Preserve routing read positions, first mutation, guidance hashes, changed
   paths, response, and assertions.
5. Do not add longer root instructions unless the concise clarification still
   produces representative failures.

### 5. Reconcile concurrent guidance and verify

1. Rebase or merge the completed Test-22 guidance work.
2. Rerun deterministic checks and one final candidate Test 27 against the
   integrated guidance hash.
3. Run documentation preparation, the focused site-assembly tests, normal
   MkDocs build, and `git diff --check`.
4. Update requirements and task evidence without claiming human readability
   confirmation.

### Implementation decisions and open questions

- Recommendation: keep one 200–300-word documentation section and route all
  detail through `docs/development/index.md` and its two pages.
- Recommendation: remove duplicated site commands rather than maintaining two
  command lists.
- Recommendation: use an immediate pre-change guidance source and two
  repetitions per side because current Test 27 evidence is mixed.
- Recommendation: do not add `CONTRIBUTING.md` to root AGENTS; it remains
  human-facing, while subtask 068 may route task-enabled agents to it.
- Exact heading wording and whether the short update-trigger sentence remains
  under Testing or the documentation section are reversible editorial choices.
- No requirement question is open.

### Documentation

- Root `AGENTS.md`
- This task and the documentation-standard requirements ledger
- Documentation-standard suite guide only if the new pre-change source or
  repeated-run command needs explanation

No public package documentation changes are planned.

### Task checklist

- [x] Pin the immediate pre-change guidance source.
- [x] Consolidate the root documentation blocks.
- [x] Align root testing terminology with risk-based selection.
- [x] Add deterministic root-structure checks.
- [x] Run paired repeated Test 27 comparisons.
- [x] Reconcile the concurrent documentation-guidance branch.
- [x] Rerun the final integrated Test 27.
- [x] Run focused deterministic, site, build, and diff verification.
- [x] Update requirement and task evidence.
- [ ] Obtain human review of the recurring root guidance.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Root concision and concentration | Source inspection and deterministic checks show one 200–300-word documentation policy/routing section, one map entry, and no duplicate command or migration block. |
| Routing | Repeated Test 27 results record both full-page reads before mutation with exact immediate-baseline/candidate guidance hashes; mixed outcomes remain visible. |
| Testing consistency | Root text selects the lowest-cost reliable boundary and retains the real-integration requirements without a conflicting “unit first” default. |
| Preservation | Diff inspection confirms commit guidance, package architecture, plugin rules, task boundaries, and unrelated testing rules remain unchanged. |
| Integrated verification | Focused tests, documentation preparation, MkDocs build, and final post-reconciliation routing run complete without a new task-caused warning or false passing claim. |

### Additional implementation verification

- Compare the root documentation-related word count before and after.
- Check every local link changed in `AGENTS.md`.
- Verify the old first-wave migration filenames no longer appear in recurring
  root guidance.
- Verify the Test 27 candidate does not read maintainer specifications.
