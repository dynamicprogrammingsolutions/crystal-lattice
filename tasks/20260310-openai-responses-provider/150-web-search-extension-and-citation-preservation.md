# OpenAI Responses Web Search Extension And Citation Preservation

Short description: Add native OpenAI Responses web search support to the `openai_responses` bundle using an extension-owned request layer and provider-owned citation/source normalization, while preserving native history and making citations visible in terminal/mobile UIs.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On: `tasks/20260310-openai-responses-provider/040-provider-streaming-event-normalization-and-finalization.md`

## Why this follow-up exists

The current `openai_responses` bundle supports plain Responses chat, tools, reasoning, usage, verbosity, native compaction, prompt caching/session keys, and attachment follow-ups, but it does not yet expose OpenAI's native web search capability.

OpenAI's current Responses API supports built-in web search via the `tools` array, and OpenAI's docs require that inline citations be preserved and shown clearly/clickably to end users. This task captures the research and implementation boundaries so the completer agent does not need to redo discovery.

This is planning/implementation work for the OpenAI Responses provider bundle only. It is not a request to add a generic cross-provider web-search abstraction.

## Architecture boundary that must hold

Keep the same architectural intent as the rest of `openai_responses`:

1. Provider remains transport/native-history focused.
2. Request-side web-search enablement and config mapping live in a dedicated provider extension.
3. Provider may still normalize provider-native output into stable core metadata when that metadata is derived directly from Responses-native items and needed by terminal/mobile/frontends.
4. Do not move web-search request shaping into the provider just because citations are provider-derived.

The intended split for this task is:

### Extension-owned

1. Config schema and UI elements for enabling web search.
2. Request payload shaping:
- inject built-in Responses tool `{"type": "web_search"}`
- optionally include `filters.allowed_domains`
- optionally include `search_context_size`
- optionally include `user_location`
- merge `include: ["web_search_call.action.sources"]`
3. Provider scoping tags / required tags so this extension only activates for `openai_responses`.

### Provider-owned

1. Preserve the native `web_search_call` and assistant `message` output items in native history.
2. Derive stable core metadata from native output items:
- `metadata.url_citations`
- `metadata.web_search_sources` or another comparably explicit provider-owned field name chosen during implementation
3. Ensure both non-streaming and streaming-final paths produce the same metadata shape.
4. Keep native replay/slice/fork behavior correct after a web-search turn.

## Official OpenAI research summary

The following points were verified against OpenAI's official docs and should be treated as the current source of truth for this task.

### 1. OpenAI Responses API supports built-in web search

OpenAI's Responses API reference currently defines a `WebSearchTool` object with:

1. `type: "web_search"` or `"web_search_2025_08_26"`
2. optional `filters`
3. optional `search_context_size`
4. optional `user_location`

The same reference also documents that `include` supports `web_search_call.action.sources`.

Official references:

1. OpenAI Responses create reference:
- `https://developers.openai.com/api/reference/resources/responses/methods/create`

Key lines collected during planning:

1. `WebSearchTool = object { type, filters, search_context_size, user_location }`
2. `type: "web_search" or "web_search_2025_08_26"`
3. `include` supports `web_search_call.action.sources`

### 2. Web-search responses include a tool-call item and a message item with citations

OpenAI's web search guide documents the Responses output shape as:

1. a `web_search_call` output item with the search call/action
2. a `message` output item
3. `message.content[0].text` for the answer text
4. `message.content[0].annotations` for cited URLs

The guide also includes a concrete example where the assistant message contains an `output_text` part with `annotations` entries of type `url_citation` including `start_index`, `end_index`, `url`, and `title`.

Official reference:

1. OpenAI web search guide:
- `https://developers.openai.com/api/docs/guides/tools-web-search`

### 3. OpenAI requires citations to be clearly visible and clickable

OpenAI's web search guide explicitly says:

1. by default, model responses include inline citations for URLs found in web search results
2. the `url_citation` annotation object contains the cited URL/title plus citation location data
3. when displaying web results or information contained in web results to end users, inline citations must be made clearly visible and clickable in the UI

This requirement is the main reason provider normalization must preserve citation data in a stable frontend-consumable form rather than leaving it only in opaque native output.

### 4. Full consulted sources are separate from inline citations

OpenAI distinguishes between:

1. inline citations, which show only the most relevant references actually cited in the answer
2. `sources`, which return the complete list of URLs the model consulted when forming the response

OpenAI's docs also note that the number of sources is often greater than the number of citations.

This matters for implementation because:

1. `url_citations` should remain the user-facing citation field
2. consulted `sources` should be preserved separately, not collapsed into citations
3. the provider should not imply that every consulted source was cited inline

### 5. Broader v1 optional request controls

