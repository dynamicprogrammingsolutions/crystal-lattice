Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md`
- `tasks/20260728-package-local-documentation-standard/030-core-python-documentation-migration.md`
- `tasks/20260728-package-local-documentation-standard/040-application-and-plugin-documentation-migration.md`
- `tasks/20260728-package-local-documentation-standard/050-cross-package-and-reference-documentation-triage.md`
- `tasks/20260728-package-local-documentation-standard/060-navigation-compatibility-and-build-triggers.md`
- `tasks/20260728-package-local-documentation-standard/065-contributing-and-ai-assisted-development-workflow.md`
- `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`

# Verification and Deferred Migration Inventory

Perform final documentation-system verification, map evidence back to the
requirements, and record deferred migration work without creating filler or
silently expanding scope.

## Requirements checklist

- [ ] Focused docs-site preparation tests pass.
- [ ] `python docs_site/scripts/prepare_mkdocs_site.py` completes successfully.
- [ ] The generated package tree contains all registered canonical
  documentation and excludes agent-only/generated-source files as designed.
- [ ] The normal MkDocs build completes successfully.
- [ ] No new build warning caused by this task remains unresolved.
- [ ] Existing pre-task strict-mode warnings are distinguished from new
  warnings; strict-mode cleanup is not claimed unless it is actually complete.
- [ ] Every first-wave and investigate/classify page in the parent migration
  inventory has a recorded outcome and verification boundary.
- [ ] Old source references and public route mappings are accounted for.
- [ ] Root `CONTRIBUTING.md` presents the approved concise six-step,
  risk-scaled workflow and short example prompts.
- [ ] Human manual verification, independent AI review, human acceptance, and
  commit authorization remain clearly distinct in contributor and agent
  guidance.
- [ ] Canonical and bundled `TASKS-v7` files match through a mechanical
  synchronization or parity check.
- [ ] Task guidance and contributor guidance do not contradict or duplicate
  each other unnecessarily.
- [ ] Deterministic task-guidance evaluation affected by the update passes;
  real-model review is recorded separately when run.
- [ ] A concise deferred migration inventory records likely owner, reason for
  deferral, and a useful future trigger.
- [ ] Parent and subtask requirement evidence is updated before completion.
- [ ] Human-review items remain incomplete until explicitly confirmed.

## Supporting details

### Verification philosophy

Verification is proportional to the documentation change:

- test the assembler as code;
- build the site through the production preparation path;
- verify links, routes, and navigation at the public documentation boundary;
- use focused existing code/tests only for factual claims touched by migration;
- do not run or modify unrelated product suites merely to claim a broad audit.

### Deferred inventory format

Recommended columns:

```markdown
| Current path | Likely owner/destination | Status | Why deferred | Revisit when |
|---|---|---|---|---|
```

Valid reasons include:

- ownership remains ambiguous;
- current behavior cannot be established without broad investigation;
- page is historical and archival policy is not defined;
- generated reference policy needs a separate decision;
- package has not yet accumulated enough documentation to justify a full
  profile.

Do not create empty target pages or TODO-only quickstarts for deferred items.

## Execution plan

Status: Draft

1. Run focused preparation tests and record exact results.
2. Run the production preparation command and inspect representative package
   trees.
3. Run the normal MkDocs build and compare warnings with the baseline.
4. Exercise representative old/new public paths and internal links.
5. Inspect the rendered contributor workflow for readability, role clarity,
   prompt concision, and human review gates.
6. Verify canonical/bundled task-guidance parity and run affected deterministic
   evaluation tests.
7. Review all migration candidates and record final disposition.
8. Create the concise deferred migration inventory.
9. Map acceptance evidence to parent and subtask requirements.
10. Identify any human review still needed and leave those requirements
   incomplete.

### Implementation decisions and open questions

- Normal build plus no new warnings is the approved required boundary.
- Strict mode may be run for information, but failure from pre-existing
  warnings is reported rather than converted into unrelated scope.
- Deferred inventory is an evidence artifact, not hidden requirements for
  later implementation.
- No requirement questions are open at task creation.

### Documentation

- Deferred migration inventory at a location selected by the documentation
  standard, likely under `docs/development/`
- Updated `docs_site/README.md` verification commands if implementation changes
  them
- Parent and subtask completion evidence

### Task checklist

- [ ] Run assembler tests.
- [ ] Run preparation command.
- [ ] Inspect generated package tree.
- [ ] Run normal MkDocs build.
- [ ] Compare warnings with baseline.
- [ ] Verify representative links and routes.
- [ ] Review contributor workflow readability and prompt examples.
- [ ] Verify task-guidance parity and deterministic evaluation.
- [ ] Record every migration outcome.
- [ ] Write deferred migration inventory.
- [ ] Update requirement evidence.
- [ ] Record human verification needs.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Assembly correctness | Focused tests pass and generated package trees match registry and precedence rules. |
| Site build | Normal MkDocs build exits successfully; warning comparison is recorded. |
| Navigation and compatibility | Representative canonical pages and old routes resolve in built output. |
| Contributor workflow | Human inspection confirms the six-step guide is easy to follow, risk-scaled, role-clear, and keeps prompt examples separate from standing rules. |
| Task guidance | Canonical/bundled parity check passes; specification/task semantics and concise-prompt evaluation cases pass deterministic checks. |
| Migration completeness | Every parent migration candidate has relocate/retain/defer outcome with owner and verification boundary. |
| Deferred work quality | Inventory is concise, contains no hidden requirements, and gives a clear future trigger without filler pages. |
| Requirements evidence | Main and subtask checklists cite test/build/inspection/human evidence accurately. |

### Additional implementation verification

- Optionally run MkDocs strict mode and report it separately from the required
  normal build.
- Inspect generated `llms.txt` and `llms-full.txt`.
- Confirm package-source changes are covered by deployment workflow filters.
- Inspect root `CONTRIBUTING.md` without source context and confirm a reviewer
  can quickly find the normal-feature path, plan gate, manual-testing rule,
  AI-review role, and commit-authorization rule.
- Inspect compiled task-enabled developer guidance and confirm it routes to the
  contributor workflow without embedding it.
- Confirm generated `docs_site/prepared/` and `docs_site/dist/` are still
  ignored and are not presented as authored changes.
