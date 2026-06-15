# Provider Wrapper

Provider plugin wrapper and streaming mixin.

Manages provider plugin state and provides typed interface for provider operations.

## ProviderWrapper

```
ProviderWrapper(plugin_class, extension_classes=None)
```

Bases: `ProviderPlugin`

Wrapper for provider plugin managing state during streaming.

Holds provider state and manages provider extensions in the same language (hot path).

Initialize wrapper with provider plugin class and optional extensions.

Parameters:

| Name                | Type                   | Description                                                  | Default    |
| ------------------- | ---------------------- | ------------------------------------------------------------ | ---------- |
| `plugin_class`      | `type`                 | Provider plugin class (instance methods; stateless behavior) | *required* |
| `extension_classes` | `Optional[List[type]]` | Optional list of provider extension classes                  | `None`     |

Source code in `agent_core/plugin/provider.py`

```
def __init__(
    self,
    plugin_class: type,
    extension_classes: Optional[List[type]] = None,
) -> None:
    """Initialize wrapper with provider plugin class and optional extensions.

    Args:
        plugin_class: Provider plugin class (instance methods; stateless behavior)
        extension_classes: Optional list of provider extension classes
    """
    global logger, log_chunk_processing
    logger = get_logger("provider")
    log_chunk_processing = get_logger("chunk_processing")

    self.plugin_class = plugin_class
    self.plugin = ProviderDefaultsAdapter(plugin_class())
    self.state: Optional[Dict[str, Any]] = None
    self.name = getattr(plugin_class, "name", plugin_class.__name__)
    self.version = getattr(plugin_class, "version", "unknown")
    self._extensions: List[ExtensionWrapper] = []
    self._active_extensions: Optional[List[ExtensionWrapper]] = None
    self._last_native_messages: List[Dict[str, Any]] = []
    self._request_context: Optional[Dict[str, Any]] = None
    if extension_classes:
        for ext_cls in extension_classes:
            self._extensions.append(ExtensionWrapper(ext_cls))
```

### extensions

```
extensions
```

Get extension wrappers.

Returns:

| Type                     | Description                                    |
| ------------------------ | ---------------------------------------------- |
| `List[ExtensionWrapper]` | List of registered ExtensionWrapper instances. |

### accepted_tool_schema_formats

```
accepted_tool_schema_formats(config, state=None)
```

Return schema formats this provider can send directly.

Source code in `agent_core/plugin/provider.py`

```
def accepted_tool_schema_formats(
    self,
    config: Dict[str, Any],
    state: Dict[str, Any] | None = None,
) -> List[str]:
    """Return schema formats this provider can send directly."""
    return self.plugin.accepted_tool_schema_formats(config, state)
```

### add_extensions

```
add_extensions(extension_classes)
```

Add provider extensions (same language).

Parameters:

| Name                | Type         | Description                                | Default    |
| ------------------- | ------------ | ------------------------------------------ | ---------- |
| `extension_classes` | `List[type]` | Extension classes to add to this provider. | *required* |

Source code in `agent_core/plugin/provider.py`

```
def add_extensions(self, extension_classes: List[type]) -> None:
    """Add provider extensions (same language).

    Args:
        extension_classes: Extension classes to add to this provider.
    """
    for ext_cls in extension_classes:
        self._extensions.append(ExtensionWrapper(ext_cls))
```

### apply_extension_transforms

```
apply_extension_transforms(messages, native_messages)
```

Apply extension transforms to provider-native messages.

Parameters:

| Name              | Type                   | Description                            | Default    |
| ----------------- | ---------------------- | -------------------------------------- | ---------- |
| `messages`        | `List[Dict[str, Any]]` | Core messages (context).               | *required* |
| `native_messages` | `List[Dict[str, Any]]` | Provider-native messages to transform. | *required* |

Returns:

| Type                   | Description                                                         |
| ---------------------- | ------------------------------------------------------------------- |
| `List[Dict[str, Any]]` | Transformed provider-native messages after applying each extension. |

Source code in `agent_core/plugin/provider.py`

