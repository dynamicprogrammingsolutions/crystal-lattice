# Shared Workspace Setup Contract

Define and implement a portable project setup-hook contract that can prepare both cloud-agent workspaces and local Git worktrees without coupling the worktree plugin to private cloud-plugin internals.

Parent Task: tasks/20260802-worktree-isolation-plugin/000-main.md

## Requirements checklist

- [ ] A project can select a setup script using a string or ordered fallback list resolved relative to the original project root.
- [ ] The selected setup script receives `WORKING_DIR` as the portable active workspace, plus `SESSION_ID`; cloud and worktree runtimes may provide additional aliases.
- [ ] Existing `.cloud-agent/install-cloud` hooks and project cloud profile overrides remain compatible.
- [ ] Cloud and worktree callers share the reusable script-candidate/path-resolution contract rather than maintaining divergent implementations.
- [ ] Setup failures retain bounded actionable diagnostics without printing secrets.
- [ ] The contract and migration guidance are documented and tested through both a cloud-compatible caller and a local-worktree fixture.

## Supporting details

- Cloud profile script fields already accept a string or ordered list, resolve project-file paths from the project root, and retain inherited candidates after project candidates.
- Cloud runtimes already set `WORKING_DIR` to the cloud workspace even though authoring documentation currently emphasizes `CLOUD_WORKSPACE_DIR`.
- A cloud install hook may depend on container-only tools. Projects must be able to provide a local-specific candidate before a shared fallback.
- This subtask defines setup selection and execution inputs. Worktree operation state and asynchronous orchestration belong to subtask `030`.

## Execution plan

Status: Draft

Extract or introduce the smallest shared helper for normalized script candidates, placeholder expansion, project-relative resolution, executable-file validation, and bounded execution diagnostics. Adapt cloud profile resolution to consume it without changing selected-profile behavior. Define the worktree-facing setup configuration shape and stable environment names, but leave its application-plugin orchestration to the backend subtask.

Update the repository's `.cloud-agent/install-cloud` example and authoring guidance to use `WORKING_DIR` where the script is portable. Keep `CLOUD_WORKSPACE_DIR` documented as a cloud-specific alias and preserve compatibility for existing scripts.

### Implementation decisions and open questions

- Shared helper ownership should be neutral. Recommendation: place it in the application layer or a small shared plugin utility package already available to both plugins, not inside either plugin package.
- Candidate values should remain strings or ordered lists of strings; do not add a dependency/package DSL.
- Missing standard optional hooks may resolve to no setup action, while explicitly configured missing paths should fail clearly.
- Execution should use argument-array subprocess invocation of the executable script, with cwd and `WORKING_DIR` set to the active workspace.

### Documentation

- Update `plugins/cloud-agent-app/docs/cloud-script-authoring.md`.
- Update cloud-agent README contract text if environment semantics change.
- Document worktree setup candidates, environment variables, relative-path base, portability guidance, and local/cloud divergence examples.

### Task checklist

- [ ] Define neutral setup script types and resolution semantics.
- [ ] Implement shared resolution helper.
- [ ] Adapt cloud profile resolution without behavior regression.
- [ ] Add worktree-facing configuration contract.
- [ ] Add cloud and local fixture coverage.
- [ ] Update hook examples and documentation.

### Requirement verification

- Resolve the same portable hook from a project-relative candidate for cloud and worktree callers and assert that it observes the correct `WORKING_DIR`.
- Verify ordered fallback, inherited cloud candidate behavior, optional missing defaults, and explicit missing-path failure.
- Run a fixture hook that records only non-secret contract fields and assert cloud-specific and worktree-specific aliases do not change portable behavior.

### Additional implementation verification

- Test placeholder expansion, paths containing spaces, non-executable files, nonzero exits, stdout/stderr truncation, and environment precedence.
- Run the existing cloud-agent profile and plugin test slices that cover install-script resolution and transfer bundle creation.