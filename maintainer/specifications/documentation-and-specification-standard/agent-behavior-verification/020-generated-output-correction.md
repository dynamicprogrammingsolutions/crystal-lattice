# Generated-output correction

Requirement coverage: `DOCGEN-001`

## Behavior under test

When a user reports a defect in generated documentation, the agent should find
and correct the maintained authored source or generator. It must not treat the
generated destination as an independent source of truth.

## Repository setup

Use the common neutral seed and exact candidate guidance overlay.

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