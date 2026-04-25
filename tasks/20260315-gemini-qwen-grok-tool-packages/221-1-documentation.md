# 222 - Documentation for Phase 2: Plugin Documentation

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`
Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/221-feature-plugin-context.md`

This subtask completes the documentation for Phase 2 of Task 221. The tasks created include this subtask.

## Goal

Create comprehensive documentation for:
1. **ApplicationPlugin capabilities and context** - Document what ApplicationPlugin can do
2. **FeaturePlugin capabilities and context** - Document the FeaturePlugin can do access with layered context
3. **ProviderExtensionPlugin capabilities and context** - Document what ProviderExtensionPlugin can access with layered context
4. **Session Actions API** - Document `execute_session_action` and `execute_lifecycle_actions` methods signatures
5. **Update existing documentation** - Match structure and style
6. **Create new documentation files** as described below

## Files Created/Updated

| File | Status | Purpose |
|------|--------|---------|
| `plugins/docs/application-plugins.md` | ✅ Created | Document ApplicationPlugin capabilities |
| `plugins/docs/feature-plugins.md` | ✅ Created | Document FeaturePlugin capabilities |
| `plugins/docs/provider-extensions.md` | ✅ Updated | Added session actions and context documentation |
| `plugins/docs/actions.md` | ✅ Updated | Added layered context section |
| `TYPES_AND_PROTOCOLS.md` | ✅ Updated | Added session actions and context section |
| `docs/api/core-sdk.md` | ✅ Updated | Added session actions documentation |

## Requirements Checklist

- [x] Investigate ApplicationPlugin implementation and capabilities
- [x] Investigate FeaturePlugin implementation and capabilities
- [x] Investigate ProviderExtensionPlugin implementation and capabilities
- [x] Document ApplicationPlugin context structure (all layers)
- [x] Document FeaturePlugin context structure (all layers)
- [x] Document ProviderExtensionPlugin context structure (all layers)
- [x] Document `execute_session_action` method signature
- [x] Document `execute_lifecycle_actions` method signature
- [x] Create `plugins/docs/application-plugins.md`
- [x] Create `plugins/docs/feature-plugins.md`
- [x] Update `plugins/docs/provider-extensions.md` with context documentation
- [x] Update `plugins/docs/actions.md` with layered context section
- [x] Update `TYPES_AND_PROTOCOLS.md` with session actions and context documentation
- [x] Update `docs/api/core-sdk.md` with session actions documentation

## Documentation Summary

### plugins/docs/application-plugins.md (New)

Comprehensive documentation for ApplicationPlugin including:
- Capabilities table (session persistence, LLM requests, event publishing, etc.)
- Protocol definition
- Context structure in `execute_action`
- Action definitions and lifecycle triggers
- Return value contract (mutations, ui_effects)
- UI elements contribution
- Example implementation
- When to use ApplicationPlugin vs FeaturePlugin

### plugins/docs/feature-plugins.md (New)

Comprehensive documentation for FeaturePlugin including:
- Core capabilities (Layer 1 - always available)
- Application capabilities (Layer 2 - when called from AgentApplication)
- Protocol definition
- Layered context in `execute_action` (detailed breakdown of each layer)
- Checking for capabilities pattern
- Return value contract (native_messages, session_metadata)
- Action definitions
- Example implementation showing both core-only and app-enhanced modes
- UI elements contribution
- When to use FeaturePlugin vs ApplicationPlugin

### plugins/docs/provider-extensions.md (Updated)

Added section on:
- Session actions for provider extensions
- `execute_action` signature
- Return value contract
- Layered context structure (Layer 1 and Layer 2)
- Checking for capabilities pattern

### plugins/docs/actions.md (Updated)

Added section after "Reserved context keys":
- Layered context for feature/extension plugins
- Layer 1: Core-level context (always present)
- Layer 2: Application-level context (when called from AgentApplication)
- Layer 3: Terminal/Server-level context (implementation-specific)
- Checking for capabilities pattern
- Context flow diagram

### TYPES_AND_PROTOCOLS.md (Updated)

Added sections:
- Session Actions (ActionDefinition, ActionContext, ActionResult)
- Layered Context (context buildup through call stack)
- Capability checking pattern

### docs/api/core-sdk.md (Updated)

Added method documentation:
- `execute_session_action` with parameters, context, returns, example
- `execute_lifecycle_actions` with parameters, context, returns, example
- Standard lifecycle triggers list

## Completion Notes

All documentation has been created/updated to match the existing documentation style:
- Follows the same structure as `provider-plugins.md` and `provider-extensions.md`
- Uses consistent formatting for tables, code blocks, and examples
- Includes practical examples and usage patterns
- Documents both the "what" and "why" for each capability
- Provides clear guidance on when to use each plugin type