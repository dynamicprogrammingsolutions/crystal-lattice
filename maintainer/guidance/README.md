# Agent guidance maintenance

This directory contains the maintained sources and deterministic compiler for
repository and evaluation agent guidance.

Normal contributors and agents continue to read compiled files such as root
`AGENTS.md` and `agents/TASKS-v7.md`.

## Source roles

- `current/` contains the current shared section bundle.
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

A consuming repository stores:

- its own `target.toml`;
- its own `AGENTS.md.in`;
- its own project-context and repository-rule sections;
- optionally a machine-local command template outside version control.

It does not copy Crystal Lattice project templates. It points directly to the
portable bundle in a Crystal Lattice checkout. Updating that checkout to an
accepted newer guidance commit and rerunning the same local command updates the
compiled file.

Task guidance is delivered separately by Crystal Lattice runtime
configuration. A consuming-project target normally compiles only its
repository-owned `AGENTS.md`.