For broader v1, OpenAI currently documents these optional controls for the Responses `web_search` tool:

1. `filters.allowed_domains`
2. `search_context_size` with `low`, `medium`, or `high`
3. approximate `user_location` with `country`, `city`, `region`, and/or `timezone`

The same guide states:

1. domain filtering allows an allow-list of up to 100 URLs
2. when formatting domains, omit `http://` or `https://`
3. this includes subdomains in the search
4. domain filtering is only available in the Responses API with the `web_search` tool
5. `country` is a two-letter ISO country code
6. `timezone` is an IANA timezone string
7. user location is not supported for deep research models using web search

## Current repo state relevant to this task

### `openai_responses` bundle currently has no web-search extension

`plugins/openai_responses/agent_plugin.json` currently registers:

1. provider
2. native compaction extension
3. tools extension
4. reasoning extension
5. usage extension
6. verbosity extension

There is no web-search extension entry today.

Relevant file:

1. [plugins/openai_responses/agent_plugin.json](plugins/openai_responses/agent_plugin.json)

### Provider currently does not normalize citations or sources from native Responses items

In `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`:

1. `from_native_messages()` currently converts only message and tool-output items into core messages and preserves ownership via `native_indices`.
2. It does not currently inspect `output_text.annotations` or `web_search_call` items to derive `metadata.url_citations` or consulted-source metadata.
3. `process_chunk()` currently treats `response.completed` as the streaming terminal event and appends final native output items as-is.

Relevant code references inspected:

1. [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py):338
2. [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py):493
3. [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py):746

### Provider already preserves a useful native-history baseline

The provider already stores the full final output items from Responses in both non-streaming and streaming finalization paths, which is the correct baseline for this feature:

1. non-streaming path appends `response.output` items directly after attaching internal response metadata
2. streaming path finalizes from `response.completed` and appends the final `output` items directly

That means the implementing agent should not need to redesign native history to support web search; the main missing pieces are request shaping and response metadata derivation.

### Sanitization currently strips annotations before replay, which is acceptable

When native items are sanitized for replay/input, the provider strips `annotations` and `logprobs` from content parts.

This should remain acceptable for request replay because:

1. citation display should come from normalized core metadata and/or stored final native output, not from replaying annotation objects back to the model
2. annotations are output/display metadata, not required input state for continued conversation

However, the task should confirm that stripping annotations does not accidentally remove any provider-owned data needed for native compaction or slice/fork operations.

### Terminal app is already wired for citation display

The terminal renderer already prints `metadata.url_citations` on assistant messages. That behavior exists today and should be reused for OpenAI Responses web search once the provider starts surfacing the metadata.

Relevant code and test references:

1. [application/python/agent_terminal_app/event_rendering.py](application/python/agent_terminal_app/event_rendering.py):450
2. [application/python/tests/test_terminal_event_rendering_web_citations.py](application/python/tests/test_terminal_event_rendering_web_citations.py)

Implication: terminal likely needs at most test coverage expansion and wording cleanup, not a brand-new UX flow.

### Mobile app is not yet wired for citation display

The React Native assistant bubble currently renders:

1. assistant content
2. reasoning block
3. tool-call block
4. generic footer elements

It does not currently render `metadata.url_citations` or any richer source list.

Relevant code inspected:

1. [mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx](mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx):449

Implication: to satisfy OpenAI's citation-display requirement for an end-user UI, this task should add at least a minimal mobile citation rendering path.

### OpenRouter `/responses` code provides direct prior art

There is already a similar pattern in the OpenRouter Responses implementation:

1. request-side web-search enablement lives in a dedicated extension
2. response-side citation extraction lives in the provider
3. provider normalizes `metadata.url_citations` from `output_text.annotations`

Relevant prior-art references:

1. [plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_websearch_extension.py](plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_websearch_extension.py)
2. [plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py](plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py):531
3. [plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py](plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py):1036
4. [plugins/openrouter_responses/tests/test_openrouter_websearch_extension_unit.py](plugins/openrouter_responses/tests/test_openrouter_websearch_extension_unit.py)
5. [plugins/openrouter_responses/tests/test_openrouter_websearch_integration.py](plugins/openrouter_responses/tests/test_openrouter_websearch_integration.py)

The implementing agent should reuse that design pattern where appropriate, while adapting it to OpenAI's documented `web_search` request schema and `web_search_call.action.sources` include behavior.

## Proposed v1 scope

Implement broader v1, but keep the breadth limited to optional config keys rather than building a large new UI system.

### In scope

1. New `OpenAIResponsesWebSearchExtension`.
2. Bundle registration in `agent_plugin.json` and package exports.
3. Config keys to enable web search and optionally shape the request.
4. Provider-side extraction of citations and consulted sources.
5. Terminal compatibility validation.
6. Minimal mobile citation rendering so the feature is visible to users.
7. Tests for non-streaming, streaming, and multi-turn/native-history continuity.

