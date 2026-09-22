"""Tests for the tool-call lifecycle and message-append plugin hooks.

Chunk 1 covers the protocol surface: default no-op implementations on
``FeaturePlugin`` and ``ProviderExtensionPlugin``, the defaulting
adapters, and the wrapper pass-throughs.

Chunk 2 covers dispatch through ``AgentCore.iter_tool_messages`` /
``execute_tool_calls``: ordering, context facts, call transformation
with re-inspection, and synthesized-error paths.

The append-hook dispatch (``AgentCore.add_message``) is added in a
later chunk in this same module.
"""

from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Tuple

from agent_core import AgentCore
from agent_core.plugin.adapters import (
    FeatureDefaultsAdapter,
    ProviderExtensionDefaultsAdapter,
)
from agent_core.plugin.extension import ExtensionWrapper
from agent_core.plugin.feature import FeatureWrapper
from agent_core.types import FeaturePlugin, ProviderExtensionPlugin
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider

from .dummy_tool import DummyCalculator


class HooklessFeature(FeaturePlugin):
    """A feature implementing none of the new hooks (backward compat)."""

    name = "hookless_feature"
    version = "0.1.0"


class HooklessExtension(ProviderExtensionPlugin):
    """An extension implementing none of the new hooks."""

    name = "hookless_extension"
    version = "0.1.0"


