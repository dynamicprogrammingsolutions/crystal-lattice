# 080 - Portable Default Config and Compiled System Message UI

Short description: After the core rebuild bug is fixed, create a fully portable default config copy, vendor all referenced prompt assets into that config directory, and add compiled-system-message metadata plus frontend rendering for system messages.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/060-simplified-system-message-configs-and-minimal-dynamics.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/070-core-rebuild-after-native-initialize-changes.md`

## Why This Follow-up Exists

Subtask `060` produced a simplified multi-vendor config and runtime prompt assets, but there are still two follow-up needs:

1. The created config is not yet fully portable because the Codex developer-message rows still reach outside the config directory into `docs/default-system-instructions/codex/...`.
2. The system-message feature should expose the first compiled system prompt as optional message metadata so the frontend can show it in a collapsible system-message section.

This task intentionally comes after task `070`, because once the core rebuild bug is fixed, a system message inserted on the native side can show up in rebuilt core `session.messages`. That makes `compiled_content` metadata on the native system message useful to the frontend without additional server-side projection logic.

## Current State Summary

### Current simplified config and runtime assets

The current simplified config lives at:

- `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`

Runtime system-message assets currently live under:

- `application/python/agent_terminal_app/system_messages/`

This includes:

1. Gemini runtime sections
2. Qwen runtime sections
3. Grok runtime sections
4. Codex template and helper files
5. helper runtime files such as:
   - `application/python/agent_terminal_app/system_messages/helpers/runtime.py`
   - `application/python/agent_terminal_app/system_messages/helpers/select_codex_developer_message.py`

### Current portability gap

The Codex agent in the simplified config still references extracted instruction files outside the config directory.

Current example references in:

- `application/python/agent_terminal_app/config_v2_multi_family_tools_simplified.json`

use paths like:

1. `${env:CONFIG_DIR}/../../../docs/default-system-instructions/codex/gpt-5.4/instructions_default.md`
2. `${env:CONFIG_DIR}/../../../docs/default-system-instructions/codex/gpt-5.3-codex/instructions_friendly.md`

That means the config is not self-contained.

### Current frontend rendering state

`SystemMessageBubble` currently renders only the visible system message content and footer fields.

Relevant component:

- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx:217`

It does not currently show a collapsible `compiled_content` block.

### Current system-message feature behavior relevant to metadata

`SystemMessageFeature.initialize_request(...)` already has all the context needed to compute the compiled system prompt for the current request:

- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:736`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:787`

Today it only uses that compiled text to populate `state["request"]["messages"]`:

- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:832`

It does not currently stamp a `compiled_content` field into native `_metadata`, and it does not print the compiled prompt to the console.

## User Decisions To Preserve

The user wants this handled after the core bugfix, and wants this work separate from task `070`.

Important requested behavior:

1. Keep the current simplified config file in place for now.
2. Make a portable copy as `config.json` under a new `default_config/` subdirectory.
3. Copy all dependent files there, including the Codex developer-message markdown files.
4. Add a logging feature to the system message so that when it is first applied, the compiled content is printed to the console.
5. Add `_metadata["compiled_content"]` to the native system message the first time the system message is applied including templating.
6. On the frontend, when a system message has metadata `compiled_content`, show it in a collapsible box similar to assistant reasoning.

Important behavior clarification from the discussion:

1. Template retention is intentional; do not replace the retained native `content` with compiled content.
2. The compiled text should live in metadata, not in the retained system-message content field.

## Concrete Goals

After this task:

1. `application/python/agent_terminal_app/default_config/config.json` is self-contained with all referenced prompt/helper assets under the same config directory.
2. The copied config no longer depends on `docs/default-system-instructions/...` for Codex prompt selection.
3. `SystemMessageFeature` stores `compiled_content` in native `_metadata` the first time it applies the system message.
4. `SystemMessageFeature` prints the compiled system prompt to the console on first application only.
5. After task `070`'s rebuild fix, the rebuilt core system message exposes `metadata.compiled_content` for frontend rendering.
6. The mobile UI renders that field in a collapsible system-message panel.

## Expected Implementation Direction

### 1. Create a portable default config tree

Recommended layout:

1. `application/python/agent_terminal_app/default_config/config.json`
2. `application/python/agent_terminal_app/default_config/system_messages/...`
3. `application/python/agent_terminal_app/default_config/system_messages/helpers/...`
4. `application/python/agent_terminal_app/default_config/codex/...`

Or an equivalent structure, as long as all references are kept under `${env:CONFIG_DIR}`.

Do not remove or rename the current simplified config during this task.

### 2. Vendor all referenced Codex files into the portable copy

Copy the actual instruction files referenced by `codex_developer_messages`, including the default/friendly/pragmatic variants currently in use.

Source currently lives under:

- `docs/default-system-instructions/codex/`

The portable config copy should reference only vendored copies under the `default_config` directory.

### 3. Add one-time compiled prompt logging and metadata

In:

- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py`

