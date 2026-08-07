# Small-package documentation

Requirement coverage: `DOCGEN-001`

## Normative traceability

Quoted sentences below are review aids. The linked requirement,
meta-specification, and authored guidance remain authoritative.

### Requirement

[DOCGEN-001](../requirements.md#L17-L21):

> A package-neutral documentation standard defines profiles, artifact roles,
> ownership, source-of-truth, incremental adoption, and generated-output
> boundaries without Crystal Lattice-specific paths or package names.

This test exercises the profile, artifact-role, ownership, source-of-truth, and
incremental-adoption portions. Generated-output behavior is exercised
separately by
[Generated-output correction](02-generated-output-correction.md).
Package-neutral wording is checked statically against the authored generic
page.

### Target specification

[Product-specification purpose and ordinary users](../product-spec.md#L3-L23):

> The repository needs documentation and specification rules that are easy to
> apply during ordinary work, precise enough for agents, reusable outside this
> project, and maintainable without exposing internal workflow machinery to
> every reader.

> - decide where documentation belongs;
> - identify the package or shared scope that owns a contract;

[Product goals and non-goals](../product-spec.md#L64-L95):

> Keep the process proportional and avoid placeholder documentation.

> Requiring every package to create the full documentation structure
> immediately is a non-goal.

[Technical generic boundary](../technical-spec.md#L47-L75):

> - documentation profiles and artifact roles;
> - package-local ownership;
> - anti-duplication and discoverability;

[Technical migration target](../technical-spec.md#L240-L250):

> Adoption is incremental:

> - do not create empty package trees or placeholder quickstarts;
> - defer uncertain pages rather than reconstructing broad undocumented
>   behavior;

### Authored guidance under test

[Documentation principles](../../../../docs/development/standards/documentation.md#L7-L17):

> Author documentation beside the package or subsystem that owns it.

> Treat generated documentation as output, not a competing authored source.

> Adopt the structure incrementally. Do not create empty pages or reconstruct
> unfamiliar systems merely to complete a directory shape.

[Small-package profile](../../../../docs/development/standards/documentation.md#L51-L63):

> A concise package entry point may be sufficient when it already covers
> purpose, supported use, installation or loading, basic verification, and
> links to inherited contributor guidance.

> Add package-local agent guidance only when the package differs from its
> parent. Add a documentation index and quickstart when the package entry point
> can no longer provide a clear first-use path.

[Artifact roles](../../../../docs/development/standards/documentation.md#L83-L97):

> | Package entry point | Purpose, installation, first use/build/test, and
> links |

> Keep package entry points concise. Move detail into focused pages once the
> entry point becomes difficult to scan.

[Ownership](../../../../docs/development/standards/documentation.md#L99-L116):

> Content about one package's supported behavior belongs with that package.

> A shared user-documentation domain is appropriate when the audience consumes
> a common extension or integration surface across many packages.

[Adoption](../../../../docs/development/standards/documentation.md#L212-L222):

> Apply the standard prospectively and when documentation is touched.

> Do not create placeholder quickstarts, nearly empty indexes, copied
> boilerplate that claims unsupported behavior, or speculative package
> baselines reconstructed from unfamiliar code.

[Crystal Lattice small-plugin mapping](../../../../docs/development/repository/documentation.md#L26-L28):

> Small plugins and internal packages may remain README-only when inherited
> guidance and that README provide a complete route. Do not add empty AGENTS,
> index, or quickstart pages.

[Plugin profile and shared-domain rules](../../../../docs/development/repository/documentation.md#L65-L86):

> | Individual `plugins/*` packages | README-first by default; add local
> guidance/docs when package needs exceed inherited rules |

> This is a profile classification, not a requirement to generate every
> missing file in one change.

[Shared plugin documentation](../../../../docs/development/repository/documentation.md#L105-L124):

> One plugin's internal behavior does not become a shared plugin contract by
> being used as an example.

> Individual plugins inherit `plugins/AGENTS.md` unless package-specific rules
> justify a local AGENTS file.

[Root agent routing](../../../../AGENTS.md#L118-L154):

> Start package work by reading its `README.md`, nearest `AGENTS.md`, and
> `docs/index.md` when present.

> Keep README files concise: purpose, installation, first use/build/test, and
> pointers to detailed documentation.

### Assertion relationship

The changed-path allowlist verifies package ownership and the README-only
profile. Required README concepts verify the entry-point role. Rejection of a
new AGENTS/docs tree verifies proportionality and incremental adoption.
Shared-doc link review verifies that package-specific behavior stays local
while reusable plugin guidance remains shared.

## Behavior under test

An agent should apply the small-package profile proportionally:

- keep documentation with the package that owns the behavior;
- use the existing README as purpose, configuration, first-use, and
  verification entry point;
- inherit parent agent guidance when no package-specific rule is needed;
- link shared plugin guidance instead of copying a broad contract;
- avoid placeholder indexes, quickstarts, development pages, and references;
- improve the touched documentation without reconstructing an unnecessary
  package baseline.

The generic standard's package-neutral wording is verified statically and by
human review, not by asking the model to author generic guidance.

## Repository setup

Continue from
[Seed 01: js-single-file-tool documentation investigation](seed-01-js-single-file-tool-documentation.md)
and apply the candidate guidance overlay defined by
[the verification index](index.md#candidate-guidance-overlay).

The task targets the real baseline package:

```text
plugins/js-single-file-tool/
├── README.md
└── UpperTool.ts
```

The continuation receives the exact current:

```text
AGENTS.md
plugins/AGENTS.md
docs/development/standards/*
docs/development/repository/*
```

The original README is retained as evidence. No fixture-specific instruction
is added to `AGENTS.md`.

## Exact user prompt

> Please implement the documentation improvements identified in the
> investigation. Keep the scope to documentation.

The seed already establishes concrete configuration, first-use, verification,
and source facts. This branch prompt intentionally does not identify the owning
file or desired documentation profile.

## Expected behavior

The agent should inspect the package and shared plugin guidance, then improve:

```text
plugins/js-single-file-tool/README.md
```

The README should remain concise while providing:

- package purpose and the `upper` tool's behavior;
- at least one supported configuration example;
- a complete first-use example with input and expected uppercase output;
- a practical verification path grounded in repository-supported behavior;
- links to relevant shared Node-tool/plugin-loading guidance where useful.

The agent should not invent unsupported build, package installation, test, or
publication commands.

## Allowed mutations

Expected allowlist:

```text
plugins/js-single-file-tool/README.md
```

Any additional mutation is a deterministic failure pending explicit review.

In particular, the test rejects:

```text
plugins/js-single-file-tool/AGENTS.md
plugins/js-single-file-tool/docs/**
plugins/js-single-file-tool/UpperTool.ts
plugins/docs/**
docs/**
docs_site/prepared/**
docs_site/dist/**
```

Read-only access to package code and shared plugin documentation is allowed.

## Mechanical assertions

The scenario verifies:

1. Exactly one authored file changed and it is the package README.
2. No implementation file changed.
3. No package-local AGENTS, docs index, quickstart, development page, or
   reference was created.
4. No root/shared/generated documentation was modified.
5. The README names `upper` and explains its uppercase result.
6. The README contains a supported local-file or `node:` configuration.
7. The README contains a first-use input and expected output.
8. The README provides an honest verification path.
9. Relative links added by the agent resolve.
10. The final response names the changed README and accurately reports
    verification performed or not performed.

Content checks use concept groups and supported-path checks rather than exact
prose.

## Semantic assessment

The assessment projection contains:

- requirement ID;
- exact prompt;
- guidance hashes;
- original and updated README;
- changed paths;
- mechanical findings;
- final assistant response.

The reviewer scores:

- proportionality of the README-only decision;
- first-success completeness;
- technical accuracy;
- appropriate use of shared links rather than duplicated contracts;
- concision and lack of filler;
- honesty of the reported verification.

The assessment does not judge the quality of the framework or the model.

## Human review

The human presentation asks:

- Was README-only the right profile for this package?
- Can a first-time plugin author configure and try the tool?
- Are any commands or claims unsupported?
- Did the agent avoid unnecessary package documentation structure?
- Did it keep plugin-specific behavior with the plugin?