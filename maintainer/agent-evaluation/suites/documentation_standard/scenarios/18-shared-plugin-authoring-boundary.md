# Test 18: shared plugin-authoring boundary

## Purpose

Verify that an agent places reusable Node-tool authoring guidance in
`plugins/docs/` while keeping one plugin's usage and behavior in that plugin's
README. The shared domain may use the plugin as an example, but must not turn
`UpperTool` behavior into a framework-wide contract.

## Normative traceability

[DOCREP-002](../../../../docs/development/specifications/crystal-lattice-guidance-integration/requirements.md):

> Repository policy defines `plugins/docs/` as shared plugin-authoring guidance
> while preserving ordinary ownership and specification rules for individual
> plugin packages and framework contracts.

[Repository-policy boundary](../../../../docs/development/specifications/documentation-guidance/technical-spec.md):

> The repository policy maps generic concepts to `plugins/docs/` as the shared
> plugin-authoring documentation domain and to individual plugin package
> ownership.

[Shared plugin documentation](../../../../../docs/development/crystal-lattice-documentation.md#L144-L166):

> `plugins/docs/` is the shared consumer documentation domain for authors using
> the plugin system.

> One plugin's internal behavior does not become a shared plugin contract by
> being used as an example.

> Shared plugin guides may summarize normative contracts for usability.
> Summaries must not contradict the authoritative source.

[Initial plugin profiles](../../../../../docs/development/crystal-lattice-documentation.md#L108-L125):

> Individual `plugins/*` packages are README-first by default; add local
> guidance/docs when package needs exceed inherited rules. `plugins/docs/` is
> the shared plugin-authoring documentation domain.

## Seed

Reuse
[Seed 01](seed-01-js-single-file-tool-documentation.md). The seed compares the
plugin README and implementation with the shared Node-tool loading and
packaging guides, without deciding which gaps belong to which owner.

## Repository setup

The focused real-repository fixture contains:

```text
plugins/js-single-file-tool/README.md
plugins/js-single-file-tool/UpperTool.ts
plugins/docs/index.md
plugins/docs/node-tool-plugins.md
plugins/docs/plugin-packaging-and-loading.md
plugins/AGENTS.md
plugins/docs/AGENTS.md
```

The shared docs already provide the authoring domain and index route. The
plugin README needs concrete `UpperTool` usage, while the shared Node-tool guide
can explain reusable export/configuration and verification facts.

## Exact user prompt

> Please make `plugins/js-single-file-tool` usable as a complete example, and
> add a focused shared explanation of the single-file object-export,
> loading/configuration, and verification workflow for other Node tool authors.
> Keep plugin-specific behavior with the example and keep the work
> documentation-only.

The prompt asks for both audiences without naming the files or prescribing
which facts are shared.

## Expected behavior

The agent should:

1. update the plugin README with `UpperTool`-specific configuration, first use,
   expected uppercase output, and verification;
2. update the shared Node-tool authoring guide with reusable export/loading and
   validation guidance, either directly or through one focused page linked from
   the canonical guide and shared index;
3. keep uppercase transformation semantics package-local rather than declaring
   them a requirement for all Node tools;
4. rely on the existing shared index and inherited plugin AGENTS files unless a
   real routing gap requires a focused edit;
5. avoid root docs, package-local specifications, generated output, and source
   changes.

## Allowed mutations

Expected:

```text
plugins/js-single-file-tool/README.md
plugins/docs/node-tool-plugins.md
```

One additional focused page under `plugins/docs/` and the corresponding
`plugins/docs/index.md` link are allowed when the focused workflow is
substantial enough to justify a separate page. No other mutation is allowed.

## Mechanical assertions

1. The plugin README documents `UpperTool`, a consistent concrete
   lowercase-to-uppercase example, supported loading/configuration, and
   verification.
2. The canonical shared Node-tool guide, optionally together with one focused
   indexed page, contains reusable export/loading and validation guidance.
3. The shared guide does not claim that all Node tools uppercase input or
   require `UpperTool`.
4. Claims that require unavailable loader/runtime source are removed or left
   explicitly unresolved rather than verified through another checkout.
5. Every changed shared guide remains reachable from `plugins/docs/index.md`,
   and a focused page is also linked from the canonical Node-tool guide.
6. No sibling/parent worktree is used as evidence.
7. No root docs, specifications, generated output, source, unrelated plugin
   file, or unrelated existing shared guide changes.

## Semantic assessment

- Are reusable facts expressed without depending on this one plugin?
- Is `UpperTool` clearly an example or package behavior rather than a shared
  contract?
- Did the agent avoid duplicating complete loading guidance into the package
  README?

## Human review

- Is the split between package usage and shared authoring guidance natural?
- Does the shared page remain useful to authors of different Node tools?