### Out of scope

1. A generic cross-provider `web_search` abstraction shared by all providers.
2. Chat Completions `web_search_options` support.
3. Deep research support.
4. Rich session-settings UI/editor for nested location/domain objects beyond what already falls out naturally from config/UI schema conventions.
5. Desktop-specific citation UX unless the implementing agent discovers an existing shared component path that makes it effectively free.

## Recommended config surface for broader v1

Use explicit optional provider-extension config keys so this can ship without inventing new generic framework primitives.

Recommended keys:

1. `enable_web_search: boolean = false`
2. `web_search_allowed_domains: string[] | null`
3. `web_search_search_context_size: "low" | "medium" | "high" | null`
4. `web_search_user_location_country: string | null`
5. `web_search_user_location_city: string | null`
6. `web_search_user_location_region: string | null`
7. `web_search_user_location_timezone: string | null`

Behavioral expectations:

1. Do not add `filters.allowed_domains` unless the allow-list is non-empty.
2. Do not add `user_location` unless at least one location field is provided.
3. If `user_location` is emitted, set `type: "approximate"` automatically.
4. Merge `include: ["web_search_call.action.sources"]` with any preexisting include values rather than overwriting them.
5. Do not duplicate the built-in web-search tool if request options/extensions already added one.

### Future note that must be preserved

Future options should be able to populate approximate user location automatically from frontend/UI state, but only as an explicit opt-in user choice. Do not make this subtask depend on automatic geolocation or implicit location capture.

## Candidate implementation approach

### 1. Add a dedicated extension

Create something like:

1. `openai_responses_plugins.openai_responses_websearch_extension.OpenAIResponsesWebSearchExtension`

Responsibilities:

1. `get_config_schema()` for the optional config keys above
2. `get_ui_elements()` with at least a checkbox for enablement and simple optional inputs if the bundle already uses provider-extension config UI this way
3. `get_tags()` / `required_tags()` for `openai_responses`
4. `init()` to store normalized web-search config in extension state
5. `initialize_request()` to merge the built-in tool and include values into the request payload

### 2. Extend provider output normalization

Add provider helpers modeled after the OpenRouter implementation:

1. `_extract_url_citations(output_items)`
2. `_extract_web_search_sources(output_items)`
3. logic in `from_native_messages()` to attach derived metadata to the canonical assistant message for a response segment

Design expectation:

1. Apply derived response-level metadata to the same canonical assistant message that owns the response segment's `native_indices`
2. Preserve separation between:
- `url_citations`: cited references actually used in the answer text
- `web_search_sources`: complete consulted source list from `web_search_call.action.sources`

### 3. Keep streaming and non-streaming behavior aligned

Since provider finalization already relies on final `response.output` items, the main requirement is that `from_native_messages()` derive the same metadata regardless of whether the response came from:

1. non-streaming `call_api()`
2. streaming `response.completed`

### 4. Render citations in mobile

Add a minimal assistant citation block in the React Native message bubble:

1. show citation entries when `metadata.url_citations` is present
2. use clickable links via `Linking.openURL(...)`
3. titles should be preferred over raw URLs when available
4. if full `web_search_sources` are also shown, keep them visually distinct from citations to avoid implying every source was cited

This does not need a complex new design system. It only needs to satisfy the docs requirement that citations be visible and clickable in an end-user UI.

## Acceptance criteria

1. `openai_responses` bundle exposes a dedicated web-search extension.
2. Enabling web search injects a Responses-native built-in tool entry of type `web_search` without breaking other tool handling.
3. Optional config keys can add:
- `filters.allowed_domains`
- `search_context_size`
- approximate `user_location`
4. The extension merges `include: ["web_search_call.action.sources"]` without clobbering preexisting include values.
5. Non-streaming web-search responses surface `metadata.url_citations` on the canonical assistant message.
6. Streaming web-search responses also surface `metadata.url_citations` on the final assistant message.
7. Provider preserves consulted-source information separately from inline citations.
8. Multi-turn follow-up requests still succeed after a web-search turn.
9. Terminal rendering works with OpenAI Responses citation metadata.
10. Mobile UI makes citations visible and clickable.
11. The implementation preserves the architectural split: request shaping in extension, native-output normalization in provider.

## Test expectations

### Extension unit tests

1. default-disabled behavior
2. enablement injects `{"type": "web_search"}`
3. include merging preserves existing include values
4. allowed-domain config maps to `filters.allowed_domains`
5. search-context-size config maps to `search_context_size`
6. location fields map to `user_location` with `type: "approximate"`
7. duplicate tool/include prevention

