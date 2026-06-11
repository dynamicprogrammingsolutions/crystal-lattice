# Root Package.json Maintainer Commands

Decide whether the repo-root `package.json` should expose a curated set of maintainer-oriented scripts for important test, build, and setup workflows, and implement that script surface if it is justified. This task should come after the broader command-guidance work is clear enough that root scripts would encode a stable, intentional command model rather than an intermediate state.

## Requirements checklist

- [ ] Audit the current role of the repo-root `package.json`.
- [ ] Decide whether adding root maintainer scripts is warranted or whether the workspace manifest should stay minimal.
- [ ] If scripts are added, keep the root script surface small and intentional.
- [ ] Consider whether root scripts should cover important test commands, build commands, and environment/setup bootstrap commands.
- [ ] Ensure any proposed root scripts are consistent with the guidance settled by the related test/build tasks.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/060-sdk-test-guidance-and-command-alignment.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/090-build-command-guidance-and-validation.md`

## Why this task exists

The repo-root `package.json` is currently only a workspace manifest:

- `package.json`
  - `name`
  - `private`
  - `license`
  - `workspaces`

It has no root-level scripts today.

If the broader cleanup settles on a clearer command story for:

- SDK/package tests
- build helpers
- setup/bootstrap flows

then the root workspace manifest may become a good place for a small set of discoverable maintainer commands. But that should be a deliberate decision, not a default assumption.

## Questions this task should answer

- Should the root `package.json` remain a minimal workspace manifest only?
- If not, which commands are important enough to expose at the root?
- Should root scripts wrap:
  - workspace package tests
  - binary build helpers
  - repo bootstrap/setup commands
  - documentation checks
- When is `nox` the better canonical entrypoint versus npm workspace scripts?

## Suggested implementation steps

1. Revisit the command model produced by tasks `060` and `090`.
2. Decide whether root-level npm scripts add real value or just duplicate other entrypoints.
3. If scripts are justified, propose a minimal script set and explain why each command belongs at the root.
4. Validate that the chosen scripts do not conflict with:
   - `noxfile.py`
   - package-local scripts
   - documented Python-first workflows
5. If implementation is approved later, keep the script surface intentionally small and maintainable.

## Likely files to inspect

- `package.json`
- `package-lock.json`
- `noxfile.py`
- task outputs from `060` and `090`
- root and package docs that would reference any new root scripts