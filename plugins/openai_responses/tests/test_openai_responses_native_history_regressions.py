from __future__ import annotations

import base64
from typing import Any, Dict, List

from agent_app.session_assets import FilesystemSessionAssetStore
from agent_core import AgentCore

from openai_responses_plugins.openai_responses_attachments_extension import (
    OpenAIResponsesAttachmentsExtension,
)
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_tools_extension import (
    OpenAIResponsesToolsExtension,
)
from plugins.math_tools import MathTools


class _ScriptedResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return self._payload


class _ScriptedResponsesResource:
    def __init__(self, payloads: List[Dict[str, Any]]) -> None:
        self._payloads = list(payloads)
        self.calls: List[Dict[str, Any]] = []
        self._cursor = 0

    def create(self, **kwargs: Any) -> _ScriptedResponse:
        self.calls.append(kwargs)
        if self._cursor >= len(self._payloads):
            raise RuntimeError("no scripted response remaining")
        payload = self._payloads[self._cursor]
        self._cursor += 1
        return _ScriptedResponse(payload)


class _ScriptedClient:
    def __init__(self, payloads: List[Dict[str, Any]]) -> None:
        self.responses = _ScriptedResponsesResource(payloads)


class _ScriptedFileObject:
    def __init__(self, file_id: str) -> None:
        self.id = file_id

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return {"id": self.id}


class _ScriptedFilesResource:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self._cursor = 0

    def create(self, **kwargs: Any) -> _ScriptedFileObject:
        self.calls.append(kwargs)
        self._cursor += 1
        return _ScriptedFileObject(f"file_{self._cursor}")


class _ScriptedUploadClient(_ScriptedClient):
    def __init__(self, payloads: List[Dict[str, Any]]) -> None:
        super().__init__(payloads)
        self.files = _ScriptedFilesResource()


class _ScriptedNativeHistoryProvider(OpenAIResponsesProvider):
    scripted_payloads: List[Dict[str, Any]] = []
    last_client: _ScriptedClient | None = None

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        if type(self).last_client is None:
            type(self).last_client = _ScriptedClient(list(type(self).scripted_payloads))
        state["client"] = type(self).last_client
        return state


class _ScriptedUploadNativeHistoryProvider(OpenAIResponsesProvider):
    scripted_payloads: List[Dict[str, Any]] = []
    last_client: _ScriptedUploadClient | None = None

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        if type(self).last_client is None:
            type(self).last_client = _ScriptedUploadClient(list(type(self).scripted_payloads))
        state["client"] = type(self).last_client
        return state


def _config() -> Dict[str, Any]:
    return {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
        "provider": "openai_responses",
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(_ScriptedNativeHistoryProvider)
    return core


def _build_upload_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(_ScriptedUploadNativeHistoryProvider, [OpenAIResponsesAttachmentsExtension])
    return core


def _response_ids(native_messages: List[Dict[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for item in native_messages:
        if not isinstance(item, dict):
            continue
        metadata = item.get("_metadata")
        if not isinstance(metadata, dict):
            continue
        response_id = metadata.get("response_id")
        if isinstance(response_id, str) and response_id:
            ids.add(response_id)
    return ids


def test_native_history_survives_across_core_instances() -> None:
    _ScriptedNativeHistoryProvider.last_client = None
    _ScriptedNativeHistoryProvider.scripted_payloads = [
        {
            "id": "resp_1",
            "output": [
                {
                    "type": "reasoning",
                    "summary": [{"type": "summary_text", "text": "first reasoning"}],
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "First answer"}],
                },
            ],
        },
        {
            "id": "resp_2",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Second answer"}],
                }
            ],
        },
    ]

    core1 = _build_core()
    config = _config()

    session = core1.create_session()
    session = core1.add_message(session, "user", "first turn")
    session_after_first, first_responses = core1.send_request(session, config)

    assert first_responses[-1]["content"] == "First answer"
    native_after_first = (session_after_first.metadata or {}).get("native_messages") or []
    assert any(isinstance(item, dict) and item.get("type") == "reasoning" for item in native_after_first)

    core2 = _build_core()
    session_after_first = core2.add_message(
        session_after_first,
        "user",
        "second turn",
        config=config,
    )
    _session_after_second, second_responses = core2.send_request(session_after_first, config)

    assert second_responses[-1]["content"] == "Second answer"

    client = _ScriptedNativeHistoryProvider.last_client
    assert client is not None
    assert len(client.responses.calls) == 2

    second_input = client.responses.calls[1]["input"]
    assert any(
        isinstance(item, dict)
        and item.get("type") == "reasoning"
        for item in second_input
    )