```
def apply_extension_transforms(
    self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Apply extension transforms to provider-native messages.

    Args:
        messages: Core messages (context).
        native_messages: Provider-native messages to transform.

    Returns:
        Transformed provider-native messages after applying each extension.
    """
    state = self._get_state()
    result = native_messages
    for ext in self._iter_extensions():
        result = ext.to_native_messages(messages, result, state)
    return result
```

### call_api

```
call_api(native_messages, state, *, request_id=None)
```

Make non-streaming API call and allow extensions to finalize outputs.

Initializes the native history baseline, calls the provider, updates wrapper state, and returns full native history for subsequent steps.

Parameters:

| Name              | Type                   | Description                                                    | Default    |
| ----------------- | ---------------------- | -------------------------------------------------------------- | ---------- |
| `native_messages` | `List[Dict[str, Any]]` | Provider-native inputs.                                        | *required* |
| `state`           | `Dict[str, Any]`       | Shared provider state (optional; wrapper state used if empty). | *required* |

Returns:

| Type                                                                                      | Description                                                                  |
| ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]` | Tuple of (partial_messages, final_messages, full_native_history, new_state). |

Source code in `agent_core/plugin/provider.py`

```
def call_api(
    self,
    native_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
    *,
    request_id: str | None = None,
) -> Tuple[
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    Dict[str, Any],
]:
    """Make non-streaming API call and allow extensions to finalize outputs.

    Initializes the native history baseline, calls the provider, updates wrapper state,
    and returns full native history for subsequent steps.

    Args:
        native_messages: Provider-native inputs.
        state: Shared provider state (optional; wrapper state used if empty).

    Returns:
        Tuple of (partial_messages, final_messages, full_native_history, new_state).
    """
    if self.state is None:
        raise RuntimeError(f"Provider {self.name} not initialized")
    working_state = state or self.state
    # Initialize history baseline
    self._last_native_messages = list(native_messages)
    partials, final_messages, native_returned, new_state = self.plugin.call_api(
        self._last_native_messages,
        working_state,
        request_id=request_id,
    )
    # Merge to full history and track
    full_history = self._merge_history(self._last_native_messages, native_returned)

    # Let extensions finalize non-streaming finals against the full history.
    for ext in self._iter_extensions():
        final_messages, full_history, new_state = ext.finalize(
            final_messages,
            full_history,
            new_state,
            context=self._request_context,
        )

    self.state = new_state
    self._last_native_messages = full_history
    return partials, final_messages, full_history, self._get_state()
```

### emitted_tool_call_formats

```
emitted_tool_call_formats(config, state=None)
```

Return tool-call formats this provider may emit.

Source code in `agent_core/plugin/provider.py`

```
def emitted_tool_call_formats(
    self,
    config: Dict[str, Any],
    state: Dict[str, Any] | None = None,
) -> List[str]:
    """Return tool-call formats this provider may emit."""
    return self.plugin.emitted_tool_call_formats(config, state)