class RecordingHooksFeature(FeaturePlugin):
    """Implements all three hooks and records every call."""

    name = "recording_hooks_feature"
    version = "0.1.0"
    priority = 200

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def prepare_tool_call(
        self,
        tool_call: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        self.calls.append(
            {
                "hook": "prepare_tool_call",
                "tool_call": tool_call,
                "state": dict(state),
                "context": dict(context or {}),
            }
        )
        return tool_call, {**state, "feature_prepare": True}

    def finalize_tool_call(
        self,
        tool_message: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        self.calls.append(
            {
                "hook": "finalize_tool_call",
                "tool_message": tool_message,
                "state": dict(state),
                "context": dict(context or {}),
            }
        )
        stamped = {
            **tool_message,
            "metadata": {
                **(tool_message.get("metadata") or {}),
                "feature_finalize": True,
            },
        }
        return stamped, {**state, "feature_finalize": True}

    def prepare_appended_message(
        self,
        message: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        self.calls.append(
            {
                "hook": "prepare_appended_message",
                "message": message,
                "state": dict(state or {}),
                "context": dict(context or {}),
            }
        )
        stamped = {
            **message,
            "metadata": {**(message.get("metadata") or {}), "feature_append": True},
        }
        return stamped, {**(state or {}), "feature_append": True}


class RecordingHooksExtension(ProviderExtensionPlugin):
    """Implements all three hooks and records every call."""

    name = "recording_hooks_extension"
    version = "0.1.0"
    priority = 50

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def prepare_tool_call(
        self,
        tool_call: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        self.calls.append({"hook": "prepare_tool_call", "tool_call": tool_call})
        return tool_call, {**state, "extension_prepare": True}

    def finalize_tool_call(
        self,
        tool_message: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        self.calls.append({"hook": "finalize_tool_call", "tool_message": tool_message})
        stamped = {
            **tool_message,
            "metadata": {
                **(tool_message.get("metadata") or {}),
                "extension_finalize": True,
            },
        }
        return stamped, {**state, "extension_finalize": True}

    def prepare_appended_message(
        self,
        message: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        self.calls.append({"hook": "prepare_appended_message", "message": message})
        stamped = {
            **message,
            "metadata": {
                **(message.get("metadata") or {}),
                "extension_append": True,
            },
        }
        return stamped, {**(state or {}), "extension_append": True}


# ---------------------------------------------------------------------------
# Protocol default no-op implementations
# ---------------------------------------------------------------------------


def test_feature_protocol_default_hooks_are_noops() -> None:
    plugin = HooklessFeature()
    call = {"id": "call_1", "function": {"name": "add"}}
    state = {"existing": True}
    message = {"role": "user", "content": "hi"}

    out_call, out_state = plugin.prepare_tool_call(call, state)
    assert out_call == call
    assert out_state == state

    out_message, out_state = plugin.finalize_tool_call(message, state)
    assert out_message == message
    assert out_state == state

    out_message, out_state = plugin.prepare_appended_message(message, state)
    assert out_message == message
    assert out_state == state

    out_message, out_state = plugin.prepare_appended_message(message)
    assert out_message == message
    assert out_state == {}


def test_extension_protocol_default_hooks_are_noops() -> None:
    plugin = HooklessExtension()
    call = {"id": "call_1", "function": {"name": "add"}}
    state = {"existing": True}
    message = {"role": "user", "content": "hi"}

    out_call, out_state = plugin.prepare_tool_call(call, state)
    assert out_call == call
    assert out_state == state

    out_message, out_state = plugin.finalize_tool_call(message, state)
    assert out_message == message
    assert out_state == state

    out_message, out_state = plugin.prepare_appended_message(message, state)
    assert out_message == message
    assert out_state == state


# ---------------------------------------------------------------------------
# Defaulting adapters
# ---------------------------------------------------------------------------


def test_feature_adapter_supplies_defaults_for_hookless_impl() -> None:
    adapter = FeatureDefaultsAdapter(HooklessFeature())
    call = {"id": "call_1", "function": {"name": "add"}}
    state = {"existing": True}
    message = {"role": "user", "content": "hi"}

    out_call, out_state = adapter.prepare_tool_call(call, state)
    assert out_call == call
    assert out_state == state

    out_message, out_state = adapter.finalize_tool_call(message, state)
    assert out_message == message
    assert out_state == state

    out_message, out_state = adapter.prepare_appended_message(message, state)
    assert out_message == message
    assert out_state == state


def test_extension_adapter_supplies_defaults_for_hookless_impl() -> None:
    adapter = ProviderExtensionDefaultsAdapter(HooklessExtension())
    call = {"id": "call_1", "function": {"name": "add"}}
    state = {"existing": True}
    message = {"role": "user", "content": "hi"}

    out_call, out_state = adapter.prepare_tool_call(call, state)
    assert out_call == call
    assert out_state == state

    out_message, out_state = adapter.finalize_tool_call(message, state)
    assert out_message == message
    assert out_state == state

    out_message, out_state = adapter.prepare_appended_message(message, state)
    assert out_message == message
    assert out_state == state


def test_feature_adapter_delegates_hook_implementations() -> None:
    impl = RecordingHooksFeature()
    adapter = FeatureDefaultsAdapter(impl)
    call = {"id": "call_1", "function": {"name": "add"}}
    state = {"existing": True}
    context = {"session_id": "s1"}
    message = {"role": "tool", "content": "result"}

    out_call, out_state = adapter.prepare_tool_call(call, state, context=context)
    assert out_call == call
    assert out_state == {"existing": True, "feature_prepare": True}
    assert impl.calls[0]["context"] == context

    out_message, out_state = adapter.finalize_tool_call(message, state, context=context)
    assert out_message["metadata"]["feature_finalize"] is True
    assert out_state == {"existing": True, "feature_finalize": True}

    out_message, out_state = adapter.prepare_appended_message(message, state, context=context)
    assert out_message["metadata"]["feature_append"] is True
    assert out_state == {"existing": True, "feature_append": True}
    assert len(impl.calls) == 3


def test_extension_adapter_delegates_hook_implementations() -> None:
    impl = RecordingHooksExtension()
    adapter = ProviderExtensionDefaultsAdapter(impl)
    call = {"id": "call_1", "function": {"name": "add"}}
    state = {"existing": True}
    message = {"role": "tool", "content": "result"}

    out_call, out_state = adapter.prepare_tool_call(call, state)
    assert out_call == call
    assert out_state == {"existing": True, "extension_prepare": True}

    out_message, out_state = adapter.finalize_tool_call(message, state)
    assert out_message["metadata"]["extension_finalize"] is True
    assert out_state == {"existing": True, "extension_finalize": True}

    out_message, out_state = adapter.prepare_appended_message(message, state)
    assert out_message["metadata"]["extension_append"] is True
    assert out_state == {"existing": True, "extension_append": True}
    assert len(impl.calls) == 3


# ---------------------------------------------------------------------------
# Wrapper pass-throughs
# ---------------------------------------------------------------------------


def test_feature_wrapper_passes_hooks_through() -> None:
    wrapper = FeatureWrapper(RecordingHooksFeature)
    impl = wrapper.plugin.impl
    call = {"id": "call_1", "function": {"name": "add"}}
    state = {"existing": True}
    message = {"role": "tool", "content": "result"}

    out_call, out_state = wrapper.prepare_tool_call(call, state)
    assert out_call == call
    assert out_state["feature_prepare"] is True

    out_message, out_state = wrapper.finalize_tool_call(message, state)
    assert out_message["metadata"]["feature_finalize"] is True

    out_message, out_state = wrapper.prepare_appended_message(message, state)
    assert out_message["metadata"]["feature_append"] is True
    assert len(impl.calls) == 3


def test_extension_wrapper_passes_hooks_through() -> None:
    wrapper = ExtensionWrapper(RecordingHooksExtension)
    impl = wrapper.plugin.impl
    call = {"id": "call_1", "function": {"name": "add"}}
    state = {"existing": True}
    message = {"role": "tool", "content": "result"}

    out_call, out_state = wrapper.prepare_tool_call(call, state)
    assert out_call == call
    assert out_state["extension_prepare"] is True

    out_message, out_state = wrapper.finalize_tool_call(message, state)
    assert out_message["metadata"]["extension_finalize"] is True

    out_message, out_state = wrapper.prepare_appended_message(message, state)
    assert out_message["metadata"]["extension_append"] is True
    assert len(impl.calls) == 3


def test_hookless_feature_wrapper_supplies_default_hooks() -> None:
    wrapper = FeatureWrapper(HooklessFeature)
    call = {"id": "call_1", "function": {"name": "add"}}
    state = {"existing": True}
    message = {"role": "user", "content": "hi"}

    out_call, out_state = wrapper.prepare_tool_call(call, state)
    assert out_call == call
    assert out_state == state

    out_message, out_state = wrapper.finalize_tool_call(message, state)
    assert out_message == message
    assert out_state == state

    out_message, out_state = wrapper.prepare_appended_message(message, state)
    assert out_message == message
    assert out_state == state


# ---------------------------------------------------------------------------
# Backward-compatibility guard (passes before and after the change)
# ---------------------------------------------------------------------------


def test_hookless_plugins_still_execute_tool_calls() -> None:
    from agent_core import AgentCore

    core = AgentCore()
    core.register_feature(HooklessFeature)
    core.register_tool(DummyCalculator)

    results = core.execute_tool_calls(
        [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "add", "arguments": {"a": 2, "b": 3}},
            }
        ],
        config={},
    )

    assert len(results) == 1
    assert "Result: 5" in str(results[0].get("content", ""))


# ---------------------------------------------------------------------------
# Chunk 2 fixtures: class-level recording participants for dispatch tests
# ---------------------------------------------------------------------------


class RecordingCalculator:
    """Calculator tool recording received calls at class level."""

    name = "recording_calculator"
    version = "0.1.0"

    _received: ClassVar[List[Dict[str, Any]]] = []

    @classmethod
    def pop_received(cls) -> List[Dict[str, Any]]:
        received = list(cls._received)
        cls._received = []
        return received

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "Add two numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number"},
                            "b": {"type": "number"},
                        },
                        "required": ["a", "b"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "multiply",
                    "description": "Multiply two numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number"},
                            "b": {"type": "number"},
                        },
                        "required": ["a", "b"],
                    },
                },
            },
        ]

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        type(self)._received.append({"tool_name": tool_name, "arguments": dict(arguments or {})})
        if tool_name == "add":
            return {
                "success": True,
                "result": arguments.get("a", 0) + arguments.get("b", 0),
            }
        if tool_name == "multiply":
            return {
                "success": True,
                "result": arguments.get("a", 0) * arguments.get("b", 0),
            }
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("success"):
            return f"Result: {result['result']}"
        return f"Error: {result.get('error')}"


