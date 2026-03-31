# Gemini Compaction Feature Plugin

A Feature-level plugin that provides Gemini-style context compaction using the layered context approach.

## Overview

This plugin implements the same compaction logic as `GeminiCompactionAppPlugin` but operates at the Feature plugin level, using the layered context to access LLM capabilities.

## Key Differences from AppPlugin

| Feature | AppPlugin | FeaturePlugin |
|---------|-----------|---------------|
| Session persistence | Built-in (via `app.save_session`) | Returns `session_metadata` patch |
| Agent switching | Full support via `app.update_agent()` | Limited (requires app context) |
| Session locking | Built-in (via `app.acquire_session_lock`) | Not available |
| Operation level | Application layer | Core layer |
| Return value | Mutations dict | `native_messages` + `session_metadata` |

## When to Use

- **Use AppPlugin when**: You need full session management, persistence, and UI integration
- **Use FeaturePlugin when**: Operating at the native-message level, provider-specific optimizations, or core-level workflows

## Configuration

```yaml
compaction:
  enabled: true           # REQUIRED for plugin to be active
  type: gemini            # REQUIRED for this plugin
  agent_id: null          # Optional: dedicated summarizer agent
  prompt: null            # Optional: custom prompt override
  settings_overrides: {}  # Optional: model/params for compaction
  verification_pass: true # Optional: enable verification pass (default: true)
```

## Layered Context

This plugin uses the layered context approach:

- **Layer 1 (Core)**: Uses `context["core"]` for session/message operations
- **Layer 2 (Application)**: Optionally uses `context.get("app")` for enhanced features like agent switching

## Installation

```bash
pip install gemini-compaction-feature
```

## Usage

Add to your configuration:

```json
{
  "plugins": [
    "gemini_compaction_feature.GeminiCompactionFeaturePlugin"
  ]
}
```

## Dependencies

This plugin depends on `gemini-compaction-app` for shared prompts and helpers.

## License

MIT
