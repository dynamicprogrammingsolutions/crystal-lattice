"""
Core SDK for the AI Agent Platform.

Functional architecture: AgentCore stores only the processing pipeline (plugins via wrappers),
all transformations are pure functions that take session/config and return new objects.

Examples:
    Basic non-streaming usage:

    ```python
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
from .types import Message, Session, MessageRole, ToolDescriptor
from .plugin import (
    ProviderWrapper,
    ExtensionWrapper,
    FeatureWrapper,
    ToolWrapper,
)
from .utils import pipeline, get_logger
import uuid
import json
import re

logger = None
log_chunk_processing = None

_PreparedToolState = Tuple[ToolWrapper, Dict[str, Any], Optional[Dict[str, Any]]]


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
            # Nothing to normalize; final_core is already in core shape.
            return final_core

        local_count = len(finals_native)

        def _normalize_message(
            msg: dict[str, Any],
            default_local_indices: list[int] | None = None,
        ) -> dict[str, Any]:
            raw_md = msg.get("metadata") or {}
            md = dict(raw_md) if isinstance(raw_md, dict) else {}
            native_indices = md.get("native_indices")

            if isinstance(native_indices, list) and all(
                isinstance(i, int) for i in native_indices
            ):
                local_indices = [i for i in native_indices if 0 <= i < local_count]
            elif default_local_indices is not None:
                local_indices = [
                    i for i in default_local_indices if 0 <= i < local_count
                ]
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
        base_metadata = (
            dict(session.metadata) if isinstance(session.metadata, dict) else {}
        )

        role_value = message_dict.get("role", "user")
        role = role_value
        content = message_dict.get("content", "")
        multipart_content = message_dict.get("multipartContent")
        raw_md = message_dict.get("metadata") or {}
        md = dict(raw_md) if isinstance(raw_md, dict) else {}

        from agent_core.types import Message  # local import to avoid cycles

        # Note on metadata preservation:
        #
        # When provider-native history is enabled (session.metadata contains
        # ``native_messages``), this helper rebuilds the full core message list
        # from the provider-native sequence.
        #
        # By design, arbitrary application-level ``Message.metadata`` is NOT
        # automatically preserved across the native -> core rebuild step.
        # If metadata must survive a native-history rebuild, providers/
        # extensions/features should explicitly persist it into the provider-
        # native message dicts under the ``_metadata`` key in
        # ``to_native_messages`` and restore it in ``from_native_messages``.

        def _core_only_session(clean_metadata):
            cleaned = dict(clean_metadata)
            cleaned.pop("native_indices", None)
            new_message = Message(
                role=role,
                content=content,
                metadata=cleaned or None,
                multipart_content=multipart_content,
            )
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

        message_count = len(session.messages)

        # When there is no retained native history, we treat add_message as
        # a core-only operation unless we have both an explicit config and a
        # session with no prior messages. This allows applications to call
        # add_message without a config for core-only sessions while avoiding
        # silently creating or dropping native history.
        if retained_native is None:
            # No native history yet: if no config is provided, append only to
            # core messages and do not create native history.
            if not config:
                return _core_only_session(md), None
            # When native history is absent but there are already messages in
            # the session, we cannot safely retrofit native history
            # incrementally, so we fall back to a core-only append even if a
            # config is provided.
            if message_count > 0:
                return _core_only_session(md), None

        if retained_native is not None:
            self._verify_native_integrity(session)
        else:
            retained_native = []

        try:
            core_suffix = [
                {
                    "role": role,
                    "content": content,
                    "metadata": md,
                }
            ]
            if multipart_content:
                core_suffix[0]["multipartContent"] = multipart_content
            suffix_native = self._core_messages_to_native_for_config(
                core_suffix, config or {}
            )
        except Exception as e:
            raise e

        # Append the native suffix to the retained history and rebuild the
        # full core message sequence from provider-native history so that
        # feature/provider transforms that operate in to_native/from_native
        # are reflected in the stored core messages. We rely on
        # `_rebuild_core_from_native` to assign `native_indices` across the
        # full history, rather than attempting to normalize the suffix in
        # isolation (which can change cardinality for features like
        # SystemMessageFeature).
        new_native_messages = [*retained_native, *suffix_native]

        try:
            rebuilt_messages, post_init_native = self._rebuild_core_from_native(
                new_native_messages, config or {}
            )
        except Exception as e:
            raise e

        # Provider/extension pipelines (including the `_metadata` convention)
        # are responsible for reconstructing per-message metadata.
        new_messages: List[Message] = [
            Message.from_dict(m.to_dict()) for m in rebuilt_messages
        ]

        # Use post-initialize native_messages (after features like
        # SystemMessageFeature may have added synthetic messages)
        new_session_metadata = {
            **base_metadata,
            "native_messages": post_init_native,
            "native_messages_integrity": self._compute_native_integrity(new_messages),
        }

        # The caller (AgentCore.add_message) does not currently use the
        # returned global_indices, and rebuilt_messages already contain
        # per-message native_indices metadata, so we return an empty list
        # here for compatibility.
        global_indices: List[int] = []

        return (
            type(session)(
                session_id=session.session_id,
                messages=new_messages,
                metadata=new_session_metadata,
            ),
            global_indices,
        )

    def _insert_single_message_with_native(
        self,
        session,
        message_dict,
        insert_at: int,
        config,
    ):
        base_metadata = (
            dict(session.metadata) if isinstance(session.metadata, dict) else {}
        )

        role_value = message_dict.get("role", "user")
        role = role_value
        content = message_dict.get("content", "")
        multipart_content = message_dict.get("multipartContent")
        raw_md = message_dict.get("metadata") or {}
        md_new = dict(raw_md) if isinstance(raw_md, dict) else {}

        from agent_core.types import Message  # local import to avoid cycles

        existing_messages = session.messages
        message_count = len(existing_messages)

        # Clamp insert_at to [0, message_count]. Caller is expected to
        # validate bounds; this is a defensive guard.
        if insert_at < 0:
            insert_at = 0
        if insert_at > message_count:
            insert_at = message_count

        # When there is no retained native history, treat insertion as a
        # core-only operation.
        if not isinstance(session.metadata, dict) or not isinstance(
            session.metadata.get("native_messages"), list
        ):
            new_messages: List[Message] = []
            for idx, msg in enumerate(existing_messages):
                if idx == insert_at:
                    new_messages.append(
                        Message(
                            role=role,
                            content=content,
                            metadata=md_new or None,
                            multipart_content=multipart_content,
                        )
                    )
                new_messages.append(msg)
            if insert_at == message_count:
                new_messages.append(
                    Message(
                        role=role,
                        content=content,
                        metadata=md_new or None,
                        multipart_content=multipart_content,
                    )
                )

            new_session_metadata = dict(base_metadata)
            new_session_metadata.pop("native_messages", None)
            new_session_metadata.pop("native_messages_integrity", None)

            return (
                type(session)(
                    session_id=session.session_id,
                    messages=new_messages,
                    metadata=new_session_metadata,
                ),
                [],
            )

        # Native-preserving insertion: split using slice_session and then
        # append+join using public helpers so that native indices and
        # provider-native extras are handled consistently.
        kept_prefix, removed_suffix = self.slice_session(
            session,
            config,
            start=0,
            end=insert_at,
            return_removed=True,
        )

        prefix_with_insert, _ = self._append_single_message_with_native(
            kept_prefix,
            message_dict,
            config or {},
        )

        joined = self.join_sessions(prefix_with_insert, removed_suffix, config or {})

        return (joined, [])

    def _modify_single_message_with_native(self, session, index, content, config):
        from agent_core.types import Message  # local import to avoid cycles

        messages = session.messages
        message_count = len(messages)

        # Normalize and validate index (supports negative indices).
        if not isinstance(index, int):
            raise TypeError("index must be an integer")

        target_index = index
        if target_index < 0:
            target_index = message_count + target_index
        if target_index < 0 or target_index >= message_count:
            raise IndexError("message index out of range")

        target = messages[target_index]

        # Only core conversation roles are supported.
        if target.role not in ("system", "user", "assistant"):
            raise ValueError(
                "modify_message only supports system, user, and assistant roles"
            )

        base_metadata = (
            dict(session.metadata) if isinstance(session.metadata, dict) else {}
        )

        # Core-only path: drop native history and indices, update content only.
        def _core_only_session() -> Session:
            new_messages: List[Message] = []
            for idx, msg in enumerate(messages):
                data = msg.to_dict()
                md = dict(data.get("metadata") or {})
                md.pop("native_indices", None)
                multipart_content = data.get("multipartContent")
                if idx == target_index:
                    new_messages.append(
                        Message(
                            role=data["role"],
                            content=content,
                            metadata=md or None,
                            multipart_content=multipart_content,
                        )
                    )
                else:
                    new_messages.append(
                        Message(
                            role=data["role"],
                            content=data["content"],
                            metadata=md or None,
                            multipart_content=multipart_content,
                        )
                    )

            new_session_metadata: Dict[str, Any] = dict(base_metadata)
            new_session_metadata.pop("native_messages", None)
            new_session_metadata.pop("native_messages_integrity", None)

            return type(session)(
                session_id=session.session_id,
                messages=new_messages,
                metadata=new_session_metadata,
            )

        # If there is no retained native history, fall back immediately.
        retained_native = None
        if isinstance(session.metadata, dict):
            rn = session.metadata.get("native_messages")
            if isinstance(rn, list):
                retained_native = rn

        if retained_native is None:
            return _core_only_session()

        # Verify integrity before attempting any native-preserving update.
        self._verify_native_integrity(session)

        original_native = retained_native

        # Determine which native indices belong to the target message.
        target_md = target.metadata if isinstance(target.metadata, dict) else {}
        native_indices = target_md.get("native_indices")
        if not native_indices:
            raise RuntimeError(
                "modify_message requires non-empty native_indices for target message"
            )

        # Use a set to de-duplicate indices; order is irrelevant for the slice
        # bounds, so we sort after collecting unique values.
        indices = sorted(set(native_indices))

        start_idx = min(indices)
        end_idx = max(indices)

        # Convert the modified core message to native using the provider pipeline.
        target_dict = target.to_dict()
        core_msg = {
            "role": target_dict["role"],
            "content": content,
            "metadata": dict(target_dict.get("metadata") or {}),
        }

        native_suffix = self._core_messages_to_native_for_config(
            [core_msg], config or {}
        )

        # Best-effort patch: replace the native slice [start_idx, end_idx] with the
        # newly converted native messages, allowing cardinality to change.
        before = original_native[:start_idx]
        after = original_native[end_idx + 1 :]
        new_native = [*before, *native_suffix, *after]

        # Rebuild core messages from the updated native history.
        # Use post-initialize native to ensure features like SystemMessageFeature
        # have their structural changes reflected in stored metadata.
        new_messages, post_init_native = self._rebuild_core_from_native(
            new_native, config or {}
        )

        new_metadata = {
            **base_metadata,
            "native_messages": post_init_native,
            "native_messages_integrity": self._compute_native_integrity(new_messages),
        }

        return type(session)(
            session_id=session.session_id,
            messages=new_messages,
            metadata=new_metadata,
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
        self._prepared_tool_states: Dict[Tuple[int, str], Dict[str, Any]] = {}
        self._prepared_tool_data: Dict[Tuple[int, str], Dict[str, Any]] = {}

    def _reset_caches(self) -> None:
        """Reset internal caches for models, dependencies, and tags."""
        self._models_cache = {}
        self._dependency_cache = {}
        self._tags_cache = {}
        self._prepared_tool_states = {}
        self._prepared_tool_data = {}

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
        *,
        multipart_content: Optional[List[Dict[str, Any]]] = None,
        after_index: Optional[int] = None,
    ) -> Session:
        """Add a message to the session (pure function).

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
            )
            return new_session

        new_session, _ = self._insert_single_message_with_native(
            session,
            message_dict,
            insert_at,
            config or {},
        )
        return new_session

    def modify_message(
        self,
        session: Session,
        index: int,
        content: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """Modify the content of an existing message (pure function).

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
            session, index, content, config or {}
        )

    def _slice_session_core_only(
        self,
        session: Session,
        keep_indices: Set[int],
    ) -> Session:
        """Core-only slice/remove that drops native history and indices."""
        messages = session.messages
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
            multipart_content = data.get("multipartContent")
            if md:
                kept_messages.append(
                    Message(
                        role=data["role"],
                        content=data["content"],
                        metadata=md,
                        multipart_content=multipart_content,
                    )
                )
            else:
                kept_messages.append(
                    Message(
                        role=data["role"],
                        content=data["content"],
                        metadata=None,
                        multipart_content=multipart_content,
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
        return_removed: bool = False,
    ) -> Session:
        """Return a new session with messages sliced/removed.

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
            messages=sliced.messages,
            metadata=sliced.metadata,
        )

    def join_sessions(
        self,
        prefix: Session,
        suffix: Session,
        config: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """Join two sessions end-to-end, preserving native history when possible.

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

    def rebuild_native_history(
        self,
        session: Session,
        config: Optional[Dict[str, Any]] = None,
        *,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ) -> Session:
        """Rebuild provider-native history from the current core messages.

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
            if start_idx < 0 or end_idx < 0 or start_idx >= end_idx or end_idx > message_count:
                raise ValueError("start/end must select a non-empty visible message slice")

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
                metadata = message.metadata if isinstance(message.metadata, dict) else {}
                native_indices = metadata.get("native_indices")
                if not isinstance(native_indices, list) or not native_indices:
                    raise RuntimeError(
                        "selective rebuild requires native_indices for every selected message"
                    )
                target_native_indices.extend(
                    index for index in native_indices if isinstance(index, int)
                )

            if not target_native_indices:
                raise RuntimeError("selected visible message slice maps to no native history")

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
            )

            before = retained_native[: unique_indices[0]]
            after = retained_native[unique_indices[-1] + 1 :]
            new_native = [*before, *replacement_native, *after]

            rebuilt_messages, post_init_native = self._rebuild_core_from_native(
                new_native, config
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
        new_native = self._core_messages_to_native_for_config(core_dicts, config)

        # Rebuild canonical core messages from the new native history so that
        # provider/feature transformations and native_indices are normalized.
        # Use post-initialize native to capture any structural changes from features.
        rebuilt_messages, post_init_native = self._rebuild_core_from_native(
            new_native, config
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

        module = (
            getattr(plugin_class, "__module__", None)
            if plugin_class is not None
            else None
        )
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
                if (
                    isinstance(cfg_name, str)
                    and cfg_name
                    and cfg_name not in class_names
                ):
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
            return cached

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
        return validated

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
            enabled_extensions = [
                ext for ext in provider.extensions if ext.name in ext_names
            ]
            enabled_features = [
                feat for feat in self._features if feat.name in feature_names
            ]
            enabled_tools = [tool for tool in self._tools if tool.name in tool_names]
            return provider, enabled_extensions, enabled_features, enabled_tools, tags

        # Get enabled_plugins from config (re-enable plugins disabled by default)
        enabled_plugins_set: Set[str] = set(config.get("enabled_plugins") or [])
        force_enabled_set: Set[str] = set(config.get("force_enabled_plugins") or [])

        # Build initial candidates, respecting default_enabled attribute
        def _filter_by_default_enabled(plugins: List[Any]) -> List[Any]:
            result = []
            for p in plugins:
                default_enabled = getattr(p.plugin_class, "default_enabled", True)
                if (
                    default_enabled is False
                    and p.name not in enabled_plugins_set
                    and p.name not in force_enabled_set
                ):
                    continue
                result.append(p)
            return result

        candidate_extensions: List[ExtensionWrapper] = _filter_by_default_enabled(
            list(provider.extensions)
        )
        candidate_features: List[FeatureWrapper] = _filter_by_default_enabled(
            list(self._features)
        )
        candidate_tools: List[ToolWrapper] = _filter_by_default_enabled(
            list(self._tools)
        )

        enabled_extensions = candidate_extensions
        enabled_features = candidate_features
        enabled_tools = candidate_tools

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

            # Get force_enabled_plugins from config
            force_enabled_set: Set[str] = set(config.get("force_enabled_plugins") or [])

            # Build context for is_enabled calls
            is_enabled_context: Dict[str, Any] = {
                "enabled_plugin_ids": {
                    "extensions": [ext.name for ext in enabled_extensions],
                    "features": [feat.name for feat in enabled_features],
                    "tools": [tool.name for tool in enabled_tools],
                },
                "disabled_plugins": config.get("disabled_plugins", []),
                "force_enabled_plugins": list(force_enabled_set),
            }

            def _check_plugin_enabled(
                plugin: Any,
                plugin_tags: List[str],
            ) -> bool:
                """Check if a plugin should be enabled using is_enabled or tag-based fallback."""
                # Check force_enabled first
                if plugin.name in force_enabled_set:
                    return True

                # Check is_enabled
                is_enabled_result = plugin.is_enabled(
                    config,
                    list(available_tags),
                    models,
                    is_enabled_context,
                )

                if is_enabled_result is True:
                    return True
                if is_enabled_result is False:
                    return False

                # Fall back to tag-based check
                if not set(plugin.required_tags()).issubset(available_tags):
                    return False
                if set(plugin.forbidden_tags()).intersection(available_tags):
                    return False
                return True

            # Filter plugins using is_enabled / required_tags / forbidden_tags
            next_enabled_extensions = [
                ext
                for ext in enabled_extensions
                if _check_plugin_enabled(ext, list(available_tags))
            ]
            next_enabled_features = [
                feat
                for feat in enabled_features
                if _check_plugin_enabled(feat, list(available_tags))
            ]
            next_enabled_tools = [
                tool
                for tool in enabled_tools
                if _check_plugin_enabled(tool, list(available_tags))
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

    def get_plugins_for_config(
        self,
        config: Dict[str, Any],
    ) -> Dict[str, List[str]]:
        """Return active plugin identifiers for the given config.

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

    def _build_plugin_context(
        self,
        *,
        config: Dict[str, Any],
        provider: Optional[ProviderWrapper],
        enabled_extensions: List[ExtensionWrapper],
        enabled_features: List[FeatureWrapper],
        enabled_tools: List[ToolWrapper],
        tags: List[str],
        models: List[Dict[str, Any]],
        available_tools: Optional[List[ToolDescriptor]] = None,
        tools: Optional[List[ToolDescriptor]] = None,
        request_id: str | None = None,
    ) -> Dict[str, Any]:
        catalog = list(available_tools or [])
        effective = list(tools if tools is not None else catalog)
        tool_interop_registry = self._get_tool_interop_registry_for_config(config)
        tool_schema_target_formats = self._get_tool_schema_target_formats_for_config(
            config
        )
        return {
            "core": self,
            "config": dict(config),
            "request_id": request_id,
            "tags": list(tags),
            "models": list(models),
            "provider": provider.name if provider is not None else None,
            "tool_interop": {
                "registry": tool_interop_registry,
                "schema_target_formats": list(tool_schema_target_formats),
            },
            "enabled_plugins": {
                "providers": [provider.name] if provider is not None else [],
                "extensions": [ext.name for ext in enabled_extensions],
                "features": [feature.name for feature in enabled_features],
                "tools": [tool.name for tool in enabled_tools],
            },
            "available_tools": catalog,
            "tools": effective,
        }

    def _init_provider_and_features_for_config(
        self,
        provider: ProviderWrapper,
        features: List[FeatureWrapper],
        tools: List[ToolWrapper],
        config: Optional[Dict[str, Any]] = None,
        *,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
        request_id: str | None = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Initialize provider and features for the given config.

        Treats a missing config as an empty dict. Builds a provider config
        with tool interop metadata and the effective ``config["tools"]``
        compatibility shim, then runs provider.init and feature.init.
        """
        base_config: Dict[str, Any] = dict(config) if isinstance(config, dict) else {}
        current_tags = list(tags or [])
        current_models = list(models or [])

        tool_init_config = self._build_tool_init_config(
            base_config,
            provider=provider,
            extensions=provider._iter_extensions(),
        )
        (
            available_tools,
            _provider,
            _extensions,
            _tool_states,
            _tool_interop_registry,
            tool_schema_target_formats,
        ) = self._get_available_tools_for_config(tool_init_config)
        include_tools_key = (
            "tools" in base_config or bool(available_tools) or bool(tools)
        )
        prepared_tools = self._prepare_tools_for_request(
            config=base_config,
            provider=provider,
            extensions=provider._iter_extensions(),
            features=features,
            tools=tools,
            tags=current_tags,
            models=current_models,
            available_tools=available_tools,
            request_id=request_id,
        )
        prepared_schemas = [descriptor.schema for descriptor in prepared_tools]
        provider_config = {
            **base_config,
            **(
                {"_tool_schema_target_formats": tool_schema_target_formats}
                if tool_schema_target_formats
                else {}
            ),
            **({"tools": prepared_schemas} if include_tools_key else {}),
        }

        state = provider.init(provider_config)
        sorted_features = sorted(
            features, key=lambda feat: getattr(feat, "priority", 100)
        )
        for feature in sorted_features:
            state = feature.init(provider_config, state)
            provider.set_state(state)
        provider.set_state(state)
        return provider_config, state

    def _core_messages_to_native_for_config(
        self,
        core_messages: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Convert core messages to provider-native messages for this config."""
        provider, enabled_extensions, features, tools, _tags = (
            self._resolve_plugins_for_config(config)
        )
        features = sorted(features, key=lambda feat: getattr(feat, "priority", 100))
        provider.set_active_extensions(enabled_extensions)
        _provider_config, state = self._init_provider_and_features_for_config(
            provider,
            features,
            tools,
            config,
        )

        native_messages = provider.to_native_messages(core_messages, state)
        native_messages = provider.apply_extension_transforms(
            core_messages, native_messages
        )
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
        *,
        skip_initialize: bool = False,
    ) -> Tuple[List[Message], List[Dict[str, Any]]]:
        """Rebuild full core messages from provider-native history.

        Uses the same provider, extensions, features, and tools that would
        be active for a normal request with this config, but skips
        core-to-native conversion and starts from the given native history.

        Note: any per-message metadata that should survive this rebuild must
        be persisted into the provider-native message dicts under the
        ``_metadata`` key and reconstructed by the provider/extensions/
        features in ``from_native_messages``.

        Args:
            native_messages: Provider-native message dicts to rebuild from.
            config: Configuration used to resolve provider and plugins.
            skip_initialize: When True, skip calling ``initialize_request``
                on provider and features. This should be used for internal
                session operations (slice, join, insert) that should not
                trigger request-preparation logic that might add or modify
                messages (e.g., SystemMessageFeature adding a system message).
                When False (default), the full request pipeline runs.

        Returns:
            Tuple of (core_messages, native_messages).
            When skip_initialize=False, native_messages is the state after
            initialize_request pipeline (may differ from input).
            When skip_initialize=True, native_messages is unchanged from input.
        """
        (
            provider,
            enabled_extensions,
            features,
            tools,
            _tags,
        ) = self._resolve_plugins_for_config(config)

        features = sorted(features, key=lambda feat: getattr(feat, "priority", 100))
        provider.set_active_extensions(enabled_extensions)

        _provider_config, state = self._init_provider_and_features_for_config(
            provider,
            features,
            tools,
            config,
        )
        request_context = self._build_plugin_context(
            config=_provider_config,
            provider=provider,
            enabled_extensions=enabled_extensions,
            enabled_features=features,
            enabled_tools=tools,
            tags=_tags,
            models=self._get_models_for_config(provider, config),
            available_tools=self.get_available_tools(config),
            tools=self._get_prepared_tools_for_config(config),
        )

        # Initialize request chains using the adjusted native history.
        # Skip this for internal session operations to avoid features like
        # SystemMessageFeature adding synthetic messages during split/join.
        if not skip_initialize:
            native_messages, state = provider.initialize_request(
                native_messages,
                state,
                context=request_context,
            )
            for feature in features:
                native_messages, state = feature.initialize_request(
                    native_messages,
                    state,
                    context=request_context,
                )
                provider.set_state(state)

        # Convert native messages back into core messages through the full
        # from-native pipeline.
        core_from_provider = provider.from_native_messages(native_messages, state)
        # Apply extension and feature from-native transforms (iterate to pass state to each)
        for ext in enabled_extensions:
            core_from_provider = ext.from_native_messages(
                native_messages, core_from_provider, state
            )
        for feature in features:
            core_from_provider = feature.from_native_messages(
                native_messages, core_from_provider, state
            )

        normalized_core = self._normalize_final_core_with_native_indices(
            core_from_provider,
            native_messages,
            baseline_offset=0,
        )
        return [Message.from_dict(m) for m in normalized_core], native_messages

    def _pre_request(
        self,
        session: Session,
        config: Dict[str, Any],
        provider: ProviderWrapper,
        features: List[FeatureWrapper],
        tools: List[ToolWrapper],
        *,
        request_id: str | None = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], bool]:
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
            A tuple of (messages, native_messages, state, native_history_changed):
            - messages: Core message dicts for the session.
            - native_messages: Provider-native full history (either retained or reconstructed).
            - state: Shared provider state after init/update/initialize_request for features as well.
            - native_history_changed: Whether request initialization replaced the native
              message array object, signaling a structural native-history change.
        """
        _provider_config, state = self._init_provider_and_features_for_config(
            provider,
            features,
            tools,
            config,
            tags=tags,
            models=models,
            request_id=request_id,
        )
        features = sorted(features, key=lambda feat: getattr(feat, "priority", 100))
        available_tools = self.get_available_tools(config)
        effective_tools = self._get_prepared_tools_for_config(config)
        request_context = self._build_plugin_context(
            config=_provider_config,
            provider=provider,
            enabled_extensions=provider._iter_extensions(),
            enabled_features=features,
            enabled_tools=tools,
            tags=list(tags or []),
            models=list(models or []),
            available_tools=available_tools,
            tools=effective_tools,
            request_id=request_id,
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
            # Reuse retained provider-native history as-is as the starting
            # point for this request. Extensions such as the OpenRouter
            # reasoning extension are responsible for treating provider-
            # native metadata as opaque and preserving it across turns.
            native_messages = list(retained_native)
        else:
            # Provider-first conversion (native_base for stateless transforms)
            native_messages = provider.to_native_messages(messages, state)
            # Apply stateless transforms from provider extensions.
            native_messages = provider.apply_extension_transforms(
                messages, native_messages
            )

        # In both cases, apply feature-level stateless transforms so that
        # structural features (such as SystemMessageFeature) can ensure that
        # template-level system messages or other adjustments are reflected
        # in the provider-native history used for this request.
        pipe = pipeline(messages)
        native_messages = pipe(
            [feature.to_native_messages for feature in features],
            native_messages,
        )

        # Initialize request chains
        native_history_changed = False

        next_native_messages, state = provider.initialize_request(
            native_messages,
            state,
            request_id=request_id,
            context=request_context,
        )
        if next_native_messages == native_messages:
            next_native_messages = native_messages
        native_history_changed = native_history_changed or (
            next_native_messages is not native_messages
        )
        native_messages = next_native_messages
        # Sort features by priority (lower numbers run first, default: 100)
        sorted_features = sorted(
            features, key=lambda feat: getattr(feat, "priority", 100)
        )
        for feature in sorted_features:
            next_native_messages, state = feature.initialize_request(
                native_messages,
                state,
                context=request_context,
            )
            if next_native_messages == native_messages:
                next_native_messages = native_messages
            native_history_changed = native_history_changed or (
                next_native_messages is not native_messages
            )
            native_messages = next_native_messages
            provider.set_state(state)

        try:
            native_preview = str(native_messages)
            if len(native_preview) > 2000:
                native_preview = native_preview[:2000] + "...<truncated>"
        except Exception:  # pragma: no cover - defensive
            native_preview = "<unprintable>"

        # logger.info(
        #     "request init complete",
        #     request=state.get("request"),
        #     native_messages=native_preview,
        # )

        return messages, native_messages, state, native_history_changed

    def send_request(
        self,
        session: Session,
        config: Dict[str, Any],
        *,
        request_id: str | None = None,
        cancellation: Any | None = None,
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
                )
            )
            baseline_native_len = len(native_messages)
            request_context = self._build_plugin_context(
                config=state.get("config") or config,
                provider=provider,
                enabled_extensions=provider._iter_extensions(),
                enabled_features=features,
                enabled_tools=tools,
                tags=_tags,
                models=self._get_models_for_config(provider, config),
                available_tools=self.get_available_tools(config),
                tools=self._get_prepared_tools_for_config(config),
                request_id=request_id,
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
        final_core = provider.from_native_messages(final_native, state)
        # Apply extension and feature from-native transforms (iterate to pass state to each)
        for ext in enabled_extensions:
            final_core = ext.from_native_messages(final_native, final_core, state)
        for feature in features:
            final_core = feature.from_native_messages(final_native, final_core, state)

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
            )
        )

        # Build new session messages by appending new Message objects
        new_metadata = dict(session.metadata)
        if response_metadata_patch:
            new_metadata.update(response_metadata_patch)
        # Persist full provider-native history for the turn (implementation detail)
        new_metadata["native_messages"] = native_messages
        if native_history_changed:
            all_messages_after, _ = self._rebuild_core_from_native(
                native_messages, config
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

    def send_request_stream(
        self,
        session: Session,
        config: Dict[str, Any],
        *,
        request_id: str | None = None,
        cancellation: Any | None = None,
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
                )
            )
            baseline_native_len = len(native_messages)
            request_context = self._build_plugin_context(
                config=state.get("config") or config,
                provider=provider,
                enabled_extensions=provider._iter_extensions(),
                enabled_features=features,
                enabled_tools=tools,
                tags=_tags,
                models=self._get_models_for_config(provider, config),
                available_tools=self.get_available_tools(config),
                tools=self._get_prepared_tools_for_config(config),
                request_id=request_id,
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

        # Feature finalize chain (native)
        for feature in features:
            final_native, native_messages, state = feature.finalize(
                final_native,
                native_messages,
                state,
                context=request_context,
            )

        logger.debug("streaming complete", final_native=final_native)

        combined_native_finals = [*aggregated_native_finals, *final_native]

        # Convert provider-native finals to core messages
        final_core = provider.from_native_messages(combined_native_finals, state)

        # Apply extension and feature from-native transforms (iterate to pass state to each)
        for ext in enabled_extensions:
            final_core = ext.from_native_messages(
                combined_native_finals, final_core, state
            )
        for feature in features:
            final_core = feature.from_native_messages(
                combined_native_finals, final_core, state
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
            )
        )

        new_metadata = dict(session.metadata)
        if response_metadata_patch:
            new_metadata.update(response_metadata_patch)
        new_metadata["native_messages"] = native_messages
        if native_history_changed:
            # Rebuild core from the post-initialize native (after structural changes)
            all_messages_after, _ = self._rebuild_core_from_native(
                native_messages, config
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

    async def send_request_stream_async(
        self,
        session: Session,
        config: Dict[str, Any],
        *,
        request_id: str | None = None,
        cancellation: Any | None = None,
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
                )
            )
            baseline_native_len = len(native_messages)
            request_context = self._build_plugin_context(
                config=state.get("config") or config,
                provider=provider,
                enabled_extensions=provider._iter_extensions(),
                enabled_features=features,
                enabled_tools=tools,
                tags=_tags,
                models=self._get_models_for_config(provider, config),
                available_tools=self.get_available_tools(config),
                tools=self._get_prepared_tools_for_config(config),
                request_id=request_id,
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

        # Feature finalize chain (native)
        for feature in features:
            final_native, native_messages, state = feature.finalize(
                final_native,
                native_messages,
                state,
                context=request_context,
            )

        combined_native_finals = [*aggregated_native_finals, *final_native]

        # Convert provider-native finals to core messages
        final_core = provider.from_native_messages(combined_native_finals, state)

        # Apply extension and feature from-native transforms (iterate to pass state to each)
        for ext in enabled_extensions:
            final_core = ext.from_native_messages(
                combined_native_finals, final_core, state
            )
        for feature in features:
            final_core = feature.from_native_messages(
                combined_native_finals, final_core, state
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
            )
        )

        new_metadata = dict(session.metadata)
        if response_metadata_patch:
            new_metadata.update(response_metadata_patch)
        new_metadata["native_messages"] = native_messages
        if native_history_changed:
            # Rebuild core from the post-initialize native (after structural changes)
            all_messages_after, _ = self._rebuild_core_from_native(
                native_messages, config
            )
        else:
            appended: List[Message] = [Message.from_dict(m) for m in final_core]
            all_messages_after = [*session.messages, *appended]
        new_metadata["native_messages_integrity"] = self._compute_native_integrity(
            all_messages_after
        )
        new_session = Session(session.session_id, all_messages_after, new_metadata)

        yield {"type": "final", "session": new_session, "messages": final_core}

    def get_config_schema(self) -> List[Dict[str, Any]]:
        """Get flattened config schema from all registered plugins.

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

    def get_ui_schema(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get flattened UI schema for the effective config.

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

    class _SessionActionValidationError(Exception):
        """Internal exception used for provider-extension session actions."""

        def __init__(
            self, message: str, details: Optional[Dict[str, Any]] = None
        ) -> None:
            super().__init__(message)
            self.details: Dict[str, Any] = details or {}

    @staticmethod
    def _session_action_param_type_matches(value: Any, expected_type: str) -> bool:
        if expected_type == "string":
            return isinstance(value, str)
        if expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "number":
            return (
                isinstance(value, int) and not isinstance(value, bool)
            ) or isinstance(value, float)
        if expected_type == "boolean":
            return isinstance(value, bool)
        return True

    def _validate_session_action_inputs(
        self,
        action_def: Dict[str, Any],
        inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        schema_raw = action_def.get("inputs") or {}
        schema = schema_raw if isinstance(schema_raw, dict) else {}
        validated: Dict[str, Any] = {}
        missing: List[str] = []
        invalid_types: Dict[str, Dict[str, str]] = {}

        for name, raw_spec in schema.items():
            if not isinstance(name, str) or not name:
                continue
            spec = raw_spec if isinstance(raw_spec, dict) else {}
            required = bool(spec.get("required", False))
            param_type = spec.get("type")

            has_value = name in inputs
            value = inputs.get(name)

            if not has_value or value is None:
                if "default" in spec:
                    validated[name] = spec["default"]
                elif required:
                    missing.append(name)
                continue

            if isinstance(param_type, str):
                if not self._session_action_param_type_matches(value, param_type):
                    invalid_types[name] = {
                        "expected": param_type,
                        "actual_type": type(value).__name__,
                    }
                else:
                    validated[name] = value
            else:
                validated[name] = value

        extra = [name for name in inputs.keys() if name not in schema]
        if missing or invalid_types or extra:
            details: Dict[str, Any] = {}
            if missing:
                details["missing_params"] = missing
            if invalid_types:
                details["invalid_types"] = invalid_types
            if extra:
                details["extra_params"] = extra
            raise self._SessionActionValidationError(
                "action input validation failed",
                details,
            )

        return validated

    def get_session_actions(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return session-scoped extension and feature actions for the config."""

        if not isinstance(config, dict):
            raise TypeError("config must be a dict")
        if not self._providers:
            return []

        _provider, _features, _state, actions = (
            self._get_core_session_actions_and_state(config)
        )
        return actions

    def _find_session_action_definition(
        self,
        actions: List[Dict[str, Any]],
        plugin_id: str,
        action_id: str,
    ) -> Optional[Dict[str, Any]]:
        for action in actions:
            if not isinstance(action, dict):
                continue
            if action.get("plugin") == plugin_id and action.get("id") == action_id:
                return action
        return None

    def _native_messages_for_session_action(
        self,
        session: Session,
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        retained_native = None
        if isinstance(session.metadata, dict):
            retained_native = session.metadata.get("native_messages")

        if isinstance(retained_native, list):
            try:
                self._verify_native_integrity(session)
                return list(retained_native)
            except Exception:
                pass

        core_messages = [message.to_dict() for message in session.messages]
        return self._core_messages_to_native_for_config(core_messages, config)

    @staticmethod
    def _action_matches_trigger(action: Dict[str, Any], trigger: str) -> bool:
        trigger_val = action.get("trigger")
        if isinstance(trigger_val, str):
            return trigger_val == trigger
        if isinstance(trigger_val, list):
            return any(
                isinstance(item, str) and item == trigger for item in trigger_val
            )
        return False

    def _get_core_session_actions_and_state(
        self,
        config: Dict[str, Any],
    ) -> Tuple[Any, List[Any], Dict[str, Any], List[Dict[str, Any]]]:
        provider, enabled_extensions, features, tools, _tags = (
            self._resolve_plugins_for_config(config)
        )
        features = sorted(features, key=lambda feat: getattr(feat, "priority", 100))
        provider.set_active_extensions(enabled_extensions)
        _provider_config, state = self._init_provider_and_features_for_config(
            provider,
            features,
            tools,
            config,
        )

        actions = self._collect_core_session_actions(provider, features, state)

        return provider, features, state, actions

    def initialize_action_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        request_runtime: Dict[str, Any],
        request_context: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Apply request-time initialization to session-action inputs.

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

    def _collect_core_session_actions(
        self,
        provider: Any,
        features: List[Any],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []

        for plugin_id, raw_actions in provider.get_extension_actions(state).items():
            for raw_action in raw_actions:
                if not isinstance(raw_action, dict):
                    continue
                action = dict(raw_action)
                action.setdefault("plugin", plugin_id)
                action.setdefault("action_owner", "provider_extension")
                actions.append(action)

        for feature in features:
            for raw_action in feature.get_actions(state):
                if not isinstance(raw_action, dict):
                    continue
                action = dict(raw_action)
                action.setdefault("plugin", feature.name)
                action.setdefault("action_owner", "feature")
                actions.append(action)

        return actions

    def _apply_session_action_result(
        self,
        session: Session,
        config: Dict[str, Any],
        result: Dict[str, Any],
    ) -> Tuple[Session, Dict[str, Any]]:
        raw_native = result.get("native_messages")
        if not isinstance(raw_native, list) or not all(
            isinstance(item, dict) for item in raw_native
        ):
            raise RuntimeError(
                "session action must return full native_messages as a list of dicts"
            )
        new_native_messages = [item for item in raw_native if isinstance(item, dict)]

        metadata_patch_raw = result.get("session_metadata")
        metadata_patch = (
            metadata_patch_raw if isinstance(metadata_patch_raw, dict) else {}
        )

        new_metadata = (
            dict(session.metadata) if isinstance(session.metadata, dict) else {}
        )
        new_metadata.update(metadata_patch)

        rebuild_config = dict(config)
        overrides = new_metadata.get("overrides")
        if isinstance(overrides, dict):
            rebuild_config.update(overrides)

        # Rebuild and get post-initialize native to ensure features' structural changes are captured
        new_messages, post_init_native = self._rebuild_core_from_native(
            new_native_messages, rebuild_config
        )

        new_metadata["native_messages"] = post_init_native
        new_metadata["native_messages_integrity"] = self._compute_native_integrity(
            new_messages
        )

        public_result = {
            key: value
            for key, value in result.items()
            if key
            not in {
                "native_messages",
                "session_metadata",
                "rebuild_messages_from_native",
            }
        }

        return (
            Session(
                session_id=session.session_id,
                messages=new_messages,
                metadata=new_metadata,
            ),
            public_result,
        )

    def execute_session_action(
        self,
        session: Session,
        config: Dict[str, Any],
        plugin_id: str,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Session, Dict[str, Any]]:
        """Execute a generic session-scoped extension or feature action."""

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

        # Layer 1: Core-level context enrichment.
        # Higher layers (application, terminal) may have already set these;
        # use setdefault so we never overwrite a richer value.
        enriched_context: Dict[str, Any] = (
            dict(context) if isinstance(context, dict) else {}
        )
        enriched_context.setdefault("core", self)
        enriched_context.setdefault("config", config)
        enriched_context.setdefault("trigger_source", "core")
        enriched_context.setdefault("session", session.to_dict())
        request_context = self._build_plugin_context(
            config=state.get("config") or config,
            provider=provider,
            enabled_extensions=provider._iter_extensions(),
            enabled_features=features,
            enabled_tools=[],
            tags=[],
            models=self._get_models_for_config(provider, config),
            available_tools=self.get_available_tools(config),
            tools=self._get_prepared_tools_for_config(config),
        )
        request_context.update(enriched_context)
        enriched_context["request_context"] = request_context
        enriched_context["request_runtime"] = {
            "provider": provider,
            "features": list(features),
        }

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
        return self._apply_session_action_result(session, config, result)

    def execute_lifecycle_actions(
        self,
        session: Session,
        config: Dict[str, Any],
        trigger: str,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Session, List[Dict[str, Any]]]:
        """Execute all extension/feature actions whose trigger matches ``trigger``."""

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

            # Layer 1: Core-level context enrichment.
            # Higher layers (application, terminal) may have already set these;
            # use setdefault so we never overwrite a richer value.
            enriched_context: Dict[str, Any] = (
                dict(context) if isinstance(context, dict) else {}
            )
            enriched_context.setdefault("core", self)
            enriched_context.setdefault("config", config)
            enriched_context.setdefault("trigger_source", "core")
            enriched_context.setdefault("lifecycle", trigger)
            enriched_context.setdefault("session", current_session.to_dict())

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

    def execute_response_lifecycle_actions(
        self,
        session: Session,
        config: Dict[str, Any],
        trigger: str,
        *,
        provider: Any,
        features: List[Any],
        state: Dict[str, Any],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        native_final_messages: List[Dict[str, Any]],
        stream: bool,
        turn_native_start_index: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]
    ]:
        """Execute core-owned response lifecycles before finals are emitted."""

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
            enriched_context: Dict[str, Any] = (
                dict(context) if isinstance(context, dict) else {}
            )
            enriched_context["core"] = self
            enriched_context["config"] = config
            enriched_context["trigger_source"] = "core"
            enriched_context["lifecycle"] = trigger
            enriched_context["session"] = session.to_dict()
            enriched_context["final_messages"] = current_final_messages
            enriched_context["native_final_messages"] = [
                msg for msg in native_final_messages if isinstance(msg, dict)
            ]
            enriched_context["native_messages"] = current_native_messages
            enriched_context["stream"] = bool(stream)
            enriched_context["turn_native_start_index"] = turn_native_start_index

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

    def get_completions(
        self, config: Dict[str, Any], text: str
    ) -> List[Dict[str, Any]]:
        """Collect completion suggestions from registered feature plugins.

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

    def apply_feature_completion(
        self,
        config: Dict[str, Any],
        text: str,
        completion: Dict[str, Any],
    ) -> str:
        """Ask features to transform an accepted completion into a snippet.

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

    def get_tool_schemas(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get the effective tool schemas for a config after feature policy."""
        return [
            descriptor.schema
            for descriptor in self._get_prepared_tools_for_config(config)
        ]

    def get_available_tools(self, config: Dict[str, Any]) -> List[ToolDescriptor]:
        """Get the full available tool catalog for a config before filtering."""
        return self._get_available_tools_for_config(config)[0]

    def _tool_descriptor_from_schema(
        self,
        tool: ToolWrapper | str,
        schema: Dict[str, Any],
        registry: Any,
        *,
        index: int,
    ) -> ToolDescriptor:
        plugin_name = tool.name if isinstance(tool, ToolWrapper) else tool
        tool_name = plugin_name
        metadata: Dict[str, Any] = {"schema_index": index}
        try:
            inspected = registry.inspect_schema(schema)
            if isinstance(inspected.tool_name, str) and inspected.tool_name:
                tool_name = inspected.tool_name
            if inspected.format_id:
                metadata["format_id"] = inspected.format_id
            if inspected.tool_type:
                metadata["tool_type"] = inspected.tool_type
            if inspected.tool_kind:
                metadata["tool_kind"] = inspected.tool_kind
            if inspected.description:
                metadata["description"] = inspected.description
        except Exception:
            pass
        return ToolDescriptor(
            plugin_name=plugin_name,
            tool_name=tool_name,
            schema=schema,
            metadata=metadata,
        )

    def _get_available_tools_for_config(
        self,
        config: Dict[str, Any],
    ) -> Tuple[
        List[ToolDescriptor],
        Optional[ProviderWrapper],
        List[ExtensionWrapper],
        List[_PreparedToolState],
        Any,
        List[str],
    ]:
        provider, extensions, tool_states = self._get_enabled_tool_states_for_config(
            config
        )
        registry = self._get_tool_interop_registry_for_config(
            config,
            provider=provider,
            extensions=extensions,
            tool_states=tool_states,
        )
        target_formats = self._get_tool_schema_target_formats_for_config(
            config,
            provider=provider,
            extensions=extensions,
        )
        descriptors: List[ToolDescriptor] = []
        for tool, state, prepared in tool_states:
            for index, schema in enumerate(
                tool.get_tool_schemas(state, prepared=prepared)
            ):
                if not isinstance(schema, dict):
                    continue
                descriptors.append(
                    self._tool_descriptor_from_schema(
                        tool, schema, registry, index=index
                    )
                )
        explicit_tools = config.get("tools") if isinstance(config, dict) else None
        if isinstance(explicit_tools, list):
            for index, schema in enumerate(explicit_tools):
                if not isinstance(schema, dict):
                    continue
                descriptor = self._tool_descriptor_from_schema(
                    "config",
                    schema,
                    registry,
                    index=index,
                )
                descriptors.append(
                    ToolDescriptor(
                        plugin_name="config",
                        tool_name=descriptor.tool_name,
                        schema=schema,
                        metadata={**descriptor.metadata, "source": "config"},
                    )
                )
        return descriptors, provider, extensions, tool_states, registry, target_formats

    def _prepare_tools_for_request(
        self,
        *,
        config: Dict[str, Any],
        provider: Optional[ProviderWrapper],
        extensions: List[ExtensionWrapper],
        features: List[FeatureWrapper],
        tools: List[ToolWrapper],
        tags: List[str],
        models: List[Dict[str, Any]],
        available_tools: Optional[List[ToolDescriptor]] = None,
        request_id: str | None = None,
    ) -> List[ToolDescriptor]:
        catalog = (
            list(available_tools)
            if isinstance(available_tools, list)
            else list(self._get_available_tools_for_config(config)[0])
        )
        effective_tools = list(catalog)
        for feature in sorted(
            features, key=lambda feat: getattr(feat, "priority", 100)
        ):
            prepare_context = self._build_plugin_context(
                config=config,
                provider=provider,
                enabled_extensions=extensions,
                enabled_features=features,
                enabled_tools=tools,
                tags=tags,
                models=models,
                available_tools=catalog,
                tools=effective_tools,
                request_id=request_id,
            )
            effective_tools = feature.prepare_tools(
                config,
                effective_tools,
                prepare_context,
            )
        return effective_tools

    def _get_prepared_tools_for_config(
        self,
        config: Dict[str, Any],
    ) -> List[ToolDescriptor]:
        explicit_tools = config.get("tools") if isinstance(config, dict) else None
        if not self._tools and not isinstance(explicit_tools, list):
            return []

        models: List[Dict[str, Any]] = []
        provider: Optional[ProviderWrapper] = None
        enabled_extensions: List[ExtensionWrapper] = []
        features: List[FeatureWrapper] = []
        tags: List[str] = []

        if self._providers:
            provider, enabled_extensions, features, tools, tags = (
                self._resolve_plugins_for_config(config)
            )
            provider.set_active_extensions(enabled_extensions)
            models = self._get_models_for_config(provider, config)
            base_config = dict(config) if isinstance(config, dict) else {}
            tool_config = self._build_tool_init_config(
                base_config,
                provider=provider,
                extensions=enabled_extensions,
            )
            available_tools = self._get_available_tools_for_config(tool_config)[0]
            return self._prepare_tools_for_request(
                config=base_config,
                provider=provider,
                extensions=enabled_extensions,
                features=features,
                tools=tools,
                tags=tags,
                models=models,
                available_tools=available_tools,
            )

        (
            available_tools,
            _provider,
            _extensions,
            _tool_states,
            _registry,
            _target_formats,
        ) = self._get_available_tools_for_config(config)
        features = sorted(
            self._features, key=lambda feat: getattr(feat, "priority", 100)
        )
        if not features:
            return available_tools
        return self._prepare_tools_for_request(
            config=dict(config) if isinstance(config, dict) else {},
            provider=None,
            extensions=[],
            features=features,
            tools=list(self._tools),
            tags=[],
            models=[],
            available_tools=available_tools,
        )

    def _resolve_tool_participants_for_config(
        self,
        config: Dict[str, Any],
    ) -> Tuple[Optional[ProviderWrapper], List[ExtensionWrapper], List[ToolWrapper]]:
        if not self._providers:
            return None, [], list(self._tools)
        try:
            provider, exts, _features, tools, _tags = self._resolve_plugins_for_config(
                config
            )
            if not self._tools:
                return provider, list(exts), []
            return provider, list(exts), list(tools)
        except Exception:
            return None, [], list(self._tools)

    def _get_enabled_tool_states_for_config(
        self,
        config: Dict[str, Any],
    ) -> Tuple[
        Optional[ProviderWrapper],
        List[ExtensionWrapper],
        List[_PreparedToolState],
    ]:
        provider, extensions, enabled_tools = (
            self._resolve_tool_participants_for_config(config)
        )
        tool_init_config = self._build_tool_init_config(
            config,
            provider=provider,
            extensions=extensions,
        )
        tool_states: List[_PreparedToolState] = []
        for tool in enabled_tools:
            cache_key = self._tool_prepare_cache_key(tool, tool_init_config)
            state = self._prepared_tool_states.get(cache_key)
            if not isinstance(state, dict):
                state = tool.init(tool_init_config)
            tool_states.append(
                (tool, state, self._prepared_tool_data.get(cache_key))
            )
        return (
            provider,
            extensions,
            tool_states,
        )

    def _build_tool_init_config(
        self,
        config: Dict[str, Any],
        *,
        provider: Optional[ProviderWrapper] = None,
        extensions: Optional[List[ExtensionWrapper]] = None,
    ) -> Dict[str, Any]:
        base_config = dict(config) if isinstance(config, dict) else {}
        local_provider = provider
        local_extensions = list(extensions or [])

        if local_provider is None and extensions is None and self._providers:
            try:
                local_provider, local_extensions, _tools = (
                    self._resolve_tool_participants_for_config(base_config)
                )
            except Exception:
                local_provider, local_extensions = None, []

        if local_provider is None and not local_extensions:
            return base_config

        tool_schema_target_formats = self._get_tool_schema_target_formats_for_config(
            base_config,
            provider=local_provider,
            extensions=local_extensions,
        )
        tool_config = dict(base_config)
        if tool_schema_target_formats:
            tool_config["_tool_schema_target_formats"] = tool_schema_target_formats
        return tool_config

    def _normalize_tool_prepare_config(self, config: Dict[str, Any]) -> str:
        sanitized = dict(config) if isinstance(config, dict) else {}
        return self._normalize_config(sanitized)

    def _tool_prepare_cache_key(
        self,
        tool: ToolWrapper,
        tool_init_config: Dict[str, Any],
    ) -> Tuple[int, str]:
        return (id(tool), self._normalize_tool_prepare_config(tool_init_config))

    def _build_tool_runtime_context(
        self,
        config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        enriched = dict(context) if isinstance(context, dict) else {}
        enriched.setdefault("core", self)
        enriched.setdefault("config", config)
        enriched.setdefault("trigger_source", "core")
        return enriched

    def prepare_tools(
        self,
        config: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        provider, extensions, enabled_tools = self._resolve_tool_participants_for_config(
            config
        )
        tool_init_config = self._build_tool_init_config(
            config,
            provider=provider,
            extensions=extensions,
        )
        tool_context = self._build_tool_runtime_context(tool_init_config, context)
        for tool in enabled_tools:
            cache_key = self._tool_prepare_cache_key(tool, tool_init_config)
            if cache_key in self._prepared_tool_states and cache_key in self._prepared_tool_data:
                continue
            state = self._prepared_tool_states.get(cache_key)
            if not isinstance(state, dict):
                state = tool.init(tool_init_config)
            prepared = tool.prepare(
                tool_init_config,
                state,
                context=tool_context,
            )
            self._prepared_tool_states[cache_key] = state
            self._prepared_tool_data[cache_key] = (
                prepared if isinstance(prepared, dict) else {}
            )

    async def prepare_tools_async(
        self,
        config: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        provider, extensions, enabled_tools = self._resolve_tool_participants_for_config(
            config
        )
        tool_init_config = self._build_tool_init_config(
            config,
            provider=provider,
            extensions=extensions,
        )
        tool_context = self._build_tool_runtime_context(tool_init_config, context)
        for tool in enabled_tools:
            cache_key = self._tool_prepare_cache_key(tool, tool_init_config)
            if cache_key in self._prepared_tool_states and cache_key in self._prepared_tool_data:
                continue
            state = self._prepared_tool_states.get(cache_key)
            if not isinstance(state, dict):
                state = tool.init(tool_init_config)
            prepared = await tool.prepare_async(
                tool_init_config,
                state,
                context=tool_context,
            )
            self._prepared_tool_states[cache_key] = state
            self._prepared_tool_data[cache_key] = (
                prepared if isinstance(prepared, dict) else {}
            )

    def _get_explicit_tool_interop_contributions(
        self,
        config: Dict[str, Any],
    ) -> List[Any]:
        from .tool_interop import ToolInteropContribution

        raw_single = config.get("tool_interop")
        raw_many = config.get("tool_interop_contributions")
        contributions: List[Any] = []
        if raw_single is not None:
            contributions.append(raw_single)
        if isinstance(raw_many, list):
            contributions.extend(raw_many)
        return [
            item for item in contributions if isinstance(item, ToolInteropContribution)
        ]

    def _get_tool_interop_registry_for_config(
        self,
        config: Dict[str, Any],
        *,
        provider: Optional[ProviderWrapper] = None,
        extensions: Optional[List[ExtensionWrapper]] = None,
        tool_states: Optional[List[_PreparedToolState]] = None,
    ) -> Any:
        from .tool_interop import compose_tool_interop_registry

        local_provider = provider
        local_extensions = extensions or []
        local_tool_states = tool_states or []
        if local_provider is None and not local_extensions and not local_tool_states:
            local_provider, local_extensions, local_tool_states = (
                self._get_enabled_tool_states_for_config(config)
            )

        contributions: List[Any] = []
        if local_provider is not None:
            contributions.append(
                local_provider.get_tool_interop_contribution(config, None)
            )
        for extension in local_extensions:
            contributions.append(extension.get_tool_interop_contribution(config, None))
        for tool, state, _prepared in local_tool_states:
            contributions.append(tool.get_tool_interop_contribution(state))

        return compose_tool_interop_registry(
            explicit=self._get_explicit_tool_interop_contributions(config),
            contributed=contributions,
        )

    def _get_tool_schema_target_formats_for_config(
        self,
        config: Dict[str, Any],
        *,
        provider: Optional[ProviderWrapper] = None,
        extensions: Optional[List[ExtensionWrapper]] = None,
    ) -> List[str]:
        local_provider = provider
        local_extensions = extensions
        if local_provider is None and local_extensions is None:
            local_provider, local_extensions, _tool_states = (
                self._get_enabled_tool_states_for_config(config)
            )
        formats: List[str] = []
        if local_provider is not None:
            formats.extend(local_provider.accepted_tool_schema_formats(config, None))
        for extension in local_extensions or []:
            formats.extend(extension.accepted_tool_schema_formats(config, None))
        return [fmt for fmt in formats if isinstance(fmt, str) and fmt]

    def extract_tool_calls_from_messages(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extract tool-call dictionaries from assistant message metadata."""

        tool_calls: List[Dict[str, Any]] = []
        for msg in messages:
            if not isinstance(msg, dict) or msg.get("role") != "assistant":
                continue
            metadata = msg.get("metadata") or {}
            calls = metadata.get("tool_calls") or []
            if isinstance(calls, list):
                tool_calls.extend([call for call in calls if isinstance(call, dict)])
        return tool_calls

    def format_tool_call_preview(
        self,
        tool_call: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Return a preview record for a single tool call."""

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

    def format_tool_call_previews(
        self,
        tool_calls: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Return preview records for all supplied tool calls."""

        return [
            self.format_tool_call_preview(tool_call, config)
            for tool_call in tool_calls
            if isinstance(tool_call, dict)
        ]

    def patch_native_internal_metadata(
        self,
        native_messages: List[Dict[str, Any]],
        indices: List[int],
        patch: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Immutably merge ``patch`` into `_metadata` on selected native items."""

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

    def _build_name_to_tool_map(
        self,
        registry: Any,
        tool_states: List[_PreparedToolState],
    ) -> Dict[str, Tuple[ToolWrapper, Dict[str, Any], Optional[Dict[str, Any]], Dict[str, Any]]]:
        name_to_tool: Dict[
            str,
            Tuple[ToolWrapper, Dict[str, Any], Optional[Dict[str, Any]], Dict[str, Any]],
        ] = {}
        for tool, state, prepared in tool_states:
            try:
                schemas = tool.get_tool_schemas(state, prepared=prepared)
            except Exception:
                schemas = []
            for schema in schemas or []:
                if not isinstance(schema, dict):
                    continue
                try:
                    inspected_schema = registry.inspect_schema(schema)
                except Exception:
                    continue
                name = inspected_schema.tool_name
                if isinstance(name, str) and name and name not in name_to_tool:
                    name_to_tool[name] = (tool, state, prepared, schema)
        return name_to_tool

    def _resolve_tool_handler_for_call(
        self,
        inspected_call: Any,
        tool_states: List[_PreparedToolState],
        registry: Any,
    ) -> Tuple[
        Optional[ToolWrapper],
        Optional[Dict[str, Any]],
        Optional[Dict[str, Any]],
        Optional[Dict[str, Any]],
    ]:
        for tool, state, prepared in tool_states:
            try:
                decision = tool.can_handle_tool_call(
                    inspected_call.tool_name,
                    inspected_call.payload,
                    state,
                    payload_kind=inspected_call.payload_kind,
                    payload_format=inspected_call.payload_format,
                    payload_metadata=inspected_call.payload_metadata,
                    tool_call=inspected_call.raw,
                    tool_schema=None,
                    prepared=prepared,
                )
            except Exception:
                decision = None
            if decision is True:
                return tool, state, prepared, None

        if isinstance(inspected_call.tool_name, str) and inspected_call.tool_name:
            by_name = self._build_name_to_tool_map(registry, tool_states)
            matched = by_name.get(inspected_call.tool_name)
            if matched is not None:
                tool, state, prepared, schema = matched
                return tool, state, prepared, schema

        return None, None, None, None

    def iter_tool_messages(
        self,
        tool_calls: List[Dict[str, Any]],
        config: Dict[str, Any],
        *,
        cancellation: Any | None = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Yield a mixed stream of partial payloads and final core ``tool`` messages.

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

            display_payload: Dict[str, Any] | None = None
            try:
                display_candidate = tool.to_display_format(
                    formatted_content or "",
                    last_result,
                    state,
                )
                if isinstance(display_candidate, dict):
                    display_payload = display_candidate
            except Exception:
                display_payload = None

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

            yield {
                "role": "tool",
                "content": formatted_content or "",
                "metadata": metadata,
            }

    def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        config: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return only the final core ``tool`` message per tool call.

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

    def stream_tool_call(
        self,
        tool_call: Dict[str, Any],
        config: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Stream partial results for a single tool call.

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
                    0
                    if _normalize_identifier(getattr(obj, "name", "")) == module_basename
                    or _class_identifier(obj) == module_basename
                    else 1,
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
