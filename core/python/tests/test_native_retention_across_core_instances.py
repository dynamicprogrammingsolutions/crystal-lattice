from typing import Any, Dict, List, Tuple
from dataclasses import dataclass

from agent_core import AgentCore
from agent_core.types import ProviderPlugin, ProviderExtensionPlugin


@dataclass
class RetentionProvider(ProviderPlugin):
    name: str = "retention_provider"
    version: str = "1.0.0"




    # --- Message conversion ---
    def to_native_messages(self, messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Convert to native; intentionally do NOT emit 'preserved' marker from core messages
        natives: List[Dict[str, Any]] = []
        for m in messages:
            natives.append({"role": m["role"], "content": m.get("content", ""), "converted_to_native": True})
        return natives

    def from_native_messages(self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Convert native to core and note that conversion happened
        cores: List[Dict[str, Any]] = []
        for m in native_messages:
            md = {"from_native_used": True}
            if m.get("preserved"):
                md["saw_preserved"] = True
            cores.append({"role": m.get("role", "assistant"), "content": m.get("content", ""), "metadata": md})
        return cores



    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # If any native message carries the 'preserved' flag, echo that we detected preservation
        has_preserved = any(isinstance(m, dict) and m.get("preserved") for m in native_messages)
        content = "Preserved" if has_preserved else "Lost"
        final = [{"role": "assistant", "content": content}]
        return final, native_messages, state


    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Non-streaming path: rely on finalize to emit finals
        return [], [], native_messages, state



@dataclass
class RetentionExtension(ProviderExtensionPlugin):
    name: str = "retention_extension"
    version: str = "1.0.0"


    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Mark full native history as preserved; this flag would be lost if recomputed from core
        marked = [{**m, "preserved": True} for m in native_messages]
        return final_messages, marked, state


def test_retains_native_history_across_core_instances():
    core1 = AgentCore()
    core1.register_provider(RetentionProvider, extensions=[RetentionExtension])

    config: Dict[str, Any] = {}
    session = core1.create_session()
    session = core1.add_message(session, "user", "Hello")

    # Turn 1
    session1, finals1 = core1.send_request(session, config)
    assert finals1[-1]["role"] == "assistant"
    # First turn may be either, we don't rely on it

    # Validate lossy round-trip property directly on the provider conversion functions
    prov = RetentionProvider()
    st: Dict[str, Any] = {}
    sample_native = [{"role": "assistant", "content": "X", "preserved": True}]
    core_from_native = prov.from_native_messages(sample_native, st)
    roundtrip = prov.to_native_messages(core_from_native, st)
    assert roundtrip != sample_native

    # Turn 2 with a new Core instance, using the session returned from Turn 1
    core2 = AgentCore()
    core2.register_provider(RetentionProvider, extensions=[RetentionExtension])

    session2 = core2.add_message(session1, "user", "Second")
    session3, finals2 = core2.send_request(session2, config)

    assert finals2[-1]["content"] == "Preserved"
