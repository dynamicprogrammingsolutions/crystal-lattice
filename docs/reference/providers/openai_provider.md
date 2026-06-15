# OpenAI-Compatible Provider

OpenAI-Compatible Provider Plugin (plugins/providers/openai/python/openai_provider.py)

Minimal provider for OpenAI-compatible Chat Completions endpoints (e.g., Ollama at /v1). Loads configuration only from the provided config dict (no environment variable usage).

## OpenAICompatibleProvider

```
OpenAICompatibleProvider()
```

Bases: `ProviderPlugin`

Source code in `plugins/openai_provider.py`

```
def __init__(self) -> None:
    self._inflight_lock = threading.Lock()
    self._inflight_requests: Dict[str, _InflightRequest] = {}
```

### extract_delta

```
extract_delta(native_chunk)
```

Extract a provider-native delta dictionary from a streaming chunk.

Returns the first choice object when present, or an empty dict.

Source code in `plugins/openai_provider.py`

```
def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a provider-native delta dictionary from a streaming chunk.

    Returns the first choice object when present, or an empty dict.
    """
    if "choices" in native_chunk and native_chunk["choices"]:
        return native_chunk["choices"][0]

    return {}
```

### finalize

```
finalize(native_messages, state)
```

Finalize streaming by emitting the accumulated partial as a final.

When streaming was used, `state["partial"]` holds the merged assistant message (content, role, reasoning, tool_calls, etc.) built up across chunks by the provider and any extensions. Non-streaming calls leave it as `None`.

Source code in `plugins/openai_provider.py`

```
def finalize(
    self,
    native_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Finalize streaming by emitting the accumulated partial as a final.

    When streaming was used, `state["partial"]` holds the merged assistant
    message (content, role, reasoning, tool_calls, etc.) built up across
    chunks by the provider and any extensions. Non-streaming calls leave it
    as ``None``.
    """
    current_partial = state.get("partial", None)

    if current_partial:
        return [current_partial], [*native_messages, current_partial], state

    return [], native_messages, state
```

### from_native_messages

```
from_native_messages(native_messages, state)
```

Convert provider-native finals to core messages.

This provider-level conversion intentionally ignores any provider-specific reasoning fields. Reasoning content should be surfaced by dedicated extensions (e.g., thinking extensions) via message metadata rather than as a top-level field.

Source code in `plugins/openai_provider.py`

```
def from_native_messages(
    self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Convert provider-native finals to core messages.

    This provider-level conversion intentionally ignores any
    provider-specific reasoning fields. Reasoning content should be
    surfaced by dedicated extensions (e.g., thinking extensions)
    via message metadata rather than as a top-level field.
    """
    normalized: List[Dict[str, Any]] = []
    for m in native_messages:
        if not isinstance(m, dict):
            continue
        if not ("role" in m or "content" in m):
            # Ignore non-message shapes (like full completion objects)
            continue

        raw_internal = m.get("_metadata") or {}
        internal_md = dict(raw_internal) if isinstance(raw_internal, dict) else {}
        internal_md.pop("native_indices", None)
        msg = {
            "role": m.get("role", "assistant"),
            "content": m.get("content", ""),
        }
        normalized.append({**msg, "metadata": internal_md})
    return normalized
```

### get_models

```
get_models(config)
```

Return minimal model descriptors for this provider.

Currently returns the configured `model` (if any) as a single ModelDescriptor with only an `id` field.

Source code in `plugins/openai_provider.py`

```
def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return minimal model descriptors for this provider.

    Currently returns the configured `model` (if any) as a single
    ModelDescriptor with only an `id` field.
    """
    model = config.get("model")
    if isinstance(model, str) and model:
        return [{"id": model}]
    return []
```

### get_tags

```
get_tags(config, models)
```

Return capability tags for the OpenAI-compatible provider.

This implementation is intentionally simple and conservative; it assumes chat-completions style models with tool calling and streaming support.

Source code in `plugins/openai_provider.py`

```
def get_tags(
    self,
    config: Dict[str, Any],
    models: List[Dict[str, Any]],
) -> List[str]:
    """Return capability tags for the OpenAI-compatible provider.

    This implementation is intentionally simple and conservative; it
    assumes chat-completions style models with tool calling and
    streaming support.
    """
    tags: List[str] = ["provider:openai_compatible"]
    tags.append("supports_streaming")
    tags.append("supports_tools")
    tags.append("supports_thinking")
    return tags
```

### process_chunk

```
process_chunk(native_chunk, native_messages, state)
```

Process a streaming chunk into provider-native partials.

Pattern:

- Extract a delta from the chunk
- Reduce it into a partial fragment and update the accumulator
- Do not emit finals or modify history; :meth:`finalize` is responsible for producing the final message from the accumulated partial.

Source code in `plugins/openai_provider.py`

```
def process_chunk(
    self,
    native_chunk: Dict[str, Any],
    native_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Process a streaming chunk into provider-native partials.

    Pattern:
    - Extract a delta from the chunk
    - Reduce it into a partial fragment and update the accumulator
    - Do not emit finals or modify history; :meth:`finalize` is responsible
      for producing the final message from the accumulated partial.
    """
    partial_msg, accumulated = self.process_delta(
        delta=self.extract_delta(native_chunk), accumulated=state.get("partial", {})
    )

    partials = [partial_msg] if partial_msg else []
    finals: List[Dict[str, Any]] = []
    new_state = {**state, "partial": accumulated}

    return partials, finals, native_messages, new_state
```

### process_delta

```
process_delta(delta, accumulated)
```

Reduce a delta dict into a new partial and accumulator.

Returns the current partial fragment from this chunk and an updated accumulator used later by :meth:`finalize` to build the final message.

Source code in `plugins/openai_provider.py`

```
def process_delta(self, delta: Dict[str, Any], accumulated):
    """Reduce a delta dict into a new partial and accumulator.

    Returns the current partial fragment from this chunk and an updated
    accumulator used later by :meth:`finalize` to build the final message.
    """
    # Normalize accumulator once
    base = accumulated or {}

    # Prefer full message objects, then deltas
    content = delta.get("message") or delta.get("delta") or None
    if content is None:
        return None, base

    new_accumulated = self._merge_delta_content(
        base,
        content,
        override=["role"],
        accumulate=["content"],
    )
    return content, new_accumulated
```