```

### execute_extension_action

```
execute_extension_action(
    plugin_id,
    action_id,
    session,
    native_messages,
    params,
    context,
    state,
)
```

Dispatch a session-scoped action to the matching active extension.

Source code in `agent_core/plugin/provider.py`

```
def execute_extension_action(
    self,
    plugin_id: str,
    action_id: str,
    session: Session,
    native_messages: List[Dict[str, Any]],
    params: Dict[str, Any],
    context: Optional[Dict[str, Any]],
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """Dispatch a session-scoped action to the matching active extension."""

    for ext in self._iter_extensions():
        if ext.name != plugin_id:
            continue
        return ext.execute_action(
            action_id, session, native_messages, params, context, state
        )
    raise KeyError(f"Unknown provider extension {plugin_id!r}")
```

### finalize

```
finalize(native_messages, state, *, context=None)
```

Finalize provider turn and let extensions enhance outputs.

Parameters:

| Name              | Type                   | Description                                                            | Default    |
| ----------------- | ---------------------- | ---------------------------------------------------------------------- | ---------- |
| `native_messages` | `List[Dict[str, Any]]` | Full provider-native history for this turn (baseline if no streaming). | *required* |
| `state`           | `Dict[str, Any]`       | Shared provider state (optional; wrapper state used if empty).         | *required* |

Returns:

| Type                                                                | Description                                                                |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]` | Tuple of (final_provider_native_messages, full_native_history, new_state). |

Source code in `agent_core/plugin/provider.py`

```
def finalize(
    self,
    native_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Finalize provider turn and let extensions enhance outputs.

    Args:
        native_messages: Full provider-native history for this turn (baseline if no streaming).
        state: Shared provider state (optional; wrapper state used if empty).

    Returns:
        Tuple of (final_provider_native_messages, full_native_history, new_state).
    """
    if self.state is None:
        raise RuntimeError(f"Provider {self.name} not initialized")
    working_state = state or self.state

    # Use full history baseline
    baseline = self._last_native_messages or list(native_messages)
    active_context = context if isinstance(context, dict) else self._request_context
    final_messages, native_returned, new_state = self.plugin.finalize(
        baseline,
        working_state,
        context=active_context,
    )

    # Merge and allow extensions to modify full history
    full_history = self._merge_history(baseline, native_returned)
    for ext in self._iter_extensions():
        final_messages, full_history, new_state = ext.finalize(
            final_messages,
            full_history,
            new_state,
            context=active_context,
        )

    self.state = new_state
    # track latest full history
    self._last_native_messages = full_history

    return final_messages, full_history, self._get_state()
```

### from_native_messages

```
from_native_messages(
    native_messages, state, *, context=None
)
```

Convert provider-native messages back to core messages.

Parameters:

| Name              | Type                   | Description                                                    | Default    |
| ----------------- | ---------------------- | -------------------------------------------------------------- | ---------- |
| `native_messages` | `List[Dict[str, Any]]` | Provider-native messages to convert.                           | *required* |
| `state`           | `Dict[str, Any]`       | Shared provider state (optional; wrapper state used if empty). | *required* |

Returns:

| Type                   | Description         |
| ---------------------- | ------------------- |
| `List[Dict[str, Any]]` | Core message dicts. |

Source code in `agent_core/plugin/provider.py`

```
def from_native_messages(
    self,
    native_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Convert provider-native messages back to core messages.

    Args:
        native_messages: Provider-native messages to convert.
        state: Shared provider state (optional; wrapper state used if empty).

    Returns:
        Core message dicts.
    """
    if self.state is None:
        raise RuntimeError(f"Provider {self.name} not initialized")
    working_state = state or self.state
    return self.plugin.from_native_messages(
        native_messages,
        working_state,
        context=context,
    )
```

### get_config_schema

```
get_config_schema()
```

Get provider configuration schema.

Returns:

| Type             | Description                                          |
| ---------------- | ---------------------------------------------------- |
| `Dict[str, Any]` | JSON schema mapping for the provider, or empty dict. |

Source code in `agent_core/plugin/provider.py`

```
def get_config_schema(self) -> Dict[str, Any]:
    """Get provider configuration schema.

    Returns:
        JSON schema mapping for the provider, or empty dict.
    """
    return self.plugin.get_config_schema()
```

### get_extension_actions

```
get_extension_actions(state)
```

Return session-scoped action definitions for active extensions.

Source code in `agent_core/plugin/provider.py`

```
def get_extension_actions(
    self,
    state: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    """Return session-scoped action definitions for active extensions."""

    return {ext.name: ext.get_actions(state) for ext in self._iter_extensions()}
```

### get_extension_config_schemas

```
get_extension_config_schemas()
```

Get config schemas for all extensions.

Returns:

| Type             | Description                                     |
| ---------------- | ----------------------------------------------- |
| `Dict[str, Any]` | Mapping from extension name to its JSON schema. |

Source code in `agent_core/plugin/provider.py`

```
def get_extension_config_schemas(self) -> Dict[str, Any]:
    """Get config schemas for all extensions.

    Returns:
        Mapping from extension name to its JSON schema.
    """
    return {ext.name: ext.get_config_schema() for ext in self._extensions}
```

### get_extension_ui_elements

```
get_extension_ui_elements(config, context=None)
```

Get UI schemas for registered extensions.

Uses the same priority-sorted extension order as the request pipeline.

Source code in `agent_core/plugin/provider.py`

```
def get_extension_ui_elements(
    self,
    config: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Get UI schemas for registered extensions.

    Uses the same priority-sorted extension order as the request pipeline.
    """

    return {
        ext.name: ext.get_ui_elements(config, context)
        for ext in self._iter_extensions()
    }
```

### get_last_native_messages

```
get_last_native_messages()
```

Return the latest accumulated provider-native messages tracked during streaming.

Returns:

| Type                   | Description                                                                |
| ---------------------- | -------------------------------------------------------------------------- |
| `List[Dict[str, Any]]` | Full provider-native history after the most recent chunk or finalize step. |

Source code in `agent_core/plugin/provider.py`

```
def get_last_native_messages(self) -> List[Dict[str, Any]]:
    """Return the latest accumulated provider-native messages tracked during streaming.

    Returns:
        Full provider-native history after the most recent chunk or finalize step.
    """
    # type: ignore[attr-defined]
    return getattr(self, "_last_native_messages", [])
```

### get_models

```
get_models(config)
```

Delegate model discovery to the underlying provider via adapter.

Source code in `agent_core/plugin/provider.py`

```
def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Delegate model discovery to the underlying provider via adapter."""
    return self.plugin.get_models(config)
```

### get_state

```
get_state()
```

Expose the current shared state for orchestration.

Returns:

| Type             | Description            |
| ---------------- | ---------------------- |
| `Dict[str, Any]` | Shared provider state. |

Source code in `agent_core/plugin/provider.py`

```
def get_state(self) -> Dict[str, Any]:
    """Expose the current shared state for orchestration.

    Returns:
        Shared provider state.
    """
    return self._get_state()
```

### get_tags

```
get_tags(config, models)
```

Delegate tag computation to the underlying provider via adapter.

Source code in `agent_core/plugin/provider.py`

```
def get_tags(
    self,
    config: Dict[str, Any],
    models: List[Dict[str, Any]],
) -> List[str]:
    """Delegate tag computation to the underlying provider via adapter."""
    return self.plugin.get_tags(config, models)
```

### get_tool_interop_contribution

```
get_tool_interop_contribution(config, state=None)
```

Return provider-contributed tool interop accessors/adapters.

Source code in `agent_core/plugin/provider.py`

```
def get_tool_interop_contribution(
    self,
    config: Dict[str, Any],
    state: Dict[str, Any] | None = None,
) -> ToolInteropContribution:
    """Return provider-contributed tool interop accessors/adapters."""
    return self.plugin.get_tool_interop_contribution(config, state)
```

### get_ui_elements

```
get_ui_elements(config, context=None)
```

Get provider UI elements.

Source code in `agent_core/plugin/provider.py`

```
def get_ui_elements(
    self,
    config: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Get provider UI elements."""
    return self.plugin.get_ui_elements(config, context)
```

### init

```
init(config)
```

Initialize provider and extensions using shared state owned by provider wrapper.

Parameters:

| Name     | Type             | Description            | Default    |
| -------- | ---------------- | ---------------------- | ---------- |
| `config` | `Dict[str, Any]` | Provider configuration | *required* |

Returns:

| Type             | Description                                                          |
| ---------------- | -------------------------------------------------------------------- |
| `Dict[str, Any]` | Shared provider state after extensions have updated it (if they do). |

Source code in `agent_core/plugin/provider.py`

```
def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize provider and extensions using shared state owned by provider wrapper.

    Args:
        config: Provider configuration

    Returns:
        Shared provider state after extensions have updated it (if they do).
    """
    self.state = self.plugin.init(config)
    # Let extensions update shared state during init
    pipe = pipeline(config)
    self.state = pipe(
        [ext.init for ext in self._iter_extensions()], self._get_state()
    )
    return self._get_state()
```

### initialize_request

```
initialize_request(
    native_messages, state, *, request_id=None, context=None
)
```

Run provider and extensions initialize_request with native messages for a new turn.

Parameters:

| Name              | Type                   | Description                                                    | Default    |
| ----------------- | ---------------------- | -------------------------------------------------------------- | ---------- |
| `native_messages` | `List[Dict[str, Any]]` | Provider-native messages to initialize the new turn.           | *required* |
| `state`           | `Dict[str, Any]`       | Shared provider state (optional; wrapper state used if empty). | *required* |

Returns:

| Type                                          | Description                                                                           |
| --------------------------------------------- | ------------------------------------------------------------------------------------- |
| `Tuple[List[Dict[str, Any]], Dict[str, Any]]` | Tuple of (full provider-native history for this turn, updated shared provider state). |

Source code in `agent_core/plugin/provider.py`

```
def initialize_request(
    self,
    native_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
    *,
    request_id: str | None = None,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Run provider and extensions initialize_request with native messages for a new turn.

    Args:
        native_messages: Provider-native messages to initialize the new turn.
        state: Shared provider state (optional; wrapper state used if empty).

    Returns:
        Tuple of (full provider-native history for this turn, updated shared provider state).
    """
    if self.state is None:
        raise RuntimeError(f"Provider {self.name} not initialized")
    working_state = state or self.state
    self._request_context = context if isinstance(context, dict) else None
    # Start full native history at request boundary
    self._last_native_messages = list(native_messages)
    native_after_provider, new_state = self.plugin.initialize_request(
        native_messages,
        working_state,
        request_id=request_id,
        context=context,
    )
    # Sort extensions by priority (lower numbers run first, default: 100)
    sorted_extensions = sorted(
        self._iter_extensions(), key=lambda ext: getattr(ext, "priority", 100)
    )
    native_after_exts = native_after_provider
    for ext in sorted_extensions:
        native_after_exts, new_state = ext.initialize_request(
            native_after_exts,
            new_state,
            context=context,
        )
    if isinstance(context, dict):
        new_state = {**new_state, "_request_context": context}
    self.state = new_state
    self._last_native_messages = list(native_after_exts)
    return native_after_exts, self._get_state()
```

### process_chunk

```
process_chunk(native_chunk, native_messages, state)
```

Process provider chunk and invoke extensions (hot path).

Converts partial messages to core using provider + extensions when possible.

Parameters:

| Name              | Type                   | Description                                                    | Default    |
| ----------------- | ---------------------- | -------------------------------------------------------------- | ---------- |
| `native_chunk`    | `Dict[str, Any]`       | Provider-native streaming chunk.                               | *required* |
| `native_messages` | `List[Dict[str, Any]]` | Full provider-native history up to this chunk.                 | *required* |
| `state`           | `Dict[str, Any]`       | Shared provider state (optional; wrapper state used if empty). | *required* |

Returns:

| Type                                                                                      | Description                                                                       |
| ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]` | Tuple of (partial_core_messages, final_messages, full_native_history, new_state). |

Source code in `agent_core/plugin/provider.py`

```
def process_chunk(
    self,
    native_chunk: Dict[str, Any],
    native_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
) -> Tuple[
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    Dict[str, Any],
]:
    """Process provider chunk and invoke extensions (hot path).

    Converts partial messages to core using provider + extensions when possible.

    Args:
        native_chunk: Provider-native streaming chunk.
        native_messages: Full provider-native history up to this chunk.
        state: Shared provider state (optional; wrapper state used if empty).

    Returns:
        Tuple of (partial_core_messages, final_messages, full_native_history, new_state).
    """
    if self.state is None:
        raise RuntimeError(f"Provider {self.name} not initialized")
    working_state = state or self.state
    # Use the provided full native history directly
    full_history = list(native_messages)

    log_chunk_processing.debug("processing chunk", chunk=native_chunk)

    partial_messages, final_messages, full_history, new_state = (
        self.plugin.process_chunk(native_chunk, full_history, working_state)
    )

    # Let extensions transform partials/finals/native history in order
    ext_state = new_state
    pipe = pipeline(native_chunk)
    partial_messages, final_messages, full_history, ext_state = pipe(
        [ext.process_chunk for ext in self._iter_extensions()],
        partial_messages,
        final_messages,
        full_history,
        ext_state,
    )
    self.state = ext_state

    log_chunk_processing.debug("processed chunk", partials=partial_messages)

    # Convert partial messages (provider-native) to core using the same
    # from_native pipeline as final messages (provider first, then active
    # extensions). Features are cold-path only and are not applied here.
    core_partials: List[Dict[str, Any]] = []
    if partial_messages:
        try:
            pipe = pipeline(partial_messages)
            core_partials = pipe(
                [self.plugin.from_native_messages]
                + [ext.from_native_messages for ext in self._iter_extensions()],
                ext_state,
            )
        except Exception as e:
            logger.warning(
                "failed to convert partials to core, using as-is", error=str(e)
            )
            core_partials = partial_messages
    # Track latest full history
    self._last_native_messages = full_history

    log_chunk_processing.debug(
        "converted partials to core", core_partials=core_partials
    )

    return core_partials, final_messages, full_history, self._get_state()