def test_slice_and_fork_keep_response_segments_coherent() -> None:
    _ScriptedNativeHistoryProvider.last_client = None
    _ScriptedNativeHistoryProvider.scripted_payloads = [
        {
            "id": "resp_1",
            "output": [
                {
                    "type": "reasoning",
                    "summary": [{"type": "summary_text", "text": "first reasoning"}],
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "First answer"}],
                },
            ],
        },
        {
            "id": "resp_2",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Second answer"}],
                }
            ],
        },
    ]

    core = _build_core()
    config = _config()

    session = core.create_session()
    session = core.add_message(session, "user", "first turn", config=config)
    session, _ = core.send_request(session, config)
    session = core.add_message(session, "user", "second turn", config=config)
    session, _ = core.send_request(session, config)

    assert [message.content for message in session.messages] == [
        "first turn",
        "First answer",
        "second turn",
        "Second answer",
    ]

    first_assistant_md = session.messages[1].metadata or {}
    native_indices = first_assistant_md.get("native_indices") or []
    assert isinstance(native_indices, list)
    assert len(native_indices) > 1

    deleted = core.slice_session(session, config, remove_indices=[0, 1])
    deleted_native = (deleted.metadata or {}).get("native_messages") or []
    assert _response_ids(deleted_native) == {"resp_2"}
    assert [message.content for message in deleted.messages] == ["second turn", "Second answer"]

    forked = core.fork_session(session, config, upto_index=1, new_session_id="forked")
    forked_native = (forked.metadata or {}).get("native_messages") or []
    assert _response_ids(forked_native) == {"resp_1"}
    assert [message.content for message in forked.messages] == ["first turn", "First answer"]


def test_rebuilt_follow_up_keeps_one_assistant_anchor_for_prior_tool_segment() -> None:
    _ScriptedNativeHistoryProvider.last_client = None
    _ScriptedNativeHistoryProvider.scripted_payloads = [
        {
            "id": "resp_tool_1",
            "output": [
                {
                    "type": "reasoning",
                    "summary": [{"type": "summary_text", "text": "plan"}],
                },
                {
                    "type": "function_call",
                    "call_id": "call_add_1",
                    "name": "add",
                    "arguments": "{\"a\":2,\"b\":3}",
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "phase": "commentary",
                    "content": [{"type": "output_text", "text": "Using tool."}],
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "phase": "final_answer",
                    "content": [],
                },
            ],
        },
        {
            "id": "resp_tool_2",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Final answer: 5"}],
                }
            ],
        },
        {
            "id": "resp_tool_3",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Follow-up answer"}],
                }
            ],
        },
    ]

    config = _config()

    core1 = AgentCore()
    core1.register_provider(_ScriptedNativeHistoryProvider, extensions=[OpenAIResponsesToolsExtension])
    core1.register_tool(MathTools)

    session = core1.create_session()
    session = core1.add_message(session, "user", "Compute 2 + 3 with tools.", config=config)
    session, first_responses = core1.send_request(session, config)

    first_assistant = first_responses[-1]
    tool_calls = (first_assistant.get("metadata") or {}).get("tool_calls") or []
    assert len(tool_calls) == 1
    assert first_assistant.get("content") == "Using tool."

    for tool_message in core1.execute_tool_calls(tool_calls, config):
        session = core1.add_message(
            session,
            role=tool_message.get("role", "tool"),
            content=tool_message.get("content", ""),
            metadata=tool_message.get("metadata"),
            config=config,
        )

    session, second_responses = core1.send_request(session, config)
    assert second_responses[-1].get("content") == "Final answer: 5"

    first_turn_assistants = [
        message
        for message in session.messages
        if message.role == "assistant"
        and (message.metadata or {}).get("response_id") == "resp_tool_1"
    ]
    assert len(first_turn_assistants) == 1

    core2 = AgentCore()
    core2.register_provider(_ScriptedNativeHistoryProvider, extensions=[OpenAIResponsesToolsExtension])
    core2.register_tool(MathTools)

    session = core2.add_message(session, "user", "Say the answer again.", config=config)
    session_after_follow_up, third_responses = core2.send_request(session, config)
    assert third_responses[-1].get("content") == "Follow-up answer"

    rebuilt_first_turn_assistants = [
        message
        for message in session_after_follow_up.messages
        if message.role == "assistant"
        and (message.metadata or {}).get("response_id") == "resp_tool_1"
    ]
    assert len(rebuilt_first_turn_assistants) == 1
    assert rebuilt_first_turn_assistants[0].content == "Using tool."


