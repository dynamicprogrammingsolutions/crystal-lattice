# Documentation-guidance suite specification

## Purpose

Verify how supported agents apply documentation, specification, requirement,
testing, routing, and task guidance in realistic repository tasks.

## Ownership

The suite owns its seeds, scenarios, semantic targets, guidance-source
adapters, deterministic assertions, semantic and pairwise evaluators, freezing
scripts, and frozen machine-readable evidence. It uses `agent_eval` but does
not define the reusable framework contract.

## Instruction provenance

Every case identifies the maintained source and effective delivery separately.
Direct system/developer injection, compiled repository guidance, workspace
availability, routed file reads, and user prompts are distinct test modes.
Discovery claims require read evidence.

## Crystal Lattice runner fidelity

All Crystal Lattice-backed cases use a reduced projection of the ordinary
default config while preserving the selected Codex or Claude system-message
mixin, production system-message feature, and matching default tool package.
Scenario `AGENTS.md` is read from the workspace by the normal helper.
Canonical task guidance is read from the config directory only when
`include_tasks` is enabled.

The preflight checks both message compilation and tool-call compatibility:
Codex exposes an array-valued `shell.command`, and Claude exposes a
string-valued `Bash.command`.

Suite-specific direct injection is permitted only for a case explicitly
testing or preserving that delivery. It is not the normal runner used for
guidance acceptance.

Semantic and pairwise stages require complete, repeat-pinned, deterministically
valid upstream records. A finished process with failed findings does not
authorize its dependent stage.

## Result boundaries

Process completion is not semantic completion. A producer result is usable only
when its expected response or file exists. Semantic and pairwise results count
only when their structured records validate. Human-readable interpretation is
published under `maintainer/docs/evaluations/`.