```

### reset_state

```
reset_state()
```

Discard internal shared state after request.

Source code in `agent_core/plugin/provider.py`

```
def reset_state(self) -> None:
    """Discard internal shared state after request."""
    self.state = None
    self._last_native_messages = []
    self._active_extensions = None
```

### set_active_extensions

```
set_active_extensions(extensions)
```

Restrict active extensions for the current request.

Source code in `agent_core/plugin/provider.py`

```
def set_active_extensions(self, extensions: List[ExtensionWrapper]) -> None:
    """Restrict active extensions for the current request."""
    self._active_extensions = list(extensions)
```

### set_state

```
set_state(state)
```

Replace the current shared state (used by features).

Parameters:

| Name    | Type             | Description                       | Default    |
| ------- | ---------------- | --------------------------------- | ---------- |
| `state` | `Dict[str, Any]` | New shared provider state to set. | *required* |

Raises:

| Type           | Description                          |
| -------------- | ------------------------------------ |
| `RuntimeError` | If wrapper has not been initialized. |

Source code in `agent_core/plugin/provider.py`

```
def set_state(self, state: Dict[str, Any]) -> None:
    """Replace the current shared state (used by features).

    Args:
        state: New shared provider state to set.

    Raises:
        RuntimeError: If wrapper has not been initialized.
    """
    if self.state is None:
        raise RuntimeError(f"Provider {self.name} not initialized")
    self.state = state
