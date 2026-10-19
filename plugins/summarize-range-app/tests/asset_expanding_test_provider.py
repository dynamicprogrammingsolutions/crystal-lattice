"""Test-only provider that mirrors the session-asset expansion contract.

Production providers that support session asset attachments (for example the
OpenAI Responses provider) expand asset references during
``initialize_request``, which runs for every native-history rebuild triggered
by ``core.add_message`` or ``core.rebuild_native_history``. Such providers
resolve the session asset store from the context passed to the provider call
(or from ``state["_request_context"]``) and fail when it is missing.

This provider reproduces that contract deterministically and without network
access, so application plugins driving internal model requests can be tested
against it. It is the test-side twin of the asset-expansion behavior covered
for the streaming leg by the Ollama integration test.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Tuple

from agent_core.types import ProviderPlugin


def _iter_asset_refs(value: Any):
    """Yield every ``asset_ref`` dict found anywhere in a native payload."""

    if isinstance(value, dict):
        ref = value.get("asset_ref")
        if isinstance(ref, dict) and isinstance(ref.get("asset_id"), str):
            yield ref
        for child in value.values():
            yield from _iter_asset_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_asset_refs(child)


class AssetExpandingTestProvider(ProviderPlugin):
    """Identity provider that expands asset refs during initialize_request."""

    name: str = "asset_expanding_test_provider"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "response_text": {"type": "string", "required": False},
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "config": dict(config),
            "runtime_state": {"accumulated_content": "", "native_chunks": []},
            "loaded_asset_ids": [],
        }

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["provider:asset_expanding_test"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return list(messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        resolved_context = (
            context
            if isinstance(context, dict)
            else (
                state.get("_request_context")
                if isinstance(state.get("_request_context"), dict)
                else None
            )
        )
        asset_refs = list(_iter_asset_refs(native_messages))
        if not asset_refs:
            return list(native_messages), {
                **state,
                "request": {
                    "payload": {"model": (state.get("config") or {}).get("model")}
                },
                "runtime_state": {"accumulated_content": "", "native_chunks": []},
            }
        store = (
            resolved_context.get("session_asset_store")
            if isinstance(resolved_context, dict)
            else None
        )
        if store is None:
            raise RuntimeError(
                "[asset_expanding_test_provider] session asset attachment "
                "requires session_asset_store in context"
            )
        loaded: List[str] = list(state.get("loaded_asset_ids") or [])
        for asset_ref in asset_refs:
            session_id = asset_ref.get("session_id")
            asset_id = asset_ref.get("asset_id")
            if not isinstance(session_id, str) or not isinstance(asset_id, str):
                raise ValueError(
                    "[asset_expanding_test_provider] invalid session asset reference"
                )
            record = store.load(session_id, asset_id)
            payload = store.load_bytes(session_id, asset_id)
            if record.attachment_type != "image":
                raise ValueError(
                    "[asset_expanding_test_provider] unexpected attachment type "
                    f"{record.attachment_type!r}"
                )
            if not payload:
                raise ValueError("[asset_expanding_test_provider] empty asset payload")
            if asset_id not in loaded:
                loaded.append(asset_id)
        return list(native_messages), {
            **state,
            "request": {"payload": {"model": (state.get("config") or {}).get("model")}},
            "loaded_asset_ids": loaded,
            "runtime_state": {"accumulated_content": "", "native_chunks": []},
        }

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        config = state.get("config") or {}
        response_text = str(config.get("response_text") or "Summary reply")
        if response_text:
            yield {"content": response_text}

    def process_chunk(
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
        partial_content = native_chunk.get("content", "")
        runtime_state = state.get("runtime_state") or {}
        new_state = {
            **state,
            "runtime_state": {
                **runtime_state,
                "accumulated_content": str(
                    runtime_state.get("accumulated_content") or ""
                )
                + str(partial_content),
                "native_chunks": list(runtime_state.get("native_chunks") or [])
                + [native_chunk],
            },
        }
        partial_msg = {"role": "assistant", "content": partial_content, "metadata": {}}
        return (
            ([partial_msg] if partial_content else []),
            [],
            list(native_messages),
            new_state,
        )

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        runtime_state = state.get("runtime_state") or {}
        content = runtime_state.get("accumulated_content") or ""
        if not isinstance(content, str) or not content:
            return [], list(native_messages), state
        assistant = {"role": "assistant", "content": content}
        return [assistant], [*native_messages, assistant], state
