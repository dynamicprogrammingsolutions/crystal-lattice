# 222 - Gemini Compaction Lifecycle Auto-Trigger

Short description: Implement automatic compaction triggered by lifecycle hooks based on token thresholds and context limits.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`
Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/221-feature-plugin-context.md`

## Goal

Add automatic compaction that triggers after requests when token usage approaches context limits. This builds on the GeminiCompactionFeaturePlugin from Task 221, adding lifecycle-triggered actions that check thresholds and optionally compact the session.

## Background

The Gemini CLI automatically compacts conversation history when:
- Token count exceeds a threshold (default: 50% of context limit)
- After tool calls complete
- Before the next user turn

This task implements similar auto-compaction behavior as a lifecycle action triggered on `request_complete`.

## Scope

### In Scope

1. **Token estimation helper**
   - Estimate token count for session messages
   - Support multiple estimation strategies (character-based, provider-specific)
   - Integrate with existing message processing

2. **Context limit registry**
   - Store known context limits per model
   - Allow configuration overrides
   - Fallback for unknown models

3. **Threshold configuration**
   - Add to agent config under `compaction` section
   - `compaction.enabled`: Enable/disable auto-compaction
   - `compaction.threshold`: Trigger when usage >= X% of limit (default: 0.5)
   - `compaction.preserve_tail`: Keep last N% uncompressed (default: 0.3)

4. **Lifecycle action**
   - Register action with `trigger: "request_complete"`
   - Check token usage vs threshold
   - Determine range to compact (preserve tail)
   - Call `compact_range` action if needed

5. **Session actions documentation**
   - Document how session actions work
   - Document lifecycle triggers
   - Add examples to `plugins/docs/actions.md`

### Out of Scope

1. Provider-native compaction (OpenAI Responses already has this)
2. UI for configuring thresholds
3. Multi-session compaction
4. Compaction before tool calls (requires different trigger)

## Implementation Plan

### Phase 1: Token Estimation

**Create new utility module**:

```python
# In core/python/agent_core/token_estimation.py

def estimate_token_count(
    messages: List[Dict[str, Any]],
    method: str = "char",
) -> int:
    """Estimate token count for messages.
    
    Args:
        messages: List of message dictionaries
        method: Estimation method
            - "char": Character-based (~4 chars/token for English)
            - "whitespace": Whitespace-based (~0.75 words/token)
    
    Returns:
        Estimated token count
    """
    if method == "char":
        total_chars = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, list):
                # Handle multimodal content
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        total_chars += len(part.get("text", ""))
        return max(1, total_chars // 4)
    
    # Add more methods as needed
    return 0


def estimate_native_token_count(
    native_messages: List[Dict[str, Any]],
    method: str = "char",
) -> int:
    """Estimate token count for provider-native messages."""
    # Similar to above but handles native format
    ...
```

### Phase 2: Context Limit Registry

**Add to core config**:

```python
# In core/python/agent_core/context_limits.py

# Known context limits by model
DEFAULT_CONTEXT_LIMITS = {
    # OpenAI
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
    
    # Anthropic
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "claude-3-5-sonnet": 200000,
    
    # Gemini
    "gemini-1.5-pro": 1000000,
    "gemini-1.5-flash": 1000000,
    "gemini-2.0-flash": 1048576,
    
    # Other
    "llama-3-70b": 8192,
    "mixtral-8x7b": 32768,
}

def get_context_limit(model: str, config_overrides: Optional[Dict] = None) -> int:
    """Get context limit for a model.
    
    Args:
        model: Model identifier
        config_overrides: Optional config with custom limits
    
    Returns:
        Context limit in tokens
    """
    if config_overrides:
        custom_limits = config_overrides.get("context_limits", {})
        if model in custom_limits:
            return custom_limits[model]
    
    # Check default limits (case-insensitive partial match)
    model_lower = model.lower()
    for key, limit in DEFAULT_CONTEXT_LIMITS.items():
        if key.lower() in model_lower or model_lower in key.lower():
            return limit
    
    # Default fallback
    return 8192
```

### Phase 3: Threshold Configuration

