"""
Example 3: Configurable web-search feature.
This feature marks finals with metadata when web_search_enabled is True and prints a notice.
"""

from typing import Any, Dict, List, Optional, Tuple

class WebSearchFeature:
    name: str = "web_search"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "web_search_enabled": {"type": "boolean", "default": False},
            "max_results": {"type": "integer", "default": 5},
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "web_search_enabled",
                "label": "Enable Web Search",
            },
            {
                "type": "number",
                "key": "max_results",
                "label": "Max Results",
                "condition": {"web_search_enabled": True},
            },
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **config}}

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not state.get("config", {}).get("web_search_enabled"):
            return final_messages, native_messages, state
        # Print a simple notice to stdout when enabled
        max_results = state.get("config", {}).get("max_results")
        print(
            f"[WebSearchFeature] Search enabled; annotating finals (max_results={max_results})"
        )
        finals = [
            {**m, "metadata": {**m.get("metadata", {}), "web_search_used": True}}
            for m in final_messages
        ]
        return finals, native_messages, state