class ExplodingStreamTool:
    """Tool whose execution raises (stream-error path)."""

    name = "exploding_stream_tool"
    version = "0.1.0"

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "explode",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        raise RuntimeError("boom")

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return "unreachable"


class DispatchRecordingExtension:
    """Extension recording hook calls at class level (priority 50)."""

    name = "dispatch_recording_extension"
    version = "0.1.0"
    priority = 50

    _events: ClassVar[List[Dict[str, Any]]] = []

    @classmethod
    def pop_events(cls) -> List[Dict[str, Any]]:
        events = list(cls._events)
        cls._events = []
        return events

    def prepare_tool_call(
        self,
        tool_call: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        type(self)._events.append(
            {
                "plugin": "extension",
                "hook": "prepare",
                "tool_call": dict(tool_call),
                "state": dict(state),
                "context": dict(context or {}),
            }
        )
        return tool_call, {**state, "extension_prepare": True}

    def finalize_tool_call(
        self,
        tool_message: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        type(self)._events.append(
            {
                "plugin": "extension",
                "hook": "finalize",
                "metadata": dict(tool_message.get("metadata") or {}),
                "state": dict(state),
                "context": dict(context or {}),
            }
        )
        stamped = {
            **tool_message,
            "metadata": {
                **(tool_message.get("metadata") or {}),
                "extension_finalize": True,
            },
        }
        return stamped, {**state, "extension_finalize": True}

    def prepare_appended_message(
        self,
        message: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        type(self)._events.append(
            {
                "plugin": "extension",
                "hook": "append",
                "metadata": dict(message.get("metadata") or {}),
                "state": dict(state or {}),
                "context": dict(context or {}),
            }
        )
        stamped = {
            **message,
            "metadata": {
                **(message.get("metadata") or {}),
                "extension_append": True,
            },
        }
        return stamped, {**(state or {}), "extension_append": True}


class DispatchRecordingFeature:
    """Feature recording hook calls at class level (priority 200)."""

    name = "dispatch_recording_feature"
    version = "0.1.0"
    priority = 200

    _events: ClassVar[List[Dict[str, Any]]] = []

    @classmethod
    def pop_events(cls) -> List[Dict[str, Any]]:
        events = list(cls._events)
        cls._events = []
        return events

    def prepare_tool_call(
        self,
        tool_call: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        type(self)._events.append(
            {
                "plugin": "feature",
                "hook": "prepare",
                "tool_call": dict(tool_call),
                "state": dict(state),
                "context": dict(context or {}),
            }
        )
        return tool_call, {**state, "feature_prepare": True}

    def finalize_tool_call(
        self,
        tool_message: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        type(self)._events.append(
            {
                "plugin": "feature",
                "hook": "finalize",
                "metadata": dict(tool_message.get("metadata") or {}),
                "state": dict(state),
                "context": dict(context or {}),
            }
        )
        stamped = {
            **tool_message,
            "metadata": {
                **(tool_message.get("metadata") or {}),
                "feature_finalize": True,
            },
        }
        return stamped, {**state, "feature_finalize": True}

    def prepare_appended_message(
        self,
        message: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        type(self)._events.append(
            {
                "plugin": "feature",
                "hook": "append",
                "metadata": dict(message.get("metadata") or {}),
                "state": dict(state or {}),
                "context": dict(context or {}),
            }
        )
        stamped = {
            **message,
            "metadata": {
                **(message.get("metadata") or {}),
                "feature_append": True,
            },
        }
        return stamped, {**(state or {}), "feature_append": True}


class SanitizingFeature:
    """Rewrites tool call arguments before execution (sanitizing)."""

    name = "sanitizing_feature"
    version = "0.1.0"
    priority = 150

    def prepare_tool_call(
        self,
        tool_call: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        function = tool_call.get("function") or {}
        arguments = function.get("arguments") or {}
        sanitized = {
            **tool_call,
            "function": {**function, "arguments": {**arguments, "b": 100}},
        }
        return sanitized, state


class InterceptingFeature:
    """Redirects the call to a different tool (interception)."""

    name = "intercepting_feature"
    version = "0.1.0"
    priority = 150

    def prepare_tool_call(
        self,
        tool_call: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        function = tool_call.get("function") or {}
        intercepted = {**tool_call, "function": {**function, "name": "multiply"}}
        return intercepted, state


class BrokenTransformFeature:
    """Returns a non-inspectable call (broken transformation)."""

    name = "broken_transform_feature"
    version = "0.1.0"
    priority = 150

    def prepare_tool_call(
        self,
        tool_call: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        return {"garbage": True}, state


def _dispatch_config() -> Dict[str, Any]:
    return {
        "provider": "echo_openai_like",
        "model": "test-model",
    }


def _build_dispatch_core(
    *,
    extensions: List[type] | None = None,
    features: List[type] | None = None,
    tools: List[type] | None = None,
) -> AgentCore:
    core = AgentCore()
    core.register_provider(EchoOpenAILikeProvider, list(extensions or []))
    for feature in features or []:
        core.register_feature(feature)
    for tool in tools or [RecordingCalculator]:
        core.register_tool(tool)
    return core


def _add_call(call_id: str, name: str = "add", **arguments: Any) -> Dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": dict(arguments)},
    }


# ---------------------------------------------------------------------------
# Chunk 2: dispatch through iter_tool_messages / execute_tool_calls
# ---------------------------------------------------------------------------


def test_tool_call_hooks_dispatch_with_facts_and_ordering() -> None:
    core = _build_dispatch_core(
        extensions=[DispatchRecordingExtension],
        features=[DispatchRecordingFeature],
    )

    results = core.execute_tool_calls(
        [_add_call("call_1", a=2, b=3)],
        _dispatch_config(),
        context={"session_id": "sess-1", "request_id": "req-1"},
    )

    assert len(results) == 1
    ext_events = DispatchRecordingExtension.pop_events()
    feat_events = DispatchRecordingFeature.pop_events()

    # Each participant saw prepare then finalize.
    assert [e["hook"] for e in ext_events] == ["prepare", "finalize"]
    assert [e["hook"] for e in feat_events] == ["prepare", "finalize"]

    # Extension finalize ran before feature finalize: the feature received
    # the extension's stamp (chained transforms).
    feature_finalize = feat_events[1]
    assert feature_finalize["metadata"].get("extension_finalize") is True

    # State threading: the feature's prepare saw the extension's state update.
    feature_prepare = feat_events[0]
    assert feature_prepare["state"].get("extension_prepare") is True

    # Prepare context facts.
    prepare_ctx = ext_events[0]["context"]
    assert prepare_ctx["tool_call_id"] == "call_1"
    assert prepare_ctx["tool_name"] == "add"
    assert prepare_ctx["tool_plugin"] == "recording_calculator"
    assert isinstance(prepare_ctx["started_at"], str)
    datetime.fromisoformat(prepare_ctx["started_at"])
    assert isinstance(prepare_ctx["started_at_mono"], float)
    assert prepare_ctx["session_id"] == "sess-1"
    assert prepare_ctx["request_id"] == "req-1"
    # Framework provides facts only: no computed durations.
    assert not any("duration" in key for key in prepare_ctx)

    # Finalize context carries the finished facts and no error.
    finalize_ctx = feature_finalize["context"]
    assert isinstance(finalize_ctx["finished_at"], str)
    datetime.fromisoformat(finalize_ctx["finished_at"])
    assert isinstance(finalize_ctx["finished_at_mono"], float)
    assert "tool_error" not in finalize_ctx

    # The returned message carries both stamps.
    metadata = results[0].get("metadata") or {}
    assert metadata.get("extension_finalize") is True
    assert metadata.get("feature_finalize") is True

    # The tool executed exactly once, with the original arguments.
    assert RecordingCalculator.pop_received() == [
        {"tool_name": "add", "arguments": {"a": 2, "b": 3}}
    ]


def test_prepare_tool_call_sanitizes_arguments() -> None:
    core = _build_dispatch_core(features=[SanitizingFeature])

    results = core.execute_tool_calls([_add_call("call_1", a=2, b=3)], _dispatch_config())

    received = RecordingCalculator.pop_received()
    assert received == [{"tool_name": "add", "arguments": {"a": 2, "b": 100}}]
    assert "Result: 102" in str(results[0].get("content", ""))


def test_prepare_tool_call_intercepts_tool_name() -> None:
    core = _build_dispatch_core(features=[InterceptingFeature])

    results = core.execute_tool_calls([_add_call("call_1", a=2, b=3)], _dispatch_config())

    received = RecordingCalculator.pop_received()
    assert received[0]["tool_name"] == "multiply"
    assert "Result: 6" in str(results[0].get("content", ""))
    # The result message reflects the transformed call.
    metadata = results[0].get("metadata") or {}
    assert metadata.get("tool_name") == "multiply"


def test_prepare_tool_call_broken_transformation_follows_synthesized_error_path() -> None:
    core = _build_dispatch_core(
        extensions=[DispatchRecordingExtension],
        features=[BrokenTransformFeature],
    )

    results = core.execute_tool_calls([_add_call("call_1", a=2, b=3)], _dispatch_config())

    # The transformed call no longer inspects: existing synthesized-error path.
    assert "Error: no tool handled" in str(results[0].get("content", ""))
    # The tool never executed.
    assert RecordingCalculator.pop_received() == []
    # Prepare fired (the original call was inspectable); finalize fired with
    # a tool_error fact.
    events = DispatchRecordingExtension.pop_events()
    assert [e["hook"] for e in events] == ["prepare", "finalize"]
    assert "tool_error" in events[1]["context"]


def test_finalize_tool_call_dispatches_for_no_handler_result() -> None:
    core = _build_dispatch_core(extensions=[DispatchRecordingExtension])

    results = core.execute_tool_calls([_add_call("call_x", name="nonexistent")], _dispatch_config())

    assert "Error: no tool handled 'nonexistent'" in str(results[0].get("content", ""))
    events = DispatchRecordingExtension.pop_events()
    assert [e["hook"] for e in events] == ["prepare", "finalize"]
    assert "tool_error" in events[1]["context"]


def test_finalize_tool_call_dispatches_for_stream_error() -> None:
    core = _build_dispatch_core(
        extensions=[DispatchRecordingExtension],
        tools=[ExplodingStreamTool],
    )

    results = core.execute_tool_calls([_add_call("call_b", name="explode")], _dispatch_config())

    assert "Tool error: boom" in str(results[0].get("content", ""))
    events = DispatchRecordingExtension.pop_events()
    assert [e["hook"] for e in events] == ["prepare", "finalize"]
    finalize_ctx = events[1]["context"]
    assert "tool_error" in finalize_ctx
    # Execution was attempted: started and finished facts are present.
    assert "started_at" in finalize_ctx
    assert "finished_at" in finalize_ctx


def test_finalize_tool_call_dispatches_without_prepare_for_uninspectable_call() -> None:
    core = _build_dispatch_core(extensions=[DispatchRecordingExtension])

    results = core.execute_tool_calls([{"weird_shape": True}], _dispatch_config())

    assert "Error: no tool handled" in str(results[0].get("content", ""))
    events = DispatchRecordingExtension.pop_events()
    # Not inspectable: no prepare, finalize still fires exactly once.
    assert [e["hook"] for e in events] == ["finalize"]
    assert "tool_error" in events[0]["context"]


def test_multiple_tool_calls_correlate_facts_per_call() -> None:
    core = _build_dispatch_core(extensions=[DispatchRecordingExtension])

    core.execute_tool_calls(
        [_add_call("call_1", a=1, b=1), _add_call("call_2", a=2, b=2)],
        _dispatch_config(),
    )

    events = DispatchRecordingExtension.pop_events()
    prepare_ids = [e["context"]["tool_call_id"] for e in events if e["hook"] == "prepare"]
    finalize_ids = [e["context"]["tool_call_id"] for e in events if e["hook"] == "finalize"]
    assert prepare_ids == ["call_1", "call_2"]
    assert finalize_ids == ["call_1", "call_2"]
    assert len(RecordingCalculator.pop_received()) == 2


def test_bare_core_tool_execution_does_not_dispatch_hooks() -> None:
    core = AgentCore()
    core.register_feature(DispatchRecordingFeature)
    core.register_tool(RecordingCalculator)

    results = core.execute_tool_calls([_add_call("call_1", a=2, b=3)], config={})

    assert "Result: 5" in str(results[0].get("content", ""))
    assert DispatchRecordingFeature.pop_events() == []


def test_tool_call_hook_state_flows_back_to_provider_state() -> None:
    core = _build_dispatch_core(extensions=[DispatchRecordingExtension])
    config = _dispatch_config()
    provider = core._providers[0]
    # Mirrors the request pipeline's provider init (core.py:2016).
    provider.init(config)

    core.execute_tool_calls([_add_call("call_1", a=2, b=3)], config)

    assert provider.state.get("extension_prepare") is True
    assert provider.state.get("extension_finalize") is True
    RecordingCalculator.pop_received()
    DispatchRecordingExtension.pop_events()


# ---------------------------------------------------------------------------
# Chunk 3: append dispatch through add_message
# ---------------------------------------------------------------------------


def test_append_hook_dispatches_for_user_message_end_append() -> None:
    core = _build_dispatch_core(
        extensions=[DispatchRecordingExtension],
        features=[DispatchRecordingFeature],
    )
    session = core.create_session()

    new_session = core.add_message(
        session,
        "user",
        "hello",
        config=_dispatch_config(),
        context={"session_id": "sess-1", "request_id": "req-1"},
    )

    ext_events = DispatchRecordingExtension.pop_events()
    feat_events = DispatchRecordingFeature.pop_events()

    # Both participants saw the append hook exactly once.
    assert [e["hook"] for e in ext_events] == ["append"]
    assert [e["hook"] for e in feat_events] == ["append"]

    # Chained: the feature received the extension's stamped message and state.
    feature_append = feat_events[0]
    assert feature_append["metadata"].get("extension_append") is True
    assert feature_append["state"].get("extension_append") is True

    # Append context facts.
    append_ctx = ext_events[0]["context"]
    assert append_ctx["session_id"] == "sess-1"
    assert append_ctx["request_id"] == "req-1"

    # The transformed message landed in the session.
    last = new_session.messages[-1]
    assert last.role == "user"
    assert last.content == "hello"
    metadata = last.metadata or {}
    assert metadata.get("extension_append") is True
    assert metadata.get("feature_append") is True


def test_append_hook_stamp_persists_into_native_metadata() -> None:
    core = _build_dispatch_core(extensions=[DispatchRecordingExtension])
    config = _dispatch_config()

    session = core.create_session()
    # A request creates provider-native history for the session.
    session = core.add_message(session, "user", "hi", config=config)
    session, _finals = core.send_request(session, config)
    assert isinstance(session.metadata, dict)
    assert isinstance(session.metadata.get("native_messages"), list)
    DispatchRecordingExtension.pop_events()

    new_session = core.add_message(session, "user", "hello again", config=config)

    # The stamp persists into the provider-native history.
    native = new_session.metadata["native_messages"]
    stamped_native = [
        m
        for m in native
        if isinstance(m.get("_metadata"), dict) and m["_metadata"].get("extension_append") is True
    ]
    assert stamped_native

    # And the rebuilt core message carries it.
    stamped_core = [
        m
        for m in new_session.messages
        if isinstance(m.metadata, dict) and m.metadata.get("extension_append") is True
    ]
    assert stamped_core


def test_append_hook_threads_state_without_touching_session() -> None:
    core = _build_dispatch_core(
        extensions=[DispatchRecordingExtension],
        features=[DispatchRecordingFeature],
    )
    config = _dispatch_config()
    session = core.create_session()

    new_session = core.add_message(session, "user", "hello", config=config)

    # Within-chain state threading: the feature saw the extension's state.
    feat_events = DispatchRecordingFeature.pop_events()
    assert [e["hook"] for e in feat_events] == ["append"]
    assert feat_events[0]["state"].get("extension_append") is True
    DispatchRecordingExtension.pop_events()

    # The session itself is never touched by the state flow.
    assert isinstance(new_session.metadata, dict)
    assert "extension_append" not in new_session.metadata
    assert "extension_prepare" not in new_session.metadata


def test_append_hook_not_fired_for_after_index_insert() -> None:
    core = _build_dispatch_core(extensions=[DispatchRecordingExtension])
    config = _dispatch_config()
    session = core.create_session()
    session = core.add_message(session, "user", "first", config=config)
    session = core.add_message(session, "user", "second", config=config)
    DispatchRecordingExtension.pop_events()

    core.add_message(session, "user", "inserted", config=config, after_index=0)

    assert DispatchRecordingExtension.pop_events() == []


def test_append_hook_not_fired_without_config() -> None:
    core = _build_dispatch_core(extensions=[DispatchRecordingExtension])
    session = core.create_session()

    core.add_message(session, "user", "hello")

    assert DispatchRecordingExtension.pop_events() == []


def test_append_hook_not_fired_on_bare_core() -> None:
    core = AgentCore()
    core.register_feature(DispatchRecordingFeature)
    session = core.create_session()
    # First message without config: core-only session.
    session = core.add_message(session, "user", "first")

    # Second message with a config on a bare core: the core-only fallback
    # path runs (no provider to resolve), so no hooks dispatch.
    new_session = core.add_message(session, "user", "hello", config={"model": "test"})

    assert DispatchRecordingFeature.pop_events() == []
    assert new_session.messages[-1].content == "hello"


def test_append_hook_tool_result_carries_tool_call_facts() -> None:
    core = _build_dispatch_core(extensions=[DispatchRecordingExtension])
    config = _dispatch_config()
    caller_context: Dict[str, Any] = {
        "session_id": "sess-1",
        "request_id": "req-1",
    }

    results = core.execute_tool_calls(
        [_add_call("call_1", a=2, b=3)], config, context=caller_context
    )
    RecordingCalculator.pop_received()
    tool_events = DispatchRecordingExtension.pop_events()
    assert [e["hook"] for e in tool_events] == ["prepare", "finalize"]

    # The tool loop records the call facts into the caller's context so they
    # flow to the append hook when the same context is reused.
    assert caller_context.get("tool_call_id") == "call_1"
    assert caller_context.get("tool_name") == "add"
    assert isinstance(caller_context.get("started_at"), str)
    assert isinstance(caller_context.get("started_at_mono"), float)
    assert isinstance(caller_context.get("finished_at"), str)
    assert isinstance(caller_context.get("finished_at_mono"), float)

    session = core.create_session()
    new_session = core.add_message(
        session,
        "tool",
        results[0]["content"],
        results[0].get("metadata"),
        config=config,
        context=caller_context,
    )

    append_events = DispatchRecordingExtension.pop_events()
    assert [e["hook"] for e in append_events] == ["append"]
    append_ctx = append_events[0]["context"]
    assert append_ctx["tool_call_id"] == "call_1"
    assert append_ctx["tool_name"] == "add"
    assert "started_at" in append_ctx
    assert "finished_at" in append_ctx
    assert new_session.messages[-1].role == "tool"


# ---------------------------------------------------------------------------
# Chunk 4: provider-call context facts (request pipeline symmetry)
# ---------------------------------------------------------------------------


class RequestContextRecordingFeature:
    """Feature recording initialize_request/finalize contexts at class level."""

    name = "request_context_recording_feature"
    version = "0.1.0"
    priority = 100

    _contexts: ClassVar[List[Dict[str, Any]]] = []

    @classmethod
    def pop_contexts(cls) -> List[Dict[str, Any]]:
        contexts = list(cls._contexts)
        cls._contexts = []
        return contexts

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        type(self)._contexts.append({"hook": "initialize_request", "context": dict(context or {})})
        return native_messages, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        type(self)._contexts.append({"hook": "finalize", "context": dict(context or {})})
        return final_messages, native_messages, state


def test_provider_call_contexts_carry_timestamp_facts() -> None:
    core = _build_dispatch_core(features=[RequestContextRecordingFeature])
    config = _dispatch_config()
    session = core.create_session()
    session = core.add_message(session, "user", "hi", config=config)

    session, _finals = core.send_request(session, config)

    contexts = RequestContextRecordingFeature.pop_contexts()
    # The request pipeline's contexts carry session_id; internal rebuild
    # contexts (no session) are not provider calls and stay fact-free.
    init_entries = [
        c for c in contexts if c["hook"] == "initialize_request" and "session_id" in c["context"]
    ]
    finalize_entries = [
        c for c in contexts if c["hook"] == "finalize" and "session_id" in c["context"]
    ]
    assert init_entries
    assert finalize_entries

    for entry in init_entries:
        ctx = entry["context"]
        assert isinstance(ctx.get("started_at"), str)
        datetime.fromisoformat(ctx["started_at"])
        assert isinstance(ctx.get("started_at_mono"), float)
        # Framework provides facts only: no computed durations.
        assert not any("duration" in key for key in ctx)

    for entry in finalize_entries:
        ctx = entry["context"]
        assert isinstance(ctx.get("finished_at"), str)
        datetime.fromisoformat(ctx["finished_at"])
        assert isinstance(ctx.get("finished_at_mono"), float)
        assert not any("duration" in key for key in ctx)


def test_provider_call_contexts_carry_timestamp_facts_streaming() -> None:
    core = _build_dispatch_core(features=[RequestContextRecordingFeature])
    config = _dispatch_config()
    session = core.create_session()
    session = core.add_message(session, "user", "hi", config=config)

    for chunk in core.send_request_stream(session, config):
        _ = chunk

    contexts = RequestContextRecordingFeature.pop_contexts()
    init_entries = [
        c for c in contexts if c["hook"] == "initialize_request" and "session_id" in c["context"]
    ]
    finalize_entries = [
        c for c in contexts if c["hook"] == "finalize" and "session_id" in c["context"]
    ]
    assert init_entries
    assert finalize_entries
    assert isinstance(init_entries[0]["context"].get("started_at"), str)
    assert isinstance(finalize_entries[0]["context"].get("finished_at"), str)