**Add to agent config schema** (extends existing compaction config from Task 220):

```yaml
# Agent-level config (flattened in base_config)
compaction:
  enabled: true              # REQUIRED for plugin to be active
  type: gemini               # REQUIRED for this plugin (gemini | qwen | kimi)
  threshold: 0.5             # Auto-compact when >= 50% of limit
  preserve_tail: 0.3         # Keep last 30% uncompressed
  min_messages: 10           # Minimum messages before considering
  agent_id: null             # Optional: use different agent for compaction
  prompt: null               # Optional: custom prompt override
  settings_overrides: {}     # Optional: model/params for compaction
  verification_pass: true    # Optional: enable verification pass (default: true)
```

**Important**: The `base_config` from `AgentApplication` is **flattened**, so access config via:
```python
compaction_cfg = base_config.get("compaction") or {}  # NOT base_config.get("agent", {}).get("compaction")
```

**Enablement Logic**:
```python
def _is_compaction_enabled(self, base_config: Dict[str, Any]) -> bool:
    compaction_cfg = base_config.get("compaction") or {}
    return compaction_cfg.get("enabled") is True and compaction_cfg.get("type") == "gemini"
```

**Config extraction helper**:

```python
def _get_compaction_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
    compaction_cfg = base_config.get("compaction") or {}
    return {
        "enabled": compaction_cfg.get("enabled", False),
        "type": compaction_cfg.get("type"),
        "threshold": compaction_cfg.get("threshold", 0.5),
        "preserve_tail": compaction_cfg.get("preserve_tail", 0.3),
        "min_messages": compaction_cfg.get("min_messages", 10),
        "agent_id": compaction_cfg.get("agent_id"),
        "prompt": compaction_cfg.get("prompt") or _GEMINI_COMPRESSION_PROMPT,
        "settings_overrides": compaction_cfg.get("settings_overrides") or {},
        "verification_pass": compaction_cfg.get("verification_pass", True),
    }
                    "description": "Compact when token usage >= this fraction of limit",
                },
                "preserve_tail": {
                    "type": "number",
                    "default": 0.3,
                    "minimum": 0.1,
                    "maximum": 0.5,
                    "description": "Keep this fraction of newest messages uncompressed",
                },
                "min_messages": {
                    "type": "integer",
                    "default": 10,
                    "description": "Minimum messages before considering compaction",
                },
                "agent_id": {
                    "type": "string",
                    "description": "Optional agent to use for compaction",
                },
            },
        },
    }
```

### Phase 4: Lifecycle Action Implementation

**Add to GeminiCompactionFeaturePlugin**:

```python
def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        # Manual action (existing from Task 221)
        {
            "id": "compact_range",
            "label": "Compact range",
            "description": "Compact a message range into a state snapshot.",
            "inputs": {
                "start": {"type": "integer", "required": False},
                "end": {"type": "integer", "required": False},
                "instructions": {"type": "string", "required": False},
            },
        },
        # Lifecycle action (new)
        {
            "id": "auto_compact_if_needed",
            "label": "Auto compact if needed",
            "description": "Check token usage and compact if threshold exceeded.",
            "inputs": {},
            "trigger": "request_complete",
        },
    ]

def execute_action(self, action_id, session, native_messages, params, context, state):
    if action_id == "compact_range":
        return self._do_compact_range(session, native_messages, params, context, state)
    elif action_id == "auto_compact_if_needed":
        return self._do_auto_compact(session, native_messages, context, state)
    ...

def _do_auto_compact(self, session, native_messages, context, state):
    """Check if compaction needed and execute if so."""
    # Get base_config (flattened) - use context["base_config"] if app-level, else context["config"]
    base_config = context.get("base_config", context.get("config", {}))
    
    # Check enablement using same logic as Task 220
    if not self._is_compaction_enabled(base_config):
        return {"native_messages": native_messages}
    
    # Get compaction config
    compaction_cfg = self._get_compaction_config(base_config)
    
    # Get thresholds
    threshold = compaction_cfg.get("threshold", 0.5)
    preserve_tail = compaction_cfg.get("preserve_tail", 0.3)
    min_messages = compaction_cfg.get("min_messages", 10)
    
    # Count messages
    message_count = len(native_messages)
    if message_count < min_messages:
        return {"native_messages": native_messages}
    
    # Estimate tokens
    token_count = estimate_native_token_count(native_messages)
    
    # Get context limit
    model = base_config.get("model", "")
    context_limit = get_context_limit(model, base_config)
    
    # Check threshold
    usage_ratio = token_count / context_limit
    if usage_ratio < threshold:
        return {"native_messages": native_messages}
    
    # Calculate compaction range
    # Preserve tail (newest messages)
    preserve_count = int(message_count * preserve_tail)
    # Also preserve leading system messages
    system_count = 0
    for msg in native_messages:
        if msg.get("role") == "system":
            system_count += 1
        else:
            break
    
    compact_end = message_count - preserve_count
    if compact_end <= system_count:
        return {"native_messages": native_messages}
    
    # Execute compaction using the same implementation as compact_range
    compact_params = {
        "start": system_count,
        "end": compact_end,
    }
    
    # Optionally use different agent
    agent_id = compaction_config.get("agent_id")
    if agent_id:
        compact_params["agent_id"] = agent_id
    
    return self._do_compact_range(
        session, 
        native_messages, 
        compact_params, 
        context, 
        state
    )
```

