# CLI maintainer scripts

This directory contains application-owned entry points for building,
installing, releasing, and smoke-testing the `crystal-lattice` command.

Use the root npm commands rather than invoking these files directly:

```bash
npm run build:cli:archive
npm run build:cli:optimized
npm run install:cli:archive
npm run install:cli:dev
npm run test:cli:source-install
npm run test:cli:archive
npm run test:cli:default-install
```

The root `scripts/` directory retains repository-wide utilities and the
cross-runtime packaging primitives used by cloud-orchestrator source bundles
and shipped runtime packages. Package-local maintainer scripts in this
directory are excluded from shipped application trees. The public
`install.sh` is published as a standalone file.

See
[CLI distribution implementation and verification](../docs/development/cli-distribution.md)
for ownership, isolation, and verification details.