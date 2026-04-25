# Config-Based Role Normalization for Developer and System Messages (Optional)

Short description: Add a configuration-driven mechanism for normalizing between `system` and `developer` messages across the entire codebase, enabling users to manually add `developer` messages and ensuring proper role handling throughout the framework. Remove any existing normalization that prevents `developer` messages from being added or preserved.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

## Status

- [ ] Optional - can be completed after core compaction functionality works

## Depends On:
- `tasks/20260310-openai-responses-provider/043-native-message-preparation-for-compaction.md` (optional - can be done in parallel for basic request handling)

## Why this task exists

The codebase currently has hardcoded normalization logic that:
1. Prevents `developer` messages from being used directly (converts them to `user` messages)
2. Assumes `system` messages should always be sent as-is, even for models that prefer `developer` messages

This task adds explicit configuration for role handling so users and applications can control the behavior rather than having it hardcoded by model family detection.

## Key problems to solve

### Problem 1: Developer messages normalized to user messages

Current code likely prevents users from manually adding `developer` messages - they get normalized to `user` or `system` somewhere in the pipeline.

### Problem 2: No config option for role preference

The original 041 scope assumed automatic model-family detection (gpt-5.*, o1*, o3*, o4* → use `developer`). This task replaces that assumption with explicit configuration:
- `use_developer_message: true` → normalize `system` → `developer` for outbound requests
- `use_developer_message: false` → normalize `developer` → `system` (preserve backward compatibility)

### Problem 3: Normalization scattered across the codebase

Multiple locations may normalize roles inconsistently. This task requires a comprehensive audit and cleanup.

## Required outcome

1. Add a config option `use_developer_message` (boolean, default `false` for backward compatibility).

2. When `use_developer_message: true`:
   - Outbound `system` messages are normalized to `developer` before sending to the API
   - Retained native history still stores the original role
   - Users can manually add `developer` messages (not normalized to `user`)

3. When `use_developer_message: false` (default):
   - Outbound `developer` messages are normalized to `system` 
   - Existing behavior is preserved for backward compatibility

4. Audit and remove any code that prevents `developer` messages from being:
   - Added manually by users
   - Stored in native history
   - Passed through the message pipeline without unwanted normalization

5. Role normalization is preserved whenever possible - only apply the minimum transformation needed for the specific provider/config combination.

## Scope

### In scope

1. Config option in provider/extension configuration
2. Request-time role normalization based on config (not model detection)
3. Preservation of original roles in retained native history
4. Core message handling that accepts `developer` role throughout the pipeline
5. Audit and removal of hardcoded role normalization that blocks `developer` messages

### Out of scope

1. Automatic model-family detection for role selection (use explicit config instead)
2. UI changes for role selection (covered by other tasks if needed)
3. Changes to placeholder rendering (working correctly per 043)

## Implementation notes

1. Prefer a shared normalization helper that applies the config-based transformation consistently.
2. Keep normalization late in the request path (just before SDK calls) so retained history remains stable.
3. The config should be readable by both the provider and any cooperating extensions.
4. Document the config option in the provider README.

## Files to audit and potentially modify

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py` - add normalization helper
2. `core/python/agent_core/core.py` - check for hardcoded role normalization
3. `core/python/agent_core/types.py` - ensure `developer` is accepted in message roles
4. Any other providers or features that normalize `developer` → `user` or `system`

## Test plan

### Test group A: config option exists and is respected

Add tests proving:
1. `use_developer_message: true` → outbound requests use `developer` role
2. `use_developer_message: false` → outbound requests use `system` role
3. Original roles are preserved in retained native history regardless of config

### Test group B: manual developer message support

Add tests proving:
1. Users can manually add `developer` messages to a session
2. Manual `developer` messages are not normalized to `user` messages
3. Manual `developer` messages flow through the pipeline correctly

### Test group C: bidirectional normalization

Add tests proving:
1. `system` → `developer` when config says use developer
2. `developer` → `system` when config says don't use developer
3. Other roles (`user`, `assistant`, `tool`) are never affected

### Test group D: backward compatibility

Add tests proving:
1. Default config (`use_developer_message: false`) preserves existing behavior
2. Existing sessions with `system` messages work unchanged
3. No breaking changes to public APIs

## Definition of done

1. Config option `use_developer_message` is available and documented.
2. Role normalization is based on config, not model family detection.
3. Users can manually add `developer` messages anywhere in the codebase.
4. All hardcoded normalization blocking `developer` messages is removed.
5. Both directions of normalization work correctly (`system`→`developer` and `developer`→`system`).
6. Retained native history always preserves the original role.
7. Tests cover config behavior, manual developer message support, and backward compatibility.
