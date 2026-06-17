"""Unit tests for AgentCore (functional architecture)."""

from typing import Any, Dict, List

import pytest
from agent_core import AgentCore, FeaturePlugin, Message, Session
from agent_core.types import ProviderPlugin
from .dummy_provider import DummyProvider
from .dummy_feature import DummyFeature
from .dummy_tool import DummyCalculator


def test_create_session():
    """Test session creation."""
    core = AgentCore()
    session = core.create_session()

    assert isinstance(session, Session)
    assert len(session.messages) == 0
    assert session.session_id is not None


def test_create_session_with_id():
    """Test session creation with specific ID."""
    core = AgentCore()
    session = core.create_session(session_id="my-session")

    assert session.session_id == "my-session"


def test_add_message():
    """Test adding message to session (functional)."""
    core = AgentCore()
    session = core.create_session()

    new_session = core.add_message(session, "user", "Hello!")

    # Original unchanged
    assert len(session.messages) == 0
    # New session has message
    assert len(new_session.messages) == 1
    assert new_session.messages[0].role == "user"
    assert new_session.messages[0].content == "Hello!"


def test_add_multiple_messages():
    """Test adding multiple messages (functional chaining)."""
    core = AgentCore()
    session = core.create_session()

    session = core.add_message(session, "system", "You are helpful")
    session = core.add_message(session, "user", "Hello")
    session = core.add_message(session, "assistant", "Hi there")

    assert len(session.messages) == 3
    assert session.messages[0].role == "system"
    assert session.messages[1].role == "user"
    assert session.messages[2].role == "assistant"


def test_add_message_with_metadata():
    """Test adding message with metadata."""
    core = AgentCore()
    session = core.create_session()

    session = core.add_message(session, "assistant", "Response", metadata={"model": "gpt-4"})

    assert session.messages[0].metadata
    assert session.messages[0].metadata["model"] == "gpt-4"


def test_get_config_schema_empty():
    """Test config schema with no plugins."""
    core = AgentCore()
    schema = core.get_config_schema()

    assert isinstance(schema, list)
    assert len(schema) == 0


