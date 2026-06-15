# AgentCore

Core SDK for the AI Agent Platform.

Functional architecture: AgentCore stores only the processing pipeline (plugins via wrappers), all transformations are pure functions that take session/config and return new objects.

Examples:

Basic non-streaming usage:

```
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

session = core.create_session()
session = core.add_message(session, "user", "Hello!")

config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
}
session, finals = core.send_request(session, config)
print(finals[-1]["content"])  # Assistant reply
```

Streaming usage:

```python
for chunk in core.send_request_stream(session, config):
if chunk["type"] == "partial":
print(chunk"message", end="", flush=True)
elif chunk["type"] == "final":
session = chunk["session"]
print("

[Done]")
```

````
Tool schemas and execution:

```python
tool_schemas = core.get_tool_schemas(config)
# Execute tool calls the model asked for (application loop)
tool_results = core.execute_tool_calls(tool_calls, config)
for msg in tool_results:
    session = core.add_message(session, msg["role"], msg["content"], msg.get("metadata"))
````

```

## AgentCore

```

AgentCore(model_cache=None)

```

Stateless processing pipeline for AI Agent Platform.

Stores registered plugin wrappers (processing logic), not runtime state.
All methods are pure functions that take session/config as parameters.
The application layer manages sessions and configuration.

Initialize core with empty plugin pipeline.

Loggers are initialized lazily so that structlog configuration can
be customized by applications before any loggers are created.

Source code in `agent_core/core.py`

```

def __init__(self, model_cache: Optional[ModelDiscoveryCache] = None): """Initialize core with empty plugin pipeline.

```
Loggers are initialized lazily so that structlog configuration can
be customized by applications before any loggers are created.
"""
global logger, log_chunk_processing
logger = get_logger("core")
log_chunk_processing = get_logger("chunk_processing")

self._providers: List[ProviderWrapper] = []
self._features: List[FeatureWrapper] = []
self._tools: List[ToolWrapper] = []
# Model discovery can be shared across fresh AgentCore instances by
# passing the same cache object. Dependency/tag/tool-preparation caches
# remain core-local because they are tied to wrapper/runtime state.
self._model_cache = model_cache or ModelDiscoveryCache()
self._dependency_cache: Dict[
    Tuple[int, str, str],
    Tuple[List[str], List[str], List[str], List[str]],
] = {}
self._tags_cache: Dict[Tuple[int, Tuple[int, str, str]], List[str]] = {}
self._prepared_tool_states: Dict[Tuple[int, str], Dict[str, Any]] = {}
self._prepared_tool_data: Dict[Tuple[int, str], Dict[str, Any]] = {}
self._context = CoreContext(core=self)
```

```

### add_message

```

add_message( session, role, content, metadata=None, config=None, \*, multipart_content=None, after_index=None, context=None, tool_result=None )

```

Add a message to the session (pure function).

When session.metadata contains provider-native history (native_messages)
and a provider is registered, converts the newly added message to
provider-native format and appends it to the stored native history.
Updates verification data for integrity checks.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `session` | `Session` | Current session. | *required* |
| `role` | `MessageRole` | Message role ("system", "user", "assistant", or "tool"). | *required* |
| `content` | `Any` | Message content. | *required* |
| `metadata` | `Optional[Dict[str, Any]]` | Optional per-message metadata. Note: when provider-native history is enabled (session metadata contains native_messages) and the core rebuilds messages from the provider-native sequence, arbitrary metadata is not preserved by default. Persist metadata explicitly via the provider/feature/extension pipelines using the _metadata key on provider-native messages. | `None` |
| `config` | `Optional[Dict[str, Any]]` | Optional configuration used to resolve provider and plugins. | `None` |
| `tool_result` | `Optional[Dict[str, Any]]` | Optional structured tool result payload for this message. This is the canonical structured representation for tool messages and may be consumed by providers when appending to provider-native history. | `None` |
| `after_index` | `Optional[int]` | Optional index after which to insert the message. When None (default), the message is appended at the end. after_index == -1 inserts at the beginning. Negative indices follow Python semantics relative to the end of the message list. | `None` |

Returns:

| Type | Description |
| --- | --- |
| `Session` | New Session with the message added (immutable update). |

Source code in `agent_core/core.py`

```

def add_message( self, session: Session, role: MessageRole, content: Any, metadata: Optional\[Dict[str, Any]\] = None, config: Optional\[Dict[str, Any]\] = None, \*, multipart_content: Optional\[List\[Dict[str, Any]\]\] = None, after_index: Optional[int] = None, context: Optional\[Dict[str, Any]\] = None, tool_result: Optional\[Dict[str, Any]\] = None, ) -> Session: """Add a message to the session (pure function).

```
When session.metadata contains provider-native history (native_messages)
and a provider is registered, converts the newly added message to
provider-native format and appends it to the stored native history.
Updates verification data for integrity checks.

Args:
    session: Current session.
    role: Message role ("system", "user", "assistant", or "tool").
    content: Message content.
    metadata: Optional per-message metadata.
        Note: when provider-native history is enabled (session metadata
        contains ``native_messages``) and the core rebuilds messages
        from the provider-native sequence, arbitrary metadata is not
        preserved by default. Persist metadata explicitly via the
        provider/feature/extension pipelines using the ``_metadata``
        key on provider-native messages.
    config: Optional configuration used to resolve provider and plugins.
    tool_result: Optional structured tool result payload for this
        message. This is the canonical structured representation for
        tool messages and may be consumed by providers when appending
        to provider-native history.
    after_index: Optional index after which to insert the message.
        When ``None`` (default), the message is appended at the end.
        ``after_index == -1`` inserts at the beginning. Negative
        indices follow Python semantics relative to the end of the
        message list.

Returns:
    New Session with the message added (immutable update).
"""
msg_md = dict(metadata) if isinstance(metadata, dict) else {}
message_dict: Dict[str, Any] = {
    "role": role,
    "content": content,
    "metadata": msg_md,
}
if multipart_content:
    message_dict["multipartContent"] = multipart_content
if tool_result is not None:
    message_dict[TOOL_RESULT_FIELD] = tool_result
# Compute insertion point. When after_index is None, append at end.
message_count = len(session.messages)
if after_index is None:
    insert_at = message_count
else:
    if after_index == -1:
        insert_at = 0
    else:
        idx = after_index
        if idx < 0:
            idx = message_count + idx
        if idx < 0 or idx >= message_count:
            raise IndexError("after_index out of range")
        insert_at = idx + 1

# Append uses the existing native-preserving helper. Insert at other
# positions rebuilds native history so that provider-native messages
# stay consistent with the updated core sequence.
if insert_at == message_count:
    # Always prefer the native-preserving helper; when native history
    # cannot be safely updated, it falls back to a core-only append.

    # TODO: Legacy behavior with no config should be removed.
    new_session, _ = self._append_single_message_with_native(
        session,
        message_dict,
        config or {},
        context=context,
    )
    return new_session

new_session, _ = self._insert_single_message_with_native(
    session,
    message_dict,
    insert_at,
    config or {},
    context=context,
)
return new_session
```

```

### apply_feature_completion

```

apply_feature_completion(config, text, completion)

```

Ask features to transform an accepted completion into a snippet.

Iterates over registered feature plugins and calls their
:meth:`apply_completion` hooks in registration order. The first
non-empty string returned is used as the replacement snippet.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `config` | `Dict[str, Any]` | Application configuration for the current agent or request. | *required* |
| `text` | `str` | Full buffer text after the completion has been applied. | *required* |
| `completion` | `Dict[str, Any]` | Completion descriptor dict that was accepted, as previously returned by :meth:get_completions. | *required* |

Returns:

| Type | Description |
| --- | --- |
| `str` | Replacement snippet string, or an empty string when no feature |
| `str` | chooses to handle the completion. |

Source code in `agent_core/core.py`

```

def apply_feature_completion( self, config: Dict[str, Any], text: str, completion: Dict[str, Any], ) -> str: """Ask features to transform an accepted completion into a snippet.

```
Iterates over registered feature plugins and calls their
:meth:`apply_completion` hooks in registration order. The first
non-empty string returned is used as the replacement snippet.

Args:
    config: Application configuration for the current agent or
        request.
    text: Full buffer text after the completion has been applied.
    completion: Completion descriptor dict that was accepted, as
        previously returned by :meth:`get_completions`.

Returns:
    Replacement snippet string, or an empty string when no feature
    chooses to handle the completion.
"""

if not self._features:
    return ""

for feature in self._features:
    out = feature.apply_completion(config, text, completion)
    if isinstance(out, str) and out:
        return out
return ""
```

```

### core_messages_to_native

```

core_messages_to_native( core_messages, config, \*, context=None )

```

Convert core-shaped messages into provider-native messages.

This is a thin public wrapper around the normal provider/extension/
feature conversion path. It is intended for request-time features and
actions that need to synthesize a core message and append its
provider-native form to an in-flight request without re-implementing
provider-specific message shaping.

Source code in `agent_core/core.py`

```

def core_messages_to_native( self, core_messages: List\[Dict[str, Any]\], config: Dict[str, Any], \*, context: Optional\[Dict[str, Any]\] = None, ) -> List\[Dict[str, Any]\]: """Convert core-shaped messages into provider-native messages.

```
This is a thin public wrapper around the normal provider/extension/
feature conversion path. It is intended for request-time features and
actions that need to synthesize a core message and append its
provider-native form to an in-flight request without re-implementing
provider-specific message shaping.
"""

if not isinstance(core_messages, list):
    raise TypeError("core_messages must be a list")
if not isinstance(config, dict):
    raise TypeError("config must be a dict")

return self._core_messages_to_native_for_config(
    core_messages,
    config,
    context=context,
)
```

```

### create_session

```

create_session(session_id=None)

```

Create a new empty session.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `session_id` | `Optional[str]` | Optional session identifier. Auto-generated if omitted. | `None` |

Returns:

| Type | Description |
| --- | --- |
| `Session` | New immutable Session instance with no messages. |

Source code in `agent_core/core.py`

```

def create_session(self, session_id: Optional[str] = None) -> Session: """Create a new empty session.

```
Args:
    session_id: Optional session identifier. Auto-generated if omitted.

Returns:
    New immutable Session instance with no messages.
"""
if session_id is None:
    session_id = str(uuid.uuid4())
return Session(session_id=session_id, messages=[])
```

```

### discover_and_register

```

discover_and_register(modules)

```

Discover plugins from Python modules and register them by duck typing.

Plugin type is inferred based on the presence of methods on the class:
- Provider: has 'stream_api' or 'call_api'
- Provider Extension: has 'process_chunk' (and no tool/provider I/O methods)
- Tool: has 'get_tool_schemas' and 'execute_tool'
- Feature: otherwise

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `modules` | `List[str]` | List of import paths to scan for plugin classes. | *required* |

Returns:

| Type | Description |
| --- | --- |
| `Dict[str, List[str]]` | Summary of registered plugin names by type with keys: providers, features, tools, extensions. |

Source code in `agent_core/core.py`

```

def discover_and_register(self, modules: List[str]) -> Dict\[str, List[str]\]: """Discover plugins from Python modules and register them by duck typing.

```
Plugin type is inferred based on the presence of methods on the class:
- Provider: has 'stream_api' or 'call_api'
- Provider Extension: has 'process_chunk' (and no tool/provider I/O methods)
- Tool: has 'get_tool_schemas' and 'execute_tool'
- Feature: otherwise

Args:
    modules: List of import paths to scan for plugin classes.

Returns:
    Summary of registered plugin names by type with keys: providers, features, tools, extensions.
"""
import importlib
import inspect

