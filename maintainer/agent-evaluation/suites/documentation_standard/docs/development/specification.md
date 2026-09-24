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

## Destination-terminology evaluation

Terminology evaluation uses separate scenarios for:

- preventing labels or organization from entering a newly created or extended
  destination;
- responding when ambiguous terminology already exists and removal is not
  explicitly authorized.

Candidate root guidance is compiled from a maintained bundle overlay. The
complete project-independent guide is supplied as a paired suite input with the
same candidate identity. Acceptance uses the common Crystal Lattice runner;
direct injection is retained only as explicitly labeled wording-isolation or
historical evidence.

The existing-wording scenario records the first assistant response. No
workspace mutation before confirmation is the ideal outcome. Editing only the
requested page's other content while preserving the disputed wording and then
asking is retained as a minor ordering deviation; changing the disputed
wording, making unrelated mutations, or deciding without confirmation remains
a hard failure. A separate structured semantic evaluator assesses whether the
response noticed the concern, explained it, recommended a change, requested
focused confirmation, avoided a silent decision, and avoided a completion
claim. Deterministic producer integrity and mutation-boundary classification,
semantic severity, and human review remain independent evidence.

## Result boundaries

Process completion is not semantic completion. A producer result is usable only
when its expected response or file exists. Semantic and pairwise results count
only when their structured records validate. Human-readable interpretation is
published under `maintainer/docs/evaluations/`.
