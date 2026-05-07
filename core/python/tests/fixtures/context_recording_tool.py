"""Tool plugin that records the context it receives.

Used for testing that context enrichment works correctly for tools.
"""

from typing import Any, Dict, List, Optional


class ContextRecordingTool:
    """Tool plugin that records the context passed to execute_tool and stream_tool."""

    name = "context_recording"
    version = "1.0.0"

    # Class-level storage for captured contexts
    _captured_contexts: List[Dict[str, Any]] = []

    @classmethod
    def get_captured_contexts(cls) -> List[Dict[str, Any]]:
        """Return all captured contexts and clear the storage."""
        contexts = list(cls._captured_contexts)
        cls._captured_contexts = []
        return contexts

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        return []

    def required_tags(self) -> List[str]:
        return []

    def forbidden_tags(self) -> List[str]:
        return []

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "record_tool_context",
                    "description": "Record the context for testing.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Optional message to include.",
                            }
                        },
                    },
                },
            }
        ]

    def execute_tool(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any | None = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Record the context
        if isinstance(context, dict):
            ContextRecordingTool._captured_contexts.append({
                **context,
                "_tool_name": tool_name,
                "_payload": payload,
            })

        return {
            "success": True,
            "result": "context_recorded",
            "tool_name": tool_name,
        }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("success"):
            return f"Context recorded for tool: {result.get('tool_name')}"
        return f"Error: {result.get('error')}"


__all__ = ["ContextRecordingTool"]