def _normalize_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

def _class_identifier(obj: type) -> str:
    snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", obj.__name__)
    return _normalize_identifier(snake_name)

providers = []
features = []
tools = []
extensions = []

for mod_path in modules:
    module = importlib.import_module(mod_path)
    module_basename = _normalize_identifier(mod_path.rsplit(".", 1)[-1])
    module_providers = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        # Only consider classes defined in the module (not imports)
        if getattr(obj, "__module__", None) != module.__name__:
            continue
        # Duck typing
        if hasattr(obj, "stream_api") or hasattr(obj, "call_api"):
            module_providers.append(obj)
        elif hasattr(obj, "get_tool_schemas") and hasattr(obj, "execute_tool"):
            tools.append(obj)
        elif hasattr(obj, "process_chunk"):
            extensions.append(obj)
        else:
            features.append(obj)
    module_providers.sort(
        key=lambda obj: (
            (
                0
                if _normalize_identifier(getattr(obj, "name", ""))
                == module_basename
                or _class_identifier(obj) == module_basename
                else 1
            ),
            obj.__name__,
        )
    )
    providers.extend(module_providers)

# Register a single provider (first), with all discovered extensions
summary: Dict[str, List[str]] = {
    "providers": [],
    "features": [],
    "tools": [],
    "extensions": [],
}
if providers:
    provider_cls = providers[0]
    provider_name = getattr(provider_cls, "name", provider_cls.__name__)
    self.register_provider(provider_cls, extensions=extensions)
    summary["providers"].append(provider_name)
    summary["extensions"].extend(
        [getattr(ext, "name", ext.__name__) for ext in extensions]
    )

# Register features and tools
for feat in features:
    self.register_feature(feat)
    summary["features"].append(getattr(feat, "name", feat.__name__))
for tool in tools:
    self.register_tool(tool)
    summary["tools"].append(getattr(tool, "name", tool.__name__))

return summary
```

```

### execute_lifecycle_actions

```

execute_lifecycle_actions( session, config, trigger, \*, context=None )

```

Execute all extension/feature actions whose trigger matches `trigger`.

Source code in `agent_core/core.py`

```

def execute_lifecycle_actions( self, session: Session, config: Dict[str, Any], trigger: str, \*, context: Optional\[Dict[str, Any]\] = None, ) -> Tuple\[Session, List\[Dict[str, Any]\]\]: """Execute all extension/feature actions whose trigger matches `trigger`."""

```
if not isinstance(config, dict):
    raise TypeError("config must be a dict")
if not isinstance(trigger, str) or not trigger:
    raise ValueError("trigger must be a non-empty string")
if not self._providers:
    return session, []

provider, features, state, available_actions = (
    self._get_core_session_actions_and_state(config)
)

current_session = session
results: List[Dict[str, Any]] = []
for action_def in available_actions:
    if not self._action_matches_trigger(action_def, trigger):
        continue

    plugin_id = action_def.get("plugin")
    action_id = action_def.get("id")
    action_owner = action_def.get("action_owner")
    if not isinstance(plugin_id, str) or not isinstance(action_id, str):
        continue

    validated_inputs = self._validate_session_action_inputs(action_def, {})
    native_messages = self._native_messages_for_session_action(
        current_session, config
    )

    request_context = self._build_request_context(
        config=state.get("config") or config,
        provider=provider,
        enabled_extensions=provider._iter_extensions(),
        enabled_features=features,
        enabled_tools=[],
        tags=[],
        models=self._get_models_for_config(provider, config),
        available_tools=self.get_available_tools(config),
        tools=self._get_prepared_tools_for_config(config),
        session=current_session,
        extra=context,
    )
    request_runtime = self._build_request_runtime(provider, features)
    enriched_context = self._build_lifecycle_action_context(
        config=config,
        session=current_session,
        lifecycle=trigger,
        request_context=request_context,
        request_runtime=request_runtime,
        extra=context,
    )

    if action_owner == "feature":
        result: Optional[Dict[str, Any]] = None
        for feature in features:
            if feature.name != plugin_id:
                continue
            result = feature.execute_action(
                action_id,
                current_session,
                native_messages,
                validated_inputs,
                enriched_context,
                state,
            )
            break
        if result is None:
            continue
    else:
        result = provider.execute_extension_action(
            plugin_id,
            action_id,
            current_session,
            native_messages,
            validated_inputs,
            enriched_context,
            state,
        )

    if not isinstance(result, dict):
        raise RuntimeError("session action must return a dict")
    current_session, public_result = self._apply_session_action_result(
        current_session,
        config,
        result,
        context=context,
    )
    results.append(
        {
            "plugin": plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "result": public_result,
        }
    )

return current_session, results
```

```

### execute_response_lifecycle_actions

```

execute_response_lifecycle_actions( session, config, trigger, \*, provider, features, state, final_messages, native_messages, native_final_messages, stream, turn_native_start_index, request_context, extra_context=None )

```

Execute core-owned response lifecycles before finals are emitted.

Source code in `agent_core/core.py`

```

def execute_response_lifecycle_actions( self, session: Session, config: Dict[str, Any], trigger: str, \*, provider: Any, features: List[Any], state: Dict[str, Any], final_messages: List\[Dict[str, Any]\], native_messages: List\[Dict[str, Any]\], native_final_messages: List\[Dict[str, Any]\], stream: bool, turn_native_start_index: int, request_context: Dict[str, Any], extra_context: Optional\[Dict[str, Any]\] = None, ) -> Tuple\[ List\[Dict[str, Any]\], List\[Dict[str, Any]\], Dict[str, Any], List\[Dict[str, Any]\] \]: """Execute core-owned response lifecycles before finals are emitted."""

```
if not isinstance(config, dict):
    raise TypeError("config must be a dict")
if not isinstance(trigger, str) or not trigger:
    raise ValueError("trigger must be a non-empty string")

current_final_messages = [
    msg for msg in final_messages if isinstance(msg, dict)
]
current_native_messages = [
    msg for msg in native_messages if isinstance(msg, dict)
]
metadata_patch: Dict[str, Any] = {}
results: List[Dict[str, Any]] = []
request_runtime = self._build_request_runtime(provider, features)

available_actions = self._collect_core_session_actions(
    provider, features, state
)

for action_def in available_actions:
    if not self._action_matches_trigger(action_def, trigger):
        continue

    plugin_id = action_def.get("plugin")
    action_id = action_def.get("id")
    action_owner = action_def.get("action_owner")
    if not isinstance(plugin_id, str) or not isinstance(action_id, str):
        continue

    validated_inputs = self._validate_session_action_inputs(action_def, {})
    enriched_context = self._build_response_lifecycle_context(
        config=config,
        session=session,
        lifecycle=trigger,
        request_context=request_context,
        request_runtime=request_runtime,
        final_messages=current_final_messages,
        native_final_messages=[
            msg for msg in native_final_messages if isinstance(msg, dict)
        ],
        native_messages=current_native_messages,
        stream=stream,
        turn_native_start_index=turn_native_start_index,
        extra=extra_context,
    )

    if action_owner == "feature":
        result: Optional[Dict[str, Any]] = None
        for feature in features:
            if feature.name != plugin_id:
                continue
            result = feature.execute_action(
                action_id,
                session,
                current_native_messages,
                validated_inputs,
                enriched_context,
                state,
            )
            break
        if result is None:
            continue
    else:
        result = provider.execute_extension_action(
            plugin_id,
            action_id,
            session,
            current_native_messages,
            validated_inputs,
            enriched_context,
            state,
        )

    if not isinstance(result, dict):
        raise RuntimeError("response lifecycle action must return a dict")

    if "final_messages" in result:
        raw_finals = result.get("final_messages")
        if not isinstance(raw_finals, list) or not all(
            isinstance(item, dict) for item in raw_finals
        ):
            raise RuntimeError(
                "response lifecycle action final_messages must be a list of dicts"
            )
        current_final_messages = [
            item for item in raw_finals if isinstance(item, dict)
        ]

    if "native_messages" in result:
        raw_native = result.get("native_messages")
        if not isinstance(raw_native, list) or not all(
            isinstance(item, dict) for item in raw_native
        ):
            raise RuntimeError(
                "response lifecycle action native_messages must be a list of dicts"
            )
        current_native_messages = [
            item for item in raw_native if isinstance(item, dict)
        ]

    metadata_patch_raw = result.get("session_metadata")
    if isinstance(metadata_patch_raw, dict):
        metadata_patch.update(metadata_patch_raw)

    public_result = {
        key: value
        for key, value in result.items()
        if key not in {"final_messages", "native_messages", "session_metadata"}
    }
    results.append(
        {
            "plugin": plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "result": public_result,
        }
    )

return current_final_messages, current_native_messages, metadata_patch, results
```

```

### execute_session_action

```

execute_session_action( session, config, plugin_id, action_id, params, context=None, )

```

Execute a generic session-scoped extension or feature action.

Source code in `agent_core/core.py`

```

def execute_session_action( self, session: Session, config: Dict[str, Any], plugin_id: str, action_id: str, params: Dict[str, Any], context: Optional\[Dict[str, Any]\] = None, ) -> Tuple\[Session, Dict[str, Any]\]: """Execute a generic session-scoped extension or feature action."""

```
if not isinstance(config, dict):
    raise TypeError("config must be a dict")
if not isinstance(plugin_id, str) or not plugin_id:
    raise ValueError("plugin_id must be a non-empty string")
if not isinstance(action_id, str) or not action_id:
    raise ValueError("action_id must be a non-empty string")
if not isinstance(params, dict):
    raise ValueError("params must be a mapping of action inputs")

provider, features, state, available_actions = (
    self._get_core_session_actions_and_state(config)
)

action_def = self._find_session_action_definition(
    available_actions, plugin_id, action_id
)
if action_def is None:
    raise KeyError(
        f"Unknown session action {action_id!r} for plugin {plugin_id!r}"
    )

validated_inputs = self._validate_session_action_inputs(action_def, params)
native_messages = self._native_messages_for_session_action(session, config)

request_context = self._build_request_context(
    config=state.get("config") or config,
    provider=provider,
    enabled_extensions=provider._iter_extensions(),
    enabled_features=features,
    enabled_tools=[],
    tags=[],
    models=self._get_models_for_config(provider, config),
    available_tools=self.get_available_tools(config),
    tools=self._get_prepared_tools_for_config(config),
    session=session,
    extra=context,
)
request_runtime = self._build_request_runtime(provider, features)
enriched_context = self._build_session_action_context(
    config=config,
    session=session,
    request_context=request_context,
    request_runtime=request_runtime,
    extra=context,
)

action_owner = action_def.get("action_owner")
if action_owner == "feature":
    result: Optional[Dict[str, Any]] = None
    for feature in features:
        if feature.name != plugin_id:
            continue
        result = feature.execute_action(
            action_id,
            session,
            native_messages,
            validated_inputs,
            enriched_context,
            state,
        )
        break
    if result is None:
        raise KeyError(
            f"Unknown feature action {action_id!r} for plugin {plugin_id!r}"
        )
