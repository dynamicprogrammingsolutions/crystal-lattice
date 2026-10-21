import pytest

from agent_core import AgentCore
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider


@pytest.mark.parametrize("role", ["user", "assistant", "system"])
def test_retained_history_edit_preserves_multipart_content(role: str) -> None:
    core = AgentCore()
    core.register_provider(EchoOpenAILikeProvider)
    config = {"provider": "echo_openai_like", "model": "test-model"}
    parts = [{"type": "text", "content": "Preserved part", "metadata": {"fixture": True}}]
    session = core.add_message(
        core.create_session(),
        role,
        "Original content",
        metadata={"fixture": True},
        config=config,
        multipart_content=parts,
    )
    session, _ = core.send_request(session, config)
    assert session.messages[0].multipart_content == parts
    assert session.metadata is not None
    assert session.metadata["native_messages"]

    modified = core.modify_message(session, 0, "Changed content", config)

    assert modified.messages[0].content == "Changed content"
    assert modified.messages[0].role == role
    assert modified.messages[0].metadata is not None
    assert modified.messages[0].metadata["fixture"] is True
    assert modified.messages[0].multipart_content == parts
    assert session.messages[0].content == "Original content"
    assert session.messages[0].multipart_content == parts
