# Provider-Extension Session Settings Lifecycle Docs

Short description: Document the new generic capability that allows non-application plugins to initialize and mutate per-session settings/overrides through lifecycle-triggered paths.

Parent Task: `tasks/20260312-provider-extension-session-settings-lifecycle/000-main.md`

Depends On: `tasks/20260312-provider-extension-session-settings-lifecycle/010-provider-extension-session-settings-lifecycle.md`

## Goal

Update the relevant docs so future plugin authors understand how to use the new capability correctly and when to use it instead of an application plugin or an explicit session action.

## Documentation requirements

1. Describe the new generic lifecycle/session-settings capability and its intended use cases.
2. Explain the boundary between:
- application plugins
- provider-extension session actions
- lifecycle-triggered session-settings writes for non-application plugins
3. Clarify expected storage/ownership when a feature needs a user-visible session setting.
4. Clarify default fork semantics for session-owned settings.
5. Include at least one small example showing the intended pattern.

## Candidate doc locations

Update whichever combination is appropriate after implementation details are finalized.

Likely locations:

1. `plugins/docs/provider-plugins.md`
2. `plugins/docs/provider-extensions.md`
3. `docs/api/core-sdk.md`
4. other architecture/reference docs directly affected by the chosen implementation

## Acceptance criteria

1. The documentation is sufficient for a new plugin author to understand when and how to use the capability.
2. The docs make the layering intent explicit so provider-specific behavior does not drift into the application layer.
3. The docs explain how this capability relates to explicit session actions and normal session settings UI.