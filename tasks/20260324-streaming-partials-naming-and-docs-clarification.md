# Streaming Partials Naming And Docs Clarification

Clarify the provider/plugin streaming contract and remove the main naming clash by renaming chunk-local partial outputs and the shared streaming accumulator across the repo.

## Status

- [ ] Planned

## Context

Multiple reviewers misread the current streaming contract in the same way:

- Returned `partial_messages` were interpreted as the evolving in-progress assistant message.
- `state["partial"]` was interpreted as the same concept, rather than the accumulator that holds the full provider-native message built so far.
- That confusion directly led to an implementation in `AccumulatorExtensionMixin.process_chunk(...)` that synthesized a new partial from accumulated state when `partial_messages` was empty.

This task includes repo-wide naming changes plus the associated documentation updates.

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

This task should perform both renames, not just document them:

- `partial_messages` -> `chunk_partials`
- `state["partial"]` -> `state["accumulator"]`

Optional local cleanup where touched:

- `patch` -> `chunk_patch` or `chunk_delta`

Rationale:

- Renaming only `partial_messages` still leaves `state["partial"]` sounding like the same concept.
- Renaming only `state["partial"]` still leaves `partial_messages` sounding like an accumulated partial message.
- The pair `chunk_partials` + `accumulator` makes the distinction explicit and consistent.

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

- `core/python/agent_core/types.py`
- `core/python/agent_core/plugin/provider.py`
- `core/python/agent_core/plugin/extension.py`
- `core/python/agent_core/plugin/adapters.py`
- `core/python/plugins/*` provider/extension implementations that currently use `state["partial"]`
- `plugins/reference-openai-compatible-provider/*`
- `plugins/template-python-provider/*`
- `plugins/openrouter/*` and `plugins/openrouter_responses/*` files that currently use `state["partial"]`
- tests and examples that refer to either old name

## Requirements checklist

- [ ] The repo-wide API/hook parameter name `partial_messages` is renamed to `chunk_partials` in code, tests, examples, and docs.
- [ ] The repo-wide shared streaming state key `state["partial"]` is renamed to `state["accumulator"]` in code, tests, examples, and docs.
- [ ] Provider docs explicitly distinguish chunk-local partial emissions from accumulated state.
- [ ] Extension docs explicitly state that returned partials must not include previously accumulated content.
- [ ] The accumulator example documents the invariant in normative language, not just as an example.
- [ ] At least one example shows the intended renderer model for partials.
- [ ] The docs warn against creating a new partial from accumulated state when `chunk_partials` is empty.
- [ ] Any touched local variable names that still imply accumulation for chunk-local outputs are updated or explicitly clarified.

## Naming decision

Chosen names:

- `partial_messages` -> `chunk_partials`
- `state["partial"]` -> `state["accumulator"]`

Alternative names considered but not chosen:

- `partial_messages` -> `stream_deltas`, `emitted_partials`
- `state["partial"]` -> `state["accumulated"]`, `state["partial_accumulator"]`

Reason for the final choice:

- `chunk_partials` keeps the existing idea of partial message outputs while making their chunk-local scope explicit.
- `accumulator` directly describes the role of the shared state value and avoids suggesting that it is itself a partial emission.
- The pair removes the ambiguity better than renaming only one side.

## Task checklist

- [ ] Rename `partial_messages` to `chunk_partials` in protocol signatures, wrappers, implementations, examples, tests, and docs.
- [ ] Rename `state["partial"]` to `state["accumulator"]` in providers, extensions, templates, tests, and docs.
- [ ] Audit the wording in `plugins/docs/provider-plugins.md`.
- [ ] Audit the wording in `plugins/docs/provider-extensions.md`.
- [ ] Check whether matching clarification is needed in `core/python/agent_core/types.py` docstrings or generated reference docs.
- [ ] Add a short normative definition of returned `chunk_partials` as chunk-local emissions.
- [ ] Add a short normative definition of `state["accumulator"]` as accumulated provider state.
- [ ] Rewrite the accumulator example to make the distinction explicit.
- [ ] Add a "wrong vs right" example showing why not to build a new partial from accumulated state.
- [ ] Verify no stale `partial_messages` / `state["partial"]` references remain except where historical context is intentional.

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
Do not create a new partial from accumulated state when chunk_partials is empty.
If the provider did not emit a current-chunk partial, extensions should update only the accumulator in state.
```

## Notes for the implementing agent

- This task includes the repo-wide rename; do not leave it as a docs-only clarification.
- If examples are updated, prefer using the exact terms "chunk-local partial" and "accumulator" consistently.
- If generated reference docs mirror protocol docstrings, update the underlying docstrings rather than only editing generated output.