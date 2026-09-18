## Crystal Lattice documentation routing

Put package-user documentation under `<package>/docs/` and current internals,
architecture, testing, and specifications under
`<package>/docs/development/`. Keep root `docs/` for project-wide guidance,
cross-package architecture and behavior, and site entry points.

Never edit `docs_site/prepared/` or `docs_site/dist/` directly. Publication and
site-generation commands are maintained in the Crystal Lattice conventions.

Before materially changing documentation structure, also read
`docs/development/crystal-lattice-documentation.md`. When changing this
guidance, task guidance, publication rules, or their validation, read:

- `maintainer/specifications/documentation-and-specification-standard/index.md`
- `maintainer/specifications/documentation-and-specification-standard/requirements.md`
