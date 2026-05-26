# Editor Tasks And Run Configurations

Define and, if approved, implement shared VS Code tasks and IntelliJ run configurations for the most important development commands in this repo. This task should sit on top of the command model established by earlier cleanup work rather than inventing a parallel command surface.

## Requirements checklist

- [ ] Audit the current state of shared editor task/run-config support in the repo.
- [ ] Decide which development commands are important enough to expose as shared editor tasks or run configurations.
- [ ] Prefer canonical short commands from the settled command model rather than duplicating long raw command lines across editor configs.
- [ ] Keep the shared editor surface intentionally small and safe by default.
- [ ] Clearly label any expensive, gated, or infrastructure-backed commands if they are exposed at all.
- [ ] Avoid broadening tracked IDE state beyond the minimum files needed for shared tasks/run configurations.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/060-sdk-test-guidance-and-command-alignment.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/090-build-command-guidance-and-validation.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/100-root-package-json-maintainer-commands.md`

## Why this is a separate task

Editor integration is a consumer layer on top of the repo’s canonical command model.

It should not be mixed into:

- command-definition work in `100`
- broader build/test guidance work in `060` and `090`

If those earlier tasks decide the canonical entrypoints are:

- root `package.json` scripts
- `nox` sessions
- package-local `pytest` / `vitest` commands

then this task should wrap those chosen entrypoints rather than introducing a second set of raw commands that will drift.

## Repo facts already verified

### Current editor config state

- There is no shared `.vscode/` task or launch config in the repo today.
- A tracked `.idea/` directory exists, but there is no shared `.idea/runConfigurations/` layout currently present.

This means editor-task support is effectively unstructured right now.

### Likely command sources this task should wrap

Based on current repo state, shared editor tasks are likely to wrap commands coming from:

- root and package-local Python test commands settled by earlier cleanup tasks
- workspace package scripts under `packages/*/package.json`
- `noxfile.py`
- possibly root `package.json` scripts if task `100` introduces them

## Recommended initial shared command set

Start small. Good first candidates are:

- fast core Python tests
- fast application Python tests
- fast major provider-plugin Python tests
- key workspace-package test commands once task `060` settles them
- `nox -s build_bundle` or the chosen canonical local bundle-build command

Potentially optional, clearly labeled candidates:

- a hosted integration command slice
- a gated SDK integration slice
- a Docker-backed build validation command

These should only be added if the command model is already stable and the labels are explicit.

## Important guardrails

- Prefer editor configs that call short canonical commands such as:
  - `npm run ...`
  - `nox -s ...`
  - small package-local `pytest` / `vitest` commands
- Avoid duplicating long raw command lines in both VS Code and IntelliJ files when a single canonical wrapper exists.
- Keep IntelliJ sharing limited to `runConfigurations` rather than tracking broader user-specific `.idea` state.
- Keep expensive or billable commands out of the default quick-access set unless they are clearly marked.

## Suggested implementation steps

1. Revisit the command model produced by tasks `060`, `090`, and `100`.
2. Decide whether root `package.json` scripts, `nox`, or direct package commands are the canonical editor-facing entrypoints.
3. Choose a minimal shared editor command set.
4. Define the file strategy:
   - `.vscode/tasks.json`
   - `.vscode/launch.json` only if needed
   - `.idea/runConfigurations/` for shared IntelliJ configs
5. Keep the initial implementation intentionally small and expand only if the first set works well.

## Likely files to inspect

- `.idea/`
- `.vscode/` if it gets introduced
- `package.json`
- `noxfile.py`
- package-local `package.json` files under `packages/`
- task outputs from `060`, `090`, and `100`