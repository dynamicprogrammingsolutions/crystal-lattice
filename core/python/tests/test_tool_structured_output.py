from __future__ import annotations

import json
from typing import Any, Dict, List

from agent_core import AgentCore


class StructuredImageTool:
    name = "structured_image"
    version = "1.0.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "structured_image",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            }
        ]

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        image_url = "data:image/png;base64,AAA"
        return {
            "success": True,
            "image_url": image_url,
            "tool_output_content": [
                {"type": "input_image", "image_url": image_url, "detail": "high"}
            ],
            "multipartContent": [
                {
                    "type": "image",
                    "content": {"url": image_url},
                    "metadata": {"detail": "high"},
                }
            ],
        }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return json.dumps({"image_url": result["image_url"], "detail": "high"})


def test_iter_tool_messages_preserves_structured_tool_output_content() -> None:
    core = AgentCore()
    core.register_tool(StructuredImageTool)

    messages = list(
        core.iter_tool_messages(
            [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "structured_image",
                        "arguments": "{}",
                    },
                }
            ],
            config={},
        )
    )

    assert len(messages) == 1
    message = messages[0]
    metadata = message["metadata"]
    assert metadata["tool_output_content"] == [
        {
            "type": "input_image",
            "image_url": "data:image/png;base64,AAA",
            "detail": "high",
        }
    ]
    assert json.loads(message["content"]) == {
        "image_url": "data:image/png;base64,AAA",
        "detail": "high",
    }
    assert message["multipartContent"] == [
        {
            "type": "image",
            "content": {"url": "data:image/png;base64,AAA"},
            "metadata": {"detail": "high"},
        }
    ]
