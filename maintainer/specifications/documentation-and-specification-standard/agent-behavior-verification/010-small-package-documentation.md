# Small-package documentation

Requirement coverage: `DOCGEN-001`

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

Use the common neutral seed and candidate guidance overlay from
[the verification index](index.md).

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

> Please improve the documentation for `plugins/js-single-file-tool` so a
> first-time plugin author can configure it, try the `upper` tool, and verify
> that it works. Keep the scope to documentation.

This prompt intentionally does not identify the owning file or desired
documentation profile.

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