```

### stream_api

```
stream_api(native_messages, state, *, request_id=None)
```

Make streaming API call (state-validated).

Parameters:

| Name              | Type                   | Description                                                    | Default    |
| ----------------- | ---------------------- | -------------------------------------------------------------- | ---------- |
| `native_messages` | `List[Dict[str, Any]]` | Provider-native inputs.                                        | *required* |
| `state`           | `Dict[str, Any]`       | Shared provider state (optional; wrapper state used if empty). | *required* |

Yields:

| Type             | Description                       |
| ---------------- | --------------------------------- |
| `Dict[str, Any]` | Provider-native streaming chunks. |

Source code in `agent_core/plugin/provider.py`

```
def stream_api(
    self,
    native_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
    *,
    request_id: str | None = None,
) -> Iterator[Dict[str, Any]]:
    """Make streaming API call (state-validated).

    Args:
        native_messages: Provider-native inputs.
        state: Shared provider state (optional; wrapper state used if empty).

    Yields:
        Provider-native streaming chunks.
    """
    if self.state is None:
        raise RuntimeError(f"Provider {self.name} not initialized")
    working_state = state or self.state
    yield from self.plugin.stream_api(
        native_messages, working_state, request_id=request_id
    )
```

### stream_api_async

```
stream_api_async(
    native_messages, state, *, request_id=None
)
```

Make async streaming API call, preferring native async if available.

Parameters:

| Name              | Type                   | Description                                                    | Default    |
| ----------------- | ---------------------- | -------------------------------------------------------------- | ---------- |
| `native_messages` | `List[Dict[str, Any]]` | Provider-native inputs.                                        | *required* |
| `state`           | `Dict[str, Any]`       | Shared provider state (optional; wrapper state used if empty). | *required* |

Yields:

| Type                            | Description                       |
| ------------------------------- | --------------------------------- |
| `AsyncIterator[Dict[str, Any]]` | Provider-native streaming chunks. |

Source code in `agent_core/plugin/provider.py`

```
async def stream_api_async(
    self,
    native_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
    *,
    request_id: str | None = None,
) -> AsyncIterator[Dict[str, Any]]:
    """Make async streaming API call, preferring native async if available.

    Args:
        native_messages: Provider-native inputs.
        state: Shared provider state (optional; wrapper state used if empty).

    Yields:
        Provider-native streaming chunks.
    """
    if self.state is None:
        raise RuntimeError(f"Provider {self.name} not initialized")
    working_state = state or self.state
    if hasattr(self.plugin, "stream_api_async"):
        async for chunk in self.plugin.stream_api_async(  # type: ignore[attr-defined]
            native_messages,
            working_state,
            request_id=request_id,
        ):
            yield chunk
        return
    # Fallback to sync stream
    for chunk in self.plugin.stream_api(
        native_messages, working_state, request_id=request_id
    ):
        yield chunk
