"""
Core SDK for the AI Agent Platform.

Functional architecture: AgentCore stores only the processing pipeline (plugins via wrappers),
all transformations are pure functions that take session/config and return new objects.
"""

from typing import Any, Dict, List, Optional, Iterator, AsyncIterator, Tuple
from .types import Message, Session, MessageRole
from .plugin import (
    ProviderWrapper,
    FeatureWrapper,
    ToolWrapper,
)
import uuid
import json


class AgentCore:
    """
    Stateless processing pipeline for AI Agent Platform.

    Stores registered plugin wrappers (processing logic), not runtime state.
    All methods are pure functions that take session/config as parameters.
    The application layer manages sessions and configuration.
    """

    # -------- Integrity helpers --------
    def _compute_native_integrity(self, messages: List[Message]) -> Dict[str, Any]:
        """Compute verification data for native history integrity."""
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

        Raises RuntimeError if mismatch is detected. Users may remove 'native_messages' from metadata
        to intentionally change history or bypass integrity check.
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
    #     Not used in current flow, kept for potential future optimization.
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

    def register_provider(
        self, plugin_class: type, extensions: Optional[List[type]] = None
    ) -> None:
        """
        Register provider plugin class with optional provider extensions.
        Extensions are loaded by the provider wrapper (same language, hot path).
        """
        wrapper = ProviderWrapper(plugin_class, extensions or [])
        self._provider = wrapper

    def register_feature(self, plugin_class: type) -> None:
        """Register feature plugin class."""
        wrapper = FeatureWrapper(plugin_class)
        self._features.append(wrapper)

    def register_tool(self, plugin_class: type) -> None:
        """Register tool plugin class."""
        wrapper = ToolWrapper(plugin_class)
        self._tools.append(wrapper)

    def create_session(self, session_id: Optional[str] = None) -> Session:
        """Create new empty session (convenience function)."""
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
        """Add message to session (pure function - returns new session).

        If session.metadata contains provider-native history (native_messages), and a provider is registered,
        convert the newly added message to provider-native format via provider + stateless transforms and append
        to the stored native history. Also updates verification data for integrity checks.
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

    def _pre_request(
        self, session: Session, config: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Prepare state and inputs for a request; returns (messages, native_messages, state).

        Integrity is verified if native history is present. When native history exists, it is trusted
        as the full provider-native history for the session. Otherwise, native is reconstructed from core messages.
        """
        assert self._provider is not None

        # Collect tool schemas from registered tools and inject into config
        tools = self.get_tool_schemas(config) if self._tools else []
        provider_config = {**config, **({"tools": tools} if tools else {})}

        # Init chain: Provider → Extensions (inside provider) → Features
        state = self._provider.init(provider_config)
        ui_state = provider_config.get("ui_state", {})
        # Update chain: Provider → Extensions (inside provider) → Features
        if ui_state:
            state = self._provider.update_state(state, ui_state)
        for feature in self._features:
            state = feature.init(provider_config, state)
            state = feature.update_state(state, ui_state) if ui_state else state
            self._provider.set_state(state)
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
            native_messages = self._provider.to_native_messages(messages, state)
            # Apply stateless transforms: Extensions then Features
            native_messages = self._provider.apply_extension_transforms(
                messages, native_messages
            )
            for feature in self._features:
                native_messages = feature.to_native_messages(messages, native_messages)

        # Initialize request chains
        state = self._provider.initialize_request(native_messages, state)
        for feature in self._features:
            state = feature.initialize_request(native_messages, state)
            self._provider.set_state(state)
        return messages, native_messages, state

    def send_request(
        self, session: Session, config: Dict[str, Any]
    ) -> Tuple[Session, List[Dict[str, Any]]]:
        """
        Send request and return new session with response (pure function).
        """
        if not self._provider:
            raise RuntimeError("No provider registered")
        messages, native_messages, state = self._pre_request(session, config)
        final_native_1, _partials, native_messages, state = (
            self._provider.call_api(native_messages, state)
        )

        # Provider finalize returns provider-native finals and full native history
        final_native_2, native_messages, state = self._provider.finalize(
            native_messages, state
        )

        # Combine provider-native finals from call_api and provider.finalize
        final_native = final_native_1 + final_native_2

        # Feature finalize chain over provider-native finals (native cold path)
        for feature in self._features:
            final_native, native_messages, state = feature.finalize(
                final_native, native_messages, state
            )

        # Convert provider-native finals to core messages once finalization completes
        final_core = self._provider.from_native_messages(final_native, state)
        # Apply extension and feature from-native transforms
        for ext in self._provider.extensions:
            final_core = ext.from_native_messages(final_native, final_core)
        for feature in self._features:
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
        """
        Stream request and yield partials, then final session (generator function).
        """
        if not self._provider:
            raise RuntimeError("No provider registered")
        messages, native_messages, state = self._pre_request(session, config)
        aggregated_native_finals: List[Dict[str, Any]] = []

        # Stream from provider using optimized streaming
        for event in self._provider.stream_messages(native_messages, state):
            if event["type"] == "partial":
                yield {"type": "partial", "message": event["message"]}
            elif event["type"] == "final_messages":
                # These are provider-native finals
                aggregated_native_finals.extend(event["messages"])

        # Finalize using the last accumulated native messages
        final_native, native_messages, state = self._provider.finalize(
            self._provider.get_last_native_messages(), self._provider.get_state()
        )

        # Feature finalize chain (native)
        for feature in self._features:
            final_native, native_messages, state = feature.finalize(
                final_native, native_messages, state
            )

        combined_native_finals = [*aggregated_native_finals, *final_native]

        # Convert provider-native finals to core messages
        final_core = self._provider.from_native_messages(combined_native_finals, state)

        # Apply extension and feature from-native transforms
        for ext in self._provider.extensions:
            final_core = ext.from_native_messages(combined_native_finals, final_core)
        for feature in self._features:
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
        """
        Async version of send_request_stream.
        """
        if not self._provider:
            raise RuntimeError("No provider registered")

        messages, native_messages, state = self._pre_request(session, config)
        aggregated_native_finals: List[Dict[str, Any]] = []

        # Stream from provider (async) using optimized streaming
        async for event in self._provider.stream_messages_async(native_messages, state):
            if event["type"] == "partial":
                yield {"type": "partial", "message": event["message"]}
            elif event["type"] == "final_messages":
                aggregated_native_finals.extend(event["messages"])  # native finals

        final_native, native_messages, state = self._provider.finalize(
            self._provider.get_last_native_messages(), self._provider.get_state()
        )

        # Feature finalize chain (native)
        for feature in self._features:
            final_native, native_messages, state = feature.finalize(
                final_native, native_messages, state
            )

        combined_native_finals = [*aggregated_native_finals, *final_native]

        # Convert provider-native finals to core messages
        final_core = self._provider.from_native_messages(combined_native_finals, state)
        
        # Apply extension and feature from-native transforms
        for ext in self._provider.extensions:
            final_core = ext.from_native_messages(combined_native_finals, final_core)
        for feature in self._features:
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
        """Get combined config schema from all registered plugins."""
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
        """Get combined UI schema from all registered plugins."""
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
        """Get tool schemas from all registered tool plugins."""
        schemas: List[Dict[str, Any]] = []
        for tool in self._tools:
            state = tool.init(config)
            schemas.extend(tool.get_tool_schemas(state))
        return schemas

    def execute_tool_calls(self, tool_calls: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute a batch of tool calls and return core "tool" messages.

        Args:
            tool_calls: List of tool call dicts normalized as
                {"id": str, "name": str, "arguments": Dict[str, Any]}
            config: Application config to initialize tools

        Returns:
            List of core message dicts with role "tool", formatted content, and metadata.tool_call_id
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
        """Export session to string."""
        if format == "json":
            return json.dumps(session.to_dict(), indent=2)
        raise ValueError(f"Unsupported format: {format}")

    def import_session(self, data: str, format: str = "json") -> Session:
        """Import session from string."""
        if format == "json":
            session_dict = json.loads(data)
            return Session.from_dict(session_dict)
        raise ValueError(f"Unsupported format: {format}")

    def discover_and_register(self, modules: List[str]) -> Dict[str, List[str]]:
        """
        Discover plugins from a list of module import paths and register them.

        Discovery is duck-typed:
        - Provider: has 'stream_api' or 'call_api'
        - Provider Extension: has 'process_chunk' and 'target_provider'
        - Tool: has 'get_tool_schemas' and 'execute_tool'
        - Feature: otherwise

        Args:

            modules: List of Python module import paths to scan

        Returns:
            Summary dict with registered plugin names by type
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
                elif hasattr(obj, "process_chunk") and hasattr(obj, "target_provider"):
                    extensions.append(obj)
                elif hasattr(obj, "get_tool_schemas") and hasattr(obj, "execute_tool"):
                    tools.append(obj)
                else:
                    features.append(obj)

        # Register a single provider (first), with matching extensions
        summary: Dict[str, List[str]] = {
            "providers": [],
            "features": [],
            "tools": [],
            "extensions": [],
        }
        if providers:
            provider_cls = providers[0]
            # Match extensions by target_provider name
            target_name = getattr(provider_cls, "name", provider_cls.__name__)
            matched_exts = [
                ext
                for ext in extensions
                if getattr(ext, "target_provider", None) in (target_name,)
            ]
            self.register_provider(provider_cls, extensions=matched_exts)
            summary["providers"].append(target_name)
            summary["extensions"].extend(
                [getattr(ext, "name", ext.__name__) for ext in matched_exts]
            )

        # Register features and tools
        for feat in features:
            self.register_feature(feat)
            summary["features"].append(getattr(feat, "name", feat.__name__))
        for tool in tools:
            self.register_tool(tool)
            summary["tools"].append(getattr(tool, "name", tool.__name__))

        return summary
