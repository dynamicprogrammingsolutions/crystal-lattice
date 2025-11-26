from typing import Any, Dict, List, Tuple, Iterator
from dataclasses import dataclass

from agent_core import AgentCore
from agent_core.types import ProviderPlugin, FeaturePlugin


@dataclass
class ConversionProvider(ProviderPlugin):
    name: str = "conversion_provider"
    version: str = "1.0.0"

    def to_native_messages(self, messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Mark that to_native was used
        return [
            {"role": m.get("role", "user"), "content": m.get("content", ""), "ctn": True}
            for m in messages
        ]

    def from_native_messages(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Mark that from_native was used on returned core finals
        return [
            {
                "role": m.get("role", "assistant"),
                "content": m.get("content", ""),
                "metadata": {"from_native_used": True},
            }
            for m in native_messages
        ]

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Echo marker if last user message was converted via to_native (ctn=True)
        has_ctn = any(isinstance(m, dict) and m.get("ctn") for m in native_messages)
        suffix = " CTN" if has_ctn else ""
        final = [{"role": "assistant", "content": "ok" + suffix}]
        return final, native_messages, state

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return [], [], native_messages, state


@dataclass
class ConversionFeature(FeaturePlugin):
    name: str = "conversion_feature"
    version: str = "1.0.0"

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Prefix native finals content; conversion to core occurs after finalize
        finals = [{**m, "content": "[F] " + m.get("content", "")} for m in final_messages]
        return finals, native_messages, state


def test_conversion_hooks_used_single_turn():
    core = AgentCore()
    core.register_provider(ConversionProvider)
    core.register_feature(ConversionFeature)

    session = core.create_session()
    session = core.add_message(session, "user", "Hello")

    new_session, finals = core.send_request(session, {})

    assert finals[-1]["content"].startswith("[F] ")
    assert finals[-1]["metadata"]["from_native_used"] is True


def test_conversion_hooks_used_two_turns_ctn_marker():
    core = AgentCore()
    core.register_provider(ConversionProvider)
    core.register_feature(ConversionFeature)

    session = core.create_session()
    session = core.add_message(session, "user", "First")
    session1, finals1 = core.send_request(session, {})

    # Second turn should still detect ctn marker on historical native messages
    core2 = AgentCore()
    core2.register_provider(ConversionProvider)
    core2.register_feature(ConversionFeature)

    session2 = core2.add_message(session1, "user", "Second")
    session3, finals2 = core2.send_request(session2, {})

    assert finals2[-1]["content"].endswith("CTN")
