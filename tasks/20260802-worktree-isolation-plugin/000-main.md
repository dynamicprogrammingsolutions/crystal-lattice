# Git Worktree Isolation Application Plugin

Build a first-party application plugin that lets one session work in a user-visible Git worktree and later return safely to the original checkout. Deliver a simple production-ready baseline first, then evaluate optional model-context and relative-path strategies without making those experiments prerequisites for the baseline.

## Requirements checklist

- [ ] A first-party application plugin lets a user open, inspect, close, and reopen a dedicated Git worktree through session actions.
- [ ] Opening a worktree creates or selects a dedicated branch from the session's current Git repository, exposes the absolute worktree path and branch to the user, and switches only that session to the worktree.
- [ ] The active worktree is stored at a stable, user-accessible location and remains directly visible and editable with ordinary local tools.
- [ ] Closing restores the session's exact prior workspace settings and never discards uncommitted work, force-removes a worktree, or deletes its branch implicitly.
- [ ] A closed branch can be reopened for follow-up modifications and can be merged by the AI after the session returns to the original checkout.
- [ ] A project-specific setup hook can prepare the worktree using a portable script contract shared with cloud-agent install hooks where possible.
- [ ] Workspace state survives application restart sufficiently to identify active, closed, retained-dirty, removed, failed, and recoverable worktrees.
- [ ] Codex, Claude, Kimi, and Gemini default configurations consistently operate against the session's effective workspace during the baseline workflow.
- [ ] The workflow SHOULD avoid requiring the model to understand that the active directory is implemented as a Git worktree; this is a behavioral preference, not a path-secrecy or sandbox guarantee.
- [ ] Real-provider coverage proves that one session can modify and commit in the worktree, close it, return to the original checkout, merge the branch with AI tools, and make a follow-up modification without incorrectly reusing a stale worktree path.
- [ ] User and developer documentation explain setup, lifecycle, recovery, manual testing, and the fact that Git worktree isolation is not hardened filesystem or shell sandboxing.

## Scope and milestones

### Required baseline production milestone

Subtasks `010` through `050` deliver the stable high-level requirements. Completion of `050` is an explicit review and stop point: the product must then be simple, production-ready, fully covered at the agreed boundaries, documented, and manually testable.

### Optional enhancement workstreams

Subtasks `060` through `110` add opt-in product enhancements and comparative evidence. They may be postponed or cancelled after the baseline review without making the baseline incomplete. Their requirements extend the product only when those subtasks are approved.

## Subtasks

### Baseline production milestone

- [ ] `tasks/20260802-worktree-isolation-plugin/010-shared-workspace-setup-contract.md`
- [ ] `tasks/20260802-worktree-isolation-plugin/020-effective-workspace-consistency.md`
- [ ] `tasks/20260802-worktree-isolation-plugin/030-worktree-plugin-backend.md`
- [ ] `tasks/20260802-worktree-isolation-plugin/040-baseline-worktree-ux-and-documentation.md`
- [ ] `tasks/20260802-worktree-isolation-plugin/050-baseline-real-model-workflow.md`

### Optional enhancements

- [ ] `tasks/20260802-worktree-isolation-plugin/060-explicit-workspace-system-context.md`
- [ ] `tasks/20260802-worktree-isolation-plugin/070-workspace-transition-reminders.md`
- [ ] `tasks/20260802-worktree-isolation-plugin/080-relative-path-mode-contract.md`
- [ ] `tasks/20260802-worktree-isolation-plugin/090-relative-path-mode-codex-and-claude.md`
- [ ] `tasks/20260802-worktree-isolation-plugin/100-relative-path-mode-kimi-and-gemini.md`
- [ ] `tasks/20260802-worktree-isolation-plugin/110-context-strategy-comparison.md`

## Decisions

- This is organizational Git/workspace isolation, not an adversarial security sandbox. Dedicated file tools should respect configured roots, but arbitrary shell commands are not claimed to be confined.
- New worktrees start from committed `HEAD`. Dirty changes remain untouched in the original checkout and produce a visible warning; the baseline does not silently stash, commit, or patch them into the new worktree.
- Normal close restores the original session workspace and removes the linked worktree only when Git can do so safely without force. Dirty or otherwise non-removable worktrees are retained and reported.
- Branches are never deleted automatically.
- Worktree paths are copyable and user-accessible. A generic cross-platform "open local folder" frontend capability is outside baseline scope.
- Setup may run asynchronously so dependency installation does not hold an action request open indefinitely.
- Existing default tool schemas and system-message behavior remain compatible unless an explicit optional setting enables an experiment.
- Explicit workspace paths, transition reminders, and relative-path behavior are separate opt-in strategies. No experiment becomes a default as part of this task without a later approved requirement change.

## Research findings