def test_uploaded_attachment_history_rebuilds_original_multipart_content() -> None:
    _ScriptedUploadNativeHistoryProvider.last_client = None
    _ScriptedUploadNativeHistoryProvider.scripted_payloads = [
        {
            "id": "resp_upload_1",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Attachment processed"}],
                }
            ],
        }
    ]

    config = {**_config(), "attachment_upload_mode": "upload_before_send"}
    core = _build_upload_core()

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Review the attachments.",
        config=config,
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "url": "data:image/png;base64,Zm9v",
                    "mime_type": "image/png",
                    "filename": "image.png",
                },
                "metadata": {},
            },
            {
                "type": "pdf",
                "content": {
                    "data_base64": "JVBERi0xLjQK",
                    "mime_type": "application/pdf",
                    "filename": "brief.pdf",
                },
                "metadata": {},
            },
        ],
    )
    session, responses = core.send_request(session, config)

    assert responses[-1]["content"] == "Attachment processed"

    native_messages = (session.metadata or {}).get("native_messages") or []
    user_message = native_messages[0]
    assert user_message["content"][1] == {
        "type": "input_image",
        "image_url": "data:image/png;base64,Zm9v",
    }
    assert user_message["content"][2] == {
        "type": "input_file",
        "file_data": "JVBERi0xLjQK",
        "filename": "brief.pdf",
    }
    assert user_message["_metadata"]["_openai_responses_uploaded_attachments"] == [
        {"content_index": 1, "uploaded_part": {"type": "input_image", "file_id": "file_1"}},
        {"content_index": 2, "uploaded_part": {"type": "input_file", "file_id": "file_2"}},
    ]

    rebuilt_user = session.messages[0]
    assert rebuilt_user.multipart_content == [
        {
            "type": "image",
            "content": {
                "url": "data:image/png;base64,Zm9v",
                "mime_type": "image/png",
                "filename": "image.png",
            },
            "metadata": {},
        },
        {
            "type": "pdf",
            "content": {
                "data_base64": "JVBERi0xLjQK",
                "mime_type": "application/pdf",
                "filename": "brief.pdf",
            },
            "metadata": {},
        },
    ]


def test_uploaded_attachment_history_slice_and_fork_keep_coherent_native_segments() -> None:
    _ScriptedUploadNativeHistoryProvider.last_client = None
    _ScriptedUploadNativeHistoryProvider.scripted_payloads = [
        {
            "id": "resp_upload_a",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "First uploaded answer"}],
                }
            ],
        },
        {
            "id": "resp_upload_b",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Second uploaded answer"}],
                }
            ],
        },
    ]

    config = {**_config(), "attachment_upload_mode": "upload_before_send"}
    core = _build_upload_core()

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "First attachment turn.",
        config=config,
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "url": "data:image/png;base64,Zm9v",
                    "mime_type": "image/png",
                    "filename": "one.png",
                },
                "metadata": {},
            }
        ],
    )
    session, _ = core.send_request(session, config)

    session = core.add_message(
        session,
        "user",
        "Second attachment turn.",
        config=config,
        multipart_content=[
            {
                "type": "pdf",
                "content": {
                    "data_base64": "JVBERi0xLjQK",
                    "mime_type": "application/pdf",
                    "filename": "two.pdf",
                },
                "metadata": {},
            }
        ],
    )
    session, _ = core.send_request(session, config)

    deleted = core.slice_session(session, config, remove_indices=[0, 1])
    deleted_native = (deleted.metadata or {}).get("native_messages") or []
    assert _response_ids(deleted_native) == {"resp_upload_b"}
    assert deleted_native[0]["_metadata"]["_openai_responses_uploaded_attachments"] == [
        {"content_index": 1, "uploaded_part": {"type": "input_file", "file_id": "file_2"}},
    ]
    assert deleted.messages[0].multipart_content == [
        {
            "type": "pdf",
            "content": {
                "data_base64": "JVBERi0xLjQK",
                "mime_type": "application/pdf",
                "filename": "two.pdf",
            },
            "metadata": {},
        }
    ]

    forked = core.fork_session(session, config, upto_index=1, new_session_id="uploaded-fork")
    forked_native = (forked.metadata or {}).get("native_messages") or []
    assert _response_ids(forked_native) == {"resp_upload_a"}
    assert forked_native[0]["_metadata"]["_openai_responses_uploaded_attachments"] == [
        {"content_index": 1, "uploaded_part": {"type": "input_image", "file_id": "file_1"}},
    ]
    assert forked.messages[0].multipart_content == [
        {
            "type": "image",
            "content": {
                "url": "data:image/png;base64,Zm9v",
                "mime_type": "image/png",
                "filename": "one.png",
            },
            "metadata": {},
        }
    ]