```

### stream_messages

```
stream_messages(native_messages, state, *, request_id=None)
```

Stream provider results while processing chunks internally.

Events yielded

- {"type": "partial", "message": }
- {"type": "final_messages", "messages": }

Parameters:

| Name              | Type                   | Description                                                | Default    |
| ----------------- | ---------------------- | ---------------------------------------------------------- | ---------- |
| `native_messages` | `List[Dict[str, Any]]` | Provider-native input messages for this request.           | *required* |
| `state`           | `Dict[str, Any]`       | Current shared provider state (or wrapper state if empty). | *required* |

Yields:

| Type             | Description                                                                      |
| ---------------- | -------------------------------------------------------------------------------- |
| `Dict[str, Any]` | Dict events representing partials and batches of final provider-native messages. |

Raises:

| Type           | Description                                        |
| -------------- | -------------------------------------------------- |
| `RuntimeError` | If the wrapper is not initialized (missing state). |

Source code in `agent_core/plugin/provider.py`

```
def stream_messages(
    self,
    native_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
    *,
    request_id: str | None = None,
) -> Iterator[Dict[str, Any]]:
    """Stream provider results while processing chunks internally.

    Events yielded:
        - {"type": "partial", "message": <partial_message_like_core>}
        - {"type": "final_messages", "messages": <list_of_provider_native_finals>}

    Args:
        native_messages: Provider-native input messages for this request.
        state: Current shared provider state (or wrapper state if empty).

    Yields:
        Dict events representing partials and batches of final provider-native messages.

    Raises:
        RuntimeError: If the wrapper is not initialized (missing state).
    """
    # Resolve initial state via wrapper; error if uninitialized
    try:
        working_state = state or self._get_state()  # type: ignore[attr-defined]
    except Exception:
        raise RuntimeError(f"Provider {self.name} not initialized")  # type: ignore[attr-defined]

    # Initialize full native history for this turn
    self._last_native_messages = list(native_messages)  # type: ignore[attr-defined]
    current_native = self._last_native_messages
    chunk_count = 0
    for native_chunk in self.plugin.stream_api(
        current_native,
        working_state,
        request_id=request_id,
    ):  # type: ignore[attr-defined]
        chunk_count += 1
        partials, finals, current_native, working_state = self.process_chunk(  # type: ignore[misc]
            native_chunk, current_native, working_state
        )
        # track latest native messages (full history)
        self._last_native_messages = current_native  # type: ignore[attr-defined]
        # yield partials first
        for p in partials:
            yield {"type": "partial", "message": p}
        if finals:
            yield {"type": "final_messages", "messages": finals}

    logger.debug("stream_messages complete")