else:
    result = provider.execute_extension_action(
        plugin_id,
        action_id,
        session,
        native_messages,
        validated_inputs,
        enriched_context,
        state,
    )
if not isinstance(result, dict):
    raise RuntimeError("session action must return a dict")
return self._apply_session_action_result(
    session,
    config,
    result,
    context=context,
)
```

```

### execute_tool_calls

```

execute_tool_calls(tool_calls, config, \*, context=None)

```

Return only the final core `tool` message per tool call.

This is a compatibility wrapper around :meth:`iter_tool_messages`
that ignores partial payloads and keeps only the last final tool
message for each call. When a streaming tool yields no items for a
call, a synthetic error message is returned.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `tool_calls` | `List[Dict[str, Any]]` | List of tool call dictionaries to execute. | *required* |
| `config` | `Dict[str, Any]` | Current resolved request configuration. | *required* |
| `context` | `Optional[Dict[str, Any]]` | Optional context for tool execution. Passed through to :meth:iter_tool_messages which enriches with Layer 1 context. | `None` |

Source code in `agent_core/core.py`

```

def execute_tool_calls( self, tool_calls: List\[Dict[str, Any]\], config: Dict[str, Any], \*, context: Optional\[Dict[str, Any]\] = None, ) -> List\[Dict[str, Any]\]: """Return only the final core `tool` message per tool call.

```
This is a compatibility wrapper around :meth:`iter_tool_messages`
that ignores partial payloads and keeps only the last final tool
message for each call. When a streaming tool yields no items for a
call, a synthetic error message is returned.

Args:
    tool_calls: List of tool call dictionaries to execute.
    config: Current resolved request configuration.
    context: Optional context for tool execution. Passed through to
        :meth:`iter_tool_messages` which enriches with Layer 1 context.
"""
results: List[Dict[str, Any]] = []
if not tool_calls:
    return results

logger.debug(
    "execute_tool_calls_start",
    count=len(tool_calls),
)

for call in tool_calls:
    last_final: Dict[str, Any] | None = None
    executed = False

    for item in self.iter_tool_messages([call], config, context=context):
        if not isinstance(item, dict):
            continue
        if "part" in item:
            # Streaming partial; ignored in final-only API.
            continue
        last_final = item
        executed = True

    if last_final is None:
        try:
            registry = self._get_tool_interop_registry_for_config(config)
            inspected_call = registry.inspect_call(call)
            call_id = inspected_call.call_id
            name = inspected_call.tool_name
        except Exception:
            call_id = None
            name = None
        metadata: Dict[str, Any] = {
            "tool_call_id": call_id,
            "tool_name": name,
        }
        last_final = {
            "role": "tool",
            "content": f"Error: no tool handled '{name}'",
            "metadata": metadata,
        }
        executed = False

    md = last_final.get("metadata") or {}
    logger.debug(
        "execute_tool_call_complete",
        tool_name=str(md.get("tool_name")),
        executed=executed,
    )
    results.append(last_final)

return results
```

```

### export_session

```

export_session(session, format='json')

```

Export session to a serialized string.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `session` | `Session` | Session to serialize. | *required* |
| `format` | `str` | Export format. Only "json" is supported. | `'json'` |

Returns:

| Type | Description |
| --- | --- |
| `str` | Serialized string representing the session. |

Raises:

| Type | Description |
| --- | --- |
| `ValueError` | If the format is not supported. |

Source code in `agent_core/core.py`

```

def export_session(self, session: Session, format: str = "json") -> str: """Export session to a serialized string.

```
Args:
    session: Session to serialize.
    format: Export format. Only "json" is supported.

Returns:
    Serialized string representing the session.

Raises:
    ValueError: If the format is not supported.
"""
if format == "json":
    return json.dumps(session.to_dict(), indent=2)
raise ValueError(f"Unsupported format: {format}")
```

```

### extract_tool_calls_from_messages

```

extract_tool_calls_from_messages(messages)

```

Extract tool-call dictionaries from assistant message metadata.

Source code in `agent_core/core.py`

```

def extract_tool_calls_from_messages( self, messages: List\[Dict[str, Any]\], ) -> List\[Dict[str, Any]\]: """Extract tool-call dictionaries from assistant message metadata."""

```
tool_calls: List[Dict[str, Any]] = []
for msg in messages:
    if not isinstance(msg, dict) or msg.get("role") != "assistant":
        continue
    metadata = msg.get("metadata") or {}
    calls = metadata.get("tool_calls") or []
    if isinstance(calls, list):
        tool_calls.extend([call for call in calls if isinstance(call, dict)])
return tool_calls
```

```

### fork_session

```

fork_session( session, config=None, \*, upto_index, new_session_id=None )

```

Convenience helper to fork a session up to upto_index.

Source code in `agent_core/core.py`

```

def fork_session( self, session: Session, config: Optional\[Dict[str, Any]\] = None, \*, upto_index: int, new_session_id: Optional[str] = None, ) -> Session: """Convenience helper to fork a session up to upto_index.""" sliced = self.slice_session( session, config, start=0, end=upto_index + 1, ) if new_session_id is None or new_session_id == sliced.session_id: return sliced return Session( session_id=new_session_id, messages=sliced.messages, metadata=sliced.metadata, )

```

### format_tool_call_preview

```

format_tool_call_preview(tool_call, config)

```

Return a preview record for a single tool call.

Source code in `agent_core/core.py`

```

def format_tool_call_preview( self, tool_call: Dict[str, Any], config: Dict[str, Any], ) -> Dict\[str, Any\]: """Return a preview record for a single tool call."""

```
provider, extensions, tool_states = self._get_enabled_tool_states_for_config(
    config
)
registry = self._get_tool_interop_registry_for_config(
    config,
    provider=provider,
    extensions=extensions,
    tool_states=tool_states,
)

try:
    inspected_call = registry.inspect_call(tool_call)
except Exception:
    inspected_call = None

if inspected_call is None:
    return {"id": None, "preview": ""}

tool, state, prepared, _matched_schema = self._resolve_tool_handler_for_call(
    inspected_call,
    tool_states,
    registry,
)
if tool is None or state is None:
    return {"id": inspected_call.call_id, "preview": ""}

try:
    preview = tool.format_tool_call_preview(
        inspected_call.tool_name,
        inspected_call.payload,
        state,
        payload_kind=inspected_call.payload_kind,
        payload_format=inspected_call.payload_format,
        payload_metadata=inspected_call.payload_metadata,
        tool_call=inspected_call.raw,
        prepared=prepared,
    )
except Exception:
    preview = ""

return {
    "id": inspected_call.call_id,
    "preview": preview if isinstance(preview, str) else "",
}
```

```

### format_tool_call_previews

```

format_tool_call_previews(tool_calls, config)

```

Return preview records for all supplied tool calls.

Source code in `agent_core/core.py`

```

def format_tool_call_previews( self, tool_calls: List\[Dict[str, Any]\], config: Dict[str, Any], ) -> List\[Dict[str, Any]\]: """Return preview records for all supplied tool calls."""

```
return [
    self.format_tool_call_preview(tool_call, config)
    for tool_call in tool_calls
    if isinstance(tool_call, dict)
]
```

```

### get_available_tools

```

get_available_tools(config)

```

Get the full available tool catalog for a config before filtering.

Source code in `agent_core/core.py`

```

def get_available_tools(self, config: Dict[str, Any]) -> List\[ToolDescriptor\]: """Get the full available tool catalog for a config before filtering.""" return self.\_get_available_tools_for_config(config)[0]

```

### get_completions

```

get_completions(config, text)

```

Collect completion suggestions from registered feature plugins.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `config` | `Dict[str, Any]` | Application configuration for the current agent or request. | *required* |
| `text` | `str` | Full text before the cursor (for example, the current input line in a terminal UI). | *required* |

Returns:

| Type | Description |
| --- | --- |
| `List[Dict[str, Any]]` | List of completion descriptor dictionaries contributed by |
| `List[Dict[str, Any]]` | features. The exact shape of each entry is feature- and |
| `List[Dict[str, Any]]` | application-defined; common keys include "replacement", |
| `List[Dict[str, Any]]` | "start", "display", and "display_meta". |

Source code in `agent_core/core.py`

```

def get_completions( self, config: Dict[str, Any], text: str ) -> List\[Dict[str, Any]\]: """Collect completion suggestions from registered feature plugins.

```
Args:
    config: Application configuration for the current agent or request.
    text: Full text before the cursor (for example, the current input
        line in a terminal UI).

Returns:
    List of completion descriptor dictionaries contributed by
    features. The exact shape of each entry is feature- and
    application-defined; common keys include "replacement",
    "start", "display", and "display_meta".
"""

completions: List[Dict[str, Any]] = []
if not self._features:
    return completions

for feature in self._features:
    try:
        items = feature.get_completions(config, text) or []
    except Exception:
        continue
    for item in items:
        if isinstance(item, dict):
            completions.append(item)
return completions
```

```

### get_config_schema

```

get_config_schema()

```

Get flattened config schema from all registered plugins.

Returns:

| Type | Description |
| --- | --- |
| `List[Dict[str, Any]]` | List of config entry descriptors. Each element is a |
| `List[Dict[str, Any]]` | dictionary that includes: |
| `List[Dict[str, Any]]` | "key": the top-level config key. |
| `List[Dict[str, Any]]` | "plugin": the contributing plugin's id/name (provider, extension, feature, or tool). |
| `List[Dict[str, Any]]` | Any additional metadata provided by the plugin (for example, "type", "default", "required", "description"). |
| `List[Dict[str, Any]]` | Multiple plugins may contribute entries for the same |
| `List[Dict[str, Any]]` | "key"; each contribution is represented as a separate |
| `List[Dict[str, Any]]` | element in the returned list. |

Source code in `agent_core/core.py`

```

def get_config_schema(self) -> List\[Dict[str, Any]\]: """Get flattened config schema from all registered plugins.

```
Returns:
    List of config entry descriptors. Each element is a
    dictionary that includes:

    - ``"key"``: the top-level config key.
    - ``"plugin"``: the contributing plugin's id/name
      (provider, extension, feature, or tool).
    - Any additional metadata provided by the plugin
      (for example, ``"type"``, ``"default"``,
      ``"required"``, ``"description"``).

    Multiple plugins may contribute entries for the same
    ``"key"``; each contribution is represented as a separate
    element in the returned list.
"""
entries: List[Dict[str, Any]] = []

def _extend(schema: Dict[str, Any] | None, plugin_name: str) -> None:
    if not schema:
        return
    for key, value in schema.items():
        if not isinstance(key, str) or not key:
            continue
        if not isinstance(value, dict):
            continue
        entry: Dict[str, Any] = dict(value)
        if "plugin" not in entry:
            entry["plugin"] = plugin_name
        entry.setdefault("key", key)
        entries.append(entry)

for provider in self._providers:
    _extend(provider.get_config_schema(), provider.name)
    # Include provider extension schemas
    for name, ext_schema in provider.get_extension_config_schemas().items():
        _extend(ext_schema, name)
for feature in self._features:
    _extend(feature.get_config_schema(), feature.name)
for tool in self._tools:
    _extend(tool.get_config_schema(), tool.name)
return entries
```

```

### get_plugins_for_config

```

get_plugins_for_config(config)

```

Return active plugin identifiers for the given config.

The result is derived from the same tag-based dependency
resolution used internally by the core. It maps plugin kinds
("providers", "extensions", "features", "tools") to lists of
active plugin identifiers for this config.

Source code in `agent_core/core.py`

```

def get_plugins_for_config( self, config: Dict[str, Any], ) -> Dict\[str, List[str]\]: """Return active plugin identifiers for the given config.

