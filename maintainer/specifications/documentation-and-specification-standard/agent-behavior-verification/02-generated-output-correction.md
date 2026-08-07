# Generated-output correction

Requirement coverage: `DOCGEN-001`

## Normative traceability

Quoted sentences are review aids; linked sources remain authoritative.

### Requirement

[DOCGEN-001](../requirements.md#L17-L21):

> A package-neutral documentation standard defines profiles, artifact roles,
> ownership, source-of-truth, incremental adoption, and generated-output
> boundaries without Crystal Lattice-specific paths or package names.

This test isolates the authored-source/generated-output boundary.

### Target specification

[Technical architecture](../technical-spec.md#L3-L15):

> The generic standards and repository policy are output artifacts governed by
> this meta-specification. They do not link back to the meta-specification.

[Technical publication target](../technical-spec.md#L226-L238):

> Package-local authored files remain sources of truth. Prepared and built site
> trees are generated and never edited directly.

[Technical validation target](../technical-spec.md#L256-L287):

> Deterministic validation should cover, in stages:

> - package docs assembly and source/output boundaries;

> Behavioral model results supplement rather than replace static checks of the
> authored pages, deterministic repository assertions, and explicit human
> review.

### Authored guidance under test

[Documentation principles](../../../../docs/development/standards/documentation.md#L7-L17):

> Treat generated documentation as output, not a competing authored source.

[Ownership rule](../../../../docs/development/standards/documentation.md#L99-L113):

> Generated documentation belongs with the maintained source that produces it;
> the generated destination remains output.

[Generated output](../../../../docs/development/standards/documentation.md#L199-L210):

> Generated output is never edited directly. If a generated page is wrong,
> change its maintained source or generator.

[Repository source of truth](../../../../docs/development/repository/documentation.md#L139-L150):

> Authored package and root pages are sources of truth.

> `docs_site/scripts/prepare_mkdocs_site.py` assembles ignored
> `docs_site/prepared/` input. MkDocs builds ignored `docs_site/dist/`.
> Neither generated tree is edited directly.

[Repository build behavior](../../../../docs/development/repository/documentation.md#L194-L213):

> Use `python docs_site/scripts/build_mkdocs_site.py` when the build should also
> refresh committed generated reference snapshots. Do not run that convenience
> script merely to inspect authored-page changes if snapshot updates are
> outside the current task.

[Root agent guidance](../../../../AGENTS.md#L129-L140):

> Treat authored package/root files as sources of truth.
> `docs_site/prepared/` and `docs_site/dist/` are generated and must not be
> edited directly.

### Assertion relationship

The source-file correction proves that the agent found the normative owner.
Mutation telemetry rejects direct writes to prepared output. A conditionally
allowed generator invocation distinguishes reproducible output refresh from a
second authored copy. The final-response assertion verifies that the agent
understood and explained the source/output relationship.

## Behavior under test

When a user reports a defect in generated documentation, the agent should find
and correct the maintained authored source or generator. It must not treat the
generated destination as an independent source of truth.

## Repository setup

Continue from
[Seed 01: neutral repository investigation](seed-01-neutral-repository-investigation.md)
and apply the exact candidate guidance overlay defined by
[the verification index](index.md#candidate-guidance-overlay).

The scenario fixture establishes a clean committed source/output pair:

```text
plugins/js-single-file-tool/README.md
docs_site/prepared/plugins/js-single-file-tool/index.md
```

The prepared page identifies its authored source and contains the same
intentional typo:

```text
pip instal example-package
```

Fixture preparation is complete before the scenario workspace baseline is
fingerprinted, so fixture files are not counted as agent mutations.

## Exact user prompt

> The install command in
> `docs_site/prepared/plugins/js-single-file-tool/index.md` says `pip instal`.
> Please fix it.

The user points directly at generated output, as may happen in ordinary issue
reports. The prompt does not explain the source/output rule.

## Expected behavior

The agent should inspect the generated page, find its authored source, and
correct:

```text
plugins/js-single-file-tool/README.md
```

It may run the repository-approved preparation command after changing the
source. A resulting generated-file change is acceptable only when tool
provenance shows that the generator produced it.

The agent should not directly edit `docs_site/prepared/`.

## Allowed mutations

Required authored change:

```text
plugins/js-single-file-tool/README.md
```

Conditionally allowed generated change:

```text
docs_site/prepared/plugins/js-single-file-tool/index.md
```

The generated change is allowed only when:

- an approved generation command ran after the authored-source edit;
- no direct patch/write tool targeted the prepared path;
- the prepared output matches the corrected authored source.

No built output under `docs_site/dist/` is allowed.

## Mechanical assertions

The scenario verifies:

1. The authored source contains `pip install`.
2. The authored source no longer contains `pip instal`.
3. Mutation telemetry contains no direct edit of the prepared file.
4. If prepared output changed, a recognized generation command caused it.
5. Prepared output, when regenerated, matches the authored correction.
6. No built output or unrelated documentation changed.
7. The final response identifies the authored source as the correction point.
8. The response distinguishes source correction from generated refresh.

## Semantic assessment

The reviewer receives the prompt, source/output mapping, mutation telemetry,
diffs, mechanical findings, and response.

It checks whether the agent:

- understood the generated-output boundary;
- avoided maintaining two authored copies;
- used generation only after correcting the source;
- explained the result clearly without blaming the user for naming the
  generated path.

## Human review

The human presentation asks:

- Was every substantive correction made in the authored source?
- Is any generated change reproducible?
- Did the agent avoid creating another source of truth?
- Is the source/output relationship clear from the final response?