```

### stream_messages_async

```
stream_messages_async(
    native_messages, state, *, request_id=None
)
```

Async variant of stream_messages.

Prefers the provider's native async streaming when available, falling back to sync streaming otherwise.

Parameters:

| Name              | Type                   | Description                                                | Default    |
| ----------------- | ---------------------- | ---------------------------------------------------------- | ---------- |
| `native_messages` | `List[Dict[str, Any]]` | Provider-native input messages for this request.           | *required* |
| `state`           | `Dict[str, Any]`       | Current shared provider state (or wrapper state if empty). | *required* |

Yields:

| Type                            | Description                                                                      |
| ------------------------------- | -------------------------------------------------------------------------------- |
| `AsyncIterator[Dict[str, Any]]` | Dict events representing partials and batches of final provider-native messages. |

Raises:

| Type           | Description                                        |
| -------------- | -------------------------------------------------- |
| `RuntimeError` | If the wrapper is not initialized (missing state). |

Source code in `agent_core/plugin/provider.py`

```
async def stream_messages_async(
    self,
    native_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
    *,
    request_id: str | None = None,
) -> AsyncIterator[Dict[str, Any]]:
    """Async variant of stream_messages.

    Prefers the provider's native async streaming when available, falling back
    to sync streaming otherwise.

    Args:
        native_messages: Provider-native input messages for this request.
        state: Current shared provider state (or wrapper state if empty).

    Yields:
        Dict events representing partials and batches of final provider-native messages.

    Raises:
        RuntimeError: If the wrapper is not initialized (missing state).
    """
    # Resolve initial state via wrapper; error if uninitialized
    try:
        working_state = state or self._get_state()  # type: ignore[attr-defined]
    except Exception:
        raise RuntimeError(f"Provider {self.name} not initialized")  # type: ignore[attr-defined]
    current_native = list(native_messages)

    if hasattr(self.plugin, "stream_api_async"):  # type: ignore[attr-defined]
        async for native_chunk in self.plugin.stream_api_async(  # type: ignore[attr-defined]
            current_native,
            working_state,
            request_id=request_id,
        ):
            partials, finals, current_native, working_state = self.process_chunk(  # type: ignore[misc]
                native_chunk, current_native, working_state
            )
            self._last_native_messages = current_native  # type: ignore[attr-defined]
            for p in partials:
                yield {"type": "partial", "message": p}
            if finals:
                yield {"type": "final_messages", "messages": finals}
        return

    # Fallback to sync stream
    for native_chunk in self.plugin.stream_api(
        current_native,
        working_state,
        request_id=request_id,
    ):  # type: ignore[attr-defined]
        partials, finals, current_native, working_state = self.process_chunk(  # type: ignore[misc]
            native_chunk, current_native, working_state
        )
        self._last_native_messages = current_native  # type: ignore[attr-defined]
        for p in partials:
            yield {"type": "partial", "message": p}
        if finals:
            yield {"type": "final_messages", "messages": finals}