```
The result is derived from the same tag-based dependency
resolution used internally by the core. It maps plugin kinds
("providers", "extensions", "features", "tools") to lists of
active plugin identifiers for this config.
"""

(
    provider,
    enabled_extensions,
    enabled_features,
    enabled_tools,
    _tags,
) = self._resolve_plugins_for_config(config)

return {
    "providers": [provider.name],
    "extensions": [ext.name for ext in enabled_extensions],
    "features": [feat.name for feat in enabled_features],
    "tools": [tool.name for tool in enabled_tools],
}
```

```

### get_session_actions

```

get_session_actions(config)

```

Return session-scoped extension and feature actions for the config.

Source code in `agent_core/core.py`

```

def get_session_actions(self, config: Dict[str, Any]) -> List\[Dict[str, Any]\]: """Return session-scoped extension and feature actions for the config."""

```
if not isinstance(config, dict):
    raise TypeError("config must be a dict")
if not self._providers:
    return []

_provider, _features, _state, actions = (
    self._get_core_session_actions_and_state(config)
)
return actions
```

```

### get_tool_schemas

```

get_tool_schemas(config)

```

Get the effective tool schemas for a config after feature policy.

Source code in `agent_core/core.py`

```

def get_tool_schemas(self, config: Dict[str, Any]) -> List\[Dict[str, Any]\]: """Get the effective tool schemas for a config after feature policy.""" return [ descriptor.schema for descriptor in self.\_get_prepared_tools_for_config(config) ]

```

### get_ui_schema

```

get_ui_schema(config)

```

Get flattened UI schema for the effective config.

Plugins receive additional context computed from `config`:

- `tags`: capability/environment tags produced by the provider and
  enabled plugins.
- `models`: model descriptors returned by `get_models` hooks.

Each element is a dictionary describing a UI element contributed by a
provider, extension, feature, or tool. The core treats the dictionaries
as opaque and simply annotates and flattens them; applications decide
how to render or interpret each entry.

Source code in `agent_core/core.py`

```

def get_ui_schema(self, config: Dict[str, Any]) -> List\[Dict[str, Any]\]: """Get flattened UI schema for the effective config.

```
Plugins receive additional context computed from ``config``:

- ``tags``: capability/environment tags produced by the provider and
  enabled plugins.
- ``models``: model descriptors returned by ``get_models`` hooks.

Each element is a dictionary describing a UI element contributed by a
provider, extension, feature, or tool. The core treats the dictionaries
as opaque and simply annotates and flattens them; applications decide
how to render or interpret each entry.
"""

if not isinstance(config, dict):
    raise TypeError("config must be a dict")

if not self._providers and not self._features and not self._tools:
    return []

provider: Optional[ProviderWrapper] = None
enabled_extensions: List[ExtensionWrapper] = []
enabled_features: List[FeatureWrapper] = list(self._features)
enabled_tools: List[ToolWrapper] = list(self._tools)
tags: List[str] = []
models: List[Dict[str, Any]] = []

if self._providers:
    (
        provider,
        enabled_extensions,
        enabled_features,
        enabled_tools,
        tags,
    ) = self._resolve_plugins_for_config(config)
    provider.set_active_extensions(enabled_extensions)
    models = self._get_models_for_config(provider, config)

enabled_features = sorted(
    enabled_features, key=lambda feat: getattr(feat, "priority", 100)
)
enabled_tools = sorted(
    enabled_tools, key=lambda tool: getattr(tool, "priority", 100)
)
available_tools = self.get_available_tools(config)
effective_tools = self._get_prepared_tools_for_config(config)
ui_context = self._build_plugin_context(
    config=config,
    provider=provider,
    enabled_extensions=enabled_extensions,
    enabled_features=enabled_features,
    enabled_tools=enabled_tools,
    tags=tags,
    models=models,
    available_tools=available_tools,
    tools=effective_tools,
)
extension_plugin_names = {ext.name for ext in enabled_extensions}
feature_plugin_names = {feature.name for feature in enabled_features}

elements: List[Dict[str, Any]] = []
config_by_key: Dict[str, Dict[str, Any]] = {}

def _extend(raw_elements: List[Dict[str, Any]], plugin_name: str) -> None:
    for el in raw_elements or []:
        if not isinstance(el, dict):
            continue
        entry: Dict[str, Any] = dict(el)
        ui_type = entry.get("ui_type")
        if not isinstance(ui_type, str) or not ui_type:
            entry["ui_type"] = "config"
            ui_type = "config"
        if "plugin" not in entry and plugin_name:
            entry["plugin"] = plugin_name

        if (
            plugin_name in extension_plugin_names
            and ui_type in {"session_action", "message_action"}
            and isinstance(entry.get("action_id"), str)
            and "action_owner" not in entry
        ):
            entry["action_owner"] = "provider_extension"
        elif (
            plugin_name in feature_plugin_names
            and ui_type in {"session_action", "message_action"}
            and isinstance(entry.get("action_id"), str)
            and "action_owner" not in entry
        ):
            entry["action_owner"] = "feature"

        if ui_type == "config":
            key = entry.get("key")
            if isinstance(key, str) and key:
                config_by_key[key] = entry
                continue

        elements.append(entry)

if provider is not None:
    _extend(provider.get_ui_elements(config, ui_context), provider.name)
    for name, ext_ui in provider.get_extension_ui_elements(
        config, ui_context
    ).items():
        _extend(ext_ui, name)
for feature in enabled_features:
    _extend(feature.get_ui_elements(config, ui_context), feature.name)
for tool in enabled_tools:
    _extend(tool.get_ui_elements(config, ui_context), tool.name)

elements.extend(config_by_key.values())
return elements
```

```

### import_session

```

import_session(data, format='json')

```

Import a session from a serialized string.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `data` | `str` | Serialized session string. | *required* |
| `format` | `str` | Import format. Only "json" is supported. | `'json'` |

Returns:

| Type | Description |
| --- | --- |
| `Session` | A new Session reconstructed from the serialized data. |

Raises:

| Type | Description |
| --- | --- |
| `ValueError` | If the format is not supported. |

Source code in `agent_core/core.py`

```

def import_session(self, data: str, format: str = "json") -> Session: """Import a session from a serialized string.

```
Args:
    data: Serialized session string.
    format: Import format. Only "json" is supported.

Returns:
    A new Session reconstructed from the serialized data.

Raises:
    ValueError: If the format is not supported.
"""
if format == "json":
    session_dict = json.loads(data)
    return Session.from_dict(session_dict)
raise ValueError(f"Unsupported format: {format}")
```

```

### initialize_action_request

```

initialize_action_request( native_messages, state, request_runtime, request_context )

```

Apply request-time initialization to session-action inputs.

Session actions should see the same request-time state that normal
provider requests see, including feature/provider `initialize_request`
changes such as compiled top-level instructions.

Source code in `agent_core/core.py`

```

def initialize_action_request( self, native_messages: List\[Dict[str, Any]\], state: Dict[str, Any], request_runtime: Dict[str, Any], request_context: Dict[str, Any], ) -> Tuple\[List\[Dict[str, Any]\], Dict[str, Any]\]: """Apply request-time initialization to session-action inputs.

```
Session actions should see the same request-time state that normal
provider requests see, including feature/provider `initialize_request`
changes such as compiled top-level instructions.
"""
if not isinstance(native_messages, list):
    raise TypeError("native_messages must be a list")
if not isinstance(state, dict):
    raise TypeError("state must be a dict")
if not isinstance(request_runtime, dict):
    raise TypeError("request_runtime must be a dict")
if not isinstance(request_context, dict):
    raise TypeError("request_context must be a dict")

provider = request_runtime.get("provider")
if provider is None:
    raise ValueError("request_runtime must include provider")
raw_features = request_runtime.get("features")
if raw_features is None:
    features: List[Any] = []
elif isinstance(raw_features, list):
    features = raw_features
else:
    raise TypeError("request_runtime['features'] must be a list")

next_native_messages, next_state = provider.initialize_request(
    native_messages,
    state,
    context=request_context,
)
initialized_native = (
    next_native_messages
    if next_native_messages != native_messages
    else native_messages
)
initialized_state = next_state

for feature in features:
    next_native_messages, initialized_state = feature.initialize_request(
        initialized_native,
        initialized_state,
        context=request_context,
    )
    if next_native_messages != initialized_native:
        initialized_native = next_native_messages
    provider.set_state(initialized_state)

return initialized_native, initialized_state
```

```

### iter_tool_messages

```

iter_tool_messages( tool_calls, config, \*, cancellation=None, context=None )

```

Yield a mixed stream of partial payloads and final core `tool` messages.

Tools stream via `ToolPlugin.stream_tool`. Partial display payloads are
yielded as-is when they contain a `"part"` key. Result dictionaries are
detected via the presence of a `"success"` key and transformed into final
core `tool` messages at the end of each tool call.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `tool_calls` | `List[Dict[str, Any]]` | List of tool call dictionaries to execute. | *required* |
| `config` | `Dict[str, Any]` | Current resolved request configuration. | *required* |
| `cancellation` | `Any | None` | Optional cancellation token. | `None` |
| `context` | `Optional[Dict[str, Any]]` | Optional context for tool execution. Layer 1 context (core, config, trigger_source) is enriched by this method if not already present. | `None` |

Source code in `agent_core/core.py`

```

def iter_tool_messages( self, tool_calls: List\[Dict[str, Any]\], config: Dict[str, Any], \*, cancellation: Any | None = None, context: Optional\[Dict[str, Any]\] = None, ) -> Iterator\[Dict[str, Any]\]: """Yield a mixed stream of partial payloads and final core `tool` messages.

```
Tools stream via ``ToolPlugin.stream_tool``. Partial display payloads are
yielded as-is when they contain a ``"part"`` key. Result dictionaries are
detected via the presence of a ``"success"`` key and transformed into final
core ``tool`` messages at the end of each tool call.

Args:
    tool_calls: List of tool call dictionaries to execute.
    config: Current resolved request configuration.
    cancellation: Optional cancellation token.
    context: Optional context for tool execution. Layer 1 context (core,
        config, trigger_source) is enriched by this method if not already
        present.
"""
if not tool_calls:
    return

logger.debug(
    "iter_tool_messages_start",
    count=len(tool_calls),
)

provider, extensions, tool_states = self._get_enabled_tool_states_for_config(
    config
)
registry = self._get_tool_interop_registry_for_config(
    config,
    provider=provider,
    extensions=extensions,
    tool_states=tool_states,
)

