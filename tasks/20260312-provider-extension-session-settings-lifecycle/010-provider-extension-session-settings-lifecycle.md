# Provider-Extension Session Settings Lifecycle

Short description: Implement a generic shared capability that allows non-application plugins to initialize and mutate per-session settings/overrides through lifecycle-triggered paths, while preserving the current architecture where provider-specific behavior remains outside the application layer.

Parent Task: `tasks/20260312-provider-extension-session-settings-lifecycle/000-main.md`

Depends On: None

## Goal

Introduce the minimal generic core/application/server capability needed so provider extensions and similar non-application plugin types can participate in session-settings lifecycle.

This should make it possible for a feature such as `openai_responses` prompt caching to ensure a session-owned setting exists at the right time, without implementing that feature as an application plugin.

## Scope

This task is about the shared capability only.

In scope:

1. generic lifecycle-triggered session settings/override writes for non-application plugins
2. create-time initialization support for new sessions
3. request-time fallback support for legacy sessions missing required session-owned settings
4. preservation of existing session-owned settings on fork unless a feature explicitly chooses to replace them
5. generic tests covering the new capability across core/application/server paths

Out of scope:

1. OpenAI prompt caching request shaping itself
2. OpenAI-specific config keys or UI labels
3. provider-specific feature logic in application code

## Requirements

1. The capability must be generic and reusable by non-application plugin types.
2. It must support at least two lifecycle moments:
- session creation
- request-send fallback/repair for existing sessions
3. It must integrate with the existing session settings / per-session override model rather than inventing a parallel storage location when the feature being enabled is a user-visible session setting.
4. Forked sessions must preserve existing session-owned settings by default.
5. The application/core/server layers must not hardcode feature-specific behavior.

## Design constraints

1. Keep the provider transport/native-history focused.
2. Keep request shaping and feature ownership in provider extensions/features.
3. Prefer one generic capability over feature-specific hooks.
4. Avoid forcing provider-owned capabilities into application plugins just to mutate session settings.

## Candidate implementation directions

The implementation should choose the smallest generic mechanism that satisfies the requirements.

Acceptable directions include:

1. lifecycle hooks for non-application plugins that can return session-settings/session-metadata patches
2. a generic lifecycle action path for non-application plugins that is triggered by application/session events
3. another comparably generic mechanism that allows create-time and pre-send fallback mutation while preserving layering

The chosen implementation must be documented in code/tests and in the follow-up docs subtask.

## Acceptance criteria

1. There is a generic way for non-application plugins to initialize session-owned settings during session creation.
2. There is a generic way for non-application plugins to repair/add missing session-owned settings during a request lifecycle path.
3. Fork keeps session-owned settings intact by default.
4. Existing session settings surfaces can still expose and edit the resulting values when those values are stored as session settings/overrides.
5. Tests cover create-time initialization, request-time fallback, and fork preservation.

## Test expectations

1. Core/application tests for create-time lifecycle writes.
2. Core/application/server tests for request-time fallback writes on legacy sessions.
3. Regression tests that fork preserves the existing session-owned values.
4. Tests should use a generic dummy plugin/extension fixture rather than an OpenAI-specific implementation.

## References

- `tasks/20260128-sandboxing-prereqs/030-add-session-override-helper-apis.md`
- `tasks/20260128-sandboxing-prereqs/040-session-aware-app-plugin-ui-and-conditions.md`
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`
- `core/python/agent_app/application_future.py`
- `application/python/agent_terminal_app/server.py`
- `application/python/agent_terminal_app/terminal_app.py`