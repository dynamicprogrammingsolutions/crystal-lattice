"""Defaulting adapters for plugin protocols.

These adapters wrap concrete plugin implementations (providers, extensions,
features, tools) and provide:

- Sensible default implementations for optional methods.
- Normalization of return types (lists, dicts, strings).
- A uniform, fully-implemented interface for wrappers and core.

Wrappers should construct these adapters internally and call their methods
instead of performing their own hasattr checks or defaulting logic.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Tuple, cast

from ..types import FeaturePlugin, ProviderExtensionPlugin, ProviderPlugin, ToolPlugin


class _BasePluginDefaults:
    """Shared helpers and default implementations for BasePlugin parts.

    Each adapter using this mixin must expose ``self.impl`` pointing to the
    underlying plugin implementation.
    """

    impl: Any

    def _identity(self, value: Any) -> Any:
        return value

    def _safe_dict(self, value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _safe_list(self, value: Any) -> List[Any]:
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        try:
            return list(value)
        except Exception:
            return []

    def _get_impl_method(self, name: str, protocol_cls: Optional[type] = None) -> Optional[Any]:
        """Return a concrete implementation for an optional hook.

        Treats Protocol stub methods (from the given protocol_cls) as "missing"
        so that adapters can supply their own defaults instead.
        """
        fn = getattr(self.impl, name, None)
        if not callable(fn):
            return None
        if protocol_cls is not None:
            proto_fn = getattr(protocol_cls, name, None)
            target = getattr(fn, "__func__", fn)
            if proto_fn is not None and target is proto_fn:
                return None
        return fn

    # ----- BasePlugin config / UI -----

    def get_config_schema(self) -> Dict[str, Any]:  # type: ignore[override]
        fn = getattr(self.impl, "get_config_schema", None)
        if callable(fn):
            return self._safe_dict(fn())
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # type: ignore[override]
        fn = getattr(self.impl, "get_ui_elements", None)
        if callable(fn):
            raw = fn()
            items = self._safe_list(raw)
            return [i for i in items if isinstance(i, dict)]
        return []


class ProviderDefaultsAdapter(_BasePluginDefaults, ProviderPlugin):
    """Adapter providing defaults for ProviderPlugin implementations.

    I/O methods (call_api, stream_api, process_chunk, finalize) remain
    required for providers and are delegated directly; this adapter focuses
    on defaulting and normalizing configuration, models/tags, and message
    conversions.
    """

    def __init__(self, impl: Any) -> None:
        self.impl = impl
        self.name = getattr(impl, "name", impl.__class__.__name__)
        self.version = getattr(impl, "version", "unknown")

    # ----- State lifecycle -----

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        fn = getattr(self.impl, "init", None)
        if callable(fn):
            state = fn(config)
            return state if isinstance(state, dict) else {"config": config}
        return {"config": config}

    def initialize_request(  # type: ignore[override]
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        fn = getattr(self.impl, "initialize_request", None)
        if callable(fn):
            out = fn(native_messages, state)
            if isinstance(out, tuple) and len(out) == 2:
                raw_native, raw_state = out
                natives = [m for m in self._safe_list(raw_native) if isinstance(m, dict)]
                new_state = raw_state if isinstance(raw_state, dict) else state
                return natives or list(native_messages), new_state
            if isinstance(out, dict):
                return list(native_messages), out
        return list(native_messages), state

    # ----- Message conversion -----

    def to_native_messages(  # type: ignore[override]
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("to_native_messages", ProviderPlugin)
        if fn is not None:
            out = fn(messages, state)
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]
        return [
            {"role": m.get("role", "user"), "content": m.get("content", "")}
            for m in messages
            if isinstance(m, dict)
        ]

    def from_native_messages(  # type: ignore[override]
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("from_native_messages", ProviderPlugin)
        if fn is not None:
            out = fn(native_messages, state)
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]

        finals: List[Dict[str, Any]] = []
        for m in native_messages:
            if not isinstance(m, dict):
                continue
            if not ("role" in m or "content" in m):
                continue
            msg: Dict[str, Any] = {
                "role": m.get("role", "assistant"),
                "content": m.get("content", ""),
            }
            finals.append({**msg, "metadata": {}})
        return finals

    # ----- Models / tags -----

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        fn = getattr(self.impl, "get_models", None)
        if callable(fn):
            out = fn(config)
            items = self._safe_list(out)
            models = [m for m in items if isinstance(m, dict)]
        else:
            model = config.get("model")
            models = [{"id": model}] if isinstance(model, str) and model else []
        return models

    def get_tags(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        fn = getattr(self.impl, "get_tags", None)
        raw = fn(config, models) if callable(fn) else []
        items = self._safe_list(raw)
        return [str(t) for t in items]

    # ----- Display formatting -----

    def to_display_format(  # type: ignore[override]
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        fn = getattr(self.impl, "to_display_format", None)
        if callable(fn):
            out = fn(message, state)
            return out if isinstance(out, dict) else message
        return message

    # ----- I/O methods: delegate with light validation -----

    def call_api(  # type: ignore[override]
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        finals, partials, natives, new_state = self.impl.call_api(  # type: ignore[attr-defined]
            native_messages, state
        )
        return (
            [m for m in self._safe_list(partials) if isinstance(m, dict)],
            [m for m in self._safe_list(finals) if isinstance(m, dict)],
            [m for m in self._safe_list(natives) if isinstance(m, dict)],
            new_state if isinstance(new_state, dict) else state,
        )

    def stream_api(  # type: ignore[override]
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        for chunk in self.impl.stream_api(native_messages, state):  # type: ignore[attr-defined]
            if isinstance(chunk, dict):
                yield chunk

    async def stream_api_async(  # type: ignore[override]
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        impl_async = getattr(self.impl, "stream_api_async", None)
        if callable(impl_async):
            async for chunk in impl_async(native_messages, state):  # type: ignore[misc]
                if isinstance(chunk, dict):
                    yield chunk
            return
        for chunk in self.stream_api(native_messages, state):
            yield chunk

    def process_chunk(  # type: ignore[override]
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
        partials, finals, natives, new_state = self.impl.process_chunk(  # type: ignore[attr-defined]
            native_chunk, native_messages, state
        )
        return (
            [m for m in self._safe_list(partials) if isinstance(m, dict)],
            [m for m in self._safe_list(finals) if isinstance(m, dict)],
            [m for m in self._safe_list(natives) if isinstance(m, dict)],
            new_state if isinstance(new_state, dict) else state,
        )

    def finalize(  # type: ignore[override]
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        finals, natives, new_state = self.impl.finalize(  # type: ignore[attr-defined]
            native_messages, state
        )
        return (
            [m for m in self._safe_list(finals) if isinstance(m, dict)],
            [m for m in self._safe_list(natives) if isinstance(m, dict)],
            new_state if isinstance(new_state, dict) else state,
        )


class ProviderExtensionDefaultsAdapter(_BasePluginDefaults, ProviderExtensionPlugin):
    """Adapter providing defaults for ProviderExtensionPlugin implementations."""

    def __init__(self, impl: Any) -> None:
        self.impl = impl
        self.name = getattr(impl, "name", impl.__class__.__name__)
        self.version = getattr(impl, "version", "unknown")

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        fn = getattr(self.impl, "init", None)
        if callable(fn):
            new_state = fn(config, state)
            return new_state if isinstance(new_state, dict) else state
        return state

    def get_models(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "get_models", None)
        if callable(fn):
            out = fn(config, models)
            items = self._safe_list(out)
            result = [m for m in items if isinstance(m, dict)]
            return result or list(models)
        return list(models)

    def get_tags(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        fn = getattr(self.impl, "get_tags", None)
        raw = fn(config, models) if callable(fn) else []
        items = self._safe_list(raw)
        return [str(t) for t in items]

    def required_tags(self) -> List[str]:  # type: ignore[override]
        fn = getattr(self.impl, "required_tags", None)
        raw = fn() if callable(fn) else []
        items = self._safe_list(raw)
        return [str(t) for t in items]

    def to_native_messages(  # type: ignore[override]
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("to_native_messages", ProviderExtensionPlugin)
        if fn is not None:
            out = fn(messages, native_messages)
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]
        return list(native_messages)

    def from_native_messages(  # type: ignore[override]
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("from_native_messages", ProviderExtensionPlugin)
        if fn is not None:
            out = fn(native_messages, messages)
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]
        return list(messages)

    def initialize_request(  # type: ignore[override]
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        fn = getattr(self.impl, "initialize_request", None)
        if callable(fn):
            out = fn(native_messages, state)
            if isinstance(out, tuple) and len(out) == 2:
                raw_native, raw_state = out
                natives = [m for m in self._safe_list(raw_native) if isinstance(m, dict)]
                new_state = raw_state if isinstance(raw_state, dict) else state
                return natives or list(native_messages), new_state
            if isinstance(out, dict):
                return list(native_messages), out
        return list(native_messages), state

    def process_chunk(  # type: ignore[override]
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        fn = getattr(self.impl, "process_chunk", None)
        if callable(fn):
            return cast(
                Tuple[
                    List[Dict[str, Any]],
                    List[Dict[str, Any]],
                    List[Dict[str, Any]],
                    Dict[str, Any],
                ],
                fn(
                    native_chunk,
                    partial_messages,
                    final_messages,
                    native_messages,
                    state,
                ),
            )
        return partial_messages, final_messages, native_messages, state

    def finalize(  # type: ignore[override]
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        fn = getattr(self.impl, "finalize", None)
        if callable(fn):
            return cast(
                Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]],
                fn(final_messages, native_messages, state),
            )
        return final_messages, native_messages, state


class FeatureDefaultsAdapter(_BasePluginDefaults, FeaturePlugin):
    """Adapter providing defaults for FeaturePlugin implementations."""

    def __init__(self, impl: Any) -> None:
        self.impl = impl
        self.name = getattr(impl, "name", impl.__class__.__name__)
        self.version = getattr(impl, "version", "unknown")

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        fn = getattr(self.impl, "init", None)
        if callable(fn):
            new_state = fn(config, state)
            return new_state if isinstance(new_state, dict) else state
        return state

    def get_models(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "get_models", None)
        if callable(fn):
            out = fn(config, models)
            items = self._safe_list(out)
            result = [m for m in items if isinstance(m, dict)]
            return result or list(models)
        return list(models)

    def get_tags(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        fn = getattr(self.impl, "get_tags", None)
        raw = fn(config, models) if callable(fn) else []
        items = self._safe_list(raw)
        return [str(t) for t in items]

    def required_tags(self) -> List[str]:  # type: ignore[override]
        fn = getattr(self.impl, "required_tags", None)
        raw = fn() if callable(fn) else []
        items = self._safe_list(raw)
        return [str(t) for t in items]

    def get_template(self, config: Dict[str, Any]) -> str:  # type: ignore[override]
        fn = getattr(self.impl, "get_template", None)
        if callable(fn):
            try:
                out = fn(config)
            except Exception:
                return ""
            return str(out) if out is not None else ""
        return ""

    def to_native_messages(  # type: ignore[override]
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("to_native_messages", FeaturePlugin)
        if fn is not None:
            out = fn(messages, native_messages)
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]
        return list(native_messages)

    def from_native_messages(  # type: ignore[override]
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("from_native_messages", FeaturePlugin)
        if fn is not None:
            out = fn(native_messages, messages)
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]
        return list(messages)

    def initialize_request(  # type: ignore[override]
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        fn = getattr(self.impl, "initialize_request", None)
        if callable(fn):
            out = fn(native_messages, state)
            if isinstance(out, tuple) and len(out) == 2:
                raw_native, raw_state = out
                natives = [m for m in self._safe_list(raw_native) if isinstance(m, dict)]
                new_state = raw_state if isinstance(raw_state, dict) else state
                return natives or list(native_messages), new_state
            if isinstance(out, dict):
                return list(native_messages), out
        return list(native_messages), state

    def finalize(  # type: ignore[override]
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        fn = getattr(self.impl, "finalize", None)
        if callable(fn):
            return cast(
                Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]],
                fn(final_messages, native_messages, state),
            )
        return final_messages, native_messages, state

    def get_completions(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        text: str,
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "get_completions", None)
        if callable(fn):
            try:
                out = fn(config, text)
            except Exception:
                return []
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]
        return []

    def apply_completion(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        text: str,
        completion: Dict[str, Any],
    ) -> str:
        fn = getattr(self.impl, "apply_completion", None)
        if callable(fn):
            try:
                out = fn(config, text, completion)
            except Exception:
                return ""
            return str(out) if out is not None else ""
        return ""


class ToolDefaultsAdapter(_BasePluginDefaults, ToolPlugin):
    """Adapter providing defaults for ToolPlugin implementations."""

    def __init__(self, impl: Any) -> None:
        self.impl = impl
        self.name = getattr(impl, "name", impl.__class__.__name__)
        self.version = getattr(impl, "version", "unknown")

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        fn = getattr(self.impl, "init", None)
        if callable(fn):
            state = fn(config)
            return state if isinstance(state, dict) else {"config": config}
        return {"config": config}

    def get_tags(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        fn = getattr(self.impl, "get_tags", None)
        raw = fn(config, models) if callable(fn) else []
        items = self._safe_list(raw)
        return [str(t) for t in items]

    def required_tags(self) -> List[str]:  # type: ignore[override]
        fn = getattr(self.impl, "required_tags", None)
        raw = fn() if callable(fn) else []
        items = self._safe_list(raw)
        return [str(t) for t in items]

    def get_tool_schemas(  # type: ignore[override]
        self, state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "get_tool_schemas", None)
        if callable(fn):
            out = fn(state)
            items = self._safe_list(out)
            return [s for s in items if isinstance(s, dict)]
        return []

    def execute_tool(  # type: ignore[override]
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        fn = getattr(self.impl, "execute_tool", None)
        if callable(fn):
            out = fn(tool_name, arguments, state)
            return (
                out
                if isinstance(out, dict)
                else {
                    "success": False,
                    "error": "invalid tool result",
                }
            )
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def format_tool_result(  # type: ignore[override]
        self, result: Dict[str, Any], state: Dict[str, Any]
    ) -> str:
        fn = getattr(self.impl, "format_tool_result", None)
        if callable(fn):
            out = fn(result, state)
            return str(out)
        if result.get("success"):
            return f"Result: {result.get('result')}"
        return f"Error: {result.get('error')}"

    def format_tool_call_preview(  # type: ignore[override]
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        fn = getattr(self.impl, "format_tool_call_preview", None)
        if callable(fn):
            out = fn(tool_name, arguments, state)
            return str(out) if out else ""
        return ""

    def stream_tool(  # type: ignore[override]
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        """Default streaming hook.

        When the underlying implementation provides ``stream_tool``, delegate to
        it and forward any dictionary chunks. Otherwise, wrap ``execute_tool``
        so that non-streaming tools yield a single RESULT dict (no partials).
        """
        fn = self._get_impl_method("stream_tool", ToolPlugin)
        if fn is None:
            # No partials; yield only the final result dict.
            result = self.execute_tool(tool_name, arguments, state)
            if isinstance(result, dict):
                yield result
            return
        out = fn(tool_name, arguments, state)
        try:
            iterator = iter(out)
        except TypeError:
            return
        for chunk in iterator:
            if isinstance(chunk, dict):
                yield chunk

    def to_display_format(  # type: ignore[override]
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Default display hook: delegate when implemented, else wrap as text payload."""
        fn = self._get_impl_method("to_display_format", ToolPlugin)
        if fn is not None:
            out = fn(text, result, state)
            if isinstance(out, dict):
                return out
        return {"type": "text", "content": str(text)}