for call in tool_calls:
    try:
        inspected_call = registry.inspect_call(call)
    except Exception:
        inspected_call = None

    if inspected_call is None:
        call_id = None
        name = None
        # No matching tool found; synthesize an error message.
        metadata: Dict[str, Any] = {
            "tool_call_id": call_id,
            "tool_name": name,
        }
        yield {
            "role": "tool",
            "content": f"Error: no tool handled '{name}'",
            "metadata": metadata,
        }
        continue

    call_id = inspected_call.call_id
    name = inspected_call.tool_name

    tool, state, prepared, matched_schema = self._resolve_tool_handler_for_call(
        inspected_call,
        tool_states,
        registry,
    )

    if tool is None or state is None:
        metadata = {
            "tool_call_id": call_id,
            "tool_name": name,
        }
        yield {
            "role": "tool",
            "content": f"Error: no tool handled '{name}'",
            "metadata": metadata,
        }
        continue
    last_result: Dict[str, Any] | None = None
    had_result = False
    stream_error: str | None = None

    # Layer 1: Core-level context enrichment.
    # Higher layers (application, terminal) may have already set these;
    # use setdefault so we never overwrite a richer value.
    tool_context = self._build_tool_runtime_context(config, context)

    try:
        iterator = tool.stream_tool(
            name,
            inspected_call.payload,
            state,
            payload_kind=inspected_call.payload_kind,
            payload_format=inspected_call.payload_format,
            payload_metadata=inspected_call.payload_metadata,
            tool_call=inspected_call.raw,
            cancellation=cancellation,
            context=tool_context,
            prepared=prepared,
        )
        iterator = iter(iterator)
    except Exception as exc:
        iterator = None
        stream_error = f"Tool error: {exc}"

    if iterator is not None:
        try:
            for chunk in iterator:
                if not isinstance(chunk, dict):
                    continue
                if "success" in chunk:
                    last_result = chunk
                    had_result = True
                elif "part" in chunk:
                    # Partial display payload; forward as-is.
                    yield chunk
                else:
                    # Backwards-compatible: treat any other dict as a partial payload.
                    yield {"part": chunk}
        except Exception as exc:
            stream_error = f"Tool error: {exc}"
            logger.error(
                "iter_tool_messages_stream_error",
                tool_name=str(name),
                error=str(exc),
            )

    if not had_result:
        # No RESULT dict was produced; synthesize an error message.
        content = stream_error or f"Error: no tool handled '{name}'"
        metadata = {
            "tool_call_id": call_id,
            "tool_name": name,
        }
        plugin_name = getattr(tool, "name", None)
        if isinstance(plugin_name, str) and plugin_name:
            metadata["tool_plugin"] = plugin_name
        yield {
            "role": "tool",
            "content": content,
            "metadata": metadata,
        }
        continue

    assert last_result is not None
    try:
        formatted_content = tool.format_tool_result(last_result, state)
    except Exception as exc:
        formatted_content = f"Tool formatting error: {exc}"

    inspected_result = registry.inspect_result(formatted_content)
    display_text = inspected_result.text
    display_payload: Dict[str, Any] | None = None
    try:
        display_candidate = tool.to_display_format(
            display_text,
            last_result,
            state,
        )
        if isinstance(display_candidate, dict):
            display_payload = display_candidate
    except Exception:
        display_payload = None

    if (
        isinstance(display_payload, dict)
        and display_payload.get("type") == "text"
        and display_payload.get("content") == display_text
        and "single_line" not in display_payload
        and isinstance(inspected_result.display, dict)
    ):
        display_payload = inspected_result.display

    tool_result_value: Dict[str, Any]
    if isinstance(formatted_content, dict) and (
        inspected_result.format_id != CORE_TEXT_TOOL_RESULT_FORMAT_ID
    ):
        tool_result_value = formatted_content
    else:
        converted_result = registry.convert_tool_result(
            formatted_content,
            target=ToolInteropTarget("core.tool_result"),
            target_formats=[CORE_TEXT_TOOL_RESULT_FORMAT_ID],
        )
        if isinstance(converted_result, dict):
            tool_result_value = converted_result
        else:
            tool_result_value = {
                "type": "tool_result",
                "text": inspected_result.text,
            }

    if display_payload is None:
        canonical_result = registry.inspect_result(tool_result_value)
        if isinstance(canonical_result.display, dict):
            display_payload = canonical_result.display

    metadata = {
        "tool_call_id": call_id,
        "tool_name": name,
    }
    if matched_schema is not None:
        metadata["tool_schema"] = matched_schema
    plugin_name = getattr(tool, "name", None)
    if isinstance(plugin_name, str) and plugin_name:
        metadata["tool_plugin"] = plugin_name
    if display_payload is not None:
        metadata["display"] = display_payload

    tool_message = {
        "role": "tool",
        "content": registry.inspect_result(tool_result_value).text,
        "metadata": metadata,
        TOOL_RESULT_FIELD: tool_result_value,
    }

    yield tool_message
```

```

### join_sessions

```

join_sessions(prefix, suffix, config=None)

```

Join two sessions end-to-end, preserving native history when possible.

This helper concatenates the core messages from `prefix` and
`suffix` and, when both sessions contain provider-native history,
combines their native histories and rebuilds core messages from the
merged native sequence.

Note: arbitrary per-message `Message.metadata` is not preserved by
default across the native-history rebuild step. If metadata must
survive native rebuilds, it must be persisted into provider-native
messages via the `_metadata` key and reconstructed in
`from_native_messages`.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `prefix` | `Session` | First session segment. | *required* |
| `suffix` | `Session` | Second session segment that should follow prefix. | *required* |
| `config` | `Optional[Dict[str, Any]]` | Optional configuration used when rebuilding from native history. When omitted, joins are performed in core-only mode. | `None` |

Returns:

| Type | Description |
| --- | --- |
| `Session` | New Session instance representing the concatenation of prefix |
| `Session` | and suffix. |

Source code in `agent_core/core.py`

```

def join_sessions( self, prefix: Session, suffix: Session, config: Optional\[Dict[str, Any]\] = None, ) -> Session: """Join two sessions end-to-end, preserving native history when possible.

```
This helper concatenates the core messages from ``prefix`` and
``suffix`` and, when both sessions contain provider-native history,
combines their native histories and rebuilds core messages from the
merged native sequence.

Note: arbitrary per-message ``Message.metadata`` is not preserved by
default across the native-history rebuild step. If metadata must
survive native rebuilds, it must be persisted into provider-native
messages via the ``_metadata`` key and reconstructed in
``from_native_messages``.

Args:
    prefix: First session segment.
    suffix: Second session segment that should follow ``prefix``.
    config: Optional configuration used when rebuilding from native
        history. When omitted, joins are performed in core-only mode.

Returns:
    New Session instance representing the concatenation of ``prefix``
    and ``suffix``.
"""

from agent_core.types import Message  # local import to avoid cycles

# Core-only join when native history is not consistently available on
# both sessions or when no configuration is provided.
has_prefix_native = isinstance(prefix.metadata, dict) and isinstance(
    prefix.metadata.get("native_messages"), list
)
has_suffix_native = isinstance(suffix.metadata, dict) and isinstance(
    suffix.metadata.get("native_messages"), list
)

if not config or not (has_prefix_native and has_suffix_native):
    combined_messages: List[Message] = [*prefix.messages, *suffix.messages]
    new_metadata: Dict[str, Any] = (
        dict(prefix.metadata) if isinstance(prefix.metadata, dict) else {}
    )
    new_metadata.pop("native_messages", None)
    new_metadata.pop("native_messages_integrity", None)
    return Session(
        session_id=prefix.session_id,
        messages=combined_messages,
        metadata=new_metadata,
    )

# Native-preserving join: concatenate native histories and rebuild
# core messages from the combined native sequence.
native_prefix = prefix.metadata.get("native_messages") or []
native_suffix = suffix.metadata.get("native_messages") or []
new_native: List[Dict[str, Any]] = list(native_prefix) + list(native_suffix)

# Skip initialize_request for session join operations.
# This prevents features like SystemMessageFeature from adding
# synthetic messages during join, which would cause duplicates
# if one of the sessions already has a system message.
rebuilt_messages, post_init_native = self._rebuild_core_from_native(
    new_native, config or {}, skip_initialize=True
)

new_metadata = (
    dict(prefix.metadata) if isinstance(prefix.metadata, dict) else {}
)
new_metadata["native_messages"] = post_init_native
new_metadata["native_messages_integrity"] = self._compute_native_integrity(
    rebuilt_messages
)

return Session(
    session_id=prefix.session_id,
    messages=rebuilt_messages,
    metadata=new_metadata,
)
```

```

### modify_message

```

modify_message( session, index, content, config=None, \*, context=None )

```

Modify the content of an existing message (pure function).

Only `system`, `user`, and `assistant` messages are supported. The
message role and metadata remain unchanged. When provider-native
history is present and safely mappable via `native_indices`, the
corresponding native messages are updated. Otherwise, native history
is dropped and will be reconstructed on the next request.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `session` | `Session` | Current session. | *required* |
| `index` | `int` | Message index to modify (0-based; negative indices supported). | *required* |
| `content` | `str` | New message content. | *required* |
| `config` | `Optional[Dict[str, Any]]` | Optional configuration used to resolve provider and plugins when updating native history. | `None` |

Returns:

| Type | Description |
| --- | --- |
| `Session` | New Session with the modified message (immutable update). |

Source code in `agent_core/core.py`

```

def modify_message( self, session: Session, index: int, content: str, config: Optional\[Dict[str, Any]\] = None, \*, context: Optional\[Dict[str, Any]\] = None, ) -> Session: """Modify the content of an existing message (pure function).

```
Only `system`, `user`, and `assistant` messages are supported. The
message role and metadata remain unchanged. When provider-native
history is present and safely mappable via `native_indices`, the
corresponding native messages are updated. Otherwise, native history
is dropped and will be reconstructed on the next request.

Args:
    session: Current session.
    index: Message index to modify (0-based; negative indices supported).
    content: New message content.
    config: Optional configuration used to resolve provider and plugins
        when updating native history.

Returns:
    New Session with the modified message (immutable update).
"""
return self._modify_single_message_with_native(
    session, index, content, config or {}, context=context
)
```

```

### patch_native_internal_metadata

```

patch_native_internal_metadata( native_messages, indices, patch )

```

Immutably merge `patch` into `_metadata` on selected native items.

Source code in `agent_core/core.py`

```

def patch_native_internal_metadata( self, native_messages: List\[Dict[str, Any]\], indices: List[int], patch: Dict[str, Any], ) -> List\[Dict[str, Any]\]: """Immutably merge `patch` into `_metadata` on selected native items."""

```
if not indices or not isinstance(patch, dict) or not patch:
    return native_messages

out: Optional[List[Dict[str, Any]]] = None
for idx in sorted({i for i in indices if isinstance(i, int)}):
    if idx < 0 or idx >= len(native_messages):
        continue
    item = native_messages[idx]
    if not isinstance(item, dict):
        continue
    raw_internal = item.get("_metadata")
    internal = dict(raw_internal) if isinstance(raw_internal, dict) else {}
    merged_internal = {**internal, **patch}
    if merged_internal == internal:
        continue
    if out is None:
        out = list(native_messages)
    out[idx] = {**item, "_metadata": merged_internal}
return out if out is not None else native_messages
```

```

### rebuild_native_history

```

rebuild_native_history( session, config=None, \*, start=None, end=None, context=None )