### Provider unit tests

1. citation extraction from `message.content[].annotations`
2. source extraction from `web_search_call.action.sources`
3. canonical assistant metadata assignment for a response segment
4. deduping behavior for repeated citations/sources if needed
5. no false positives when non-web-search responses omit these fields

### Integration and fixture-backed tests

1. fixture-backed non-streaming provider test with web-search output shape
2. fixture-backed streaming provider test where `response.completed` contains web-search output shape
3. multi-turn continuity test after a web-search turn
4. native-history regression ensuring slice/fork/replay still works

### UI tests

1. terminal rendering test can be reused or expanded to prove OpenAI-generated `url_citations` render the same as existing OpenRouter citation metadata
2. React Native component test for assistant message citation rendering and link handling if practical in the existing test setup

### Optional live integration tests

If adding live OpenAI integration coverage is practical, gate it with the existing `OPENAI_API_KEY` convention and keep it marked so it does not become a default local requirement.

## Suggested files likely touched during implementation

### Bundle and extension

1. `plugins/openai_responses/agent_plugin.json`
2. `plugins/openai_responses/src/openai_responses_plugins/__init__.py`
3. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_websearch_extension.py`

### Provider

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`

### Tests

1. `plugins/openai_responses/tests/test_openai_responses_websearch_extension_unit.py`
2. `plugins/openai_responses/tests/test_openai_responses_websearch_integration.py`
3. possibly updates to existing provider/native-history regression tests
4. `application/python/tests/test_terminal_event_rendering_web_citations.py`
5. mobile/component tests if present for `MessageBubble`

### Docs

1. `plugins/openai_responses/README.md`
2. optionally link or note this capability in `tasks/20260310-openai-responses-provider/100-docs-readme-and-config-examples.md` completion notes if useful

## Research references for the implementing agent

### Official OpenAI docs

1. Web search guide:
- `https://developers.openai.com/api/docs/guides/tools-web-search`

Verified details from that guide:

1. web-search responses include a `web_search_call` item plus assistant `message` text with annotations
2. citations are inline by default
3. citations must be clearly visible and clickable to end users
4. domain filtering is available via `filters.allowed_domains`
5. domain filtering allow-lists up to 100 URLs and expects domains without protocol prefixes
6. `sources` returns the full set of consulted URLs and can exceed the citation count
7. user location can be provided as approximate geography
8. deep research web search does not support user location

Collected lines during planning that are especially useful:

1. `web_search_call` + `message.content[0].annotations` shape:
- guide lines around 684-693 and 722-748 during planning lookup
2. citations visible/clickable requirement:
- guide lines around 691-693 and 846-848 during planning lookup
3. domain filtering and `include: ["web_search_call.action.sources"]` example:
- guide lines around 893-897 and 925-947 during planning lookup
4. user location details:
- guide lines around 1050-1057 and 1083-1094 during planning lookup

2. Responses create API reference:
- `https://developers.openai.com/api/reference/resources/responses/methods/create`

Verified details from that reference:

1. `WebSearchTool = object { type, filters, search_context_size, user_location }`
2. `type` may be `web_search` or `web_search_2025_08_26`
3. `include` supports `web_search_call.action.sources`

### In-repo prior art and affected code

1. OpenRouter request-side extension pattern:
- [plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_websearch_extension.py](plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_websearch_extension.py)

2. OpenRouter provider-side citation normalization:
- [plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py](plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py):531
- [plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py](plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py):1036

3. Existing OpenRouter tests to mirror structurally:
- [plugins/openrouter_responses/tests/test_openrouter_websearch_extension_unit.py](plugins/openrouter_responses/tests/test_openrouter_websearch_extension_unit.py)
- [plugins/openrouter_responses/tests/test_openrouter_websearch_integration.py](plugins/openrouter_responses/tests/test_openrouter_websearch_integration.py)

4. Existing terminal citation rendering:
- [application/python/agent_terminal_app/event_rendering.py](application/python/agent_terminal_app/event_rendering.py):450
- [application/python/tests/test_terminal_event_rendering_web_citations.py](application/python/tests/test_terminal_event_rendering_web_citations.py)

5. Existing mobile assistant rendering gap:
- [mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx](mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx):449

6. Existing `openai_responses` provider paths to inspect first:
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py):338
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py):493
- [plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py](plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py):746

## Completion notes guidance for the implementing agent

When this subtask is completed, the completion notes should explicitly record:

1. the final metadata field names chosen for citations and full consulted sources
2. whether mobile now renders only citations or both citations and full source lists
3. how include merging was implemented
4. whether any model or tag gating was needed for `web_search`
5. whether live OpenAI integration tests were added or intentionally deferred