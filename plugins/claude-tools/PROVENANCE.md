# Claude Tools Provenance

Claude Tools is an independently developed Crystal Lattice compatibility
implementation. It is not affiliated with, sponsored by, or endorsed by
Anthropic.

Claude and Claude Code are product and trademark names belonging to Anthropic.
They are used in this repository only to identify the software and behavior
with which Claude Tools is designed to interoperate.

## How the compatibility assets were produced

The tool schemas, result shapes, prompt behavior, investigation notes, and
normalized fixtures in this subtree were produced through AI-assisted
observation and normalization of Claude Code behavior exposed through publicly
visible interfaces. The investigation harnesses run controlled cases, observe
the resulting externally visible API traffic and output, remove volatile or
private data, and retain implementation-relevant normalized records.

These normalized fixtures are generated Crystal Lattice project materials.
They are not raw Claude Code logs or a distribution of the Claude Code
application. Together with the independently authored implementation,
investigation scripts and notes, tests, and system-message compatibility
assets in this subtree, they are distributed under the Apache License,
Version 2.0.

Literal references to Claude Code and observed identity, schema, prompt, or
result strings may be retained when they are needed to describe or test
compatibility. Their presence does not indicate affiliation, endorsement, or
ownership by Anthropic.

## Excluded material

Raw investigation logs, authentication material, local settings, and other
run-specific private data are not part of the committed compatibility corpus.
They must remain under ignored local investigation directories and must not be
committed.

See [LICENSE](LICENSE) for the full Apache-2.0 terms.