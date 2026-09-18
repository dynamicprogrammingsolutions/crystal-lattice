# Seed 01: js-single-file-tool documentation investigation

## Purpose

This seed performs one narrow factual investigation that can feed several
documentation-task branches for `plugins/js-single-file-tool`.

It is deliberately concrete enough for a small inexpensive model. It does not
ask for general repository understanding or for documentation-structure
decisions controlled by the candidate guidance.

The same cached seed may be reused while comparing multiple revisions or
delivery variations of the documentation guidance. Candidate guidance is added
only to child continuations and is not part of seed compatibility.

## Normative traceability

Quoted text is included for review convenience; linked sources remain
authoritative.

[DOCVAL-005](../../../../docs/development/specifications/crystal-lattice-guidance-integration/requirements.md):

> Programmatic behavioral tests exercise every `DOCGEN-*` and `DOCREP-*`
> instruction requirement through narrow guidance-neutral cached task-specific
> base runs and clean continuations, preserving canonical artifacts for human
> review.

[Agent-evaluation first-consumer target](../../../docs/development/specifications/framework/technical-spec.md#L726-L775):

> A guidance-neutral seed may feed multiple closely related clean
> continuations and may be reused across candidate-guidance revisions.

> The candidate guidance is supplied through the normal AGENTS and routed-file
> mechanism. User prompts describe ordinary work and do not repeat the rules
> being evaluated.

## Repository setup

The seed uses the pinned repository baseline:

```text
c00d14954a503b96a6e2bbdb90a4c31c8af785e1
```

Relevant baseline files include:

```text
plugins/js-single-file-tool/README.md
plugins/js-single-file-tool/UpperTool.ts
plugins/AGENTS.md
plugins/docs/node-tool-plugins.md
plugins/docs/plugin-packaging-and-loading.md
```

The focused test fixture appends one small `Verify npm` block with the typo
`npm --vesion` to the package README before the seed runs.
That source state is shared by every Seed 01 branch so the cached investigation
does not become stale when generated-output pressure is added later.

The candidate root AGENTS and documentation-standard pages do not exist at the
pinned baseline and are not overlaid during the seed.

## Exact seed prompt

> Please investigate `plugins/js-single-file-tool` as preparation for a
> documentation-only follow-up. Compare its README configuration, first-use,
> and verification instructions with `UpperTool.ts` and the relevant shared
> Node tool documentation. Report factual gaps or unsupported claims and name
> the files containing the relevant facts. Do not modify files and do not
> recommend a documentation structure.

The prompt asks for facts needed by several later tasks without asking the seed
model to decide whether the package should use README-only documentation,
package docs, shared docs, or generated output. Those decisions remain under
test after the candidate guidance is added.

## Request profile

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
- repository scope: the named plugin and directly relevant shared docs;
- candidate guidance overlay: absent;
- task-guidance injection: absent;
- output: concise factual comparison rather than a broad repository summary.

## Seed assertions

The cached seed is reusable only when:

1. No file changed and no mutation-classified tool call occurred.
2. The response identifies the README and `UpperTool.ts`.
3. The response compares configuration claims with supported loader forms.
4. The response identifies missing or weak first-use/verification information.
5. Unsupported claims, if found, are tied to source evidence.
6. The response does not propose README-only, a docs tree, a shared-doc edit,
   or a generated-output policy.
7. Candidate guidance paths and hashes are absent.
8. The immutable snapshot and canonical/raw provenance are complete.

## Current branches

- [Small-package documentation](01-small-package-documentation.md): implement
  the documentation improvements using the candidate guidance.
- [Generated-output correction](02-generated-output-correction.md): add a
  branch-specific prepared-output fixture and correct a reported generated-page
  typo through the proper authored source.
- [Failed generated refresh](16-failed-generated-refresh.md): use the same
  source/output pair with a recognized generator that fails, verifying safe
  partial completion without a direct generated-file fallback.
- [Shared plugin-authoring boundary](18-shared-plugin-authoring-boundary.md):
  split plugin-specific usage from reusable Node-tool authoring guidance.

## Reuse across guidance revisions

The seed cache fingerprint includes the baseline, narrow prompt, model,
request profile, environment, and snapshot schema. It intentionally excludes
candidate guidance hashes.

Each branch records its own exact AGENTS/routed-file overlay and guidance hash.
This permits the same factual investigation to compare current, proposed, or
delivery-variant guidance without paying for the investigation again.