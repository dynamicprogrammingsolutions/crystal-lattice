# Seed 01: neutral repository investigation

## Purpose

This seed performs the expensive repository investigation once without the
candidate documentation-standard guidance. Behavioral tests reuse its immutable
conversation snapshot while receiving fresh workspaces and their own candidate
guidance overlays.

The seed establishes repository familiarity, not documentation-policy
understanding. It must not expose the rules whose effectiveness the child tests
measure.

## Normative traceability

Quoted text below is included for review convenience. The linked requirement
and specifications remain authoritative.

### Documentation-standard verification requirement

[DOCVAL-005](../requirements.md#L66-L74):

> Programmatic behavioral tests exercise every `DOCGEN-*` and `DOCREP-*`
> instruction requirement through a neutral cached repository investigation
> and clean continuations, preserving canonical artifacts for human review.

### Agent-evaluation requirements

[AEVAL-009 and AEVAL-010](../../agent-evaluation-framework/requirements.md#L21-L22):

> A run can continue from an immutable hash-verified parent snapshot in a
> compatible environment and clean workspace while preserving parent and
> restore/rebase provenance.

> Explicit cache keys reuse compatible expensive runs using environment,
> workspace, parent, and schema fingerprints and reject incompatible or
> partial cache entries.

[AEVAL-016 and AEVAL-017](../../agent-evaluation-framework/requirements.md#L28-L29):

> The first consumer tests exercise all `DOCGEN-*` and `DOCREP-*`
> documentation-standard instruction requirements through cached repository
> context and clean continuations.

> Real-model artifacts preserve exact instruction, prompt,
> model/configuration, parent seed, response, tool, error, projection,
> assessment, and presentation provenance while AI scoring remains supporting
> evidence rather than human verification.

### Evaluation-framework target

[First consumer: documentation-standard instructions](../../agent-evaluation-framework/technical-spec.md#L726-L774):

> The initial suite uses `CrystalLatticeEnvironment` and a pinned repository
> baseline that does not expose the candidate instruction through the warm-up
> context. One guidance-neutral investigation may feed multiple clean
> continuations.

> The candidate guidance is supplied through the normal AGENTS and routed-file
> mechanism. User prompts describe ordinary work and do not repeat the rules
> being evaluated.

## Repository baseline

The default pinned baseline is:

```text
c00d14954a503b96a6e2bbdb90a4c31c8af785e1
```

This commit immediately predates the documentation-standard task,
meta-specification, authored generic standards, and repository policy. The
seed therefore cannot discover the candidate rules from those later files.

The baseline still contains the real package and documentation layout needed
for a meaningful investigation.

## Exact seed prompt

> Please inspect this repository and summarize its major package boundaries,
> existing documentation entry points, generated documentation locations, and
> where package-specific development guidance is found. Focus on current
> repository facts. Do not propose changes and do not modify files.

The prompt does not mention the candidate standard, expected package profiles,
specification workflow, or test scenarios.

## Request profile

The seed uses the normal Crystal Lattice request and tool loop with:

```python
{
    "include_tasks": False,
    "skills_enabled": False,
    "mcp_enabled": False,
    "web_search_enabled": False,
}
```

Additional controls:

- mutation-call limit: zero;
- workspace: clean pinned Git worktree;
- candidate overlay: absent;
- maintainer specification injection: absent;
- task-guidance injection: absent;
- network-dependent repository research: absent;
- output limit: sufficient for a concise repository summary.

The model may use read-only repository tools.

## Cache identity

The cache key and compatibility fingerprint include:

- repository remote identity;
- exact baseline commit;
- seed prompt hash;
- request-profile hash;
- Crystal Lattice environment/configuration fingerprint;
- subject agent and model identity;
- snapshot schema and codec versions;
- workspace schema;
- absence of candidate-guidance hashes.

Changing any of these inputs produces a new seed rather than silently reusing
an incompatible snapshot.

## Seed assertions

Before the seed can be reused, deterministic checks verify:

1. The workspace began at the exact pinned commit.
2. The workspace remained clean.
3. No mutation-classified tool call occurred.
4. No candidate guidance path or content hash was supplied.
5. No task or maintainer specification was injected.
6. The final response describes observed repository facts without proposing a
   documentation reorganization.
7. The snapshot is present, hash-verified, and restorable.
8. Canonical artifacts contain the prompt, response, configuration
   fingerprint, tool summary, workspace status, and snapshot identity.
9. Raw artifacts preserve the full session and environment evidence allowed by
   the retention policy.

## Continuation contract

Every child test:

1. Restores the immutable seed snapshot.
2. Creates a fresh workspace from the compatible baseline.
3. Rebases workspace paths in restored Crystal Lattice state.
4. Applies its exact candidate AGENTS/routed-file overlay before the scenario
   request is compiled.
5. Records the seed run ID, snapshot hash, baseline, and rebase evidence.
6. Keeps the parent seed artifacts and workspace unchanged.

Fixture-specific files are established and fingerprinted before the child
request begins. They are not counted as model mutations.

## Human review

The seed presentation should be brief. It asks:

- Did the seed learn useful repository facts without receiving the candidate
  rules?
- Is the baseline early enough to prevent instruction leakage?
- Was the seed entirely read-only?
- Is its snapshot safe and useful for all child scenarios that reference it?