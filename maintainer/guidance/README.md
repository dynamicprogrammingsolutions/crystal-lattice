# Agent guidance maintenance

This directory contains the maintained sources and deterministic compiler for
repository and evaluation agent guidance.

Normal contributors and agents continue to read compiled files such as root
`AGENTS.md` and `agents/TASKS-v7.md`.

Documentation:

- [Documentation index](docs/index.md)
- [Quickstart](docs/quickstart.md)
- [Development](docs/development/index.md)

## Source roles

- `current/` contains the current shared Documentation, Requirements, Testing,
  and task-guidance sections.
- `candidates/` contains explicitly selected source variations.
- `targets/` contains Crystal Lattice's own project base and local sections.
- Every consuming repository owns its own target templates and local sections.
- `compiler.py` assembles one bundle and one target and records exact input and
  output hashes.

## Commands

Check that current Crystal Lattice outputs match their source:

```bash
python -m maintainer.guidance check \
  --bundle /absolute/path/to/ai-agent-platform/maintainer/guidance/current \
  --target /absolute/path/to/ai-agent-platform/maintainer/guidance/targets/crystal-lattice \
  --destination /absolute/path/to/ai-agent-platform
```

Compile a candidate into a temporary directory:

```bash
python -m maintainer.guidance compile \
  --bundle /absolute/path/to/ai-agent-platform/maintainer/guidance/candidates/root-requirements-testing-v2 \
  --target /absolute/path/to/consumer-project/maintainer/guidance/target \
  --destination /absolute/path/to/consumer-project/tmp/guidance-preview \
  --lock /absolute/path/to/consumer-project/tmp/guidance-preview.lock.json
```

The compiler script, bundle directory, target directory, and destination may
all be in different filesystem locations. A developer may keep the complete
absolute-path command in a machine-local script or shell configuration outside
either repository.

To compile a historical guidance version, check out that Crystal Lattice
revision or use a separate worktree and point `--bundle` at it. The content
hash remains stable across absolute locations.

Writing repository outputs is a manual post-approval operation:

```bash
python -m maintainer.guidance write \
  --bundle /absolute/path/to/ai-agent-platform/maintainer/guidance/current \
  --target /absolute/path/to/ai-agent-platform/maintainer/guidance/targets/crystal-lattice \
  --destination /absolute/path/to/ai-agent-platform
```

Do not run `write` merely because a candidate test passes. First merge the
approved candidate sections into `current/`, then compile current source.

## Consuming repositories

Known consumers:

- `dprog-website` (git): vendored guidance under `maintainer/guidance/`,
  outputs `AGENTS.md` and `TASKS-v7.md`.
- IOCharts (tracked through its `frontend` repository): vendored guidance
  under `frontend/.workspace-root/maintainer/guidance/`, compiles the
  workspace-root `AGENTS.md` and its tracked mirror, plus `TASKS-v7.md`.

A consuming repository owns:

- its own `target.toml`, templates, and project-context/repository-rule
  sections;
- a `sync.toml` describing which portable sections and shared doc files it
  consumes;
- its compile wrapper and delivery decisions.

Portable (shared) bundle content: the `documentation`, `requirements`, and
`testing-strategy` sections, the `tasks-v7` section when the consumer keeps a
repository copy, and the project-independent authoring guide
`docs/development/documentation.md`. The `root-testing` section is
Crystal Lattice-specific and is not portable. The consuming target keeps only
its project-specific routes, paths, and exceptions; the consuming runtime
determines how compiled files are delivered and what authority they have.

### Consumer synchronization

`consumer_sync.py` is the shared synchronization tool. Each consumer vendors
it unchanged next to `compiler.py` and describes itself in `sync.toml`
(consumer id, portable sections, shared files with destination roots). From
the consumer, refresh against a Crystal Lattice checkout:

```bash
python <consumer-guidance-dir>/consumer_sync.py \
  /absolute/path/to/ai-agent-platform [--check]
```

The sync refreshes the vendored compiler and sync tool, the configured
sections, regenerates the vendored `current/bundle.toml`, copies configured
shared doc files to every destination root, and records the source revision
and hashes in `sync-lock.json`. Recompile the consumer outputs afterwards
with its compile wrapper.