def test_session_asset_attachment_history_rebuilds_original_asset_ref(tmp_path) -> None:
    _ScriptedUploadNativeHistoryProvider.last_client = None
    _ScriptedUploadNativeHistoryProvider.scripted_payloads = [
        {
            "id": "resp_asset_1",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Asset processed"}],
                }
            ],
        }
    ]

    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    image_record = asset_store.store_base64(
        session_id="sess_asset",
        attachment_type="image",
        filename="square.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-bytes").decode("ascii"),
    )

    config = {
        **_config(),
        "attachment_upload_mode": "upload_before_send",
        "_session_asset_store": asset_store,
    }
    core = _build_upload_core()

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Review the stored image.",
        config=config,
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "asset_ref": image_record.asset_ref(),
                    "mime_type": image_record.mime_type,
                    "filename": image_record.filename,
                },
                "metadata": {},
            }
        ],
    )
    session, responses = core.send_request(session, config)

    assert responses[-1]["content"] == "Asset processed"
    native_messages = (session.metadata or {}).get("native_messages") or []
    user_message = native_messages[0]
    assert user_message["_metadata"]["_openai_responses_uploaded_attachments"] == [
        {"content_index": 1, "uploaded_part": {"type": "input_image", "file_id": "file_1"}}
    ]

    rebuilt_user = session.messages[0]
    assert rebuilt_user.multipart_content == [
        {
            "type": "image",
            "content": {
                "asset_ref": image_record.asset_ref(),
                "mime_type": "image/png",
                "filename": "square.png",
            },
            "metadata": {},
        }
    ]


def test_native_history_retains_reasoning_items_with_encrypted_content_for_follow_up() -> (
    None
):
    """Reasoning items with ``encrypted_content`` must survive core/native
    conversion and be replayed into the follow-up request's ``input``.

    This verifies that the existing native-history replay mechanism is
    sufficient for ``reasoning.context: "all_turns"`` — no second
    conversation-state mechanism is needed. The API's requirement ("manually
    replaying the complete response history") is already satisfied by the
    retained native history.
    """
    _ScriptedNativeHistoryProvider.last_client = None
    _ScriptedNativeHistoryProvider.scripted_payloads = [
        {
            "id": "resp_enc_1",
            "output": [
                {
                    "type": "reasoning",
                    "id": "rs_enc_1",
                    "summary": [
                        {"type": "summary_text", "text": "first reasoning with encrypted content"}
                    ],
                    "content": None,
                    "encrypted_content": "enc_blob_abc123",
                    "status": None,
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": "First answer"}
                    ],
                },
            ],
        },
        {
            "id": "resp_enc_2",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": "Second answer"}
                    ],
                }
            ],
        },
    ]

    core = _build_core()
    config = _config()

    session = core.create_session()
    session = core.add_message(session, "user", "first turn")
    session_after_first, first_responses = core.send_request(session, config)

    assert first_responses[-1]["content"] == "First answer"

    # After turn 1, the retained native history must contain the reasoning
    # item with its ``encrypted_content`` intact.
    native_after_first = (
        session_after_first.metadata or {}
    ).get("native_messages") or []
    reasoning_items_after_first = [
        item
        for item in native_after_first
        if isinstance(item, dict) and item.get("type") == "reasoning"
    ]
    assert reasoning_items_after_first, "expected a reasoning item after turn 1"
    assert any(
        item.get("encrypted_content") == "enc_blob_abc123"
        for item in reasoning_items_after_first
    ), "reasoning item must retain its encrypted_content"

    session_after_first = core.add_message(
        session_after_first,
        "user",
        "second turn",
        config=config,
    )
    _session_after_second, second_responses = core.send_request(
        session_after_first, config
    )

    assert second_responses[-1]["content"] == "Second answer"

    client = _ScriptedNativeHistoryProvider.last_client
    assert client is not None
    assert len(client.responses.calls) == 2

    # The second request's ``input`` must contain the reasoning item from
    # turn 1 (with its ``encrypted_content``), replayed via native history.
    second_input = client.responses.calls[1]["input"]
    reasoning_in_second_input = [
        item
        for item in second_input
        if isinstance(item, dict) and item.get("type") == "reasoning"
    ]
    assert reasoning_in_second_input, (
        "expected the reasoning item from turn 1 to be replayed into turn 2"
    )
    assert any(
        item.get("encrypted_content") == "enc_blob_abc123"
        for item in reasoning_in_second_input
    ), "replayed reasoning item must retain its encrypted_content"