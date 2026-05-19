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

import inspect
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Tuple, cast

from ..tool_interop import ToolInteropContribution
from ..tool_result_payloads import is_provider_native_tool_result
from ..types import (
    FeaturePlugin,
    ProviderExtensionPlugin,
    ProviderPlugin,
    Session,
    ToolDescriptor,
    ToolPlugin,
)


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

    @staticmethod
    def _ensure_state_config(
        config: Dict[str, Any],
        state: Any,
    ) -> Dict[str, Any]:
        if not isinstance(state, dict):
            return {"config": config}
        existing = state.get("config")
        if isinstance(existing, dict):
            return state
        return {**state, "config": config}

    @staticmethod
    def _call_with_optional_context(
        fn: Any,
        args_before_context: Tuple[Any, ...],
        context: Any,
        args_after_context: Tuple[Any, ...] = (),
    ) -> Any:
        """Call ``fn`` with ``context`` when the implementation accepts it.

        This preserves backward compatibility for existing plugins whose
        ``execute_action`` implementations predate the extra context argument.
        """

        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return fn(*args_before_context, context, *args_after_context)

        params = list(sig.parameters.values())
        if any(
            p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            for p in params
        ):
            return fn(*args_before_context, context, *args_after_context)

        positional = [
            p
            for p in params
            if p.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]

        if len(positional) >= len(args_before_context) + len(args_after_context) + 1:
            return fn(*args_before_context, context, *args_after_context)
        return fn(*args_before_context, *args_after_context)

    def _get_impl_method(
        self, name: str, protocol_cls: Optional[type] = None
    ) -> Optional[Any]:
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

    @staticmethod
    def _call_with_optional_kwargs(fn: Any, *args: Any, **kwargs: Any) -> Any:
        """Call ``fn`` with only the keyword arguments it accepts.

        This preserves backward compatibility for implementations that still
        use the older positional-only tool hook signatures.
        """

        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return fn(*args, **kwargs)

        params = list(sig.parameters.values())
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params):
            return fn(*args, **kwargs)

        accepted = {
            name: value for name, value in kwargs.items() if name in sig.parameters
        }
        return fn(*args, **accepted)

    @staticmethod
    def _call_message_conversion_hook(
        fn: Any,
        first: Any,
        second: Any,
        state: Any,
        context: Any,
    ) -> Any:
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return fn(first, second, state, context=context)

        params = list(sig.parameters.values())
        has_var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params)
        positional = [
            p
            for p in params
            if p.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        args = [first, second]
        if len(positional) >= 3:
            args.append(state)
        kwargs: Dict[str, Any] = {}
        if has_var_keyword or "context" in sig.parameters:
            kwargs["context"] = context
        return fn(*args, **kwargs)

    # ----- BasePlugin config / UI -----

    def get_config_schema(self) -> Dict[str, Any]:  # type: ignore[override]
        fn = getattr(self.impl, "get_config_schema", None)
        if callable(fn):
            return self._safe_dict(fn())
        return {}

    def get_ui_elements(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "get_ui_elements", None)
        if not callable(fn):
            return []
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            raw = fn(config, context)
        else:
            params = list(sig.parameters.values())
            has_variadic = any(
                p.kind
                in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                )
                for p in params
            )
            positional = [
                p
                for p in params
                if p.kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            ]
            if not positional and not has_variadic:
                raw = fn()
            else:
                ui_context = context if isinstance(context, dict) else {}
                raw = self._call_with_optional_kwargs(
                    fn,
                    config,
                    tags=ui_context.get("tags", []),
                    models=ui_context.get("models", []),
                    context=context,
                )
        items = self._safe_list(raw)
        return [i for i in items if isinstance(i, dict)]


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
            return self._ensure_state_config(config, state)
        return {"config": config}

    def initialize_request(  # type: ignore[override]
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        fn = getattr(self.impl, "initialize_request", None)
        if callable(fn):
            out = self._call_with_optional_kwargs(
                fn,
                native_messages,
                state,
                request_id=request_id,
                context=context,
            )
            if isinstance(out, tuple) and len(out) == 2:
                raw_native, raw_state = out
                new_state = raw_state if isinstance(raw_state, dict) else state
                if isinstance(raw_native, list):
                    if all(isinstance(m, dict) for m in raw_native):
                        return raw_native, new_state
                    return native_messages, new_state
                return native_messages, new_state
            if isinstance(out, dict):
                return native_messages, out
        return native_messages, state

    def get_tool_interop_contribution(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> ToolInteropContribution:
        fn = self._get_impl_method("get_tool_interop_contribution", ProviderPlugin)
        if fn is None:
            return ToolInteropContribution()
        out = self._call_with_optional_kwargs(fn, config, state)
        return (
            out
            if isinstance(out, ToolInteropContribution)
            else ToolInteropContribution()
        )

    def accepted_tool_schema_formats(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> List[str]:
        fn = self._get_impl_method("accepted_tool_schema_formats", ProviderPlugin)
        if fn is None:
            return []
        out = self._call_with_optional_kwargs(fn, config, state)
        items = self._safe_list(out)
        return [item for item in items if isinstance(item, str) and item]

    def emitted_tool_call_formats(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> List[str]:
        fn = self._get_impl_method("emitted_tool_call_formats", ProviderPlugin)
        if fn is None:
            return []
        out = self._call_with_optional_kwargs(fn, config, state)
        items = self._safe_list(out)
        return [item for item in items if isinstance(item, str) and item]

    # ----- Message conversion -----

    def to_native_messages(  # type: ignore[override]
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("to_native_messages", ProviderPlugin)
        if fn is not None:
            out = self._call_with_optional_kwargs(
                fn,
                messages,
                state,
                context=context,
            )
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]
        return [
            {"role": m.get("role", "user"), "content": m.get("content", "")}
            for m in messages
            if isinstance(m, dict)
        ]

    def from_native_messages(  # type: ignore[override]
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("from_native_messages", ProviderPlugin)
        if fn is not None:
            out = self._call_with_optional_kwargs(
                fn,
                native_messages,
                state,
                context=context,
            )
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
        *,
        request_id: str | None = None,
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        partials, finals, natives, new_state = self._call_with_optional_kwargs(
            self.impl.call_api,  # type: ignore[attr-defined]
            native_messages,
            state,
            request_id=request_id,
        )
        return (
            [m for m in self._safe_list(partials) if isinstance(m, dict)],
            [m for m in self._safe_list(finals) if isinstance(m, dict)],
            [m for m in self._safe_list(natives) if isinstance(m, dict)],
            new_state if isinstance(new_state, dict) else state,
        )

    def stream_api(  # type: ignore[override]
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Iterator[Dict[str, Any]]:
        stream = self._call_with_optional_kwargs(
            self.impl.stream_api,  # type: ignore[attr-defined]
            native_messages,
            state,
            request_id=request_id,
        )
        for chunk in stream:
            if isinstance(chunk, dict):
                yield chunk

    async def stream_api_async(  # type: ignore[override]
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        impl_async = getattr(self.impl, "stream_api_async", None)
        if callable(impl_async):
            async_iter = self._call_with_optional_kwargs(
                impl_async,
                native_messages,
                state,
                request_id=request_id,
            )
            async for chunk in async_iter:  # type: ignore[misc]
                if isinstance(chunk, dict):
                    yield chunk
            return
        for chunk in self.stream_api(native_messages, state, request_id=request_id):
            yield chunk

    def cancel_request(self, request_id: str) -> bool:  # type: ignore[override]
        fn = getattr(self.impl, "cancel_request", None)
        if callable(fn):
            try:
                return bool(fn(request_id))
            except Exception:
                return False
        return False

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
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        finals, natives, new_state = self._call_with_optional_kwargs(
            self.impl.finalize,  # type: ignore[attr-defined]
            native_messages,
            state,
            context=context,
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
            return self._ensure_state_config(
                config, new_state if isinstance(new_state, dict) else state
            )
        return self._ensure_state_config(config, state)

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

    def forbidden_tags(self) -> List[str]:  # type: ignore[override]
        fn = getattr(self.impl, "forbidden_tags", None)
        raw = fn() if callable(fn) else []
        items = self._safe_list(raw)
        return [str(t) for t in items]

    def is_enabled(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Optional[bool]:
        fn = getattr(self.impl, "is_enabled", None)
        if callable(fn):
            return fn(config, tags, models, context)
        return None

    def to_native_messages(  # type: ignore[override]
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any] | None = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("to_native_messages", ProviderExtensionPlugin)
        if fn is not None:
            out = self._call_message_conversion_hook(
                fn,
                messages,
                native_messages,
                state,
                context,
            )
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]
        return list(native_messages)

    def from_native_messages(  # type: ignore[override]
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any] | None = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("from_native_messages", ProviderExtensionPlugin)
        if fn is not None:
            out = self._call_message_conversion_hook(
                fn,
                native_messages,
                messages,
                state,
                context,
            )
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]
        return list(messages)

    def initialize_request(  # type: ignore[override]
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        fn = getattr(self.impl, "initialize_request", None)
        if callable(fn):
            out = self._call_with_optional_kwargs(
                fn,
                native_messages,
                state,
                context=context,
            )
            if isinstance(out, tuple) and len(out) == 2:
                raw_native, raw_state = out
                new_state = raw_state if isinstance(raw_state, dict) else state
                if isinstance(raw_native, list):
                    if all(isinstance(m, dict) for m in raw_native):
                        return raw_native, new_state
                    return native_messages, new_state
                return native_messages, new_state
            if isinstance(out, dict):
                return native_messages, out
        return native_messages, state

    def get_tool_interop_contribution(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> ToolInteropContribution:
        fn = self._get_impl_method(
            "get_tool_interop_contribution", ProviderExtensionPlugin
        )
        if fn is None:
            return ToolInteropContribution()
        out = self._call_with_optional_kwargs(fn, config, state)
        return (
            out
            if isinstance(out, ToolInteropContribution)
            else ToolInteropContribution()
        )

    def accepted_tool_schema_formats(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> List[str]:
        fn = self._get_impl_method(
            "accepted_tool_schema_formats", ProviderExtensionPlugin
        )
        if fn is None:
            return []
        out = self._call_with_optional_kwargs(fn, config, state)
        items = self._safe_list(out)
        return [item for item in items if isinstance(item, str) and item]

    def emitted_tool_call_formats(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        state: Dict[str, Any] | None = None,
    ) -> List[str]:
        fn = self._get_impl_method("emitted_tool_call_formats", ProviderExtensionPlugin)
        if fn is None:
            return []
        out = self._call_with_optional_kwargs(fn, config, state)
        items = self._safe_list(out)
        return [item for item in items if isinstance(item, str) and item]

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
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        fn = getattr(self.impl, "finalize", None)
        if callable(fn):
            return cast(
                Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]],
                self._call_with_optional_kwargs(
                    fn,
                    final_messages,
                    native_messages,
                    state,
                    context=context,
                ),
            )
        return final_messages, native_messages, state

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        fn = self._get_impl_method("get_actions", ProviderExtensionPlugin)
        if fn is not None:
            out = fn(state)
            items = self._safe_list(out)
            return [item for item in items if isinstance(item, dict)]
        return []

    def execute_action(  # type: ignore[override]
        self,
        action_id: str,
        session: Session,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        fn = self._get_impl_method("execute_action", ProviderExtensionPlugin)
        if fn is not None:
            out = self._call_with_optional_context(
                fn,
                (action_id, session, native_messages, params),
                context,
                (state,),
            )
            return (
                out
                if isinstance(out, dict)
                else {"native_messages": list(native_messages)}
            )
        return {"native_messages": list(native_messages)}


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
            return self._ensure_state_config(
                config, new_state if isinstance(new_state, dict) else state
            )
        return self._ensure_state_config(config, state)

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

    def forbidden_tags(self) -> List[str]:  # type: ignore[override]
        fn = getattr(self.impl, "forbidden_tags", None)
        raw = fn() if callable(fn) else []
        items = self._safe_list(raw)
        return [str(t) for t in items]

    def is_enabled(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Optional[bool]:
        fn = getattr(self.impl, "is_enabled", None)
        if callable(fn):
            return fn(config, tags, models, context)
        return None

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
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any] | None = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("to_native_messages", FeaturePlugin)
        if fn is not None:
            out = self._call_message_conversion_hook(
                fn,
                messages,
                native_messages,
                state,
                context,
            )
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]
        return list(native_messages)

    def from_native_messages(  # type: ignore[override]
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any] | None = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        fn = self._get_impl_method("from_native_messages", FeaturePlugin)
        if fn is not None:
            out = self._call_message_conversion_hook(
                fn,
                native_messages,
                messages,
                state,
                context,
            )
            items = self._safe_list(out)
            return [m for m in items if isinstance(m, dict)]
        return list(messages)

    def initialize_request(  # type: ignore[override]
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        fn = getattr(self.impl, "initialize_request", None)
        if callable(fn):
            out = self._call_with_optional_kwargs(
                fn,
                native_messages,
                state,
                context=context,
            )
            if isinstance(out, tuple) and len(out) == 2:
                raw_native, raw_state = out
                new_state = raw_state if isinstance(raw_state, dict) else state
                if isinstance(raw_native, list):
                    if all(isinstance(m, dict) for m in raw_native):
                        return raw_native, new_state
                    return native_messages, new_state
                return native_messages, new_state
            if isinstance(out, dict):
                return native_messages, out
        return native_messages, state

    def prepare_tools(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        tools: List[ToolDescriptor],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ToolDescriptor]:
        fn = self._get_impl_method("prepare_tools", FeaturePlugin)
        if fn is not None:
            try:
                sig = inspect.signature(fn)
            except (TypeError, ValueError):
                out = fn(config, tools, context)
            else:
                params = list(sig.parameters.values())
                positional = [
                    p
                    for p in params
                    if p.kind
                    in (
                        inspect.Parameter.POSITIONAL_ONLY,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    )
                ]
                if positional and positional[0].name == "tools":
                    out = self._call_with_optional_kwargs(
                        fn,
                        tools,
                        context=context,
                    )
                else:
                    out = self._call_with_optional_kwargs(
                        fn,
                        config,
                        tools,
                        context=context,
                    )
            items = self._safe_list(out)
            return [item for item in items if isinstance(item, ToolDescriptor)]
        return list(tools)

    def finalize(  # type: ignore[override]
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        fn = getattr(self.impl, "finalize", None)
        if callable(fn):
            return cast(
                Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]],
                self._call_with_optional_kwargs(
                    fn,
                    final_messages,
                    native_messages,
                    state,
                    context=context,
                ),
            )
        return final_messages, native_messages, state

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        fn = self._get_impl_method("get_actions", FeaturePlugin)
        if fn is not None:
            out = fn(state)
            items = self._safe_list(out)
            return [item for item in items if isinstance(item, dict)]
        return []

    def execute_action(  # type: ignore[override]
        self,
        action_id: str,
        session: Session,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        fn = self._get_impl_method("execute_action", FeaturePlugin)
        if fn is not None:
            out = self._call_with_optional_context(
                fn,
                (action_id, session, native_messages, params),
                context,
                (state,),
            )
            return (
                out
                if isinstance(out, dict)
                else {"native_messages": list(native_messages)}
            )
        return {"native_messages": list(native_messages)}

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

    def forbidden_tags(self) -> List[str]:  # type: ignore[override]
        fn = getattr(self.impl, "forbidden_tags", None)
        raw = fn() if callable(fn) else []
        items = self._safe_list(raw)
        return [str(t) for t in items]

    def is_enabled(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Optional[bool]:
        fn = getattr(self.impl, "is_enabled", None)
        if callable(fn):
            return fn(config, tags, models, context)
        return None

    def prepare(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        fn = self._get_impl_method("prepare", ToolPlugin)
        if fn is None:
            return {}
        out = self._call_with_optional_kwargs(fn, config, state, context=context)
        return out if isinstance(out, dict) else {}

    async def prepare_async(  # type: ignore[override]
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        fn = getattr(self.impl, "prepare_async", None)
        if callable(fn):
            out = self._call_with_optional_kwargs(fn, config, state, context=context)
            if inspect.isawaitable(out):
                out = await out
            return out if isinstance(out, dict) else {}
        return self.prepare(config, state, context=context)

    def get_tool_schemas(  # type: ignore[override]
        self,
        state: Dict[str, Any],
        *,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        fn = getattr(self.impl, "get_tool_schemas", None)
        if callable(fn):
            out = self._call_with_optional_kwargs(fn, state, prepared=prepared)
            items = self._safe_list(out)
            return [s for s in items if isinstance(s, dict)]
        return []

    def get_tool_interop_contribution(  # type: ignore[override]
        self,
        state: Dict[str, Any],
    ) -> ToolInteropContribution:
        fn = self._get_impl_method("get_tool_interop_contribution", ToolPlugin)
        if fn is None:
            return ToolInteropContribution()
        out = fn(state)
        return (
            out
            if isinstance(out, ToolInteropContribution)
            else ToolInteropContribution()
        )

    def can_handle_tool_call(  # type: ignore[override]
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        tool_schema: Optional[Dict[str, Any]] = None,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Optional[bool]:
        fn = self._get_impl_method("can_handle_tool_call", ToolPlugin)
        if fn is None:
            return None
        out = self._call_with_optional_kwargs(
            fn,
            tool_name,
            payload,
            state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            tool_schema=tool_schema,
            prepared=prepared,
        )
        return out if isinstance(out, bool) else None

    def execute_tool(  # type: ignore[override]
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any | None = None,
        context: Optional[Dict[str, Any]] = None,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        fn = self._get_impl_method("execute_tool", ToolPlugin)
        if callable(fn):
            out = self._call_with_optional_kwargs(
                fn,
                tool_name,
                payload,
                state,
                payload_kind=payload_kind,
                payload_format=payload_format,
                payload_metadata=payload_metadata,
                tool_call=tool_call,
                cancellation=cancellation,
                context=context,
                prepared=prepared,
            )
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
    ) -> Any:
        fn = getattr(self.impl, "format_tool_result", None)
        if callable(fn):
            out = fn(result, state)
            return out if is_provider_native_tool_result(out) else str(out)
        if result.get("success"):
            return f"Result: {result.get('result')}"
        return f"Error: {result.get('error')}"

    def format_tool_call_preview(  # type: ignore[override]
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> str:
        fn = getattr(self.impl, "format_tool_call_preview", None)
        if callable(fn):
            out = self._call_with_optional_kwargs(
                fn,
                tool_name,
                payload,
                state,
                payload_kind=payload_kind,
                payload_format=payload_format,
                payload_metadata=payload_metadata,
                tool_call=tool_call,
                prepared=prepared,
            )
            return str(out) if out else ""
        return ""

    def stream_tool(  # type: ignore[override]
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any | None = None,
        context: Optional[Dict[str, Any]] = None,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Default streaming hook.

        When the underlying implementation provides ``stream_tool``, delegate to
        it and forward any dictionary chunks. Otherwise, wrap ``execute_tool``
        so that non-streaming tools yield a single RESULT dict (no partials).
        """
        fn = self._get_impl_method("stream_tool", ToolPlugin)
        if fn is None:
            # No partials; yield only the final result dict.
            result = self.execute_tool(
                tool_name,
                payload,
                state,
                payload_kind=payload_kind,
                payload_format=payload_format,
                payload_metadata=payload_metadata,
                tool_call=tool_call,
                cancellation=cancellation,
                context=context,
                prepared=prepared,
            )
            if isinstance(result, dict):
                yield result
            return
        out = self._call_with_optional_kwargs(
            fn,
            tool_name,
            payload,
            state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            cancellation=cancellation,
            context=context,
            prepared=prepared,
        )
        try:
            iterator = iter(out)
        except TypeError:
            return
        for chunk in iterator:
            if isinstance(chunk, dict):
                yield chunk

    async def execute_tool_async(  # type: ignore[override]
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any | None = None,
        context: Optional[Dict[str, Any]] = None,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        fn = self._get_impl_method("execute_tool_async", ToolPlugin)
        if callable(fn):
            out = self._call_with_optional_kwargs(
                fn,
                tool_name,
                payload,
                state,
                payload_kind=payload_kind,
                payload_format=payload_format,
                payload_metadata=payload_metadata,
                tool_call=tool_call,
                cancellation=cancellation,
                context=context,
                prepared=prepared,
            )
            if inspect.isawaitable(out):
                out = await out
            return (
                out
                if isinstance(out, dict)
                else {
                    "success": False,
                    "error": "invalid tool result",
                }
            )

        fn = getattr(self.impl, "execute_tool", None)
        if callable(fn):
            out = self._call_with_optional_kwargs(
                fn,
                tool_name,
                payload,
                state,
                payload_kind=payload_kind,
                payload_format=payload_format,
                payload_metadata=payload_metadata,
                tool_call=tool_call,
                cancellation=cancellation,
                context=context,
                prepared=prepared,
            )
            if inspect.isawaitable(out):
                out = await out
            return (
                out
                if isinstance(out, dict)
                else {
                    "success": False,
                    "error": "invalid tool result",
                }
            )

        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    async def stream_tool_async(  # type: ignore[override]
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any | None = None,
        context: Optional[Dict[str, Any]] = None,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        fn = self._get_impl_method("stream_tool_async", ToolPlugin)
        if callable(fn):
            out = self._call_with_optional_kwargs(
                fn,
                tool_name,
                payload,
                state,
                payload_kind=payload_kind,
                payload_format=payload_format,
                payload_metadata=payload_metadata,
                tool_call=tool_call,
                cancellation=cancellation,
                context=context,
                prepared=prepared,
            )
            if inspect.isawaitable(out):
                out = await out
            if hasattr(out, "__aiter__"):
                async for chunk in cast(AsyncIterator[Any], out):
                    if isinstance(chunk, dict):
                        yield chunk
                return
            try:
                iterator = iter(out)
            except TypeError:
                return
            for chunk in iterator:
                if isinstance(chunk, dict):
                    yield chunk
            return

        fn = self._get_impl_method("stream_tool", ToolPlugin)
        if callable(fn):
            for chunk in self.stream_tool(
                tool_name,
                payload,
                state,
                payload_kind=payload_kind,
                payload_format=payload_format,
                payload_metadata=payload_metadata,
                tool_call=tool_call,
                cancellation=cancellation,
                context=context,
                prepared=prepared,
            ):
                yield chunk
            return

        result = await self.execute_tool_async(
            tool_name,
            payload,
            state,
            payload_kind=payload_kind,
            payload_format=payload_format,
            payload_metadata=payload_metadata,
            tool_call=tool_call,
            cancellation=cancellation,
            context=context,
            prepared=prepared,
        )
        if isinstance(result, dict):
            yield result

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
