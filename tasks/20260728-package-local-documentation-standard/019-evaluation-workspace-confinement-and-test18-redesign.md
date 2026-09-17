Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`
- `tasks/20260728-package-local-documentation-standard/017-shared-plugin-guidance-calibration.md`

Related Specifications:

- `maintainer/specifications/agent-evaluation-framework/index.md`
- `maintainer/specifications/documentation-and-specification-standard/index.md`

Requirement IDs:
`AEVAL-011`, `AEVAL-017`, `DOCREP-002`, `DOCVAL-010`

# Evaluation Workspace Confinement and Test 18 Redesign

Prevent documentation evaluations from using mutable sibling or parent
worktrees as evidence, align the array shell's workdir handling with configured
allowed paths, and replace Test 18 with bounded factual and cross-owner
scenarios whose pass/fail result reflects documentation quality.

## Requirements checklist

- [ ] `ShellArrayTool` rejects an explicit workdir outside configured
  `allowed_paths` using path-aware containment rather than string prefixes.
- [ ] Tool documentation and tests state clearly whether `allowed_paths`
  restricts only process workdirs or also command-level filesystem access.
- [ ] Documentation evaluations do not treat editable installs, sibling
  worktrees, the primary checkout, or another mutable repository revision as
  evidence for a pinned fixture.
- [ ] Test 18 has every implementation fact and executable check needed for its
  acceptance contract inside the pinned fixture, or removes that claim from
  the scenario.
- [ ] Package-example quality and shared plugin-authoring ownership are tested
  through focused branches plus a bounded cross-owner sentinel.
- [ ] A valid concrete transformation example is accepted regardless of the
  chosen input token.
- [ ] Assertions reject unsupported loader claims, unrelated existing
  shared-page mutations, broken discoverability, incomplete runs, and
  plugin-specific behavior presented as a framework-wide rule.
- [ ] Documentation commands or code samples used as acceptance evidence are
  executed against fixture-owned source or verified by an explicitly supplied
  fixture-owned test.
- [ ] Immediate-baseline and candidate comparisons preserve exact prompts,
  fixtures, guidance, model, reasoning effort, and normal tool budget.
- [ ] Concise session transcripts, deterministic findings, semantic review,
  and raw diagnostics remain separate evidence surfaces.

## Supporting details

September 14 calibration found:

- the array-based shell resolves arbitrary workdirs but does not enforce
  `allowed_paths`; the legacy shell checks workdir containment;
- shell commands can inspect paths outside their workdir, so workdir validation
  alone is not a complete process sandbox;
- multiple Test 18 runs read or executed code from unrelated sibling
  worktrees, while the file-reader tool correctly rejected those paths;
- the fixture omits runtime sources that `plugins/docs/AGENTS.md` tells agents
  to use for factual verification;
- the original assertions accepted unsupported claims and any mutation under
  `plugins/docs/`, and rejected a valid `hi` to `HI` example;
- a 45-call diagnostic completed in 11 calls, so increasing the budget did not
  explain success.

## Execution plan

Status: Draft

### 1. Define the confinement contract

1. Confirm the intended `allowed_paths` contract for shell tools.
2. Add path-aware explicit-workdir enforcement to `ShellArrayTool`, matching
   the legacy shell where applicable.
3. Decide whether evaluation acceptance also requires process-level
   filesystem isolation or whether fixture-contained facts plus external-path
   detection are sufficient.
4. Add regression tests for sibling paths, common-prefix paths, symlinks, and
   valid nested workdirs.

### 2. Remove mutable external evidence

1. Ensure projected evaluation environments do not advertise unrelated
   editable checkout paths as factual sources.
2. Detect explicit external-repository paths and report them as invalid
   evaluation evidence.
3. If full process isolation is selected, implement it at the environment/tool
   boundary rather than through scenario wording.

### 3. Redesign Test 18

1. Create a package-example branch with `UpperTool.ts`, a fixture-local
   executable smoke test, and README acceptance.
2. Create a shared-authoring branch with the exact loader/export/configuration
   contract needed by the shared page inside the fixture.
3. Retain one small cross-owner sentinel that checks package-specific behavior
   stays in the example while reusable authoring facts remain indexed in
   `plugins/docs/`.
4. Avoid requiring one model turn to research, verify, author two substantial
   pages, update two indexes, and execute broad repository tests.

### 4. Replace keyword-only acceptance

1. Keep deterministic path, indexing, completion, and fixture-fact checks.
2. Execute fixture-owned examples and relevant commands.
3. Add a narrow semantic assessment for unsupported generalization,
   duplication, factual uncertainty, and audience split.
4. Do not use one exact example word as the transformation contract.

### 5. Run baseline-first comparisons

1. Pin the immediate guidance revision after concurrent guidance
   reconciliation.
2. Run each focused branch at the normal 30-call limit.
3. Preserve a small number of repeated GLM samples to measure variance.
4. Use a second model only after explicit hosted authorization.

### Implementation decisions and open questions

- Recommendation: enforce explicit shell workdir containment immediately, but
  do not describe that as complete command filesystem sandboxing.
- Recommendation: use fixture-contained source and executable checks rather
  than permitting access to the primary or sibling worktrees.
- Recommendation: split the broad scenario into two focused branches and one
  cross-owner sentinel.
- Material question: should evaluation shell commands run in an OS/container
  sandbox, or is deterministic rejection/detection of external repository
  evidence sufficient for this suite?
- Material question: should shell `allowed_paths` become a public
  command-filesystem restriction, or remain a workdir restriction with a
  separately named stronger sandbox option?

### Documentation

- `plugins/codex-tools/README.md` if shell path semantics change
- Agent-evaluation environment/workspace documentation
- Revised Test 18 scenario, seed, fixture, and review guidance
- This task and affected requirements evidence

No documentation-standard guidance wording change is planned unless the
redesigned paired scenario later isolates a guidance defect.

### Task checklist

- [ ] Approve the shell/evaluation confinement boundary.
- [ ] Add ShellArrayTool workdir containment and regression tests.
- [ ] Prevent or detect mutable external repository evidence.
- [ ] Specify focused package, shared, and cross-owner scenarios.
- [ ] Add fixture-owned executable verification.
- [ ] Replace keyword-only assertions.
- [ ] Run deterministic tests.
- [ ] Run immediate-baseline and candidate model comparisons.
- [ ] Review concise transcripts and semantic findings.
- [ ] Update requirements and completion evidence.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Shell workdir boundary | Focused shell-tool tests reject sibling, prefix-collision, and symlink-escape workdirs while valid nested workdirs execute. |
| Evaluation evidence isolation | Scenario records contain no source, command, or claim derived from a mutable external checkout; an intentional external-access fixture is rejected. |
| Package example | Fixture-owned execution proves the documented config/example behavior and the package README remains complete without unsupported loader internals. |
| Shared authoring | Shared-page scenario documents only fixture-provided reusable behavior and remains indexed from the canonical guide and shared index. |
| Cross-owner behavior | Sentinel preserves the package/shared split without duplicating whole guides or generalizing `UpperTool` behavior. |
| Model calibration | Paired normal-budget runs and concise transcripts show assertion status agrees with actual model behavior. |

### Additional implementation verification

- Verify shell path checks use resolved paths and do not accept
  `/allowed-prefix-other`.
- Verify external checkout detection does not flag the isolated run workspace
  itself.
- Verify no test passes solely because a command or page contains expected
  keywords.
