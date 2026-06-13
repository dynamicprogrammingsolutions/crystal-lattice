# Build Command Guidance And Validation

Audit the repo’s documented build-command surfaces, packaging flows, and release-oriented helper commands, then define a cleaner, verified build-guidance story for contributors and maintainers. This task is about command guidance and validation first; if build implementation changes are needed, they should be split into `091+` follow-ups rather than mixed into the initial audit.

## Requirements checklist

- [ ] Inventory the major documented build-command surfaces across the repo.
- [ ] Identify where build guidance already exists and where it drifts from actual scripts or helper entrypoints.
- [ ] Define a practical command model for common build work versus release-oriented or infrastructure-heavy build work.
- [ ] Identify commands that are expensive, platform-specific, or dangerous to run casually and should be documented with stronger caveats.
- [ ] Decide whether any resulting work should be split into `091+` follow-up subtasks.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

## Why this task exists

The test-command story is now much clearer than the build-command story. Build and release guidance is spread across several places:

- `noxfile.py`
  - currently provides:
    - `build_bundle`
    - `install_prod_local`
    - `install_dev_local`
- `application/python/README.md`
  - documents binary builds, release flows, workflow validation, Docker validation, and nox commands
- workspace package scripts under `packages/frontend-sdk/package.json`
  - include several AWS build/status/down helper commands mixed into integration scripts

That means contributors still need a repo-wide fact check for what counts as:

- a normal local build command
- a package-specific build command
- a release-maintainer flow
- an infrastructure-backed or environment-heavy maintenance command

## Repo facts already verified

- `noxfile.py`
  - `build_bundle`
  - `install_prod_local`
  - `install_dev_local`
- `application/python/README.md`
  - documents `scripts/build_crystal_lattice_binary.py`
  - documents `nox -s build_bundle`
  - documents release workflow validation commands
- `packages/frontend-sdk/package.json`
  - mixes test integration commands with several AWS build/status/down helper scripts
- root `package.json`
  - currently has no scripts

## Suggested implementation steps

1. Inventory build/release/helper command entrypoints in:
   - `noxfile.py`
   - root and package-local docs
   - `package.json` / package-level scripts
   - notable build/release scripts referenced by docs
2. Classify commands into:
   - common local build commands
   - package-specific build commands
   - release-maintainer commands
   - infrastructure-backed or environment-heavy commands
3. Compare the documented guidance with the actual command entrypoints.
4. Decide whether the fixes are doc-only or whether there is enough drift to justify `091+` implementation subtasks.

## Likely files to inspect

- `noxfile.py`
- `README.md`
- `application/python/README.md`
- `package.json`
- `packages/frontend-sdk/package.json`
- release/build scripts under `scripts/`, `application/python`, `bridge-elixir`, and `cloud-orchestrator` as needed