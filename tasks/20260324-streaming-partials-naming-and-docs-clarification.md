# Streaming Partials Naming And Docs Clarification

Clarify the provider/plugin streaming contract and remove the main naming clash by renaming the shared streaming accumulator state key across the repo.

## Status

- [x] Completed

## Context

Multiple reviewers misread the current streaming contract in the same way:

- Returned `partial_messages` were interpreted as the evolving in-progress assistant message.
- `state["partial"]` was interpreted as the same concept, rather than the accumulator that holds the full provider-native message built so far.
- That confusion directly led to an implementation in `AccumulatorExtensionMixin.process_chunk(...)` that synthesized a new partial from accumulated state when `partial_messages` was empty.

This task includes a repo-wide state key rename plus the associated documentation updates. It intentionally does not rename the `partial_messages` hook parameter.

## Core problem to document

The missing invariant is:

- Returned partials are chunk-local emissions only.
- They must contain only data introduced by the current chunk.
- They must not be synthesized from previous accumulated content.
- Accumulation belongs in `state`, not in returned partials.

Equivalent renderer mental model:

```text
rendered_content = previous_rendered_content + partial_message.content
```

not:

```text
partial_message.content = previous_partial_message.content + current_chunk.content
```

## Chosen rename scope

This task should rename only the shared streaming accumulator state key:

- `state["partial"]` -> `state["accumulator"]`

Optional local cleanup where touched:

- `patch` -> `chunk_patch` or `chunk_delta`

Rationale:

- `state["partial"]` is the larger source of confusion because it names the accumulated provider-native assistant message as though it were a returned partial emission.
- Keeping `partial_messages` avoids broad hook signature churn while docs clarify that returned partial messages are chunk-local outputs.
- The pair `partial_messages` + `state["accumulator"]` is explicit enough once docs state that returned partials are not accumulated messages.

Compatibility decision:

- No backwards compatibility is needed for outside plugin implementations.
- Built-in providers and extensions should use `state["accumulator"]` consistently and should not read or write `state["partial"]` as a fallback.

## Key references

- `plugins/docs/provider-plugins.md:80-108`
  - Defines partials as incremental streaming updates, but the nearby recommended state shape uses `state["partial"]`, which is easy to confuse with those partials.
- `plugins/docs/provider-plugins.md:130-145`
  - Tells authors to update `state["partial"]` on the streaming hot path, without explicitly contrasting that accumulator with returned chunk-local partials.
- `plugins/docs/provider-extensions.md:130-132`
  - Encourages extensions to update `state["partial"]` as the shared accumulator.