- Session setting helpers, session-aware application UI context, conditional session actions, and application-plugin close hooks already exist. The January prerequisite handoffs are therefore not authoritative for current architecture.
- Codex and Claude default system-message runtimes resolve effective `working_directory`; the shared runtime used by Kimi and Gemini currently derives cwd from process state and needs baseline correction.
- Relative `allowed_paths` semantics remain inconsistent across tool families. The baseline plugin can function safely for dedicated file tools by installing an absolute worktree root and restoring the exact previous value.
- Modern shell tools are not uniformly restricted by `allowed_paths`, so the plugin must not advertise security containment.
- Cloud-agent project hooks already support project-local configuration, ordered script candidates, project-relative resolution, and stable `WORKING_DIR`/`SESSION_ID` variables. The reusable part should become a small shared contract rather than a worktree-plugin dependency on private cloud internals.
- Prior absolute paths remain in conversation and tool history after switching workspaces. The baseline real-model matrix must measure whether corrected dynamic system context is sufficient before optional reminder or relative-path strategies are promoted.

## Execution plan

Status: Draft

Deliver the work in dependency order. First establish the portable setup contract and correct effective-workspace context. Then implement the Git/session backend independently of frontend behavior. Add session actions, progress/status presentation, default configuration, deterministic public-boundary tests, documentation, and a manual test path. Finally run the hosted model/tool-family matrix and correct product defects exposed by that realistic workflow.

Pause for product review after subtask `050`. Do not begin optional context experiments merely because their task files exist. When approved, implement each experiment behind an explicit opt-in setting, preserve the baseline when disabled, and use a shared comparison scenario to decide whether any strategy deserves later default status.

### Implementation decisions and open questions

- Baseline worktree base directory: use a configurable stable location outside the source checkout. Recommendation: default to a repository-parent `.crystal-worktrees/<repo-name>/...` layout so it is discoverable and cannot dirty the source checkout.
- Setup operation persistence: record operation state in session metadata and use the application runtime/background facilities for in-process execution. Reconcile interrupted operations on restart rather than pretending they succeeded.
- Source repository identity: resolve with `git -C <effective-working-directory> rev-parse --show-toplevel`; do not rely on process cwd.
- Concurrent branch/worktree operations: use per-session locking plus Git's own repository locking, and turn branch/path conflicts into recoverable status rather than destructive retries.
- Optional relative-path mode still needs a design choice between schema guidance and runtime rejection of absolute paths. Recommendation: define the contract in subtask `080` using baseline matrix evidence before changing tools.
- Explicit-path system context and path-minimizing mode conflict semantically. Recommendation: permit explicit context and reminders to compose, but reject or clearly prioritize incompatible explicit-path and path-minimizing settings.

### Documentation

- Add plugin documentation covering configuration, metadata/state, actions, setup hooks, worktree storage, close/reopen behavior, failure recovery, and security limits.
- Update cloud script-authoring documentation for the portable `WORKING_DIR` setup convention without removing cloud-specific aliases.
- Add default-config reference material for baseline and optional settings as they land.
- Provide a deterministic manual walkthrough and separate credentialed real-model commands.
- Document results and recommendations from the optional strategy comparison without changing defaults automatically.

### Task checklist

- [ ] Complete and verify shared setup contract.
- [ ] Complete and verify effective workspace consistency.
- [ ] Complete and verify worktree backend.
- [ ] Complete and verify baseline UX, default configuration, documentation, and manual path.
- [ ] Complete and verify the baseline real-model matrix.
- [ ] Hold baseline product review and record whether optional work proceeds.
- [ ] If approved, implement explicit system context.
- [ ] If approved, implement transition reminders.
- [ ] If approved, define and implement relative-path mode across all four tool families.
- [ ] If approved, run comparative validation and document a recommendation.

### Requirement verification

- Exercise create/open/status/close/reopen through the public application action API and inspect persisted session metadata and effective settings.
- Prove with temporary real Git repositories that branches and user work survive safe close, dirty worktrees are retained, and exact prior settings are restored.
- Execute a project setup fixture through both worktree and cloud-compatible environments and assert the portable environment contract.
- Use production tool adapters to read, edit, run tests, and commit inside the effective worktree for Codex, Claude, Kimi, and Gemini configurations.
- Run the credentialed model/tool matrix through the application request loop and assert the final Git graph, files, and post-close tool workdirs.
- Follow the documented manual workflow from a normal checkout without internal API calls or test-only behavior.

### Additional implementation verification

- Unit-test path/branch validation, command construction, metadata transitions, script candidate resolution, and status reconciliation.
- Cover setup failure, interrupted setup, missing directories, externally removed worktrees, existing branches, branch already checked out elsewhere, source dirtiness, dirty close, and repeated/idempotent actions.
- Verify session action conditions and action displays through the production frontend SDK adapter.
- Run relevant package-local tests and default-config validation; run hosted suites only with their explicit markers and credentials.