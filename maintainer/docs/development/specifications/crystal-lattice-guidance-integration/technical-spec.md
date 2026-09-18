# Crystal Lattice guidance integration technical specification

## Documentation routes

- `docs/development/documentation.md` is the reusable guide.
- `docs/development/crystal-lattice-documentation.md` maps package paths,
  plugin guidance, publication, migration, and repository exceptions.
- Package README and docs directories own package-facing material.
- `maintainer/docs/` owns cross-cutting maintainer concepts and interpreted
  evaluation results.

## Repository guidance

`maintainer/guidance/current/` owns portable sections. The Crystal Lattice
target adds package routes and maintainer entry points and compiles root
`AGENTS.md`. The source path, compilation hash, and runtime delivery are
recorded separately.

Canonical `agents/TASKS-v7.md` is synchronized byte-identically to the bundled
application copy. Its content is delivered through the task-enabled developer
message; it is not inferred from the filename.

## Publication and generated output

`docs_site/packages.toml` registers package documentation. Preparation assembles
maintained sources into `docs_site/prepared/`; build output lives under
`docs_site/dist/`. Generated directories are never edited directly. Navigation,
triggers, and compatibility routes remain repository integration concerns.

## Maintainer boundary

Maintainer concepts and results live under `maintainer/docs/`. Package-owned
framework and compiler specifications live with their packages. Cross-cutting
documentation guidance and this integration specification live under
`maintainer/docs/development/specifications/`.

## Evaluation

The documentation-guidance suite is a consumer of the reusable evaluation
framework. Scenario prompts and targets are suite inputs; frozen JSON is suite
evidence; dated Markdown reports live under
`maintainer/docs/evaluations/documentation-guidance/`.