```

Rebuild provider-native history from the current core messages.

This helper converts the session's core messages to provider-native
form using the configured provider, extensions, and features, then
rebuilds the full core message sequence from that native history. When
`start`/`end` are provided, only the visible message slice
`session.messages[start:end]` is rebuilt back into native history
before the canonical full core transcript is reconstructed.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `session` | `Session` | Current session. | *required* |
| `config` | `Optional[Dict[str, Any]]` | Configuration used to resolve provider and plugins. | `None` |
| `start` | `Optional[int]` | Optional inclusive visible-message start index for selective rebuild. Requires retained native history on the session. | `None` |
| `end` | `Optional[int]` | Optional exclusive visible-message end index for selective rebuild. Requires retained native history on the session. | `None` |

Returns:

| Type | Description |
| --- | --- |
| `Session` | New Session with native history rebuilt from core messages. |

Source code in `agent_core/core.py`

```

def rebuild_native_history( self, session: Session, config: Optional\[Dict[str, Any]\] = None, \*, start: Optional[int] = None, end: Optional[int] = None, context: Optional\[Dict[str, Any]\] = None, ) -> Session: """Rebuild provider-native history from the current core messages.

```
This helper converts the session's core messages to provider-native
form using the configured provider, extensions, and features, then
rebuilds the full core message sequence from that native history. When
``start``/``end`` are provided, only the visible message slice
``session.messages[start:end]`` is rebuilt back into native history
before the canonical full core transcript is reconstructed.

Args:
    session: Current session.
    config: Configuration used to resolve provider and plugins.
    start: Optional inclusive visible-message start index for selective
        rebuild. Requires retained native history on the session.
    end: Optional exclusive visible-message end index for selective
        rebuild. Requires retained native history on the session.

Returns:
    New Session with native history rebuilt from core messages.
"""

if config is None:
    raise ValueError("config must be provided to rebuild native history")

if not isinstance(config, dict):
    raise TypeError("config must be a dict when rebuilding native history")

if start is not None or end is not None:
    message_count = len(session.messages)
    start_idx = 0 if start is None else start
    end_idx = message_count if end is None else end
    if (
        start_idx < 0
        or end_idx < 0
        or start_idx >= end_idx
        or end_idx > message_count
    ):
        raise ValueError(
            "start/end must select a non-empty visible message slice"
        )

    retained_native = None
    base_metadata: Dict[str, Any] = (
        dict(session.metadata) if isinstance(session.metadata, dict) else {}
    )
    rn = base_metadata.get("native_messages")
    if isinstance(rn, list):
        retained_native = rn

    if retained_native is None:
        raise RuntimeError(
            "selective rebuild requires retained native history on the session"
        )

    self._verify_native_integrity(session)

    target_messages = session.messages[start_idx:end_idx]
    target_native_indices: List[int] = []
    for message in target_messages:
        metadata = (
            message.metadata if isinstance(message.metadata, dict) else {}
        )
        native_indices = metadata.get("native_indices")
        if not isinstance(native_indices, list) or not native_indices:
            raise RuntimeError(
                "selective rebuild requires native_indices for every selected message"
            )
        target_native_indices.extend(
            index for index in native_indices if isinstance(index, int)
        )

    if not target_native_indices:
        raise RuntimeError(
            "selected visible message slice maps to no native history"
        )

    unique_indices = sorted(set(target_native_indices))
    expected_indices = list(range(unique_indices[0], unique_indices[-1] + 1))
    if unique_indices != expected_indices:
        raise RuntimeError(
            "selected visible message slice does not map to a contiguous native slice"
        )

    replacement_core = [message.to_dict() for message in target_messages]
    replacement_native = self._core_messages_to_native_for_config(
        replacement_core,
        config,
        context=context,
    )

    before = retained_native[: unique_indices[0]]
    after = retained_native[unique_indices[-1] + 1 :]
    new_native = [*before, *replacement_native, *after]

    rebuilt_messages, post_init_native = self._rebuild_core_from_native(
        new_native, config, context=context
    )

    base_metadata["native_messages"] = post_init_native
    base_metadata["native_messages_integrity"] = self._compute_native_integrity(
        rebuilt_messages
    )

    return Session(
        session_id=session.session_id,
        messages=rebuilt_messages,
        metadata=base_metadata,
    )

# Convert core messages to provider-native history.
core_dicts: List[Dict[str, Any]] = [m.to_dict() for m in session.messages]
new_native = self._core_messages_to_native_for_config(
    core_dicts,
    config,
    context=context,
)

# Rebuild canonical core messages from the new native history so that
# provider/feature transformations and native_indices are normalized.
# Use post-initialize native to capture any structural changes from features.
rebuilt_messages, post_init_native = self._rebuild_core_from_native(
    new_native, config, context=context
)

new_metadata: Dict[str, Any] = (
    dict(session.metadata) if isinstance(session.metadata, dict) else {}
)
new_metadata["native_messages"] = post_init_native
new_metadata["native_messages_integrity"] = self._compute_native_integrity(
    rebuilt_messages
)

return Session(
    session_id=session.session_id,
    messages=rebuilt_messages,
    metadata=new_metadata,
)
```

```

### register_feature

```

register_feature(plugin_class)

```

Register a feature plugin class.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `plugin_class` | `type` | Feature plugin class. | *required* |

Source code in `agent_core/core.py`

```

def register_feature(self, plugin_class: type) -> None: """Register a feature plugin class.

```
Args:
    plugin_class: Feature plugin class.
"""
wrapper = FeatureWrapper(plugin_class)
self._features.append(wrapper)
self._reset_caches()
```

```

### register_provider

```

register_provider(plugin_class, extensions=None)

```

Register provider plugin class with optional provider extensions.

Extensions are loaded by the provider wrapper (same language, hot path).

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `plugin_class` | `type` | Provider plugin class. | *required* |
| `extensions` | `Optional[List[type]]` | Optional list of provider extension classes to register with the provider. | `None` |

Source code in `agent_core/core.py`

```

def register_provider( self, plugin_class: type, extensions: Optional\[List[type]\] = None ) -> None: """Register provider plugin class with optional provider extensions.

```
Extensions are loaded by the provider wrapper (same language, hot path).

Args:
    plugin_class: Provider plugin class.
    extensions: Optional list of provider extension classes to register with the provider.
"""
wrapper = ProviderWrapper(plugin_class, extensions or [])
self._providers = [*self._providers, wrapper]
self._reset_caches()
```

```

### register_tool

```

register_tool(plugin_class)

```

Register a tool plugin class.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `plugin_class` | `type` | Tool plugin class. | *required* |

Source code in `agent_core/core.py`

```

def register_tool(self, plugin_class: type) -> None: """Register a tool plugin class.

```
Args:
    plugin_class: Tool plugin class.
"""
wrapper = ToolWrapper(plugin_class)
self._tools.append(wrapper)
self._reset_caches()
```

```

### send_request

```

send_request( session, config, \*, request_id=None, cancellation=None, context=None )

```

Send request and return a new session with the response.

Runs provider call + finalize with features operating on provider-native data;
converts provider-native finals to core at the end and appends them to the session.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `session` | `Session` | Current session. | *required* |
| `config` | `Dict[str, Any]` | Application-provided configuration for this request. | *required* |

Returns:

| Type | Description |
| --- | --- |
| `Session` | Tuple of (new_session, final_core_messages) where the new session includes the |
| `List[Dict[str, Any]]` | appended final messages and retained provider-native history for this turn. |

Raises:

| Type | Description |
| --- | --- |
| `RuntimeError` | If no provider is registered. |

Source code in `agent_core/core.py`

```

def send_request( self, session: Session, config: Dict[str, Any], \*, request_id: str | None = None, cancellation: Any | None = None, context: Optional\[Dict[str, Any]\] = None, ) -> Tuple\[Session, List\[Dict[str, Any]\]\]: """Send request and return a new session with the response.

```
Runs provider call + finalize with features operating on provider-native data;
converts provider-native finals to core at the end and appends them to the session.

Args:
    session: Current session.
    config: Application-provided configuration for this request.

Returns:
    Tuple of (new_session, final_core_messages) where the new session includes the
    appended final messages and retained provider-native history for this turn.

Raises:
    RuntimeError: If no provider is registered.
"""
if not self._providers:
    raise RuntimeError("No provider registered")

provider, enabled_extensions, features, tools, _tags = (
    self._resolve_plugins_for_config(config)
)

features = sorted(features, key=lambda feat: getattr(feat, "priority", 100))

logger.debug(
    "plugins_resolved_for_config",
    provider=provider.name,
    extensions=[ext.name for ext in enabled_extensions],
    features=[feat.name for feat in features],
    tools=[tool.name for tool in tools],
    tags=_tags,
)

provider.set_active_extensions(enabled_extensions)
cancel_token: Any | None = None
if request_id and cancellation is not None:
    try:
        cancel_token = cancellation.add_callback(
            lambda: provider.cancel_request(request_id)
        )
    except Exception:
        cancel_token = None

try:
    messages, native_messages, state, native_history_changed = (
        self._pre_request(
            session,
            config,
            provider,
            features,
            tools,
            request_id=request_id,
            tags=_tags,
            models=self._get_models_for_config(provider, config),
            context=context,
        )
    )
    baseline_native_len = len(native_messages)
    request_context = self._build_request_context(
        config=state.get("config") or config,
        provider=provider,
        enabled_extensions=provider._iter_extensions(),
        enabled_features=features,
        enabled_tools=tools,
        tags=_tags,
        models=self._get_models_for_config(provider, config),
        available_tools=self.get_available_tools(config),
        tools=self._get_prepared_tools_for_config(config),
        session=session,
        request_id=request_id,
        stream=False,
        extra=context,
    )

    logger.debug(
        "sending request",
        native_messages=str(native_messages)[:1000],
        request=str(state.get("request"))[:1000],
    )

    _partials, final_native_1, native_messages, state = provider.call_api(
        native_messages,
        state,
        request_id=request_id,
    )
finally:
    if cancellation is not None and cancel_token is not None:
        try:
            cancellation.remove_callback(cancel_token)
        except Exception:
            pass

# Provider finalize returns provider-native finals and full native history
final_native_2, native_messages, state = provider.finalize(
    native_messages,
    state,
    context=request_context,
)

# Combine provider-native finals from call_api and provider.finalize
final_native = final_native_1 + final_native_2

# Feature finalize chain over provider-native finals (native cold path)
for feature in features:
    final_native, native_messages, state = feature.finalize(
        final_native,
        native_messages,
        state,
        context=request_context,
    )

# Convert provider-native finals to core messages once finalization completes
final_core = provider.from_native_messages(
    final_native,
    state,
    context=request_context,
)
# Apply extension and feature from-native transforms (iterate to pass state to each)
for ext in enabled_extensions:
    final_core = ext.from_native_messages(
        final_native,
        final_core,
        state,
        context=request_context,
    )
for feature in features:
    final_core = feature.from_native_messages(
        final_native,
        final_core,
        state,
        context=request_context,
    )

# Attach global native_indices for final core messages
final_core = self._normalize_final_core_with_native_indices(
    final_core,
    final_native,
    baseline_native_len,
)

final_core, native_messages, response_metadata_patch, _response_results = (
    self.execute_response_lifecycle_actions(
        session,
        config,
        "response_finalize",
        provider=provider,
        features=features,
        state=state,
        final_messages=final_core,
        native_messages=native_messages,
        native_final_messages=final_native,
        stream=False,
        turn_native_start_index=baseline_native_len,
        request_context=request_context,
        extra_context=context,
    )
)
state_metadata_patch = (
    state.get("session_metadata_patch")
    if isinstance(state.get("session_metadata_patch"), dict)
    else {}
)
if state_metadata_patch:
    response_metadata_patch = {
        **state_metadata_patch,
        **(response_metadata_patch or {}),
    }

# Build new session messages by appending new Message objects
new_metadata = dict(session.metadata)
if response_metadata_patch:
    new_metadata.update(response_metadata_patch)
# Persist full provider-native history for the turn (implementation detail)
new_metadata["native_messages"] = native_messages
if native_history_changed:
    all_messages_after, _ = self._rebuild_core_from_native(
        native_messages,
        config,
        context=context,
    )
else:
    appended: List[Message] = [Message.from_dict(m) for m in final_core]
    all_messages_after = [*session.messages, *appended]
new_metadata["native_messages_integrity"] = self._compute_native_integrity(
    all_messages_after
)
new_session = Session(session.session_id, all_messages_after, new_metadata)

logger.info(
    "send_request_complete",
    final_native=final_native,
    final_core=final_core,
)

return new_session, final_core
```

```

### send_request_stream

```

send_request_stream( session, config, \*, request_id=None, cancellation=None, context=None )

```

Stream request and yield partial events, then the final session.

Uses provider streaming with optimized hot-path processing; features operate on the
provider-native finals at finalize, then core converts once and appends to the session.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `session` | `Session` | Current session. | *required* |
| `config` | `Dict[str, Any]` | Application-provided configuration for this request. | *required* |

Yields:

| Type | Description |
| --- | --- |
| `Dict[str, Any]` | Event dictionaries: |
| `Dict[str, Any]` | {"type": "partial", "message": core-like partial dict} |
| `Dict[str, Any]` | {"type": "final", "session": new_session, "messages": final_core_messages} |

Raises:

| Type | Description |
| --- | --- |
| `RuntimeError` | If no provider is registered. |

Source code in `agent_core/core.py`

```

def send_request_stream( self, session: Session, config: Dict[str, Any], \*, request_id: str | None = None, cancellation: Any | None = None, context: Optional\[Dict[str, Any]\] = None, ) -> Iterator\[Dict[str, Any]\]: """Stream request and yield partial events, then the final session.

