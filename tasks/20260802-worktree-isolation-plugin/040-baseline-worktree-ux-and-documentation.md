# Baseline Worktree UX, Default Integration, and Documentation

Expose the backend as a complete plugin-driven user workflow, enable it in the appropriate default runtime, and provide deterministic public-boundary coverage plus a credential-free manual test path.

Parent Task: tasks/20260802-worktree-isolation-plugin/000-main.md

Depends On: tasks/20260802-worktree-isolation-plugin/030-worktree-plugin-backend.md

## Requirements checklist

- [ ] Session UI conditionally exposes appropriate open, status, close, reopen, and safe-cleanup actions from persisted worktree state.
- [ ] Action displays expose a copyable absolute path, branch, source repository, setup progress/result, dirty warning, close outcome, and recovery guidance.
- [ ] The first-party plugin is packaged and integrated into default configuration without hardcoding its semantics into mobile, desktop, or terminal clients.
- [ ] The workflow is usable through the generic HTTP action API and production frontend SDK/action adapters.
- [ ] A user can manually exercise creation, editing, committing, closing, merging, and reopening from a normal checkout without test-only behavior.
- [ ] Documentation clearly states the non-security threat model and safe data-retention behavior.
- [ ] Baseline UX does not yet add model-visible transition reminders or change existing absolute-path tool guidance.

## Supporting details

- Session-aware application UI schema and generic action conditions/dialogs already support this workflow.
- Generic displays support copy-text and follow-up run-action controls. A new local-folder-opening frontend capability is out of scope.
- Asynchronous setup needs status refresh and a truthful pending/failed display. Do not make frontends infer plugin metadata.
- Stable test identifiers should exist on production action/dialog surfaces when native UI coverage needs them.

## Execution plan

Status: Draft

Define session actions and conditions directly in the application plugin. Use generic forms for optional branch selection/reopen choices, confirmations for close/cleanup, and generic displays for paths, progress, warnings, and next actions. Add the plugin to the bundled/default configuration and ensure UI aggregation works for sessions using every default agent family.

Exercise the production REST backend and frontend SDK adapter with a temporary Git repository. Add a concise manual walkthrough that uses the actual application and visible action surfaces. Keep optional context strategies absent or disabled so this milestone provides a clean baseline for later comparison.

### Implementation decisions and open questions

- "Open worktree" should default to creating a new branch; reopening the last owned branch should be an explicit choice/action to avoid surprising branch reuse.
- Close should default to switching back and attempting only safe clean removal. Its confirmation must explain dirty retention.
- Status should be available while setup is pending or failed; action conditions must not hide recovery.
- Present paths as text plus copy action. Do not add file-manager/editor launch behavior.
- Do not expose a force-cleanup control in baseline UI.

### Documentation

- Plugin user guide with screenshots or schema examples only where useful.
- Default-config reference for storage base, branch prefix, setup candidates, and operation settings.
- Manual workflow: clean source, dirty-source warning, create, edit externally, AI commit, close, AI merge, follow-up, reopen, and retained-dirty recovery.
- Troubleshooting for missing Git, invalid repository, setup failure, branch conflicts, externally removed directories, and restart recovery.

### Task checklist

- [ ] Define conditional action/UI schema.
- [ ] Add generic displays and progress/recovery actions.
- [ ] Integrate package and default configuration.
- [ ] Add REST plus frontend-adapter integration coverage.
- [ ] Add credential-free manual workflow.
- [ ] Complete user, config, and troubleshooting documentation.

### Requirement verification

- Retrieve session application UI schema before, during, and after worktree use and assert only valid actions are offered.
- Execute the full deterministic lifecycle through public HTTP actions and the production frontend SDK adapter, including setup status and dirty retention.
- Follow the manual guide from a clean local checkout and confirm external edits are visible to both user and session tools.

### Additional implementation verification

- Run plugin tests, application server tests, frontend SDK tests, default-config compilation, package/import validation, and relevant terminal/mobile action-rendering tests.
- Verify clients require no worktree-specific branching beyond generic action/display contracts.