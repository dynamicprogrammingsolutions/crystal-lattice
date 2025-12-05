"""
Core SDK for the AI Agent Platform.

Functional architecture: AgentCore stores only the processing pipeline (plugins via wrappers),
all transformations are pure functions that take session/config and return new objects.

Examples:
    Basic non-streaming usage:

    ```python
    from agent_core import AgentCore
    from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider

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
            print(chunk["message"]["content"], end="", flush=True)
        elif chunk["type"] == "final":
            session = chunk["session"]
            print("\n[Done]")
    ```

    Tool schemas and execution:

    ```python
    tool_schemas = core.get_tool_schemas(config)
    # Execute tool calls the model asked for (application loop)
    tool_results = core.execute_tool_calls(tool_calls, config)
    for msg in tool_results:
        session = core.add_message(session, msg["role"], msg["content"], msg.get("metadata"))
    ```
"""

from typing import Any, Dict, List, Optional, Iterator, AsyncIterator, Tuple, Set
from .types import Message, Session, MessageRole
from .plugin import (
    ProviderWrapper,
    ExtensionWrapper,
    FeatureWrapper,
    ToolWrapper,
)
from .utils import pipeline, get_logger
import uuid
import json

logger = None
log_chunk_processing = None

class AgentCore:
    """Stateless processing pipeline for AI Agent Platform.

    Stores registered plugin wrappers (processing logic), not runtime state.
    All methods are pure functions that take session/config as parameters.
    The application layer manages sessions and configuration.
    """

    # -------- Integrity helpers --------
    def _compute_native_integrity(self, messages: List[Message]) -> Dict[str, Any]:
        """Compute verification data for native history integrity.

        Args:
            messages: Core messages in the session.

        Returns:
            Dict containing a simple integrity checksum of the current session messages
            used to guard retained provider-native history. Keys:
            - message_count: Number of messages in the session
            - total_chars: Sum of content lengths for all messages (non-strings count as 0)
        """
        total_chars = 0
        for m in messages:
            try:
                total_chars += len(m.content or "")
            except Exception:
                # Defensive: treat non-string content as 0 for integrity length
                total_chars += 0
        return {"message_count": len(messages), "total_chars": total_chars}

    def _verify_native_integrity(self, session: Session) -> None:
        """Verify that session messages match integrity data when native history is present.

        This ensures the retained provider-native history still corresponds to the
        immutable core message sequence.

        Args:
            session: Current session with potential retained native history in metadata.

        Raises:
            RuntimeError: If integrity is missing or does not match the current messages.
                Users may remove 'native_messages' from metadata to intentionally change
                history or bypass integrity check.
        """
        md = session.metadata if isinstance(session.metadata, dict) else {}
        if "native_messages" not in md:
            return
        integ = md.get("native_messages_integrity")
        if not isinstance(integ, dict):
            raise RuntimeError(
                "Integrity data missing for native_messages; remove 'native_messages' from session.metadata to modify history."
            )
        expected_count = integ.get("message_count")
        expected_chars = integ.get("total_chars")
        actual = self._compute_native_integrity(session.messages)
        if (
            actual.get("message_count") != expected_count
            or actual.get("total_chars") != expected_chars
        ):
            raise RuntimeError(
                "Session messages changed without updating native history; remove 'native_messages' from session.metadata to modify history."
            )

    def _normalize_final_core_with_native_indices(
        self,
        final_core: list[dict[str, Any]],
        finals_native: list[dict[str, Any]],
        baseline_offset: int,
    ) -> list[dict[str, Any]]:
        if not final_core or not finals_native:
            # Nothing to normalize; return shallow copies to avoid mutation.
            return [dict(m) for m in final_core]

        local_count = len(finals_native)

        def _normalize_message(
            msg: dict[str, Any],
            default_local_indices: list[int] | None = None,
        ) -> dict[str, Any]:
            raw_md = msg.get("metadata") or {}
            md = dict(raw_md) if isinstance(raw_md, dict) else {}
            native_indices = md.get("native_indices")

            if isinstance(native_indices, list) and all(isinstance(i, int) for i in native_indices):
                local_indices = [i for i in native_indices if 0 <= i < local_count]
            elif default_local_indices is not None:
                local_indices = [i for i in default_local_indices if 0 <= i < local_count]
            else:
                raise RuntimeError(
                    "from_native_messages changed message count without providing native_indices mapping"
                )

            global_indices = [baseline_offset + i for i in local_indices]
            if global_indices:
                md["native_indices"] = global_indices
            else:
                md.pop("native_indices", None)
            return {**msg, "metadata": md}

        if len(final_core) == local_count:
            return [
                _normalize_message(msg, default_local_indices=[idx])
                for idx, msg in enumerate(final_core)
            ]

        normalized: list[dict[str, Any]] = []
        for msg in final_core:
            normalized.append(_normalize_message(msg, default_local_indices=None))
        return normalized

    def _append_single_message_with_native(
        self,
        session,
        message_dict,
        config,
    ):
        base_metadata = dict(session.metadata)

        role_value = message_dict.get("role", "user")
        role = role_value
        content = message_dict.get("content", "")
        raw_md = message_dict.get("metadata") or {}
        md = dict(raw_md) if isinstance(raw_md, dict) else {}

        from agent_core.types import Message  # local import to avoid cycles

        def _core_only_session(clean_metadata):
            cleaned = dict(clean_metadata)
            cleaned.pop("native_indices", None)
            new_message = Message(role=role, content=content, metadata=cleaned)
            new_messages = [*session.messages, new_message]
            new_session_metadata = dict(base_metadata)
            new_session_metadata.pop("native_messages", None)
            new_session_metadata.pop("native_messages_integrity", None)
            return type(session)(
                session_id=session.session_id,
                messages=new_messages,
                metadata=new_session_metadata,
            )

        retained_native = None
        if isinstance(session.metadata, dict):
            rn = session.metadata.get("native_messages")
            if isinstance(rn, list):
                retained_native = rn

        if retained_native is None:
            return _core_only_session(md), None

        self._verify_native_integrity(session)

        try:
            core_suffix = [
                {
                    "role": role,
                    "content": content,
                    "metadata": md,
                }
            ]
            suffix_native = self._core_messages_to_native_for_config(core_suffix, config)
        except Exception:
            return _core_only_session(md), None


        base_len = len(retained_native)
        global_indices = list(range(base_len, base_len + len(suffix_native)))

        new_md = dict(md)
        if global_indices:
            new_md["native_indices"] = global_indices
        else:
            new_md.pop("native_indices", None)

        new_message = Message(role=role, content=content, metadata=new_md)
        new_messages = [*session.messages, new_message]
        new_native_messages = [*retained_native, *suffix_native]
        new_session_metadata = {
            **base_metadata,
            "native_messages": new_native_messages,
            "native_messages_integrity": self._compute_native_integrity(new_messages),
        }

        return (
            type(session)(
                session_id=session.session_id,
                messages=new_messages,
                metadata=new_session_metadata,
            ),
            global_indices,
        )
    def __init__(self):

        """Initialize core with empty plugin pipeline.

        Loggers are initialized lazily so that structlog configuration can
        be customized by applications before any loggers are created.
        """
        global logger, log_chunk_processing
        logger = get_logger("core")
        log_chunk_processing = get_logger("chunk_processing")

        self._providers: List[ProviderWrapper] = []
        self._features: List[FeatureWrapper] = []
        self._tools: List[ToolWrapper] = []
        # Caches for model discovery and tag-based dependency resolution.
        # Keys use provider wrapper id for uniqueness, independent of
        # human-readable provider names.
        self._models_cache: Dict[Tuple[int, str], List[Dict[str, Any]]] = {}
        self._dependency_cache: Dict[
            Tuple[int, str, str],
            Tuple[List[str], List[str], List[str], List[str]],
        ] = {}
        self._tags_cache: Dict[Tuple[int, Tuple[int, str, str]], List[str]] = {}

    def _reset_caches(self) -> None:
        """Reset internal caches for models, dependencies, and tags."""
        self._models_cache = {}
        self._dependency_cache = {}
        self._tags_cache = {}

    def register_provider(
        self, plugin_class: type, extensions: Optional[List[type]] = None
    ) -> None:
        """Register provider plugin class with optional provider extensions.

        Extensions are loaded by the provider wrapper (same language, hot path).

        Args:
            plugin_class: Provider plugin class.
            extensions: Optional list of provider extension classes to register with the provider.
        """
        wrapper = ProviderWrapper(plugin_class, extensions or [])
        self._providers = [*self._providers, wrapper]
        self._reset_caches()

    def register_feature(self, plugin_class: type) -> None:
        """Register a feature plugin class.

        Args:
            plugin_class: Feature plugin class.
        """
        wrapper = FeatureWrapper(plugin_class)
        self._features.append(wrapper)
        self._reset_caches()

    def register_tool(self, plugin_class: type) -> None:
        """Register a tool plugin class.

        Args:
            plugin_class: Tool plugin class.
        """
        wrapper = ToolWrapper(plugin_class)
        self._tools.append(wrapper)
        self._reset_caches()

    def create_session(self, session_id: Optional[str] = None) -> Session:
        """Create a new empty session.

        Args:
            session_id: Optional session identifier. Auto-generated if omitted.

        Returns:
            New immutable Session instance with no messages.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        return Session(session_id=session_id, messages=[])

    def add_message(
         self,
         session: Session,
         role: MessageRole,
         content: str,
         metadata: Optional[Dict[str, Any]] = None,
         config: Optional[Dict[str, Any]] = None,
     ) -> Session:
         """Add a message to the session (pure function).
 
         When session.metadata contains provider-native history (native_messages)
         and a provider is registered, converts the newly added message to
         provider-native format and appends it to the stored native history.
         Updates verification data for integrity checks.
 
         When ``config`` is provided, native history is updated using the same
         provider/feature pipeline as regular requests. When ``config`` is
         omitted, legacy best-effort behavior is preserved.
 
         Args:
             session: Current session.
             role: Message role ("system", "user", "assistant", or "tool").
             content: Message content.
             metadata: Optional per-message metadata.
             config: Optional configuration used to resolve provider and plugins.
 
         Returns:
             New Session with the message appended (immutable update).
         """
         if config is not None:
             # Config-aware path: delegate to helper that preserves native history
             msg_md = dict(metadata) if isinstance(metadata, dict) else {}
             message_dict: Dict[str, Any] = {
                 "role": role,
                 "content": content,
                 "metadata": msg_md,
             }
             new_session, _ = self._append_single_message_with_native(
                 session,
                 message_dict,
                 config,
             )
             return new_session
 
         # Legacy behavior when no config is provided.
         message = Message(role=role, content=content, metadata=metadata)
         new_messages: List[Message] = [*session.messages, message]
 
         # Default metadata passthrough
         new_metadata: Dict[str, Any] = dict(session.metadata)
 
         # If native history exists, verify integrity before modification
         if isinstance(session.metadata, dict) and "native_messages" in session.metadata:
             self._verify_native_integrity(session)
 
         # Attempt to append native for the new message if a single provider is
         # available and native history exists. When multiple providers are
         # registered, this method does not attempt to infer which provider was
         # used; native history is left unchanged.
         if self._providers and isinstance(session.metadata, dict):
             retained_native = session.metadata.get("native_messages")
             if isinstance(retained_native, list) and len(self._providers) == 1:
                 provider = self._providers[0]
                 # Initialize minimal state for stateless transforms
                 state = provider.init({})
                 for feature in self._features:
                     state = feature.init({}, state)
                     provider.set_state(state)
                 # Build core dict for the single new message only
                 core_new_msg = [message.to_dict()]
                 # Convert single message to provider-native and apply stateless
                 # transforms (single-message context)
                 suffix_native = provider.to_native_messages(core_new_msg, state)
                 suffix_native = provider.apply_extension_transforms(core_new_msg, suffix_native)
                 pipe = pipeline(core_new_msg)
                 suffix_native = pipe(
                     [feature.to_native_messages for feature in self._features],
                     suffix_native,
                 )
                 new_metadata["native_messages"] = [*retained_native, *suffix_native]
 
         # Always update integrity data when we have native history
         if "native_messages" in new_metadata:
             new_metadata["native_messages_integrity"] = self._compute_native_integrity(
                 new_messages
             )

         return Session(
             session_id=session.session_id,
             messages=new_messages,
             metadata=new_metadata,
         )

    def _slice_session_core_only(
        self,
        session: Session,
        keep_indices: Set[int],
    ) -> Session:
        """Core-only slice/remove that drops native history and indices."""
        messages = list(session.messages)
        message_count = len(messages)
        all_indices: Set[int] = set(range(message_count))
        valid_keep: Set[int] = {i for i in keep_indices if 0 <= i < message_count}

        if valid_keep == all_indices:
            # No change in indices; preserve session and native history as-is.
            return session

        kept_messages: List[Message] = []
        for idx in sorted(valid_keep):
            msg = messages[idx]
            data = msg.to_dict()
            md = dict(data.get("metadata") or {})
            md.pop("native_indices", None)
            if md:
                kept_messages.append(
                    Message(
                        role=data["role"],
                        content=data["content"],
                        metadata=md,
                    )
                )
            else:
                kept_messages.append(
                    Message(
                        role=data["role"],
                        content=data["content"],
                        metadata=None,
                    )
                )

        new_metadata: Dict[str, Any] = (
            dict(session.metadata) if isinstance(session.metadata, dict) else {}
        )
        new_metadata.pop("native_messages", None)
        new_metadata.pop("native_messages_integrity", None)

        return Session(
            session_id=session.session_id,
            messages=kept_messages,
            metadata=new_metadata,
        )

    def slice_session(
        self,
        session: Session,
        config: Optional[Dict[str, Any]] = None,
        *,
        start: Optional[int] = None,
        end: Optional[int] = None,
        remove_indices: Optional[List[int]] = None,
    ) -> Session:
        """Return a new session with messages sliced/removed.

        Operations are expressed in core message indices but, when possible,
        provider-native history is adjusted consistently and preserved.
        """
        messages = list(session.messages)
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

        if keep_set == all_indices:
            return session

        if config is None:
            return self._slice_session_core_only(session, keep_set)

        if not isinstance(session.metadata, dict):
            return self._slice_session_core_only(session, keep_set)

        if len(self._providers) != 1:
            return self._slice_session_core_only(session, keep_set)

        original_native = session.metadata.get("native_messages")
        if not isinstance(original_native, list):
            return self._slice_session_core_only(session, keep_set)

        try:
            self._verify_native_integrity(session)
        except Exception:
            return self._slice_session_core_only(session, keep_set)

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
                return self._slice_session_core_only(session, keep_set)
            normalized_indices: List[int] = []
            for j in native_indices:
                if j < 0 or j >= native_len:
                    return self._slice_session_core_only(session, keep_set)
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
                return self._slice_session_core_only(session, keep_set)

        native_candidates: Set[int] = set()
        for idx in keep_set:
            for j in core_to_native.get(idx, []):
                native_candidates.add(j)

        if not native_candidates:
            new_native: List[Dict[str, Any]] = []
        else:
            final_native_indices = {
                j
                for j in native_candidates
                if native_to_core.get(j, set()).issubset(keep_set)
            }
            sorted_indices = sorted(final_native_indices)
            new_native = [original_native[j] for j in sorted_indices]

        try:
            new_messages = self._rebuild_core_from_native(new_native, config)
        except Exception:
            return self._slice_session_core_only(session, keep_set)

        new_metadata = dict(session.metadata)
        new_metadata["native_messages"] = new_native
        new_metadata["native_messages_integrity"] = self._compute_native_integrity(
            new_messages
        )

        return Session(
            session_id=session.session_id,
            messages=new_messages,
            metadata=new_metadata,
        )

    def fork_session(
        self,
        session: Session,
        config: Optional[Dict[str, Any]] = None,
        *,
        upto_index: int,
        new_session_id: Optional[str] = None,
    ) -> Session:
        """Convenience helper to fork a session up to upto_index."""
        sliced = self.slice_session(
            session,
            config,
            start=0,
            end=upto_index + 1,
        )
        if new_session_id is None or new_session_id == sliced.session_id:
            return sliced
        return Session(
            session_id=new_session_id,
            messages=list(sliced.messages),
            metadata=dict(sliced.metadata),
        )

    def _normalize_config(self, config: Dict[str, Any]) -> str:
        """Normalize config for use in cache keys.

        Uses a stable JSON representation when possible, falling back to a
        best-effort repr when values are not JSON-serializable.
        """
        try:
            return json.dumps(
                config,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except TypeError:
            try:
                return repr(sorted(config.items()))
            except Exception:
                return repr(config)

    def _normalize_models(self, models: List[Dict[str, Any]]) -> str:
        """Normalize model descriptors for use in cache keys."""
        try:
            return json.dumps(
                models,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except TypeError:
            return repr(models)

    def _provider_identities(self, provider: ProviderWrapper) -> List[str]:
        """Return identifier strings that can refer to this provider.

        Includes the provider's configured name and fully-qualified variants
        derived from the plugin class. This helper centralizes naming so it
        is easy to extend with additional variants in the future.
        """
        names: List[str] = []

        plugin_class = getattr(provider, "plugin_class", None)

        raw_names: List[Any] = [getattr(provider, "name", None)]
        if plugin_class is not None:
            raw_names.extend(
                [
                    getattr(plugin_class, "name", None),
                    getattr(plugin_class, "__name__", None),
                    getattr(plugin_class, "__qualname__", None),
                ]
            )

        for value in raw_names:
            if isinstance(value, str) and value:
                names.append(value)

        module = getattr(plugin_class, "__module__", None) if plugin_class is not None else None
        if isinstance(module, str) and module:
            class_names: List[str] = []
            if plugin_class is not None:
                qual = getattr(plugin_class, "__qualname__", "") or ""
                if qual:
                    class_names.append(qual)
                cls_name = getattr(plugin_class, "__name__", "") or ""
                if cls_name and cls_name not in class_names:
                    class_names.append(cls_name)
                cfg_name = getattr(plugin_class, "name", None)
                if isinstance(cfg_name, str) and cfg_name and cfg_name not in class_names:
                    class_names.append(cfg_name)
            for cls_name in class_names:
                names.append(f"{module}.{cls_name}")

        # De-duplicate while preserving order.
        seen: Set[str] = set()
        unique: List[str] = []
        for n in names:
            if n not in seen:
                seen.add(n)
                unique.append(n)
        return unique

    def _select_provider_for_config(self, config: Dict[str, Any]) -> ProviderWrapper:
        """Select a provider for the given config.

        When multiple providers are registered, the "provider" key in config
        is mandatory and may use either a short name or a fully-qualified name
        such as "plugins.openai_provider.OpenAICompatibleProvider".
        """
        if not self._providers:
            raise RuntimeError("No provider registered")

        # Fast path: single provider and no explicit selector.
        if len(self._providers) == 1 and "provider" not in config:
            return self._providers[0]

        provider_value = config.get("provider")

        # Build mapping from identifier -> providers sharing it.
        identity_map: Dict[str, List[ProviderWrapper]] = {}
        for prov in self._providers:
            for ident in self._provider_identities(prov):
                identity_map.setdefault(ident, []).append(prov)

        def _format_available() -> str:
            items: List[str] = []
            for prov in self._providers:
                idents = self._provider_identities(prov)
                if not idents:
                    continue
                primary = idents[0]
                extras = [i for i in idents[1:] if i != primary]
                if extras:
                    items.append(f"{primary} (also: {', '.join(extras)})")
                else:
                    items.append(primary)
            return ", ".join(items)

        if not isinstance(provider_value, str) or not provider_value.strip():
            msg = (
                "Configuration must include a non-empty 'provider' string when multiple providers are registered. "  # noqa: E501
                "Known providers (you may use either a short name or a fully-qualified name like 'package.module.ProviderClass'): "  # noqa: E501
                f"{_format_available()}"
            )
            raise ValueError(msg)

        provider_key = provider_value.strip()
        matches = identity_map.get(provider_key, [])

        if not matches:
            msg = (
                f"Unknown provider '{provider_key}' in configuration. "  # noqa: E501
                "Known providers (you may use either a short name or a fully-qualified name like 'package.module.ProviderClass') are: "  # noqa: E501
                f"{_format_available()}"
            )
            raise ValueError(msg)

        if len(matches) > 1:
            # Ambiguous identifier; recommend fully-qualified names.
            suggestions: List[str] = []
            for prov in matches:
                idents = self._provider_identities(prov)
                fq = next((i for i in idents if "." in i), idents[0] if idents else "")
                if fq:
                    suggestions.append(fq)
            suggestions_str = ", ".join(sorted(set(suggestions)))
            msg = (
                f"Ambiguous provider name '{provider_key}' in configuration; it matches multiple registered providers. "  # noqa: E501
                "Please choose a more specific name, for example one of: "  # noqa: E501
                f"{suggestions_str}"
            )
            raise ValueError(msg)

        return matches[0]

    # Model and tag result normalization is handled by plugin adapters.

    def _get_models_for_config(
        self,
        provider: ProviderWrapper,
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Return cached or freshly-computed model descriptors for this provider+config."""
        provider_id = id(provider)
        norm_config = self._normalize_config(config)
        cache_key = (provider_id, norm_config)
        cached = self._models_cache.get(cache_key)
        if cached is not None:
            # Return shallow copies to avoid accidental mutation of cached structures
            return [dict(m) for m in cached]

        # Start with provider-declared models and let extensions and features
        # participate in model discovery. Adapters normalize shapes so that
        # `get_models` always returns a list of dicts.
        models: List[Dict[str, Any]] = provider.get_models(config)
        for ext in provider.extensions:
            models = ext.get_models(config, models)
        for feature in self._features:
            models = feature.get_models(config, models)

        # Validate and normalize
        validated: List[Dict[str, Any]] = []
        for model in models:
            if not isinstance(model, Dict):
                continue
            model_id = model.get("id")
            if not isinstance(model_id, str) or not model_id:
                continue
            validated.append(dict(model))

        self._models_cache = {**self._models_cache, cache_key: validated}
        return [dict(m) for m in validated]

    def _resolve_plugins_for_config(
        self,
        config: Dict[str, Any],
    ) -> Tuple[
        ProviderWrapper,
        List[ExtensionWrapper],
        List[FeatureWrapper],
        List[ToolWrapper],
        List[str],
    ]:
        """Resolve enabled plugins and tags for a given config.

        Uses tag-based dependencies declared by non-provider plugins and
        cached per (provider, config, models) triple.
        """
        provider = self._select_provider_for_config(config)
        models = self._get_models_for_config(provider, config)
        provider_id = id(provider)
        norm_config = self._normalize_config(config)
        norm_models = self._normalize_models(models)
        dep_key = (provider_id, norm_config, norm_models)

        cached = self._dependency_cache.get(dep_key)
        if cached is not None:
            ext_names, feature_names, tool_names, tags = cached
            enabled_extensions = [ext for ext in provider.extensions if ext.name in ext_names]
            enabled_features = [feat for feat in self._features if feat.name in feature_names]
            enabled_tools = [tool for tool in self._tools if tool.name in tool_names]
            return provider, enabled_extensions, enabled_features, enabled_tools, list(tags)

        # Build initial candidates
        candidate_extensions: List[ExtensionWrapper] = list(provider.extensions)
        candidate_features: List[FeatureWrapper] = list(self._features)
        candidate_tools: List[ToolWrapper] = list(self._tools)

        enabled_extensions = list(candidate_extensions)
        enabled_features = list(candidate_features)
        enabled_tools = list(candidate_tools)

        available_tags: Set[str] = set()
        while True:
            available_tags = set()

            # Provider tags
            provider_tag_key = (provider_id, dep_key)
            provider_tags = self._tags_cache.get(provider_tag_key)
            if provider_tags is None:
                try:
                    provider_tags = provider.get_tags(config, models)
                except Exception:
                    provider_tags = []
                self._tags_cache = {
                    **self._tags_cache,
                    provider_tag_key: provider_tags,
                }
            available_tags.update(provider_tags)

            # Extension tags
            for ext in enabled_extensions:
                key = (id(ext), dep_key)
                tags = self._tags_cache.get(key)
                if tags is None:
                    try:
                        tags = ext.get_tags(config, models)
                    except Exception:
                        tags = []
                    self._tags_cache = {**self._tags_cache, key: tags}
                available_tags.update(tags)

            # Feature tags
            for feat in enabled_features:
                key = (id(feat), dep_key)
                tags = self._tags_cache.get(key)
                if tags is None:
                    try:
                        tags = feat.get_tags(config, models)
                    except Exception:
                        tags = []
                    self._tags_cache = {**self._tags_cache, key: tags}
                available_tags.update(tags)

            # Tool tags
            for tool in enabled_tools:
                key = (id(tool), dep_key)
                tags = self._tags_cache.get(key)
                if tags is None:
                    try:
                        tags = tool.get_tags(config, models)
                    except Exception:
                        tags = []
                    self._tags_cache = {**self._tags_cache, key: tags}
                available_tags.update(tags)

            # Filter by required_tags
            next_enabled_extensions = [
                ext
                for ext in enabled_extensions
                if set(ext.required_tags()).issubset(available_tags)
            ]
            next_enabled_features = [
                feat
                for feat in enabled_features
                if set(feat.required_tags()).issubset(available_tags)
            ]
            next_enabled_tools = [
                tool for tool in enabled_tools if set(tool.required_tags()).issubset(available_tags)
            ]

            cur_ext_names = [ext.name for ext in enabled_extensions]
            cur_feat_names = [feat.name for feat in enabled_features]
            cur_tool_names = [tool.name for tool in enabled_tools]
            next_ext_names = [ext.name for ext in next_enabled_extensions]
            next_feat_names = [feat.name for feat in next_enabled_features]
            next_tool_names = [tool.name for tool in next_enabled_tools]

            if (
                cur_ext_names == next_ext_names
                and cur_feat_names == next_feat_names
                and cur_tool_names == next_tool_names
            ):
                break

            enabled_extensions = next_enabled_extensions
            enabled_features = next_enabled_features
            enabled_tools = next_enabled_tools

        enabled_extension_names = [ext.name for ext in enabled_extensions]
        enabled_feature_names = [feat.name for feat in enabled_features]
        enabled_tool_names = [tool.name for tool in enabled_tools]
        final_tags = sorted(available_tags)

        self._dependency_cache = {
            **self._dependency_cache,
            dep_key: (
                enabled_extension_names,
                enabled_feature_names,
                enabled_tool_names,
                final_tags,
            ),
        }

        return provider, enabled_extensions, enabled_features, enabled_tools, final_tags

    def _init_provider_and_features_for_config(
        self,
        provider: ProviderWrapper,
        features: List[FeatureWrapper],
        tools: List[ToolWrapper],
        config: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Initialize provider and features for the given config.

        Builds a provider_config including tool schemas, runs provider.init
        and feature.init, and returns (provider_config, state).
        """
        tool_schemas: List[Dict[str, Any]] = []
        for tool in tools:
            tool_state = tool.init(config)
            tool_schemas.extend(tool.get_tool_schemas(tool_state))
        provider_config = {**config, **({"tools": tool_schemas} if tool_schemas else {})}

        state = provider.init(provider_config)
        for feature in features:
            state = feature.init(provider_config, state)
            provider.set_state(state)
        return provider_config, state

    def _core_messages_to_native_for_config(
        self,
        core_messages: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Convert core messages to provider-native messages for this config."""
        provider, _enabled_extensions, features, tools, _tags = self._resolve_plugins_for_config(
            config
        )
        _provider_config, state = self._init_provider_and_features_for_config(
            provider,
            features,
            tools,
            config,
        )

        native_messages = provider.to_native_messages(core_messages, state)
        native_messages = provider.apply_extension_transforms(core_messages, native_messages)
        pipe = pipeline(core_messages)
        native_messages = pipe(
            [feature.to_native_messages for feature in features],
            native_messages,
        )
        return native_messages

    def _rebuild_core_from_native(
        self,
        native_messages: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> List[Message]:
        """Rebuild full core messages from provider-native history.

        Uses the same provider, extensions, features, and tools that would
        be active for a normal request with this config, but skips
        core-to-native conversion and starts from the given native history.
        """
        (
            provider,
            enabled_extensions,
            features,
            tools,
            _tags,
        ) = self._resolve_plugins_for_config(config)

        _provider_config, state = self._init_provider_and_features_for_config(
            provider,
            features,
            tools,
            config,
        )

        # Initialize request chains using the adjusted native history.
        state = provider.initialize_request(native_messages, state)
        for feature in features:
            state = feature.initialize_request(native_messages, state)
            provider.set_state(state)

        # Convert native messages back into core messages through the full
        # from-native pipeline.
        core_from_provider = provider.from_native_messages(native_messages, state)
        pipe = pipeline(native_messages)
        core_full = pipe(
            [ext.from_native_messages for ext in enabled_extensions]
            + [feature.from_native_messages for feature in features],
            core_from_provider,
        )

        normalized_core = self._normalize_final_core_with_native_indices(
            core_full,
            native_messages,
            baseline_offset=0,
        )
        return [Message.from_dict(m) for m in normalized_core]

 
    def _pre_request(
        self,
        session: Session,
        config: Dict[str, Any],
        provider: ProviderWrapper,
        features: List[FeatureWrapper],
        tools: List[ToolWrapper],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Prepare shared state and inputs for a request.

        Integrity is verified if native history is present. When native
        history exists, it is trusted as the full provider-native history
        for the session. Otherwise, native is reconstructed from core
        messages.

        Args:
            session: Current session.
            config: Application-provided configuration for this request.
            provider: Provider wrapper selected for this request.
            features: Enabled feature wrappers for this request.
            tools: Enabled tool wrappers for this request.

        Returns:
            A tuple of (messages, native_messages, state):
            - messages: Core message dicts for the session.
            - native_messages: Provider-native full history (either retained or reconstructed).
            - state: Shared provider state after init/update/initialize_request for features as well.
        """
        _provider_config, state = self._init_provider_and_features_for_config(
            provider,
            features,
            tools,
            config,
        )
        # Build messages (core shape)
        messages = [msg.to_dict() for msg in session.messages]

        # If native history exists, verify integrity and trust it
        retained_native: Optional[List[Dict[str, Any]]] = None
        if isinstance(session.metadata, dict) and "native_messages" in session.metadata:
            self._verify_native_integrity(session)
            rn = session.metadata.get("native_messages")
            if isinstance(rn, list):
                retained_native = rn

        if retained_native is not None:
            # Reuse retained provider-native history as-is, including any
            # reasoning or reasoning_details fields that were returned by
            # the provider. Extensions such as the OpenRouter reasoning
            # extension are responsible for treating these fields as opaque
            # provider-native metadata and, when streaming, for accumulating
            # them correctly across chunks.
            native_messages = list(retained_native)
        else:
            # Provider-first conversion (native_base for stateless transforms)
            native_messages = provider.to_native_messages(messages, state)
            # Apply stateless transforms: Extensions then Features
            native_messages = provider.apply_extension_transforms(messages, native_messages)
            pipe = pipeline(messages)
            native_messages = pipe(
                [feature.to_native_messages for feature in features],
                native_messages,
            )

        # Initialize request chains
        state = provider.initialize_request(native_messages, state)
        for feature in features:
            state = feature.initialize_request(native_messages, state)
            provider.set_state(state)

        logger.info("request init complete", request=state.get("request"))

        return messages, native_messages, state

    def send_request(
        self, session: Session, config: Dict[str, Any]
    ) -> Tuple[Session, List[Dict[str, Any]]]:
        """Send request and return a new session with the response.

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

        provider, enabled_extensions, features, tools, _tags = self._resolve_plugins_for_config(
            config
        )

        provider.set_active_extensions(enabled_extensions)
        messages, native_messages, state = self._pre_request(
            session,
            config,
            provider,
            features,
            tools,
        )
        baseline_native_len = len(native_messages)

        logger.info(
            "sending request",
            native_messages=native_messages,
            request=state.get("request"),
        )

        _partials, final_native_1, native_messages, state = provider.call_api(
            native_messages, state
        )

        # Provider finalize returns provider-native finals and full native history
        final_native_2, native_messages, state = provider.finalize(native_messages, state)

        # Combine provider-native finals from call_api and provider.finalize
        final_native = final_native_1 + final_native_2

        # Feature finalize chain over provider-native finals (native cold path)
        pipe = pipeline()
        final_native, native_messages, state = pipe(
            [feature.finalize for feature in features], final_native, native_messages, state
        )

        # Convert provider-native finals to core messages once finalization completes
        final_core = provider.from_native_messages(final_native, state)
        # Apply extension and feature from-native transforms
        pipe = pipeline(final_native)
        final_core = pipe(
            [ext.from_native_messages for ext in enabled_extensions]
            + [feature.from_native_messages for feature in features],
            final_core,
        )

        # Attach global native_indices for final core messages
        final_core = self._normalize_final_core_with_native_indices(
            final_core,
            final_native,
            baseline_native_len,
        )

        # Build new session messages by appending new Message objects
        appended: List[Message] = [Message.from_dict(m) for m in final_core]

        new_metadata = dict(session.metadata)
        # Persist full provider-native history for the turn (implementation detail)
        new_metadata["native_messages"] = native_messages
        all_messages_after = [*session.messages, *appended]
        new_metadata["native_messages_integrity"] = self._compute_native_integrity(
            all_messages_after
        )
        new_session = Session(session.session_id, all_messages_after, new_metadata)

        logger.info(
            "send_request_complete",
            final_core=final_core,
        )

        return new_session, final_core


    def send_request_stream(
        self, session: Session, config: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Stream request and yield partial events, then the final session.

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

        provider, enabled_extensions, features, tools, _tags = self._resolve_plugins_for_config(
            config
        )

        provider.set_active_extensions(enabled_extensions)
        messages, native_messages, state = self._pre_request(
            session,
            config,
            provider,
            features,
            tools,
        )
        baseline_native_len = len(native_messages)

        logger.debug(
            "start streaming request",
            native_messages=native_messages,
            requrest=state.get("request", None),
        )

        aggregated_native_finals: List[Dict[str, Any]] = []

        # Stream from provider using optimized streaming
        partial_count = 0
        for event in provider.stream_messages(native_messages, state):
            #logger.debug("streaming event received", _event=event) # the first positional argument is also named 'event', we cannot use that name
            if event["type"] == "partial":
                partial_count += 1
                log_chunk_processing.debug("partial message received", partial=event["message"])
                yield {"type": "partial", "message": event["message"]}
            elif event["type"] == "final_messages":
                # These are provider-native finals
                log_chunk_processing.debug("final message received", final=event["message"])
                aggregated_native_finals.extend(event["messages"])

        # Finalize using the last accumulated native messages
        final_native, native_messages, state = provider.finalize(
            provider.get_last_native_messages(), provider.get_state()
        )

        # Feature finalize chain (native)
        pipe = pipeline()
        final_native, native_messages, state = pipe(
            [feature.finalize for feature in features], final_native, native_messages, state
        )

        logger.debug("streaming complete", final_native=final_native)

        combined_native_finals = [*aggregated_native_finals, *final_native]

        # Convert provider-native finals to core messages
        final_core = provider.from_native_messages(combined_native_finals, state)

        # Apply extension and feature from-native transforms
        pipe = pipeline(combined_native_finals)
        final_core = pipe(
            [ext.from_native_messages for ext in enabled_extensions]
            + [feature.from_native_messages for feature in features],
            final_core,
        )

        # Attach global native_indices for final core messages
        final_core = self._normalize_final_core_with_native_indices(
            final_core,
            combined_native_finals,
            baseline_native_len,
        )

        appended: List[Message] = [Message.from_dict(m) for m in final_core]
        new_metadata = dict(session.metadata)
        new_metadata["native_messages"] = native_messages
        all_messages_after = [*session.messages, *appended]
        new_metadata["native_messages_integrity"] = self._compute_native_integrity(
            all_messages_after
        )
        new_session = Session(session.session_id, all_messages_after, new_metadata)

        logger.info("streaming request complete", final_message=final_core)

        yield {"type": "final", "session": new_session, "messages": final_core}

    async def send_request_stream_async(
        self, session: Session, config: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Async version of send_request_stream.

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
        provider, enabled_extensions, features, tools, _tags = self._resolve_plugins_for_config(
            config
        )

        provider.set_active_extensions(enabled_extensions)
        messages, native_messages, state = self._pre_request(
            session,
            config,
            provider,
            features,
            tools,
        )
        baseline_native_len = len(native_messages)

        aggregated_native_finals: List[Dict[str, Any]] = []


        # Stream from provider (async) using optimized streaming
        async for event in provider.stream_messages_async(native_messages, state):
            if event["type"] == "partial":
                yield {"type": "partial", "message": event["message"]}
            elif event["type"] == "final_messages":
                aggregated_native_finals.extend(event["messages"])  # native finals

        final_native, native_messages, state = provider.finalize(
            provider.get_last_native_messages(), provider.get_state()
        )

        # Feature finalize chain (native)
        pipe = pipeline()
        final_native, native_messages, state = pipe(
            [feature.finalize for feature in features], final_native, native_messages, state
        )

        combined_native_finals = [*aggregated_native_finals, *final_native]

        # Convert provider-native finals to core messages
        final_core = provider.from_native_messages(combined_native_finals, state)

        # Apply extension and feature from-native transforms
        pipe = pipeline(combined_native_finals)
        final_core = pipe(
            [ext.from_native_messages for ext in enabled_extensions]
            + [feature.from_native_messages for feature in features],
            final_core,
        )

        # Attach global native_indices for final core messages
        final_core = self._normalize_final_core_with_native_indices(
            final_core,
            combined_native_finals,
            baseline_native_len,
        )

        appended: List[Message] = [Message.from_dict(m) for m in final_core]
        new_metadata = dict(session.metadata)
        new_metadata["native_messages"] = native_messages
        all_messages_after = [*session.messages, *appended]
        new_metadata["native_messages_integrity"] = self._compute_native_integrity(
            all_messages_after
        )
        new_session = Session(session.session_id, all_messages_after, new_metadata)

        yield {"type": "final", "session": new_session, "messages": final_core}

    def get_config_schema(self) -> Dict[str, Any]:
        """Get combined config schema from all registered plugins.

        Returns:
            Mapping from plugin name to JSON schema of its configuration. Includes provider,
            provider extensions, features, and tools when registered.
        """
        schema: Dict[str, Any] = {}
        for provider in self._providers:
            schema[provider.name] = provider.get_config_schema()
            # Include provider extension schemas
            for (
                name,
                ext_schema,
            ) in provider.get_extension_config_schemas().items():
                schema[name] = ext_schema
        for feature in self._features:
            schema[feature.name] = feature.get_config_schema()
        for tool in self._tools:
            schema[tool.name] = tool.get_config_schema()
        return schema

    def get_ui_schema(self) -> List[Dict[str, Any]]:
        """Get flattened UI schema from all registered plugins.

        Each element is a dictionary describing a UI element contributed by a
        provider, extension, feature, or tool. Plugins may optionally include
        a "ui_type" field to classify elements as "config" (default),
        "action", or "info". Callers that are only interested in
        configuration inputs should filter for elements with
        ``element.get("ui_type", "config") == "config"``.
        """

        elements: List[Dict[str, Any]] = []

        def _extend(raw_elements: List[Dict[str, Any]]) -> None:
            for el in raw_elements or []:
                if not isinstance(el, dict):
                    continue
                entry: Dict[str, Any] = dict(el)
                ui_type = entry.get("ui_type")
                if not isinstance(ui_type, str) or not ui_type:
                    entry["ui_type"] = "config"
                elements.append(entry)

        for provider in self._providers:
            _extend(provider.get_ui_elements())
            # Include provider extension UI schemas
            for _name, ext_ui in provider.get_extension_ui_elements().items():
                _extend(ext_ui)
        for feature in self._features:
            _extend(feature.get_ui_elements())
        for tool in self._tools:
            _extend(tool.get_ui_elements())
        return elements

    def get_tool_schemas(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get tool schemas from enabled tool plugins for a config.

        Args:
            config: Application configuration passed to each tool's init.

        Returns:
            List of OpenAI-style function definitions across enabled tools.
        """
        schemas: List[Dict[str, Any]] = []
        if not self._tools:
            return schemas

        # When no provider is registered, fall back to exposing all tools.
        if not self._providers:
            for tool in self._tools:
                state = tool.init(config)
                schemas.extend(tool.get_tool_schemas(state))
            return schemas

        _provider, _exts, _features, tools, _tags = self._resolve_plugins_for_config(config)
        for tool in tools:
            state = tool.init(config)
            schemas.extend(tool.get_tool_schemas(state))
        return schemas

    def execute_tool_calls(
        self, tool_calls: List[Dict[str, Any]], config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute a batch of tool calls and return core "tool" messages.

        Accepts OpenAI-style tool call objects. The method initializes tool state from the
        provided config once per batch and invokes each registered tool to handle the call by name.
        If no tool handles a given call, an error tool message is returned.

        Args:
            tool_calls: List of tool call dictionaries normalized as
                {"id": str, "name": str, "arguments": dict | str} or OpenAI {"function": {"name", "arguments"}}.
            config: Application configuration passed to initialize tool plugins.

        Returns:
            List of core message dicts with role "tool". content contains formatted tool output; metadata
            includes tool_call_id and tool_name.
        """
        results: List[Dict[str, Any]] = []
        if not tool_calls:
            return results

        logger.debug(
            "execute_tool_calls_start",
            count=len(tool_calls),
        )

        # Initialize tool states once per call set
        tool_states = [(tool, tool.init(config)) for tool in self._tools]


        for call in tool_calls:
            call_id = call.get("id") or call.get("tool_call_id")
            name = call.get("name") or (call.get("function") or {}).get("name")
            args = call.get("arguments") or (call.get("function") or {}).get("arguments") or {}
            # Accept OpenAI-style string arguments; parse JSON when needed
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            executed = False
            formatted_content = None

            for tool, state in tool_states:
                try:
                    result = tool.execute_tool(str(name), args, state)
                except Exception as e:
                    result = {"success": False, "error": f"Tool error: {e}"}
                # Consider success if plugin reports success True
                if result.get("success"):
                    formatted_content = tool.format_tool_result(result, state)
                    executed = True
                    break
            if not executed:
                formatted_content = f"Error: no tool handled '{name}'"

            logger.debug(
                "execute_tool_call_complete",
                tool_name=str(name),
                executed=executed,
            )

            results.append(

                {
                    "role": "tool",
                    "content": formatted_content or "",
                    "metadata": {"tool_call_id": call_id, "tool_name": name},
                }
            )

        return results

    def export_session(self, session: Session, format: str = "json") -> str:
        """Export session to a serialized string.

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

    def import_session(self, data: str, format: str = "json") -> Session:
        """Import a session from a serialized string.

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

    def discover_and_register(self, modules: List[str]) -> Dict[str, List[str]]:
        """Discover plugins from Python modules and register them by duck typing.

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

        providers = []
        features = []
        tools = []
        extensions = []

        for mod_path in modules:
            module = importlib.import_module(mod_path)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                # Only consider classes defined in the module (not imports)
                if getattr(obj, "__module__", None) != module.__name__:
                    continue
                # Duck typing
                if hasattr(obj, "stream_api") or hasattr(obj, "call_api"):
                    providers.append(obj)
                elif hasattr(obj, "get_tool_schemas") and hasattr(obj, "execute_tool"):
                    tools.append(obj)
                elif hasattr(obj, "process_chunk"):
                    extensions.append(obj)
                else:
                    features.append(obj)

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
            summary["extensions"].extend([getattr(ext, "name", ext.__name__) for ext in extensions])

        # Register features and tools
        for feat in features:
            self.register_feature(feat)
            summary["features"].append(getattr(feat, "name", feat.__name__))
        for tool in tools:
            self.register_tool(tool)
            summary["tools"].append(getattr(tool, "name", tool.__name__))

        return summary