- `plugins/docs/provider-extensions.md:175-205`
  - Shows the `AccumulatorExtensionMixin` skeleton; this is the main place to add the missing chunk-local invariant and a wrong-vs-right example.
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/_extension_accumulator.py:46-76`
  - Current implementation site where accumulated state and returned partials were conflated.

Likely rename touchpoints beyond docs:

- `core/python/plugins/*` provider/extension implementations that currently use `state["partial"]`
- `plugins/reference-openai-compatible-provider/*`
- `plugins/template-python-provider/*`
- `plugins/openrouter/*` and `plugins/openrouter_responses/*` files that currently use `state["partial"]`
- docs, tests, and examples that refer to the old state key
- core protocol docstrings only where they mention the old state key; hook parameter signatures should remain unchanged

## Requirements checklist

- [x] The repo-wide shared streaming state key `state["partial"]` is renamed to `state["accumulator"]` in code, tests, examples, and docs.
- [x] Built-in providers and extensions do not read or write `state["partial"]`, including as a compatibility fallback.
- [x] Provider docs explicitly distinguish chunk-local partial emissions from accumulated state.
- [x] Extension docs explicitly state that returned partials must not include previously accumulated content.
- [x] The accumulator example documents the invariant in normative language, not just as an example.
- [x] At least one example shows the intended renderer model for partials.
- [x] The docs warn against creating a new partial from accumulated state when `partial_messages` is empty.
- [x] Any touched local variable names that still imply accumulation for chunk-local outputs are updated or explicitly clarified.

## Naming decision

Chosen names:

- Keep the existing `partial_messages` hook parameter name.
- `state["partial"]` -> `state["accumulator"]`

Alternative names considered but not chosen:

- `partial_messages` -> `stream_deltas`, `emitted_partials`
- `state["partial"]` -> `state["accumulated"]`, `state["partial_accumulator"]`

Reason for the final choice:

- `accumulator` directly describes the role of the shared state value and avoids suggesting that it is itself a partial emission.
- Keeping `partial_messages` limits the change to the misleading state key while docs clarify that those returned partials are chunk-local.

## Task checklist

- [x] Rename `state["partial"]` to `state["accumulator"]` in providers, extensions, templates, tests, and docs.
- [x] Verify built-in providers and extensions do not retain fallback reads from `state["partial"]`.
- [x] Audit the wording in `plugins/docs/provider-plugins.md`.
- [x] Audit the wording in `plugins/docs/provider-extensions.md`.
- [x] Check whether matching clarification is needed in `core/python/agent_core/types.py` docstrings or generated reference docs.
- [x] Add a short normative definition of returned `partial_messages` as chunk-local emissions.
- [x] Add a short normative definition of `state["accumulator"]` as accumulated provider state.
- [x] Rewrite the accumulator example to make the distinction explicit.
- [x] Add a "wrong vs right" example showing why not to build a new partial from accumulated state.
- [x] Verify no stale `state["partial"]` references remain except where historical context is intentional.

## Suggested wording

Suggested normative text to reuse in docs:

```text
Returned partials are chunk-local stream emissions, not accumulated in-progress messages.
Each call to process_chunk should return only the new data introduced by the current chunk.
Do not merge previously returned partials into the new result.
If accumulated state is needed, store it in state.
```

Suggested explicit warning for the accumulator section:

```text
Do not create a new partial from accumulated state when partial_messages is empty.
If the provider did not emit a current-chunk partial, extensions should update only the accumulator in state.
```

## Notes for the implementing agent

- This task includes the repo-wide state key rename; do not leave it as a docs-only clarification.
- Do not rename the `partial_messages` hook parameter.
- Do not add backwards-compatible reads or writes for `state["partial"]`; built-in plugins should move together to `state["accumulator"]`.
- If examples are updated, prefer using the exact terms "chunk-local partial" and "accumulator" consistently.
- If generated reference docs mirror protocol docstrings, update the underlying docstrings rather than only editing generated output.

## Execution plan

Added during completion.

1. Rename the shared streaming state key from `partial` to `accumulator` in built-in providers/extensions and their focused tests.
2. Update current plugin development docs under `plugins/docs` first, then update secondary legacy/reference docs that still describe the old key.
3. Leave the `partial_messages` hook parameter and public stream event type `"partial"` unchanged.
4. Verify no active code/docs references to `state["partial"]` remain except task/history notes.
5. Run focused unit suites for changed providers/extensions, then run selected hosted API tests when the required credentials are available.

## Completion Notes

Added during completion.

- Renamed built-in shared streaming state usage to `state["accumulator"]` across core-packaged providers/extensions, template provider files, OpenRouter, OpenRouter Responses, and the reference OpenAI-compatible provider.
- Kept `partial_messages` and public stream events named `"partial"` unchanged.
- Updated current plugin docs under `plugins/docs` with chunk-local partial wording, the renderer mental model, and the warning not to synthesize partials from accumulated state.
- Verified active code/current docs have no stale `state["partial"]` reads or writes; older task files may still mention historical context.
- Focused unit tests passed for core OpenAI tools, template provider, reference provider, OpenRouter usage/tools/provider accumulator paths, and OpenRouter Responses provider.
- Hosted API checks: OpenRouter basic streaming passed and Z.ai reference-provider integration passed. Broader OpenRouter basic integration had one model-specific failure for `x-ai/grok-4.1-fast` returning no responses; Fireworks integration failed because the configured model was not found/deployed.