```
Uses provider streaming with optimized hot-path processing; features operate on the
provider-native finals at finalize, then core converts once and appends to the session.

Args:
    session: Current session.
    config: Application-provided configuration for this request.

Yields:
    Event dictionaries:
    - {"type": "partial", "message": core-like partial dict}
    - {"type": "final", "session": new_session, "messages": final_core_messages}

Raises:
    RuntimeError: If no provider is registered.
"""
if not self._providers:
    raise RuntimeError("No provider registered")

provider, enabled_extensions, features, tools, _tags = (
    self._resolve_plugins_for_config(config)
)

features = sorted(features, key=lambda feat: getattr(feat, "priority", 100))

logger.debug(
    "plugins_resolved_for_config",
    provider=provider.name,
    extensions=[ext.name for ext in enabled_extensions],
    features=[feat.name for feat in features],
    tools=[tool.name for tool in tools],
    tags=_tags,
)

provider.set_active_extensions(enabled_extensions)
cancel_token: Any | None = None
if request_id and cancellation is not None:
    try:
        cancel_token = cancellation.add_callback(
            lambda: provider.cancel_request(request_id)
        )
    except Exception:
        cancel_token = None

try:
    messages, native_messages, state, native_history_changed = (
        self._pre_request(
            session,
            config,
            provider,
            features,
            tools,
            request_id=request_id,
            tags=_tags,
            models=self._get_models_for_config(provider, config),
            context=context,
        )
    )
    baseline_native_len = len(native_messages)
    request_context = self._build_request_context(
        config=state.get("config") or config,
        provider=provider,
        enabled_extensions=provider._iter_extensions(),
        enabled_features=features,
        enabled_tools=tools,
        tags=_tags,
        models=self._get_models_for_config(provider, config),
        available_tools=self.get_available_tools(config),
        tools=self._get_prepared_tools_for_config(config),
        session=session,
        request_id=request_id,
        stream=True,
        extra=context,
    )

    logger.debug(
        "start streaming request",
        native_messages=str(native_messages)[:1000],
        requrest=str(state.get("request", None))[:1000],
    )

    aggregated_native_finals: List[Dict[str, Any]] = []

    # Stream from provider using optimized streaming
    partial_count = 0
    for event in provider.stream_messages(
        native_messages, state, request_id=request_id
    ):
        # logger.debug("streaming event received", _event=event) # the first positional argument is also named 'event', we cannot use that name
        if event["type"] == "partial":
            partial_count += 1
            log_chunk_processing.debug(
                "partial message received", partial=event["message"]
            )
            yield {"type": "partial", "message": event["message"]}
        elif event["type"] == "final_messages":
            # These are provider-native finals
            log_chunk_processing.debug(
                "final message received", final=event.get("messages")
            )
            aggregated_native_finals.extend(event["messages"])
finally:
    if cancellation is not None and cancel_token is not None:
        try:
            cancellation.remove_callback(cancel_token)
        except Exception:
            pass

# Finalize using the last accumulated native messages
final_native, native_messages, state = provider.finalize(
    provider.get_last_native_messages(),
    provider.get_state(),
    context=request_context,
)

combined_native_finals = [*aggregated_native_finals, *final_native]

# Feature finalize chain (native)
for feature in features:
    combined_native_finals, native_messages, state = feature.finalize(
        combined_native_finals,
        native_messages,
        state,
        context=request_context,
    )

logger.debug(
    "streaming complete", combined_native_finals=combined_native_finals
)

# Convert provider-native finals to core messages
final_core = provider.from_native_messages(
    combined_native_finals,
    state,
    context=request_context,
)

# Apply extension and feature from-native transforms (iterate to pass state to each)
for ext in enabled_extensions:
    final_core = ext.from_native_messages(
        combined_native_finals,
        final_core,
        state,
        context=request_context,
    )
for feature in features:
    final_core = feature.from_native_messages(
        combined_native_finals,
        final_core,
        state,
        context=request_context,
    )

# Attach global native_indices for final core messages
final_core = self._normalize_final_core_with_native_indices(
    final_core,
    combined_native_finals,
    baseline_native_len,
)

final_core, native_messages, response_metadata_patch, _response_results = (
    self.execute_response_lifecycle_actions(
        session,
        config,
        "response_finalize",
        provider=provider,
        features=features,
        state=state,
        final_messages=final_core,
        native_messages=native_messages,
        native_final_messages=combined_native_finals,
        stream=True,
        turn_native_start_index=baseline_native_len,
        request_context=request_context,
        extra_context=context,
    )
)
state_metadata_patch = (
    state.get("session_metadata_patch")
    if isinstance(state.get("session_metadata_patch"), dict)
    else {}
)
if state_metadata_patch:
    response_metadata_patch = {
        **state_metadata_patch,
        **(response_metadata_patch or {}),
    }

new_metadata = dict(session.metadata)
if response_metadata_patch:
    new_metadata.update(response_metadata_patch)
new_metadata["native_messages"] = native_messages
if native_history_changed:
    # Rebuild core from the post-initialize native (after structural changes)
    all_messages_after, _ = self._rebuild_core_from_native(
        native_messages,
        config,
        context=context,
    )
else:
    appended: List[Message] = [Message.from_dict(m) for m in final_core]
    all_messages_after = [*session.messages, *appended]
new_metadata["native_messages_integrity"] = self._compute_native_integrity(
    all_messages_after
)
new_session = Session(session.session_id, all_messages_after, new_metadata)

logger.debug("streaming request complete", final_message=final_core)

yield {"type": "final", "session": new_session, "messages": final_core}
```

```

### send_request_stream_async

```

send_request_stream_async( session, config, \*, request_id=None, cancellation=None, context=None )

```

Async version of send_request_stream.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `session` | `Session` | Current session. | *required* |
| `config` | `Dict[str, Any]` | Application-provided configuration for this request. | *required* |

Yields:

| Type | Description |
| --- | --- |
| `AsyncIterator[Dict[str, Any]]` | Event dictionaries analogous to send_request_stream, but from an async iterator. |

Raises:

| Type | Description |
| --- | --- |
| `RuntimeError` | If no provider is registered. |

Source code in `agent_core/core.py`

```

async def send_request_stream_async( self, session: Session, config: Dict[str, Any], \*, request_id: str | None = None, cancellation: Any | None = None, context: Optional\[Dict[str, Any]\] = None, ) -> AsyncIterator\[Dict[str, Any]\]: """Async version of send_request_stream.

```
Args:
    session: Current session.
    config: Application-provided configuration for this request.

Yields:
    Event dictionaries analogous to send_request_stream, but from an async iterator.

Raises:
    RuntimeError: If no provider is registered.
"""
if not self._providers:
    raise RuntimeError("No provider registered")
provider, enabled_extensions, features, tools, _tags = (
    self._resolve_plugins_for_config(config)
)

features = sorted(features, key=lambda feat: getattr(feat, "priority", 100))

logger.debug(
    "plugins_resolved_for_config",
    provider=provider.name,
    extensions=[ext.name for ext in enabled_extensions],
    features=[feat.name for feat in features],
    tools=[tool.name for tool in tools],
    tags=_tags,
)

provider.set_active_extensions(enabled_extensions)
cancel_token: Any | None = None
if request_id and cancellation is not None:
    try:
        cancel_token = cancellation.add_callback(
            lambda: provider.cancel_request(request_id)
        )
    except Exception:
        cancel_token = None

try:
    messages, native_messages, state, native_history_changed = (
        self._pre_request(
            session,
            config,
            provider,
            features,
            tools,
            request_id=request_id,
            tags=_tags,
            models=self._get_models_for_config(provider, config),
            context=context,
        )
    )
    baseline_native_len = len(native_messages)
    request_context = self._build_request_context(
        config=state.get("config") or config,
        provider=provider,
        enabled_extensions=provider._iter_extensions(),
        enabled_features=features,
        enabled_tools=tools,
        tags=_tags,
        models=self._get_models_for_config(provider, config),
        available_tools=self.get_available_tools(config),
        tools=self._get_prepared_tools_for_config(config),
        session=session,
        request_id=request_id,
        stream=True,
        extra=context,
    )

    aggregated_native_finals: List[Dict[str, Any]] = []

    # Stream from provider (async) using optimized streaming
    async for event in provider.stream_messages_async(
        native_messages,
        state,
        request_id=request_id,
    ):
        if event["type"] == "partial":
            yield {"type": "partial", "message": event["message"]}
        elif event["type"] == "final_messages":
            aggregated_native_finals.extend(event["messages"])  # native finals
finally:
    if cancellation is not None and cancel_token is not None:
        try:
            cancellation.remove_callback(cancel_token)
        except Exception:
            pass

final_native, native_messages, state = provider.finalize(
    provider.get_last_native_messages(),
    provider.get_state(),
    context=request_context,
)

combined_native_finals = [*aggregated_native_finals, *final_native]

# Feature finalize chain (native)
for feature in features:
    combined_native_finals, native_messages, state = feature.finalize(
        combined_native_finals,
        native_messages,
        state,
        context=request_context,
    )

# Convert provider-native finals to core messages
final_core = provider.from_native_messages(
    combined_native_finals,
    state,
    context=request_context,
)

# Apply extension and feature from-native transforms (iterate to pass state to each)
for ext in enabled_extensions:
    final_core = ext.from_native_messages(
        combined_native_finals,
        final_core,
        state,
        context=request_context,
    )