augment the native system message `_metadata` on first application with at least:

1. `compiled_content`
2. a marker indicating the compiled prompt has already been logged/stamped

Intended behavior:

1. If the target native system message does not yet have the marker, compute the compiled text, print it, and store it in `_metadata`.
2. On later requests against the retained same system-message entry, do not print again.
3. Keep native `content` as the template text.

This task does not require a larger logging framework. Simple console output is sufficient.

### 4. Frontend system-message collapsible UI

In:

- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`

extend `SystemMessageBubble` so that when `message.metadata.compiled_content` is a non-empty string, it shows:

1. a chevron toggle in the system-message header or nearby UI
2. a collapsible block
3. styling close to the assistant reasoning block

The visible main system message content should remain unchanged.

### 5. Avoid extra backend projection if task 070 is in place

Once task `070` is complete, rebuilt core messages should carry metadata restored from native `_metadata` through the provider pipeline. That should make `compiled_content` available through normal session-message listing without a separate server-side enrichment layer.

If implementation reveals a gap here, document it explicitly before broadening scope.

## Acceptance Criteria

1. The new portable config copy resolves all prompt/helper file references under `${env:CONFIG_DIR}`.
2. The copied config includes the vendored Codex prompt files required by its `codex_developer_messages` rows.
3. First application of a system message prints the compiled prompt to the console once.
4. The retained native system message keeps template content but gains `_metadata["compiled_content"]`.
5. After request completion and reload, the corresponding system message in `session.messages` exposes `metadata.compiled_content`.
6. The mobile UI shows that field in a collapsible system-message section.

## Tests To Add

### Plugin/unit tests

Add or extend tests under:

- `plugins/feature-system-message/tests/test_system_message_feature.py`
- `plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py`

Suggested coverage:

1. `compiled_content` is stamped into native `_metadata` the first time the system message is applied.
2. The console-print behavior happens once and not again on the next request.
3. The retained system-message `content` remains the template rather than the compiled text.

### Config portability tests

Extend config/docs/runtime coverage under:

- `core/python/tests/test_default_system_instructions_docs.py`

Suggested coverage:

1. `application/python/agent_terminal_app/default_config/config.json` exists.
2. All referenced files for the portable config exist under the copied config directory.
3. No Codex rows in the portable config reference `../../../docs/...` or any other path outside `${env:CONFIG_DIR}`.

### Application/integration tests

Add or extend application-path tests so they load the portable config and verify expected compiled prompt substrings still appear for representative vendors/models.

### Frontend tests

Add a React Native component test for `SystemMessageBubble` that verifies:

1. no collapsible appears when `compiled_content` is absent
2. the collapsible appears when `compiled_content` is present
3. expanding it shows the compiled text

## Verification Required

Run the relevant suites for the touched layers. At minimum:

1. `pytest plugins/feature-system-message/tests -q`
2. `pytest core/python/tests/test_default_system_instructions_docs.py -q`
3. any added/updated application integration tests under `application/python/tests` or plugin integration tests
4. the relevant mobile test command for the added React Native component test

Also validate the portable config JSON syntax.

## Commit Boundary Requested By User

This work should be handled after task `070` and in a separate commit from the core bugfix.

## Notes For The Implementing Agent

1. The earlier discussion temporarily considered a server-side enrichment step for `compiled_content`, but after clarifying the intended core fix, the preferred path is to rely on rebuilt core messages carrying provider-restored metadata.
2. If that assumption fails in implementation, stop and document the exact gap before broadening the task.

## Plan Added During Completion

Added during completion on approval.

1. Create `application/python/agent_terminal_app/default_config/config.json` as a portable copy of the simplified multi-family config and vendor every referenced prompt/helper asset under the new `default_config` tree, including the Codex developer-message markdown files.
2. Rewrite the copied config so every prompt/helper reference uses `${env:CONFIG_DIR}` and the portable copy no longer depends on `docs/default-system-instructions/...`.
3. Extend `SystemMessageFeature.initialize_request(...)` so the chosen native system message gets `_metadata["compiled_content"]` and a one-time logged marker the first time the compiled prompt is applied, while retaining template text in native `content`.
4. Add focused plugin/application coverage for the new metadata and one-time console logging behavior.
5. Extend the mobile `SystemMessageBubble` with a collapsible compiled-content panel modeled on the assistant reasoning panel, plus a React Native component test.
6. Add portability/config tests and integration checks for the copied default config, then run the relevant Python and mobile test suites plus JSON validation.

## Completion Notes Added During Completion

Implemented:

1. Added a portable config copy at `application/python/agent_terminal_app/default_config/config.json` and vendored the dependent runtime assets under `application/python/agent_terminal_app/default_config/`, including the full `system_messages/` tree and the referenced Codex prompt files under `default_config/codex/`.
2. Rewrote the copied Codex developer-message references so the portable config now resolves them from `${env:CONFIG_DIR}/codex/...` rather than escaping back into `docs/default-system-instructions/...`.
3. `SystemMessageFeature.initialize_request(...)` now stamps native `_metadata["compiled_content"]` plus a one-time logged marker on the chosen system message the first time it applies a compiled prompt, while preserving the templated native `content`.
4. The first compiled prompt is printed to the console exactly once per retained native system message via a simple `[system_message compiled]` console print.
5. Added a collapsible compiled-content panel to the mobile `SystemMessageBubble`, using the same visual treatment as the existing assistant reasoning panel.
6. Added Python regression coverage for compiled-content metadata/logging and portable-config resolution, plus a React Native component test for the new collapsible system-message panel.

Files touched:

1. `application/python/agent_terminal_app/default_config/config.json`
2. `application/python/agent_terminal_app/default_config/system_messages/...`
3. `application/python/agent_terminal_app/default_config/codex/...`
4. `plugins/feature-system-message/src/feature_system_message/system_message_feature.py`
5. `plugins/feature-system-message/tests/test_system_message_feature.py`
6. `plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py`
7. `core/python/tests/test_default_system_instructions_docs.py`
8. `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`
9. `mobile/crystal-lattice-control-rn/__tests__/MessageBubble.test.tsx`

Verification run:

1. `pytest plugins/feature-system-message/tests/test_system_message_feature.py -q`
2. `pytest plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py -q`
3. `pytest plugins/feature-system-message/tests -q`
4. `pytest core/python/tests/test_default_system_instructions_docs.py -q`
5. `python -m json.tool application/python/agent_terminal_app/default_config/config.json >/dev/null`
6. `ruff check plugins/feature-system-message/src/feature_system_message/system_message_feature.py plugins/feature-system-message/tests/test_system_message_feature.py plugins/feature-system-message/tests/test_system_message_feature_agent_application_integration.py core/python/tests/test_default_system_instructions_docs.py`
7. `npm test -- --runInBand __tests__/MessageBubble.test.tsx` from `mobile/crystal-lattice-control-rn/`

Notes:

1. The targeted Jest run passes, but it emits the existing `baseline-browser-mapping` staleness warning from the frontend toolchain.
2. The docs-only pytest run still emits the existing narrow-suite `pytest-cov` no-data warning.
