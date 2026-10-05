# Isolated Synthetic Evaluation Repositories

Correct the evaluation workspace mechanism so synthetic Eleventy, FastAPI,
Flask/Vue, assessment, and mini-evaluation worktrees belong to a dedicated
shared Git repository rather than the Crystal Lattice repository.

## Requirements checklist

- [ ] Synthetic evaluation worktrees are registered only in an isolated
  fixture repository and never appear in Crystal Lattice's worktree
  administration, refs, or object database.
- [ ] One isolated repository shares fixture Git objects across concurrent and
  repeated evaluations instead of creating one complete object database per
  run.
- [ ] Each active run still receives an independent checked-out working tree
  so concurrent agents cannot observe or overwrite one another's files.
- [ ] After an agent finishes and before cleanup, the evaluator records the
  final net workspace change set relative to the deterministic fixture
  baseline: tracked/staged changes, additions, deletions, binary changes, and
  hashed copies of every relevant untracked file.
- [ ] The optional Crystal Lattice linked-worktree helper remains available
  only for evaluations that intentionally evaluate an actual revision of a
  supplied repository.
- [ ] Isolated fixture worktrees preserve deterministic baseline commits,
  fixture and guidance fingerprints, cache invalidation, status/diff capture,
  continuation, parent forks, assessment flows, and result-package behavior.
- [ ] Every completed or failed run preserves tracked changes and all
  untracked workspace content needed for review or reconstruction before its
  worktree can be removed.
- [ ] Normal completion, exceptions, and user interruption run visible,
  verified cleanup; cleanup failures identify the retained path and cause the
  command to report an incomplete cleanup.
- [ ] Abandoned fixture worktrees can be discovered and removed through their
  isolated owner repository by a dry-run-first retention command without
  consulting or mutating Crystal Lattice worktree administration.
- [ ] Existing committed result packages and historical raw records remain
  readable and regenerate byte-identically; no model rerun is required for the
  migration.
- [ ] Deterministic tests prove that synthetic evaluation creation and cleanup
  leave the source Crystal Lattice repository's worktree listing, refs, HEAD,
  object database, and working content unchanged.

Parent Task: `tasks/20260728-package-local-documentation-standard/000-main.md`

Depends On:

- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`

Coordinates With:

- `tasks/20260728-package-local-documentation-standard/019-evaluation-workspace-confinement-and-test18-redesign.md`
- `tasks/20260728-package-local-documentation-standard/100-task-guidance-suite-restructure.md`

## Scope

This follow-up owns the isolated fixture-repository manager, the
documentation-standard and task-guidance synthetic fixture factories,
workspace evidence capture, lifecycle cleanup reporting, stale fixture
worktree discovery, and affected maintainer documentation.

It does not remove the generic `git_workspace()` helper or prohibit linked
worktrees when the evaluated subject really is a supplied repository revision.
It does not change evaluation prompts, scoring, models, fixture content,
guidance wording, result-package schemas, or the confinement policy owned by
subtask 019. It does not by itself impose a retention policy on virtual
environments, provider caches, sessions, or other non-workspace artifacts.
Git evidence in this task describes final net workspace state, not a real-time
filesystem event history; transient files created and removed within one run
remain tool/runtime telemetry concerns.

## Supporting details

The current synthetic factories call `git_workspace(source=REPOSITORY_ROOT,
revision=...)`, then delete most or all Crystal Lattice files and write an
unrelated fixture repository. That reuse gives the fixture Git status and a
baseline commit, but unnecessarily registers it as a Crystal Lattice
worktree. Older runs expose the mismatch as roughly 4,500 Crystal Lattice
deletions plus a small synthetic project.

A separate standalone repository per run would fix the ownership problem but
duplicate fixture commit objects. A shared isolated owner repository preserves
the useful worktree mechanics and stores each deterministic fixture object
once. Every active run still needs its own checked-out files because agents
mutate them independently; Git worktrees share objects and administration, not
working-directory files.

The shared repository primarily improves ownership and setup cost compared
with the current Crystal Lattice-linked design: it avoids checking out and
deleting thousands of Crystal Lattice files and reuses prepared fixture
commits. Its steady-state disk saving over today's design is modest because
today's worktrees already share one object database. Prompt post-capture
worktree removal and separate artifact/cache retention remain the larger disk
controls.

The isolated owner should contain synthetic fixture history only. Making it a
temporary clone of Crystal Lattice would move the registration but retain the
wrong baseline, unnecessary Crystal Lattice objects, and thousands of
synthetic deletion records.

The generic kernel already accepts arbitrary workspace factories. A fixture
repository manager can therefore seed deterministic fixture commits in its own
object database and return ordinary linked worktrees without introducing
suite semantics into the kernel.

Subtask 019 remains complementary: it prevents an evaluation from treating
mutable external repositories as evidence. This task changes repository
creation and lifecycle ownership.

## Execution plan

Status: Approved (October 4, 2026; execution sequenced after the
remaining subtask-125 increments per the recorded coordination)

Add an isolated fixture-repository manager beside the optional pinned
repository helper. The manager owns one shared synthetic Git object database,
deterministic fixture refs, per-run linked worktrees, locking, and cleanup. A
caller provides fixture materialization and a stable fingerprint; the generic
layer remains unaware of scenarios, guidance, prompts, and assessments.

Use a bare repository under the configured evaluation state or cache root
unless implementation testing shows that Git operations require a minimal
control checkout. Seed one deterministic commit per unique fixture and
guidance baseline, identified by content rather than timestamps or Crystal
Lattice revision. Serialize seed creation and worktree administration while
allowing independent run worktrees to execute concurrently.

For each run, add a detached worktree from the isolated owner into the run's
workspace location. Agent output remains uncommitted working state unless a
suite explicitly needs a deterministic child baseline. Continuations and
parent forks create deterministic fixture-owned commits or restore persisted
tracked/untracked state inside the isolated repository; no commit or ref is
written to Crystal Lattice.

Move complete final-state observation ahead of cleanup for every success,
cache hit, structured failure, and cache-publication failure. Store porcelain
status, a binary `HEAD` diff covering staged and unstaged tracked state,
baseline/tree identity, and hashed copies of all relevant untracked files in
raw workspace evidence. Keep ignored build/cache products outside the authored
change set unless a suite explicitly includes them. Make cleanup outcomes
observable instead of suppressing them.

Bound live worktree lifetime to the dependency chain that needs it. Retain a
worktree while a same-chain stage must read its live files, then remove it
after the dependent state is persisted. Add dry-run-first stale-worktree
discovery and pruning against the isolated owner repository for abrupt process
termination. Garbage collection may remove fixture objects only when no
retained run, cache entry, deterministic seed ref, or rescue record needs
them.

Migrate documentation-standard scenario, assessment, parent-fork, and
requirement-quality factories plus task-guidance fixture, assessment, and
handoff factories. Invalidate only execution-cache entries whose identity
depended on the old Crystal Lattice-linked fixture commit. Historical raw runs
and committed result packages stay readable and are verified without model
calls.

### Implementation decisions and open questions

- Recommendation for approval: use one shared bare synthetic repository per
  configured evaluation artifact/cache root. This shares objects across runs
  without adding a permanent owner checkout.
- Recommendation for approval: do not clone Crystal Lattice into the isolated
  owner. Materialize only fixture-owned files and guidance into deterministic
  seed commits.
- Recommendation for approval: retain per-run worktrees because independent
  mutable working files are required for concurrency; save space through the
  shared object database and prompt removal after evidence capture.
- Recommendation for approval: keep the generic linked-worktree helper for
  true repository-revision evaluations, while synthetic suites use the
  isolated manager.
- Recommendation for approval: cleanup failures are no longer silently
  ignored. They become structured cleanup evidence and make the invoking
  command incomplete or failed while preserving the workspace for diagnosis.
- The existing configurable artifact-root contract remains compatible. Moving
  its default is not required because synthetic registrations and objects no
  longer belong to Crystal Lattice.
- Exact API names, lock implementation, and bare-versus-minimal-control
  fallback are local implementation choices.
- No unresolved requirement question remains. Approval of this plan approves
  the recommendations above.

### Documentation

- Amend the framework workspace/continuation/cache specification and
  requirements to distinguish isolated synthetic worktrees from pinned
  source-repository worktrees and to require complete pre-cleanup evidence.
- Add `TGEVAL-022` for isolated synthetic task-guidance repositories and
  `DSEVAL-004` for isolated documentation-guidance repositories.
- Update framework workspace, artifact, continuation, and cleanup guidance.
- Update both suite running guides with repository ownership, shared-object
  behavior, temporary lifetime, cleanup-failure, and stale-worktree recovery
  behavior.
- Update task 015 through its post-completion follow-up and record
  implementation evidence in this task.

### Task checklist

- [ ] Update target specifications and add `TGEVAL-022` and `DSEVAL-004`.
- [ ] Add the isolated shared fixture-repository manager.
- [ ] Add deterministic seed refs and concurrent administration locking.
- [ ] Capture complete tracked and untracked evidence before every cleanup.
- [ ] Make cleanup failures visible and outcome-affecting.
- [ ] Migrate documentation-standard synthetic workspace factories.
- [ ] Migrate task-guidance synthetic workspace factories.
- [ ] Rework parent/continuation workspace lifetime and reconstruction.
- [ ] Add dry-run-first stale isolated-worktree discovery and cleanup.
- [ ] Add source-repository non-mutation and ownership tests.
- [ ] Add deterministic commit, fingerprint, cache, continuation, failure, and
  interruption tests.
- [ ] Verify historical raw-record and result-package compatibility without
  model calls.
- [ ] Update framework and suite documentation and requirement evidence.
- [ ] Run focused package and suite verification.

### Requirement verification

- **Repository isolation:** integration tests snapshot Crystal Lattice's
  worktree list, refs, HEAD, object database, and working status; create,
  mutate, continue, assess, and clean synthetic fixtures; and prove the
  snapshots are unchanged afterward.
- **Shared-object behavior:** two concurrent worktrees from the same fixture
  resolve to one owner repository and one deterministic seed commit while
  retaining independent working-file mutations.
- **Suite production paths:** one documentation-standard fixture chain and one
  task-guidance producer/continuation/assessment chain use their production
  factories and register only under the isolated owner.
- **Evidence completeness:** success and failure tests reconstruct the final
  tracked and untracked workspace state from raw artifacts after the temporary
  worktree is gone.
- **Net-change observation:** a production-path test makes staged, unstaged,
  deleted, binary, and untracked changes in one run and proves the persisted
  evidence reports and reconstructs the resulting final state before cleanup.
- **Lifecycle behavior:** normal, exception, `KeyboardInterrupt`, cleanup
  failure, and stale-worktree cases have deterministic tests; failed cleanup
  is visible and preserves a diagnosable path.
- **Compatibility:** both committed task-guidance result packages pass `check`
  and regenerate byte-identically, documentation-standard frozen readers
  remain valid, and no hosted/model execution occurs.

### Additional implementation verification

- Run `pytest maintainer/agent-evaluation/tests -q`.
- Run the focused documentation-standard deterministic workspace tests.
- Run the task-guidance fixture, runner-assembly, package-adapter, and
  prune/retention tests.
- Run Ruff and mypy for the affected package paths, reporting pre-existing
  failures separately.
- Run focused documentation links and `git diff --check`.