# Gemini Compaction App Plugin

Gemini-style context compaction application plugin for the AI Agent Platform.

## Overview

This plugin provides manual context compaction using Gemini's structured XML `<state_snapshot>` prompt format. It exposes session and message actions for compacting conversation history, with an optional verification pass that asks the model to self-critique and improve its summary.

**Important**: This plugin is **disabled by default** and must be explicitly enabled per-agent.

## Features

- **Session Actions**: "Compact range", "Compact full history"
- **Message Action**: "Compact messages up to here"
- **Gemini `<state_snapshot>` prompt**: Structured XML output with sections for goals, constraints, knowledge, artifacts, file state, actions, and task state
- **Optional verification pass**: Second LLM call for self-correction
- **Configurable summarizer agent**: Use a dedicated agent for compaction
- **Explicit enablement**: Only active when `enabled: true` and `type: "gemini"`

## Install

From the repo root:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/gemini-compaction-app[dev]"
```

## Environment

- `OPENROUTER_API_KEY` is required for OpenRouter-based configs.
- `BUILTIN_PLUGINS` should point to the `plugins` directory for `path:` plugin loading.
- For local use in this repo, keeping `OPENROUTER_API_KEY` in the repo root `.env` is the simplest setup.
- Do not commit real API keys into configs or docs.

## Quickstart

This is the smallest useful terminal/app-layer config when you want Gemini-style compaction with an OpenRouter-backed agent.

```json
{
  "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache/plugins",
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/openrouter",
    "path:${env:BUILTIN_PLUGINS}/gemini-compaction-app"
  ],
  "providers": {
    "openrouter_gemini": {
      "provider": "openrouter",
      "model": "google/gemini-2.5-flash-lite",
      "api_key": "${env:OPENROUTER_API_KEY}",
      "base_url": "https://openrouter.ai/api/v1",
      "timeout": 180
    }
  },
  "agents": {
    "default": {
      "provider": "openrouter_gemini",
      "compaction": {
        "enabled": true,
        "type": "gemini"
      }
    }
  }
}
```

Run the terminal app:

```bash
cd application/python
python -m agent_terminal_app --console --config /path/to/config_gemini_compaction.json
```

## Configuration

Configuration is **agent-level** with explicit enablement control. The plugin is only active when both `enabled` is `true` and `type` is `"gemini"`.

```json
{
  "agents": {
    "default": {
      "provider": "openrouter_gemini",
      "compaction": {
        "enabled": true,
        "type": "gemini",
        "agent_id": null,
        "prompt": null,
        "settings_overrides": {},
        "verification_pass": true
      }
    }
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Must be `true` to enable compaction for this agent |
| `type` | string | `null` | Must be `"gemini"` for this plugin. Other values (e.g., `"qwen"`, `"kimi"`) are for other compaction implementations |
| `agent_id` | string | `null` | Optional dedicated summarizer agent ID |
| `prompt` | string | Gemini prompt | Custom compaction prompt |
| `settings_overrides` | object | `{}` | Request settings overrides (e.g., `model`, `reasoningEffort`) |
| `verification_pass` | boolean | `true` | Enable/disable verification pass |

### Enablement Logic

The plugin is enabled **only when**:
1. `compaction.enabled` is `true` **AND**
2. `compaction.type` is `"gemini"`

In all other cases:
- `get_ui_elements()` returns `[]` (no UI elements)
- `execute_action()` returns an error with `error_type: "disabled"`

## Usage

### Session Action: "Compact range"

Select a range of messages to compact using Python-style slice indices (start:end). The selected messages will be replaced with a structured state snapshot.

### Message Action: "Compact messages up to here"

Click on a message and select this action to compact all messages before it.

### Session Action: "Compact full history"

Compact the entire conversation history into a single state snapshot.

## History Injection Shape

After compaction, the history becomes:

```
[system messages...]
user: <state_snapshot>...</state_snapshot>
assistant: Got it. Thanks for the additional context!
[preserved tail messages...]
```

## Example Configurations

### With dedicated summarizer agent

```json
{
  "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache/plugins",
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/openrouter",
    "path:${env:BUILTIN_PLUGINS}/gemini-compaction-app"
  ],
  "providers": {
    "main": {
      "provider": "openrouter",
      "model": "anthropic/claude-3.5-sonnet",
      "api_key": "${env:OPENROUTER_API_KEY}",
      "base_url": "https://openrouter.ai/api/v1",
      "timeout": 180
    },
    "summarizer": {
      "provider": "openrouter",
      "model": "openai/gpt-4o-mini",
      "api_key": "${env:OPENROUTER_API_KEY}",
      "base_url": "https://openrouter.ai/api/v1",
      "timeout": 120
    }
  },
  "agents": {
    "default": {
      "provider": "main",
      "compaction": {
        "enabled": true,
        "type": "gemini",
        "agent_id": "summarizer",
        "verification_pass": false
      }
    },
    "summarizer": {
      "provider": "summarizer"
    }
  }
}
```

### With model override for compaction

```json
{
  "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache/plugins",
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/openrouter",
    "path:${env:BUILTIN_PLUGINS}/gemini-compaction-app"
  ],
  "providers": {
    "openrouter_claude": {
      "provider": "openrouter",
      "model": "anthropic/claude-3.5-sonnet",
      "api_key": "${env:OPENROUTER_API_KEY}",
      "base_url": "https://openrouter.ai/api/v1",
      "timeout": 180
    }
  },
  "agents": {
    "default": {
      "provider": "openrouter_claude",
      "compaction": {
        "enabled": true,
        "type": "gemini",
        "settings_overrides": {
          "model": "openai/gpt-4o-mini"
        }
      }
    }
  }
}
```

## Testing

### Unit Tests

```bash
cd plugins/gemini-compaction-app
pytest tests/test_gemini_compaction_app_unit.py -v
```

### Integration Tests (requires OpenRouter API key)

```bash
export OPENROUTER_API_KEY=your_key_here
cd plugins/gemini-compaction-app
pytest tests/test_gemini_compaction_app_openrouter_integration.py -v -m openrouter
```

## License

Apache 2.0