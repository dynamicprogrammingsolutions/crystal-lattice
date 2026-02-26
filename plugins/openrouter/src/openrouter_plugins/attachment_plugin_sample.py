"""
OpenRouter Provider Plugin

Provides access to multiple LLM providers through OpenRouter's unified API.
Compatible with OpenAI Chat Completions API format.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core import FeaturePlugin

class OpenRouterAttachmentPluginSample(FeaturePlugin):
    name: str = "openrouter_attachment_plugin_sample"
    version: str = "0.1.0"

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "composer_attachment",
                "key": "openrouter:attachment:image",
                "attachment_type": "image",
                "supports_url": True,
                "supported_file_types": ["png", "jpg", "jpeg", "webp", "gif"],
                "display_placement": "above",
                "label": "Image",
                "icon": "image",
                "metadata_ui": {
                    "prompt": "if_missing_required",
                    "defaults": {
                        "notes": "",
                    },
                    "config_schema": [
                        {
                            "key": "title",
                            "type": "string",
                            "label": "Title",
                            "description": "Testing-only attachment metadata (not sent to OpenRouter).",
                            "required": True,
                        },
                        {
                            "key": "notes",
                            "type": "multiline",
                            "label": "Notes",
                            "description": "Testing-only attachment metadata (not sent to OpenRouter).",
                            "required": False,
                            "default": "",
                        },
                        {
                            "key": "source_url",
                            "type": "string",
                            "label": "Source URL",
                            "description": "Testing-only attachment metadata (not sent to OpenRouter).",
                            "required": False,
                        },
                    ],
                    "ui_schema": [
                        {
                            "ui_type": "config",
                            "type": "string",
                            "key": "title",
                            "label": "Title",
                        },
                        {
                            "ui_type": "config",
                            "type": "multiline",
                            "key": "notes",
                            "label": "Notes",
                        },
                        {
                            "ui_type": "config",
                            "type": "string",
                            "key": "source_url",
                            "label": "Source URL",
                        },
                    ],
                },
            },
            {
                "ui_type": "composer_attachment",
                "key": "openrouter:attachment:pdf",
                "attachment_type": "pdf",
                "supports_url": True,
                "supported_file_types": ["pdf"],
                "display_placement": "above",
                "label": "PDF (UI only)",
                "icon": "file-text",
                "metadata_ui": {
                    "prompt": "if_missing_required",
                    "defaults": {
                        "notes": "",
                    },
                    "config_schema": [
                        {
                            "key": "title",
                            "type": "string",
                            "label": "Title",
                            "description": "Testing-only attachment metadata (not sent to OpenRouter).",
                            "required": True,
                        },
                        {
                            "key": "notes",
                            "type": "multiline",
                            "label": "Notes",
                            "description": "Testing-only attachment metadata (not sent to OpenRouter).",
                            "required": False,
                            "default": "",
                        },
                    ],
                    "ui_schema": [
                        {
                            "ui_type": "config",
                            "type": "string",
                            "key": "title",
                            "label": "Title",
                        },
                        {
                            "ui_type": "config",
                            "type": "multiline",
                            "key": "notes",
                            "label": "Notes",
                        },
                    ],
                },
            },
        ]