### Phase 5: Documentation

**Update `plugins/docs/actions.md`**:
- Add section on lifecycle-triggered auto-compaction
- Document the `request_complete` trigger
- Add example configuration

**Create `plugins/docs/compaction.md`** (new):
- Overview of compaction features
- Manual compaction actions
- Automatic compaction configuration
- Provider-native vs plugin-based compaction

## Requirements Checklist

- [ ] Create `core/python/agent_core/token_estimation.py`
- [ ] Implement `estimate_token_count()` function
- [ ] Implement `estimate_native_token_count()` function
- [ ] Create `core/python/agent_core/context_limits.py`
- [ ] Implement `DEFAULT_CONTEXT_LIMITS` registry
- [ ] Implement `get_context_limit()` function
- [ ] Add compaction config schema to feature plugin
- [ ] Add `auto_compact_if_needed` lifecycle action
- [ ] Implement `_do_auto_compact()` method
- [ ] Add unit tests for token estimation
- [ ] Add unit tests for context limits
- [ ] Add unit tests for auto-compaction logic
- [ ] Add integration tests for lifecycle trigger
- [ ] Update `plugins/docs/actions.md`
- [ ] Create `plugins/docs/compaction.md`

## Key Files

| File | Purpose |
|------|---------|
| `core/python/agent_core/token_estimation.py` | Token estimation utilities |
| `core/python/agent_core/context_limits.py` | Context limit registry |
| `plugins/gemini-compaction-app/src/.../feature_plugin.py` | Lifecycle action implementation |
| `plugins/docs/actions.md` | Actions documentation (update) |
| `plugins/docs/compaction.md` | Compaction documentation (new) |

## Configuration Reference

```yaml
# Agent-level configuration (flattened in base_config)
compaction:
  enabled: true              # REQUIRED for plugin to be active
  type: gemini               # REQUIRED for this plugin (gemini | qwen | kimi)
  threshold: 0.5             # Auto-compact when >= 50% of limit
  preserve_tail: 0.3         # Keep last 30% uncompressed
  min_messages: 10           # Minimum messages before considering
  agent_id: null             # Optional: use different agent for compaction
  prompt: null               # Optional: custom prompt override
  settings_overrides: {}     # Optional: model/params for compaction
  verification_pass: true    # Optional: enable verification pass (default: true)
```

**Important**: 
- Config is **agent-level** (not application-level)
- `base_config` is **flattened**, so access via `base_config.get("compaction")`
- Both `enabled: true` AND `type: "gemini"` required for Gemini compaction

## Notes

- Auto-compaction runs after every request (via `request_complete` trigger)
- Should be lightweight: quick token estimation, only compact when needed
- The `min_messages` threshold prevents compacting short conversations
- Provider-native compaction (OpenAI Responses) takes precedence when available