```

### to_display_format

```
to_display_format(message, state)
```

Format a message for display if supported; otherwise return as-is.

Parameters:

| Name      | Type             | Description                                                    | Default    |
| --------- | ---------------- | -------------------------------------------------------------- | ---------- |
| `message` | `Dict[str, Any]` | Core message to format.                                        | *required* |
| `state`   | `Dict[str, Any]` | Shared provider state (optional; wrapper state used if empty). | *required* |

Returns:

| Type             | Description                                                         |
| ---------------- | ------------------------------------------------------------------- |
| `Dict[str, Any]` | Display-friendly message dictionary or the input message unchanged. |

Source code in `agent_core/plugin/provider.py`

```
def to_display_format(
    self, message: Dict[str, Any], state: Dict[str, Any]
) -> Dict[str, Any]:
    """Format a message for display if supported; otherwise return as-is.

    Args:
        message: Core message to format.
        state: Shared provider state (optional; wrapper state used if empty).

    Returns:
        Display-friendly message dictionary or the input message unchanged.
    """
    if self.state is None:
        raise RuntimeError(f"Provider {self.name} not initialized")
    working_state = state or self.state
    return self.plugin.to_display_format(message, working_state)
```

### to_native_messages

```
to_native_messages(messages, state, *, context=None)
```

Convert core messages to provider's native format (provider-first).

Parameters:

| Name       | Type                   | Description                                                    | Default    |
| ---------- | ---------------------- | -------------------------------------------------------------- | ---------- |
| `messages` | `List[Dict[str, Any]]` | Core message dicts.                                            | *required* |
| `state`    | `Dict[str, Any]`       | Shared provider state (optional; wrapper state used if empty). | *required* |

Returns:

| Type                   | Description                   |
| ---------------------- | ----------------------------- |
| `List[Dict[str, Any]]` | Provider-native message list. |

Source code in `agent_core/plugin/provider.py`

```
def to_native_messages(
    self,
    messages: List[Dict[str, Any]],
    state: Dict[str, Any],
    *,
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Convert core messages to provider's native format (provider-first).

    Args:
        messages: Core message dicts.
        state: Shared provider state (optional; wrapper state used if empty).

    Returns:
        Provider-native message list.
    """
    if self.state is None:
        raise RuntimeError(f"Provider {self.name} not initialized")
    working_state = state or self.state
    return self.plugin.to_native_messages(
        messages,
        working_state,
        context=context,
    )
```