def test_get_config_schema_with_plugins():
    """Test flattened config schema with registered plugins."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(DummyFeature)
    core.register_tool(DummyCalculator)

    schema = core.get_config_schema()

    assert isinstance(schema, list)

    # Top-level keys should appear as entries with a "key" field.
    keys = {entry.get("key") for entry in schema if isinstance(entry, dict)}
    assert "model" in keys
    assert "prefix" in keys

    # Each entry should include the contributing plugin name.
    providers = [
        entry.get("plugin")
        for entry in schema
        if isinstance(entry, dict) and entry.get("key") == "model"
    ]
    assert any(p in {"dummy_provider", "DummyProvider"} for p in providers)

    features = [
        entry.get("plugin")
        for entry in schema
        if isinstance(entry, dict) and entry.get("key") == "prefix"
    ]
    assert any(p in {"dummy_feature", "DummyFeature"} for p in features)


def test_get_ui_schema_empty():
    """Test UI schema with a provider that returns no UI elements."""
    class _EmptyUiProvider(DummyProvider):
        def get_ui_elements(self, config=None, tags=None, models=None):
            return []

    core = AgentCore()
    core.register_provider(_EmptyUiProvider)
    schema = core.get_ui_schema(config={})
    assert isinstance(schema, list)
    assert len(schema) == 0


def test_get_ui_schema_with_plugins():
    """Test UI schema with registered plugins and plugin annotation."""
    core = AgentCore()
    core.register_provider(DummyProvider)
    core.register_feature(DummyFeature)

    schema = core.get_ui_schema(config={})

    assert isinstance(schema, list)
    keys = {el.get("key") for el in schema if isinstance(el, dict)}
    # DummyProvider UI exposes the "model" field; DummyFeature exposes
    # the "prefix" field.
    assert "model" in keys
    assert "prefix" in keys
 



def test_get_tool_schemas():
    """Test getting tool schemas."""
    core = AgentCore()
    core.register_tool(DummyCalculator)

    config = {}
    schemas = core.get_tool_schemas(config)

    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "add"


class _DummyCompletionFeature(FeaturePlugin):
    name: str = "dummy_completion_feature"
    version: str = "1.0.0"

    def get_completions(self, config: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        # Echo back the input text in a simple replacement descriptor so
        # we can assert that AgentCore.get_completions delegates correctly.
        return [
            {
                "replacement": f"<{text}>",
                "start": 0,
                "display": "dummy",
                "display_meta": "test",
            }
        ]


def test_get_completions_from_features() -> None:
    core = AgentCore()
    core.register_feature(_DummyCompletionFeature)

    config: Dict[str, Any] = {}
    items = core.get_completions(config, "abc")

    assert isinstance(items, list)
    assert items
    first = items[0]
    assert first.get("replacement") == "<abc>"


def test_export_session():
    """Test session export."""
    core = AgentCore()
    session = core.create_session(session_id="test")
    session = core.add_message(session, "user", "Hello")

    exported = core.export_session(session)

    assert isinstance(exported, str)
    assert "test" in exported
    assert "Hello" in exported


def test_import_session():
    """Test session import."""
    core = AgentCore()
    session1 = core.create_session(session_id="test")
    session1 = core.add_message(session1, "user", "Hello")

    exported = core.export_session(session1)
    session2 = core.import_session(exported)

    assert session2.session_id == "test"
    assert len(session2.messages) == 1
    assert session2.messages[0].content == "Hello"


def test_export_import_session_roundtrips_multipart_content():
    core = AgentCore()
    session1 = core.create_session(session_id="test")
    session1 = core.add_message(
        session1,
        "user",
        "",
        multipart_content=[{"type": "image", "content": {"url": "data:..."}}],
    )

    exported = core.export_session(session1)
    session2 = core.import_session(exported)

    assert session2.session_id == "test"
    assert len(session2.messages) == 1
    assert session2.messages[0].multipart_content == [
        {"type": "image", "content": {"url": "data:..."}}
    ]


def test_send_request_without_provider():
    """Test error when sending request without provider."""
    core = AgentCore()
    session = core.create_session()
    config = {}

    with pytest.raises(RuntimeError, match="No provider registered"):
        core.send_request(session, config)


def test_discover_and_register_plugins():
    core = AgentCore()
    summary = core.discover_and_register(
        [
            "tests.dummy_provider",
            "tests.dummy_feature",
            "tests.dummy_tool",
            "tests.dummy_extension",
        ]
    )

    # At least provider discovered
    assert summary["providers"]
    assert summary["providers"] == ["dummy_provider"]

    # Run a basic streaming flow to ensure discovered registration works
    config = {"model": "test-model", "enabled": True}
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")

    final_message = None
    print("sending request")
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_message = chunk["messages"][-1]

    assert final_message is not None
    assert "Echo: Hello" in final_message["content"]
    # Extension may add metadata
    assert "metadata" in final_message


def test_normalize_final_core_infers_indices_for_1_to_1():
    core = AgentCore()
    final_core = [
        {"role": "assistant", "content": "a", "metadata": {}},
        {"role": "assistant", "content": "b"},
    ]
    finals_native = [
        {"role": "assistant", "content": "na"},
        {"role": "assistant", "content": "nb"},
    ]

    normalized = core._normalize_final_core_with_native_indices(
        final_core,
        finals_native,
        baseline_offset=3,
    )

    indices_lists = [m.get("metadata", {}).get("native_indices") for m in normalized]
    assert indices_lists == [[3], [4]]


def test_normalize_final_core_raises_on_mismatch_without_indices():
    core = AgentCore()
    final_core = [
        {"role": "assistant", "content": "a"},
        {"role": "assistant", "content": "b"},
    ]
    finals_native = [{"role": "assistant", "content": "only-native"}]

    with pytest.raises(RuntimeError):
        core._normalize_final_core_with_native_indices(
            final_core,
            finals_native,
            baseline_offset=0,
        )


def test_normalize_final_core_respects_existing_indices():
    core = AgentCore()
    final_core = [
        {
            "role": "assistant",
            "content": "grouped",
            "metadata": {"native_indices": [0, 2]},
        }
    ]
    finals_native = [
        {"role": "assistant", "content": "n0"},
        {"role": "assistant", "content": "n1"},
        {"role": "assistant", "content": "n2"},
    ]

    normalized = core._normalize_final_core_with_native_indices(
        final_core,
        finals_native,
        baseline_offset=10,
    )

    assert normalized[0]["metadata"]["native_indices"] == [10, 12]


def test_slice_drops_native_without_indices():
    core = AgentCore()
    core.register_provider(DummyProvider)
    config = {"model": "test"}

    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    session, _ = core.send_request(session, config)

    cleaned_messages = []
    for msg in session.messages:
        data = msg.to_dict()
        md = dict(data.get("metadata") or {})
        md.pop("native_indices", None)
        cleaned_messages.append(
            Message(
                role=data["role"],
                content=data["content"],
                metadata=md or None,
            )
        )

    legacy = Session(
        session_id=session.session_id,
        messages=cleaned_messages,
        metadata=dict(session.metadata),
    )

    assert "native_messages" in legacy.metadata
    assert all("native_indices" not in (m.metadata or {}) for m in legacy.messages)

    sliced = core.slice_session(legacy, config, remove_indices=[1])

    assert len(sliced.messages) == 1
    assert sliced.messages[0].content == "Hello"
    assert "native_messages" not in sliced.metadata
    assert "native_messages_integrity" not in sliced.metadata
    assert "native_indices" not in (sliced.messages[0].metadata or {})


def test_slice_preserves_native_with_indices_simple():
    core = AgentCore()
    core.register_provider(DummyProvider)
    config = {"model": "test"}

    native_messages = [
        {"role": "assistant", "content": "n0"},
        {"role": "assistant", "content": "n1"},
        {"role": "assistant", "content": "n2"},
    ]

    messages = [
        Message(role="assistant", content="m0", metadata={"native_indices": [0]}),
        Message(role="assistant", content="m1", metadata={"native_indices": [1]}),
        Message(role="assistant", content="m2", metadata={"native_indices": [2]}),
    ]

    session = Session(
        session_id="s-simple",
        messages=messages,
        metadata={
            "native_messages": native_messages,
            "native_messages_integrity": core._compute_native_integrity(messages),
        },
    )

    sliced = core.slice_session(session, config, start=0, end=2)

    new_native = sliced.metadata.get("native_messages")
    assert isinstance(new_native, list)
    assert [m["content"] for m in new_native] == ["n0", "n1"]

    assert len(sliced.messages) == len(new_native)
    indices_lists = [
        (msg.metadata or {}).get("native_indices") for msg in sliced.messages
    ]
    assert indices_lists == [[0], [1]]


def test_slice_forward_reverse_mapping_on_chain():
    core = AgentCore()
    core.register_provider(DummyProvider)
    config = {"model": "test"}

    native_messages = [
        {"role": "assistant", "content": "n0", "id": "n0"},
        {"role": "assistant", "content": "n1", "id": "n1"},
        {"role": "assistant", "content": "n2", "id": "n2"},
        {"role": "assistant", "content": "n3", "id": "n3"},
    ]

    messages = [
        Message(role="assistant", content="m0", metadata={"native_indices": [0, 1]}),
        Message(role="assistant", content="m1", metadata={"native_indices": [1, 2]}),
        Message(role="assistant", content="m2", metadata={"native_indices": [2, 3]}),
    ]

    session = Session(
        session_id="s-chain",
        messages=messages,
        metadata={
            "native_messages": native_messages,
            "native_messages_integrity": core._compute_native_integrity(messages),
        },
    )

    sliced = core.slice_session(session, config, remove_indices=[1])

    new_native = sliced.metadata.get("native_messages")
    assert isinstance(new_native, list)
    ids = [m.get("id") for m in new_native]
    assert ids == ["n0", "n3"]


def test_fork_session_convenience():
    core = AgentCore()
    core.register_provider(DummyProvider)
    config = {"model": "test"}

    native_messages = [
        {"role": "assistant", "content": "n0"},
        {"role": "assistant", "content": "n1"},
        {"role": "assistant", "content": "n2"},
    ]

    messages = [
        Message(role="assistant", content="m0", metadata={"native_indices": [0]}),
        Message(role="assistant", content="m1", metadata={"native_indices": [1]}),
        Message(role="assistant", content="m2", metadata={"native_indices": [2]}),
    ]

    session = Session(
        session_id="s-fork",
        messages=messages,
        metadata={
            "native_messages": native_messages,
            "native_messages_integrity": core._compute_native_integrity(messages),
        },
    )

    prefix = core.slice_session(session, config, start=0, end=2)
    forked = core.fork_session(session, config, upto_index=1, new_session_id="forked")

    assert forked.session_id == "forked"
    assert forked.messages == prefix.messages
    assert forked.metadata == prefix.metadata


def test_modify_message_core_only_no_provider():
    core = AgentCore()
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
 
    modified = core.modify_message(session, 0, "Changed")
 
    assert len(modified.messages) == 1
    assert modified.messages[0].content == "Changed"
    assert session.messages[0].content == "Hello"
    assert "native_messages" not in modified.metadata
    assert "native_messages_integrity" not in modified.metadata
 
 
def test_modify_message_preserves_native_simple_1_to_1():
    core = AgentCore()
    core.register_provider(DummyProvider)
    config = {"model": "test"}
 
    native_messages = [
        {"role": "assistant", "content": "n0"},
        {"role": "assistant", "content": "n1"},
        {"role": "assistant", "content": "n2"},
    ]
 
    messages = [
        Message(role="assistant", content="m0", metadata={"native_indices": [0]}),
        Message(role="assistant", content="m1", metadata={"native_indices": [1]}),
        Message(role="assistant", content="m2", metadata={"native_indices": [2]}),
    ]
 
    session = Session(
        session_id="s-mod",
        messages=messages,
        metadata={
            "native_messages": native_messages,
            "native_messages_integrity": core._compute_native_integrity(messages),
        },
    )
 
    modified = core.modify_message(session, 1, "m1-updated", config=config)
 
    assert modified.messages[1].content == "m1-updated"
    assert session.messages[1].content == "m1"
 
    new_native = modified.metadata.get("native_messages")
    assert isinstance(new_native, list)
    assert len(new_native) == len(native_messages)
    assert new_native[0] is native_messages[0]
    assert new_native[2] is native_messages[2]
    assert new_native[1]["content"] == "m1-updated"
 
    indices_lists = [
        (msg.metadata or {}).get("native_indices") for msg in modified.messages
    ]
    assert indices_lists == [[0], [1], [2]]
 
 
def test_modify_message_shared_indices_with_provider_rebuild():
    core = AgentCore()
    core.register_provider(DummyProvider)
    config = {"model": "test"}

    native_messages = [
        {"role": "assistant", "content": "n0", "id": "n0"},
        {"role": "assistant", "content": "n1", "id": "n1"},
        {"role": "assistant", "content": "n2", "id": "n2"},
        {"role": "assistant", "content": "n3", "id": "n3"},
    ]

    messages = [
        Message(role="assistant", content="m0", metadata={"native_indices": [0, 1]}),
        Message(role="assistant", content="m1", metadata={"native_indices": [1, 2]}),
        Message(role="assistant", content="m2", metadata={"native_indices": [2, 3]}),
    ]

    session = Session(
        session_id="s-mod-shared",
        messages=messages,
        metadata={
            "native_messages": native_messages,
            "native_messages_integrity": core._compute_native_integrity(messages),
        },
    )

    modified = core.modify_message(session, 1, "m1-updated", config=config)

    # We no longer drop native history on shared indices; instead, we
    # patch native history and let the provider + features rebuild the
    # full core message sequence. This test only asserts that native
    # history is still present and integrity is updated.
    assert "native_messages" in modified.metadata
    assert "native_messages_integrity" in modified.metadata
    assert isinstance(modified.metadata["native_messages"], list)
 
 
def test_modify_message_rejects_tool_role():
    core = AgentCore()
    session = core.create_session()
    session = core.add_message(session, "tool", "Tool output", metadata={"k": "v"})
 
    with pytest.raises(ValueError):
        core.modify_message(session, 0, "Updated")
 
 
def test_add_message_suffix_native_indices_with_and_without_config():
    core = AgentCore()
    core.register_provider(DummyProvider)
    config = {"model": "test"}

    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    session, _ = core.send_request(session, config)

    assert "native_messages" in session.metadata
    base_len = len(session.metadata["native_messages"])

    # Without explicit config, add_message still uses the provider pipeline
    # and assigns native_indices for the appended message when native
    # history is present and a single provider is registered.
    no_config = core.add_message(session, "user", "No config path")
    native_no_config = no_config.metadata.get("native_messages")
    assert isinstance(native_no_config, list)
    assert len(native_no_config) >= base_len
    last_no_cfg = no_config.messages[-1]
    idx_no_cfg = (last_no_cfg.metadata or {}).get("native_indices")
    assert isinstance(idx_no_cfg, list) and idx_no_cfg
    assert idx_no_cfg[0] == base_len

    # With explicit config, behavior is consistent: the new suffix is mapped
    # to a contiguous range at the tail of native history.
    with_config = core.add_message(session, "user", "Config path", config=config)
    native_with_config = with_config.metadata.get("native_messages")
    assert isinstance(native_with_config, list)
    assert len(native_with_config) >= base_len

    last_with_cfg = with_config.messages[-1]
    idx_with_cfg = (last_with_cfg.metadata or {}).get("native_indices")
    assert isinstance(idx_with_cfg, list) and idx_with_cfg
    assert idx_with_cfg[0] == base_len
    assert idx_with_cfg == list(range(idx_with_cfg[0], idx_with_cfg[0] + len(idx_with_cfg)))



def test_modify_message_shared_indices_cardinality_change_removes_first():
    core = AgentCore()

    # Monkeypatch conversion helpers to control cardinality.
    original_to_native = core._core_messages_to_native_for_config
    original_rebuild = core._rebuild_core_from_native

    def fake_core_to_native(core_messages, config, **_kwargs):  # type: ignore[override]
        msg = core_messages[0]
        return [
            {"role": msg["role"], "content": f"n:{msg['content']}", "metadata": {}},
        ]

    def fake_rebuild(native_messages, config, **_kwargs):  # type: ignore[override]
        # Return tuple of (core_messages, post_init_native_messages)
        core_msgs = [
            Message(
                role=nm["role"],
                content=nm["content"],
                metadata={"native_indices": [i]},
            )
            for i, nm in enumerate(native_messages)
        ]
        return core_msgs, list(native_messages)

    try:
        core._core_messages_to_native_for_config = fake_core_to_native  # type: ignore[assignment]
        core._rebuild_core_from_native = fake_rebuild  # type: ignore[assignment]

        native_messages = [
            {"role": "assistant", "content": "n0"},
            {"role": "assistant", "content": "n1"},
        ]

        messages = [
            Message(role="assistant", content="m0", metadata={"native_indices": [0, 1]}),
            Message(role="assistant", content="m1", metadata={"native_indices": [0, 1]}),
        ]

        session = Session(
            session_id="s-shared",
            messages=messages,
            metadata={
                "native_messages": native_messages,
                "native_messages_integrity": core._compute_native_integrity(messages),
            },
        )

        modified = core.modify_message(session, 1, "m1-updated")

        new_native = modified.metadata.get("native_messages")
        assert isinstance(new_native, list)
        # Two native messages [0, 1] are replaced by a single one.
        assert [m["content"] for m in new_native] == ["n:m1-updated"]

        # Rebuilt core should now have a single message, effectively removing the first.
        assert [m.content for m in modified.messages] == ["n:m1-updated"]

    finally:
        core._core_messages_to_native_for_config = original_to_native  # type: ignore[assignment]
        core._rebuild_core_from_native = original_rebuild  # type: ignore[assignment]



def test_streaming_feature_finalize_receives_aggregated_finals():
    """Regression: feature finalize must see finals emitted during streaming.

    Providers like openai_responses emit final messages during process_chunk
    (e.g., on response.completed). These accumulate in aggregated_native_finals.
    Previously, feature finalize only ran on provider.finalize() output,
    missing the streaming finals entirely.
    """
    from dataclasses import dataclass
    from typing import Iterator, Tuple

    @dataclass
    class _StreamingFinalsProvider(ProviderPlugin):
        name: str = "streaming_finals_provider"
        version: str = "1.0.0"

        def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
            return {"config": config}

        def from_native_messages(
            self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
        ) -> List[Dict[str, Any]]:
            return native_messages

        def initialize_request(
            self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
        ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
            return list(native_messages), state

        def process_chunk(
            self,
            native_chunk: Dict[str, Any],
            native_messages: List[Dict[str, Any]],
            state: Dict[str, Any],
        ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
            partials: List[Dict[str, Any]] = []
            finals: List[Dict[str, Any]] = []
            if native_chunk.get("type") == "partial":
                partials = [{"role": "assistant", "content": native_chunk.get("content", "")}]
            elif native_chunk.get("type") == "final":
                finals = [{"role": "assistant", "content": native_chunk.get("content", "")}]
                native_messages = [*native_messages, *finals]
            return partials, finals, native_messages, state

        def finalize(
            self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
        ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
            # Provider finalize returns empty finals (already emitted during streaming)
            return [], list(native_messages), state

        def stream_api(
            self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
        ) -> Iterator[Dict[str, Any]]:
            yield {"type": "partial", "content": "hello "}
            yield {"type": "final", "content": "hello world"}

    @dataclass
    class _StampFeature(FeaturePlugin):
        name: str = "stamp_feature"
        version: str = "1.0.0"

        def get_config_schema(self) -> Dict[str, Any]:
            return {}

        def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
            return state

        def finalize(
            self,
            final_messages: List[Dict[str, Any]],
            native_messages: List[Dict[str, Any]],
            state: Dict[str, Any],
        ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
            stamped = [
                {**m, "metadata": {**(m.get("metadata") or {}), "stamped": True}}
                for m in final_messages
            ]
            # Also stamp the corresponding messages in native history
            start = len(native_messages) - len(stamped) if len(stamped) <= len(native_messages) else 0
            stamped_history = list(native_messages)
            for offset, final_msg in enumerate(stamped):
                hist_idx = start + offset
                if 0 <= hist_idx < len(stamped_history):
                    stamped_history[hist_idx] = final_msg
            return stamped, stamped_history, state

    core = AgentCore()
    core.register_provider(_StreamingFinalsProvider)
    core.register_feature(_StampFeature)

    config = {"model": "test-model"}
    session = core.create_session()
    session = core.add_message(session, "user", "hi")

    final_messages: List[Dict[str, Any]] = []
    final_session = None
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_messages = chunk.get("messages") or []
            final_session = chunk.get("session")

    assert final_messages
    assert final_messages[-1].get("metadata", {}).get("stamped") is True

    assert final_session is not None
    native = (final_session.metadata or {}).get("native_messages")
    assert isinstance(native, list)
    last_native = native[-1]
    assert isinstance(last_native, dict)
    assert last_native.get("metadata", {}).get("stamped") is True