for feature in features:
    final_core = feature.from_native_messages(
        combined_native_finals,
        final_core,
        state,
        context=request_context,
    )

# Attach global native_indices for final core messages
final_core = self._normalize_final_core_with_native_indices(
    final_core,
    combined_native_finals,
    baseline_native_len,
)

final_core, native_messages, response_metadata_patch, _response_results = (
    self.execute_response_lifecycle_actions(
        session,
        config,
        "response_finalize",
        provider=provider,
        features=features,
        state=state,
        final_messages=final_core,
        native_messages=native_messages,
        native_final_messages=combined_native_finals,
        stream=True,
        turn_native_start_index=baseline_native_len,
        request_context=request_context,
        extra_context=context,
    )
)
state_metadata_patch = (
    state.get("session_metadata_patch")
    if isinstance(state.get("session_metadata_patch"), dict)
    else {}
)
if state_metadata_patch:
    response_metadata_patch = {
        **state_metadata_patch,
        **(response_metadata_patch or {}),
    }

new_metadata = dict(session.metadata)
if response_metadata_patch:
    new_metadata.update(response_metadata_patch)
new_metadata["native_messages"] = native_messages
if native_history_changed:
    # Rebuild core from the post-initialize native (after structural changes)
    all_messages_after, _ = self._rebuild_core_from_native(
        native_messages,
        config,
        context=context,
    )
else:
    appended: List[Message] = [Message.from_dict(m) for m in final_core]
    all_messages_after = [*session.messages, *appended]
new_metadata["native_messages_integrity"] = self._compute_native_integrity(
    all_messages_after
)
new_session = Session(session.session_id, all_messages_after, new_metadata)

yield {"type": "final", "session": new_session, "messages": final_core}
```

```

### slice_session

```

slice_session( session, config=None, \*, start=None, end=None, remove_indices=None, return_removed=False )

```

Return a new session with messages sliced/removed.

Operations are expressed in core message indices but, when possible,
provider-native history is adjusted consistently and preserved.

Source code in `agent_core/core.py`

```

def slice_session( self, session: Session, config: Optional\[Dict[str, Any]\] = None, \*, start: Optional[int] = None, end: Optional[int] = None, remove_indices: Optional\[List[int]\] = None, return_removed: bool = False, ) -> Session: """Return a new session with messages sliced/removed.

```
Operations are expressed in core message indices but, when possible,
provider-native history is adjusted consistently and preserved.
"""
messages = session.messages
message_count = len(messages)
all_indices: Set[int] = set(range(message_count))

def _normalize_bound(bound: Optional[int], default: int) -> int:
    if bound is None:
        return default
    value = bound
    if value < 0:
        value = message_count + value
    if value < 0:
        return 0
    if value > message_count:
        return message_count
    return value

start_idx = _normalize_bound(start, 0)
end_idx = _normalize_bound(end, message_count)

range_indices: Optional[Set[int]] = None
if start is not None or end is not None:
    if start_idx >= end_idx:
        range_indices = set()
    else:
        range_indices = set(range(start_idx, end_idx))

remove_set: Set[int] = set()
if remove_indices:
    for idx in remove_indices:
        if not isinstance(idx, int):
            continue
        value = idx
        if value < 0:
            value = message_count + value
        if 0 <= value < message_count:
            remove_set.add(value)

if range_indices is not None:
    keep_set: Set[int] = range_indices.difference(remove_set)
else:
    keep_set = all_indices.difference(remove_set)

remove_set: Set[int] = all_indices.difference(keep_set)

if keep_set == all_indices:
    if not return_removed:
        return session
    # No messages removed; return an empty complement session that
    # mirrors the original metadata shape but without native history.
    empty = self._slice_session_core_only(session, set())
    return (session, empty)  # type: ignore[return-value]

if (
    config is None
    or not isinstance(session.metadata, dict)
    or len(self._providers) != 1
):
    kept = self._slice_session_core_only(session, keep_set)
    if not return_removed:
        return kept
    removed = self._slice_session_core_only(session, remove_set)
    return (kept, removed)  # type: ignore[return-value]

original_native = session.metadata.get("native_messages")
if not isinstance(original_native, list):
    kept = self._slice_session_core_only(session, keep_set)
    if not return_removed:
        return kept
    removed = self._slice_session_core_only(session, remove_set)
    return (kept, removed)  # type: ignore[return-value]

try:
    self._verify_native_integrity(session)
except Exception:
    kept = self._slice_session_core_only(session, keep_set)
    if not return_removed:
        return kept
    removed = self._slice_session_core_only(session, remove_set)
    return (kept, removed)  # type: ignore[return-value]

native_len = len(original_native)

core_to_native: Dict[int, List[int]] = {}
native_to_core: Dict[int, Set[int]] = {}

for idx, msg in enumerate(messages):
    md = msg.metadata if isinstance(msg.metadata, dict) else {}
    native_indices = md.get("native_indices")
    if native_indices is None:
        continue
    if not isinstance(native_indices, list) or not all(
        isinstance(j, int) for j in native_indices
    ):
        kept = self._slice_session_core_only(session, keep_set)
        if not return_removed:
            return kept
        removed = self._slice_session_core_only(session, remove_set)
        return (kept, removed)  # type: ignore[return-value]
    normalized_indices: List[int] = []
    for j in native_indices:
        if j < 0 or j >= native_len:
            kept = self._slice_session_core_only(session, keep_set)
            if not return_removed:
                return kept
            removed = self._slice_session_core_only(session, remove_set)
            return (kept, removed)  # type: ignore[return-value]
        if j not in normalized_indices:
            normalized_indices.append(j)
    if not normalized_indices:
        continue
    core_to_native[idx] = normalized_indices
    for j in normalized_indices:
        owners = native_to_core.get(j)
        if owners is None:
            native_to_core[j] = {idx}
        else:
            owners.add(idx)

for idx in keep_set:
    if idx not in core_to_native:
        kept = self._slice_session_core_only(session, keep_set)
        if not return_removed:
            return kept
        removed = self._slice_session_core_only(session, remove_set)
        return (kept, removed)  # type: ignore[return-value]

# Build native subsets for kept and removed halves in one pass so we
# can support split-like operations without duplicating logic.
native_candidates_keep: Set[int] = set()
native_candidates_remove: Set[int] = set()
for idx in keep_set:
    for j in core_to_native.get(idx, []):
        native_candidates_keep.add(j)
for idx in remove_set:
    for j in core_to_native.get(idx, []):
        native_candidates_remove.add(j)

if not native_candidates_keep:
    new_native_keep: List[Dict[str, Any]] = []
else:
    final_native_indices_keep = {
        j
        for j in native_candidates_keep
        if native_to_core.get(j, set()).issubset(keep_set)
    }
    sorted_keep = sorted(final_native_indices_keep)
    new_native_keep = [original_native[j] for j in sorted_keep]

if not native_candidates_remove:
    new_native_remove: List[Dict[str, Any]] = []
else:
    final_native_indices_remove = {
        j
        for j in native_candidates_remove
        if native_to_core.get(j, set()).issubset(remove_set)
    }
    sorted_remove = sorted(final_native_indices_remove)
    new_native_remove = [original_native[j] for j in sorted_remove]

try:
    # Skip initialize_request for session split operations.
    # This prevents features like SystemMessageFeature from adding
    # synthetic messages to partial sessions during split, which
    # would cause duplicates when the sessions are joined back.
    new_messages_keep, post_init_keep = self._rebuild_core_from_native(
        new_native_keep, config, skip_initialize=True
    )
    if new_native_remove:
        new_messages_remove, post_init_remove = self._rebuild_core_from_native(
            new_native_remove, config, skip_initialize=True
        )
    else:
        new_messages_remove = []
        post_init_remove = []
except Exception:
    kept = self._slice_session_core_only(session, keep_set)
    if not return_removed:
        return kept
    removed = self._slice_session_core_only(session, remove_set)
    return (kept, removed)  # type: ignore[return-value]

new_metadata_keep = dict(session.metadata)
new_metadata_keep["native_messages"] = post_init_keep
new_metadata_keep["native_messages_integrity"] = self._compute_native_integrity(
    new_messages_keep
)

kept_session = Session(
    session_id=session.session_id,
    messages=new_messages_keep,
    metadata=new_metadata_keep,
)

if not return_removed:
    return kept_session

new_metadata_remove = dict(session.metadata)
new_metadata_remove["native_messages"] = post_init_remove
new_metadata_remove["native_messages_integrity"] = (
    self._compute_native_integrity(new_messages_remove)
)

removed_session = Session(
    session_id=session.session_id,
    messages=new_messages_remove,
    metadata=new_metadata_remove,
)

return (kept_session, removed_session)  # type: ignore[return-value]
```

```

### stream_tool_call

```

stream_tool_call(tool_call, config, \*, context=None)

```

Stream partial results for a single tool call.

Uses the same tool resolution logic as :meth:`execute_tool_calls` but
invokes the optional :meth:`ToolPlugin.stream_tool` hook instead of the
synchronous execute/format path. If no tool provides streaming for the
given call, yields nothing.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `tool_call` | `Dict[str, Any]` | Tool call dictionary to execute. | *required* |
| `config` | `Dict[str, Any]` | Current resolved request configuration. | *required* |
| `context` | `Optional[Dict[str, Any]]` | Optional context for tool execution. Layer 1 context (core, config, trigger_source) is enriched by this method if not already present. | `None` |

Source code in `agent_core/core.py`

```

def stream_tool_call( self, tool_call: Dict[str, Any], config: Dict[str, Any], \*, context: Optional\[Dict[str, Any]\] = None, ) -> Iterator\[Dict[str, Any]\]: """Stream partial results for a single tool call.

```
Uses the same tool resolution logic as :meth:`execute_tool_calls` but
invokes the optional :meth:`ToolPlugin.stream_tool` hook instead of the
synchronous execute/format path. If no tool provides streaming for the
given call, yields nothing.

Args:
    tool_call: Tool call dictionary to execute.
    config: Current resolved request configuration.
    context: Optional context for tool execution. Layer 1 context (core,
        config, trigger_source) is enriched by this method if not already
        present.
"""
if not self._tools:
    return

provider, extensions, tool_states = self._get_enabled_tool_states_for_config(
    config
)
registry = self._get_tool_interop_registry_for_config(
    config,
    provider=provider,
    extensions=extensions,
    tool_states=tool_states,
)
try:
    inspected_call = registry.inspect_call(tool_call)
except Exception:
    return

tool, state, prepared, _schema = self._resolve_tool_handler_for_call(
    inspected_call,
    tool_states,
    registry,
)
if tool is None or state is None:
    return

# Layer 1: Core-level context enrichment.
tool_context = self._build_tool_runtime_context(config, context)

try:
    iterator = tool.stream_tool(
        inspected_call.tool_name,
        inspected_call.payload,
        state,
        payload_kind=inspected_call.payload_kind,
        payload_format=inspected_call.payload_format,
        payload_metadata=inspected_call.payload_metadata,
        tool_call=inspected_call.raw,
        context=tool_context,
        prepared=prepared,
    )
    iterator = iter(iterator)
except Exception:
    return
for chunk in iterator:
    if isinstance(chunk, dict):
        yield chunk
```

```
```
