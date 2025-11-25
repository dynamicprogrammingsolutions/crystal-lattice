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

    config = {"model": "gpt-4o", "base_url": "https://api.openai.com/v1", "api_key": "sk-..."}
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
import uuid
import json


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
        if actual.get("message_count") != expected_count or actual.get("total_chars") != expected_chars:
            raise RuntimeError(
                "Session messages changed without updating native history; remove 'native_messages' from session.metadata to modify history."
            )

    # -------- Optional future helper (not used currently) --------
    # def _try_reconstruct_native_with_suffix(
    #     self,
    #     messages: List[Dict[str, Any]],
    #     retained_native: List[Dict[str, Any]],
    #     state: Dict[str, Any],
    # ) -> List[Dict[str, Any]]:
    #     """Attempt to append only the suffix of new core messages to retained native history.
    #
    #     Not used in current flow, kept for potential future optimization.
    #
    #     Args:
    #         messages: Full core messages.
    #         retained_native: Previously retained provider-native messages.
    #         state: Current provider shared state.
    #
    #     Returns:
    #         Full provider-native messages after attempting suffix append, or full
    #         reconstruction when suffixing is not feasible.
    #     """
    #     base_core = self._provider.from_native_messages(retained_native, state)  # type: ignore[union-attr]
    #     # Compare role/content only to ignore metadata differences
    #     def _strip(lst: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #         return [{"role": m.get("role"), "content": m.get("content", "")} for m in lst]
    #     if _strip(messages[: len(base_core)]) == _strip(base_core):
    #         suffix_core = messages[len(base_core) :]
    #         suffix_native = self._provider.to_native_messages(suffix_core, state)  # type: ignore[union-attr]
    #         suffix_native = self._provider.apply_extension_transforms(messages, suffix_native)  # type: ignore[union-attr]
    #         for feature in self._features:
    #             suffix_native = feature.to_native_messages(messages, suffix_native)
    #         return [*retained_native, *suffix_native]
    #     # Fallback: full conversion path
    #     native_messages = self._provider.to_native_messages(messages, state)  # type: ignore[union-attr]
    #     native_messages = self._provider.apply_extension_transforms(messages, native_messages)  # type: ignore[union-attr]
    #     for feature in self._features:
    #         native_messages = feature.to_native_messages(messages, native_messages)
    #     return native_messages

    def __init__(self):
        """Initialize core with empty plugin pipeline."""
        self._provider: Optional[ProviderWrapper] = None
        self._features: List[FeatureWrapper] = []
        self._tools: List[ToolWrapper] = []
        # Caches for model discovery and tag-based dependency resolution
        self._models_cache: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        self._dependency_cache: Dict[
            Tuple[str, str, str],
            Tuple[List[str], List[str], List[str], List[str]],
        ] = {}
        self._tags_cache: Dict[Tuple[str, Tuple[str, str, str]], List[str]] = {}

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
        self._provider = wrapper
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
    ) -> Session:
        """Add a message to the session (pure function).

        When session.metadata contains provider-native history (native_messages), and a provider is
        registered, converts the newly added message to provider-native format via the provider and
        stateless transforms, and appends it to the stored native history. Updates verification data
        for integrity checks.

        Args:
            session: Current session.
            role: Message role ("system", "user", "assistant", or "tool").
            content: Message content.
            metadata: Optional per-message metadata.

        Returns:
            New Session with the message appended (immutable update).
        """
        message = Message(role=role, content=content, metadata=metadata)
        new_messages: List[Message] = [*session.messages, message]

        # Default metadata passthrough
        new_metadata: Dict[str, Any] = dict(session.metadata)

        # If native history exists, verify integrity before modification
        if isinstance(session.metadata, dict) and "native_messages" in session.metadata:
            self._verify_native_integrity(session)

        # Attempt to append native for the new message if provider is available and native history exists
        if self._provider and isinstance(session.metadata, dict):
            retained_native = session.metadata.get("native_messages")
            if isinstance(retained_native, list):
                # Initialize minimal state for stateless transforms
                state = self._provider.init({})
                for feature in self._features:
                    state = feature.init({}, state)
                    self._provider.set_state(state)
                # Build core dict for the single new message only
                core_new_msg = [message.to_dict()]
                # Convert single message to provider-native and apply stateless transforms (single-message context)
                suffix_native = self._provider.to_native_messages(core_new_msg, state)
                suffix_native = self._provider.apply_extension_transforms(
                    core_new_msg, suffix_native
                )
                for feature in self._features:
                    suffix_native = feature.to_native_messages(core_new_msg, suffix_native)
                new_metadata["native_messages"] = [*retained_native, *suffix_native]

        # Always update integrity data when we have native history
        if "native_messages" in new_metadata:
            new_metadata["native_messages_integrity"] = self._compute_native_integrity(new_messages)

        return Session(
            session_id=session.session_id,
            messages=new_messages,
            metadata=new_metadata,
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

    def _coerce_models_result(
        self,
        result: Any,
        previous: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Normalize a plugin `get_models` result into a list.

        Treats ``None`` as "no change" (returns ``previous``) and
        attempts to coerce other iterables to a list. On type errors,
        falls back to ``previous``.
        """
        if result is None:
            return list(previous)
        if isinstance(result, list):
            return result
        if isinstance(result, tuple):
            return list(result)
        try:
            return list(result)
        except TypeError:
            return list(previous)

    def _coerce_tags_result(self, result: Any) -> List[str]:
        """Normalize a plugin `get_tags` result into a list of strings.

        Treats ``None`` as an empty list and attempts to coerce other
        iterables to a list. Non-iterable values result in an empty
        list.
        """
        if result is None:
            return []
        if isinstance(result, (list, tuple, set)):
            seq = result
        else:
            try:
                seq = list(result)
            except TypeError:
                return []
        return [str(tag) for tag in seq]

    def _get_models_for_config(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return cached or freshly-computed model descriptors for this config."""
        if not self._provider:
            return []
        provider = self._provider
        provider_name = provider.name
        norm_config = self._normalize_config(config)
        cache_key = (provider_name, norm_config)
        cached = self._models_cache.get(cache_key)
        if cached is not None:
            # Return shallow copies to avoid accidental mutation of cached structures
            return [dict(m) for m in cached]

        # Start with provider-declared models and let extensions and features
        # participate in model discovery. Each contribution is normalized via
        # _coerce_models_result so that `None` and non-list values do not
        # break the pipeline.
        models: List[Dict[str, Any]] = self._coerce_models_result(
            provider.get_models(config),
            [],
        )
        for ext in provider.extensions:
            models = self._coerce_models_result(
                ext.get_models(config, models),
                models,
            )
        for feature in self._features:
            models = self._coerce_models_result(
                feature.get_models(config, models),
                models,
            )


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
        if not self._provider:
            raise RuntimeError("No provider registered")

        provider = self._provider
        models = self._get_models_for_config(config)
        provider_name = provider.name
        norm_config = self._normalize_config(config)
        norm_models = self._normalize_models(models)
        dep_key = (provider_name, norm_config, norm_models)

        cached = self._dependency_cache.get(dep_key)
        if cached is not None:
            ext_names, feature_names, tool_names, tags = cached
            enabled_extensions = [
                ext for ext in provider.extensions if ext.name in ext_names
            ]
            enabled_features = [
                feat for feat in self._features if feat.name in feature_names
            ]
            enabled_tools = [
                tool for tool in self._tools if tool.name in tool_names
            ]
            return provider, enabled_extensions, enabled_features, enabled_tools, list(
                tags
            )

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
            provider_tag_key = (provider.name, dep_key)
            provider_tags = self._tags_cache.get(provider_tag_key)
            if provider_tags is None:
                try:
                    provider_tags = provider.get_tags(config, models)
                except Exception:
                    provider_tags = []
                provider_tags = self._coerce_tags_result(provider_tags)
                self._tags_cache = {
                    **self._tags_cache,
                    provider_tag_key: provider_tags,
                }
            available_tags.update(provider_tags)
 
            # Extension tags
            for ext in enabled_extensions:
                key = (ext.name, dep_key)
                tags = self._tags_cache.get(key)
                if tags is None:
                    try:
                        tags = ext.get_tags(config, models)
                    except Exception:
                        tags = []
                    tags = self._coerce_tags_result(tags)
                    self._tags_cache = {**self._tags_cache, key: tags}
                available_tags.update(tags)
 
            # Feature tags
            for feat in enabled_features:
                key = (feat.name, dep_key)
                tags = self._tags_cache.get(key)
                if tags is None:
                    try:
                        tags = feat.get_tags(config, models)
                    except Exception:
                        tags = []
                    tags = self._coerce_tags_result(tags)
                    self._tags_cache = {**self._tags_cache, key: tags}
                available_tags.update(tags)
 
            # Tool tags
            for tool in enabled_tools:
                key = (tool.name, dep_key)
                tags = self._tags_cache.get(key)
                if tags is None:
                    try:
                        tags = tool.get_tags(config, models)
                    except Exception:
                        tags = []
                    tags = self._coerce_tags_result(tags)
                    self._tags_cache = {**self._tags_cache, key: tags}
                available_tags.update(tags)


            # Filter by required_tags
            next_enabled_extensions = [
                ext
                for ext in enabled_extensions
                if set(self._coerce_tags_result(ext.required_tags())).issubset(
                    available_tags
                )
            ]
            next_enabled_features = [
                feat
                for feat in enabled_features
                if set(self._coerce_tags_result(feat.required_tags())).issubset(
                    available_tags
                )
            ]
            next_enabled_tools = [
                tool
                for tool in enabled_tools
                if set(self._coerce_tags_result(tool.required_tags())).issubset(
                    available_tags
                )
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
        # Collect tool schemas from enabled tools and inject into config
        tool_schemas: List[Dict[str, Any]] = []
        for tool in tools:
            tool_state = tool.init(config)
            tool_schemas.extend(tool.get_tool_schemas(tool_state))
        provider_config = {**config, **({"tools": tool_schemas} if tool_schemas else {})}

        # Init chain: Provider  Extensions (inside provider)  Features
        # Configuration (including any UI-driven values) is passed directly via
        # provider_config; there is no separate update_state step.
        state = provider.init(provider_config)
        for feature in features:
            state = feature.init(provider_config, state)
            provider.set_state(state)
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
            native_messages = retained_native
        else:
            # Provider-first conversion (native_base for stateless transforms)
            native_messages = provider.to_native_messages(messages, state)
            # Apply stateless transforms: Extensions then Features
            native_messages = provider.apply_extension_transforms(
                messages, native_messages
            )
            for feature in features:
                native_messages = feature.to_native_messages(messages, native_messages)

        # Initialize request chains
        state = provider.initialize_request(native_messages, state)
        for feature in features:
            state = feature.initialize_request(native_messages, state)
            provider.set_state(state)
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
        if not self._provider:
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
        final_native_1, _partials, native_messages, state = provider.call_api(
            native_messages, state
        )
 
        # Provider finalize returns provider-native finals and full native history
        final_native_2, native_messages, state = provider.finalize(
            native_messages, state
        )
 
        # Combine provider-native finals from call_api and provider.finalize
        final_native = final_native_1 + final_native_2
 
        # Feature finalize chain over provider-native finals (native cold path)
        for feature in features:
            final_native, native_messages, state = feature.finalize(
                final_native, native_messages, state
            )
 
        # Convert provider-native finals to core messages once finalization completes
        final_core = provider.from_native_messages(final_native, state)
        # Apply extension and feature from-native transforms
        for ext in enabled_extensions:
            final_core = ext.from_native_messages(final_native, final_core)
        for feature in features:
            final_core = feature.from_native_messages(final_native, final_core)


        # Build new session messages by appending new Message objects
        appended: List[Message] = [Message.from_dict(m) for m in final_core]
        new_metadata = dict(session.metadata)
        # Persist full provider-native history for the turn (implementation detail)
        new_metadata["native_messages"] = native_messages
        all_messages_after = [*session.messages, *appended]
        new_metadata["native_messages_integrity"] = self._compute_native_integrity(all_messages_after)
        new_session = Session(
            session.session_id, all_messages_after, new_metadata
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
        if not self._provider:
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
        aggregated_native_finals: List[Dict[str, Any]] = []
 
        # Stream from provider using optimized streaming
        for event in provider.stream_messages(native_messages, state):
            if event["type"] == "partial":
                yield {"type": "partial", "message": event["message"]}
            elif event["type"] == "final_messages":
                # These are provider-native finals
                aggregated_native_finals.extend(event["messages"])
 
        # Finalize using the last accumulated native messages
        final_native, native_messages, state = provider.finalize(
            provider.get_last_native_messages(), provider.get_state()
        )
 
        # Feature finalize chain (native)
        for feature in features:
            final_native, native_messages, state = feature.finalize(
                final_native, native_messages, state
            )
 
        combined_native_finals = [*aggregated_native_finals, *final_native]
 
        # Convert provider-native finals to core messages
        final_core = provider.from_native_messages(combined_native_finals, state)
 
        # Apply extension and feature from-native transforms
        for ext in enabled_extensions:
            final_core = ext.from_native_messages(combined_native_finals, final_core)
        for feature in features:
            final_core = feature.from_native_messages(combined_native_finals, final_core)


        appended: List[Message] = [Message.from_dict(m) for m in final_core]
        new_metadata = dict(session.metadata)
        new_metadata["native_messages"] = native_messages
        all_messages_after = [*session.messages, *appended]
        new_metadata["native_messages_integrity"] = self._compute_native_integrity(all_messages_after)
        new_session = Session(
            session.session_id, all_messages_after, new_metadata
        )

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
        if not self._provider:
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
        for feature in features:
            final_native, native_messages, state = feature.finalize(
                final_native, native_messages, state
            )
 
        combined_native_finals = [*aggregated_native_finals, *final_native]
 
        # Convert provider-native finals to core messages
        final_core = provider.from_native_messages(combined_native_finals, state)
         
        # Apply extension and feature from-native transforms
        for ext in enabled_extensions:
            final_core = ext.from_native_messages(combined_native_finals, final_core)
        for feature in features:
            final_core = feature.from_native_messages(combined_native_finals, final_core)


        appended: List[Message] = [Message.from_dict(m) for m in final_core]
        new_metadata = dict(session.metadata)
        new_metadata["native_messages"] = native_messages
        all_messages_after = [*session.messages, *appended]
        new_metadata["native_messages_integrity"] = self._compute_native_integrity(all_messages_after)
        new_session = Session(
            session.session_id, all_messages_after, new_metadata
        )

        yield {"type": "final", "session": new_session, "messages": final_core}

    def get_config_schema(self) -> Dict[str, Any]:
        """Get combined config schema from all registered plugins.

        Returns:
            Mapping from plugin name to JSON schema of its configuration. Includes provider,
            provider extensions, features, and tools when registered.
        """
        schema: Dict[str, Any] = {}
        if self._provider:
            schema[self._provider.name] = self._provider.get_config_schema()
            # Include provider extension schemas
            for (
                name,
                ext_schema,
            ) in self._provider.get_extension_config_schemas().items():
                schema[name] = ext_schema
        for feature in self._features:
            schema[feature.name] = feature.get_config_schema()
        for tool in self._tools:
            schema[tool.name] = tool.get_config_schema()
        return schema

    def get_ui_schema(self) -> Dict[str, Any]:
        """Get combined UI schema from all registered plugins.

        Returns:
            Mapping from plugin name to UI element definitions. Includes provider,
            provider extensions, features, and tools when registered.
        """
        ui: Dict[str, Any] = {}
        if self._provider:
            ui[self._provider.name] = self._provider.get_ui_elements()
            # Include provider extension UI schemas
            for name, ext_ui in self._provider.get_extension_ui_elements().items():
                ui[name] = ext_ui
        for feature in self._features:
            ui[feature.name] = feature.get_ui_elements()
        for tool in self._tools:
            ui[tool.name] = tool.get_ui_elements()
        return ui

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
        if not self._provider:
            for tool in self._tools:
                state = tool.init(config)
                schemas.extend(tool.get_tool_schemas(state))
            return schemas

        _provider, _exts, _features, tools, _tags = self._resolve_plugins_for_config(
            config
        )
        for tool in tools:
            state = tool.init(config)
            schemas.extend(tool.get_tool_schemas(state))
        return schemas


    def execute_tool_calls(self, tool_calls: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
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
