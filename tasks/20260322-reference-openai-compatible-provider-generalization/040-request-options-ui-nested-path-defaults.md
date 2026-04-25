# Request Options UI Nested Paths And Defaults

Short description: Extend the request-options feature so settings UIs can expose nested `request_options` fields with flat override keys, while still resolving current/default values from nested base config.

Parent Task: tasks/20260322-reference-openai-compatible-provider-generalization/000-main.md
Depends On: tasks/20260322-reference-openai-compatible-provider-generalization/030-other-provider-integration-matrix.md

## Task checklist

- [x] Add nested-object and boolean support to `request_options_ui`.
- [x] Emit `config_path` and `default` metadata on generated request-options UI elements.
- [x] Deep-merge flat request-options overrides back into nested `request_options` during feature initialization.
- [x] Update session settings resolution so terminal/mobile/desktop UIs can resolve effective values from `config_path` and UI defaults.
- [x] Update default config examples and plugin documentation.
- [x] Add targeted Python and TypeScript tests covering nested defaults and non-clobbering merges.

## Scope

This follow-up keeps the existing flat override key model, such as `request_options__reasoning_history`, but makes the base/default value side nested-aware so provider configs can use natural nested `request_options` objects.

Target outcomes:

1. `request_options_ui` may contain nested objects, not only flat leaf entries.
2. Generated UI elements keep a flat override `key` but also include a nested `config_path` like `request_options.thinking.clear_thinking`.
3. Generated UI elements may include a `default` copied from nested `request_options` in the effective config.
4. Settings UIs resolve values in this order: flat override key, flat base key, nested base key via `config_path`, UI-element `default`, then schema default.
5. Nested flat overrides must deep-merge so overriding `request_options__thinking__clear_thinking` does not replace the whole `thinking` object or discard `type`.

## Execution plan

Added during completion on 2026-03-30.

1. Extend the feature-request-options plugin to recursively generate UI elements and inflate nested override paths.
2. Add `config_path` and `default` metadata to generated config UI elements.
3. Update shared session-settings logic and terminal help/current-value rendering to resolve nested values through `config_path`.
4. Update default config examples for Fireworks and Z.ai to use nested `request_options` defaults.
5. Expand Python and TypeScript tests, then run targeted verification.

## Completion Notes

Added during completion on 2026-03-30.

- Extended `plugins/feature-request-options/src/feature_request_options/request_options_feature.py` so `request_options_ui` now supports nested objects plus `boolean`/`checkbox` leaves.
- Generated request-options UI elements now include flat override keys, nested `config_path` metadata, and `default` values copied from nested `request_options` when present.
- Replaced shallow overlay merging with nested inflation plus deep merge, so overriding `request_options__thinking__clear_thinking` preserves sibling keys like `request_options.thinking.type`.
- Updated shared session-settings resolution in `packages/frontend-sdk-react/src/sessionSettings/logic.ts` and the terminal help rendering in `application/python/agent_terminal_app/terminal.py` so current/default values can be resolved from nested config paths.
- Updated `application/python/agent_terminal_app/default_config/config.json` so the Fireworks and Z.ai agent examples use nested `request_options` defaults instead of requiring duplicated flat config keys.
- Updated `plugins/feature-request-options/README.md` to document nested `request_options_ui`, boolean controls, `config_path`, UI defaults, and deep-merge semantics.
- Added targeted coverage in `plugins/feature-request-options/tests/test_request_options_feature.py` and `packages/frontend-sdk-react/src/sessionSettings/logic.test.ts`.
- Verification completed with:
  - `pytest plugins/feature-request-options/tests/test_request_options_feature.py -q`
  - `npm test -- --run src/sessionSettings/logic.test.ts` in `packages/frontend-sdk-react`
  - `python -m py_compile application/python/agent_terminal_app/terminal.py plugins/feature-request-options/src/feature_request_options/request_options_feature.py`