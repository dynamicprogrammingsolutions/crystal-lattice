"""OpenAI Responses usage tracking extension.

This extension owns public usage metadata attachment and cumulative accounting.
The provider only passes through raw response usage in private native metadata so
the non-streaming path can expose the same metadata fields as the streaming path.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin

from .chatgpt_rate_limits import (
    load_rate_limits_state,
    resolve_rate_limits_path,
)
from .chatgpt_usage_journal import (
    append_request_usage,
    iter_journal_records,
    resolve_usage_journal_path,
    resolve_working_directory,
    session_id_from_state,
)
from .cost_bucket import resolve_cost_bucket
from .openai_responses_pricing import (
    estimate_usage_cost,
    estimate_usage_cost_breakdown,
)
from .openai_responses_codex_models import (
    load_manual_chatgpt_model_pricing as _load_manual_chatgpt_model_pricing_shared,
)

_RAW_USAGE_METADATA_KEY = "_openai_responses_usage_raw"
_RAW_SERVICE_TIER_METADATA_KEY = "_openai_responses_service_tier"
_RAW_REASONING_MODE_METADATA_KEY = "_openai_responses_reasoning_mode"
_CHATGPT_RATE_LIMIT_SNAPSHOTS_STATE_KEY = (
    "_openai_responses_chatgpt_rate_limit_snapshots"
)
_PERSISTED_USAGE_ROOT_KEYS = frozenset(
    {
        "input_tokens",
        "input_tokens_details",
        "output_tokens",
        "output_tokens_details",
        "completion_tokens_details",
        "total_tokens",
    }
)
_PERSISTED_USAGE_DETAIL_KEYS = {
    "input_tokens_details": frozenset(
        {
            "cached_tokens",
            "cache_write_tokens",
        }
    ),
    "output_tokens_details": frozenset({"reasoning_tokens"}),
    "completion_tokens_details": frozenset({"reasoning_tokens"}),
}
_PUBLIC_USAGE_METADATA_KEYS = (
    "usage_turn_input_tokens_cumulative",
    "usage_turn_input_tokens_cumulative_formatted",
    "usage_turn_cached_tokens_cumulative",
    "usage_turn_cached_tokens_cumulative_formatted",
    "usage_turn_cache_write_tokens_cumulative",
    "usage_turn_cache_write_tokens_cumulative_formatted",
    "usage_turn_output_tokens_cumulative",
    "usage_turn_output_tokens_cumulative_formatted",
    "usage_prompt_tokens_formatted",
    "usage_cached_tokens_formatted",
    "usage_cache_write_tokens_formatted",
    "usage_estimated_cached_tokens",
    "usage_estimated_cached_tokens_formatted",
    "usage_completion_tokens_formatted",
    "usage_effective_auth_mode",
    "usage_effective_auth_mode_label",
    "usage_bucket",
    "usage_service_tier",
    "usage_reasoning_mode",
    "usage_total_cost",
    "usage_total_cost_formatted",
    "usage_total_cost_cumulative",
    "usage_total_cost_cumulative_formatted",
    "usage_turn_cost_cumulative",
    "usage_turn_cost_cumulative_formatted",
    "usage_turn_reasoning_tokens_cumulative",
    "usage_turn_reasoning_tokens_cumulative_formatted",
)
_USAGE_MESSAGE_FOOTER_FIELDS = (
    "input",
    "cached",
    "cache_write",
    "estimated_cached",
    "completion",
    "auth",
    "tier",
    "mode",
    "cost",
    "turn_cost",
    "turn_reasoning",
    "turn_input",
    "turn_cached",
    "turn_output",
)


def unsupported_usage_root_keys(usage: Dict[str, Any]) -> Tuple[str, ...]:
    """Return OpenAI usage root keys outside the persisted local contract."""

    return tuple(key for key in usage if key not in _PERSISTED_USAGE_ROOT_KEYS)


def unsupported_usage_paths(usage: Dict[str, Any]) -> Tuple[str, ...]:
    """Return OpenAI usage paths outside the persisted local contract."""

    unsupported = list(unsupported_usage_root_keys(usage))
    for root_key, supported_detail_keys in _PERSISTED_USAGE_DETAIL_KEYS.items():
        details = usage.get(root_key)
        if not isinstance(details, dict):
            continue
        unsupported.extend(
            f"{root_key}.{detail_key}"
            for detail_key in details
            if detail_key not in supported_detail_keys
        )
    return tuple(unsupported)


def project_usage_for_persistence(usage: Dict[str, Any]) -> Dict[str, Any]:
    """Project raw OpenAI usage onto the supported persisted field paths."""

    if not unsupported_usage_paths(usage):
        return usage

    projected: Dict[str, Any] = {}
    for key, value in usage.items():
        if key not in _PERSISTED_USAGE_ROOT_KEYS:
            continue
        supported_detail_keys = _PERSISTED_USAGE_DETAIL_KEYS.get(key)
        if supported_detail_keys is None or not isinstance(value, dict):
            projected[key] = value
            continue
        projected[key] = {
            detail_key: detail_value
            for detail_key, detail_value in value.items()
            if detail_key in supported_detail_keys
        }
    return projected


class OpenAIResponsesUsageExtension(ProviderExtensionPlugin):
    name: str = "openai_responses_usage"
    version: str = "0.1.0"
    priority: int = 60

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "pricing_snapshot_path": {
                "type": "string",
                "required": False,
                "description": "Optional path override for the checked-in OpenAI pricing snapshot.",
            },
            "show_usage": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Show OpenAI usage message-footer and status-bar elements.",
            },
            "usage_message_footer_fields": {
                "type": "array",
                "required": False,
                "items": {
                    "type": "string",
                    "enum": list(_USAGE_MESSAGE_FOOTER_FIELDS),
                },
                "description": (
                    "Optional field filter for OpenAI usage message footers. "
                    "When omitted, the existing complete footer is preserved."
                ),
            },
            "cost_bucket": {
                "type": "string",
                "required": False,
                "default": "openai-responses",
                "description": (
                    "Base name of the provider-defined cost bucket used by the "
                    "generic cost tracking plugin. The provider appends the "
                    "active endpoint suffix ('-chatgpt' or '-api') to form the "
                    "final bucket."
                ),
            },
            "show_estimated_cached_tokens": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Show estimated cached tokens for ChatGPT-backed usage footers.",
            },
            "show_openai_auth_mode": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Show the effective OpenAI auth mode in usage footers.",
            },
            "track_chatgpt_usage_journal": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Append ChatGPT-backed request usage and rate-limit snapshots "
                    "to the append-only ChatGPT usage journal (NDJSON)."
                ),
            },
            "chatgpt_usage_journal_path": {
                "type": "string",
                "required": False,
                "description": (
                    "Optional path override for the ChatGPT usage journal file. "
                    "Defaults to a chatgpt-usage-journal.ndjson file next to the "
                    "ChatGPT rate-limits file."
                ),
            },
            "track_chatgpt_usage_summary_csv": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Also append a simplified per-record summary CSV "
                    "(time, working_directory, session_id, estimated_cost, "
                    "total_cost since the last reset, used_percent) whenever a "
                    "journal record is written."
                ),
            },
            "chatgpt_usage_summary_csv_path": {
                "type": "string",
                "required": False,
                "description": (
                    "Optional path override for the simplified ChatGPT usage "
                    "summary CSV. Defaults to a chatgpt-usage-summary.csv file "
                    "next to the usage journal."
                ),
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = (tags, models)
        if isinstance(config, dict) and config.get("show_usage") is False:
            return []

        configured_fields = (
            config.get("usage_message_footer_fields")
            if isinstance(config, dict)
            else None
        )
        selected_fields = (
            {
                value
                for value in configured_fields
                if isinstance(value, str) and value in _USAGE_MESSAGE_FOOTER_FIELDS
            }
            if isinstance(configured_fields, list)
            else None
        )

        def includes(field: str) -> bool:
            return selected_fields is None or field in selected_fields

        elements: List[Dict[str, Any]] = []
        if includes("input"):
            elements.append(
                {
                    "ui_type": "message_footer",
                    "data": "metadata.usage_prompt_tokens_formatted",
                    "template": "input: {{data}}",
                }
            )
        if includes("cached"):
            elements.append(
                {
                    "ui_type": "message_footer",
                    "data": "metadata.usage_cached_tokens_formatted",
                    "template": "cached: {{data}}",
                    "condition": {
                        "not": {
                            "path": "metadata.usage_effective_auth_mode",
                            "eq": "chatgpt",
                        }
                    },
                }
            )
        if includes("cache_write"):
            elements.append(
                {
                    "ui_type": "message_footer",
                    "data": "metadata.usage_cache_write_tokens_formatted",
                    "template": "cache write: {{data}}",
                    "condition": {
                        "path": "metadata.usage_cache_write_tokens_formatted",
                        "exists": True,
                    },
                }
            )
        if (
            includes("estimated_cached")
            and isinstance(config, dict)
            and config.get("show_estimated_cached_tokens") is True
        ):
            elements.append(
                {
                    "ui_type": "message_footer",
                    "data": "metadata.usage_estimated_cached_tokens_formatted",
                    "template": "estimated cached: {{data}}",
                    "condition": {
                        "all": [
                            {
                                "path": "metadata.usage_effective_auth_mode",
                                "eq": "chatgpt",
                            },
                            {
                                "path": "metadata.usage_estimated_cached_tokens_formatted",
                                "exists": True,
                            },
                        ]
                    },
                }
            )
        if includes("completion"):
            elements.append(
                {
                    "ui_type": "message_footer",
                    "data": "metadata.usage_completion_tokens_formatted",
                    "template": "completion: {{data}}",
                }
            )
        if (
            includes("auth")
            and isinstance(config, dict)
            and config.get("show_openai_auth_mode") is True
        ):
            elements.append(
                {
                    "ui_type": "message_footer",
                    "data": "metadata.usage_effective_auth_mode_label",
                    "template": "auth: {{data}}",
                    "condition": {
                        "path": "metadata.usage_effective_auth_mode_label",
                        "exists": True,
                    },
                }
            )
        if includes("tier"):
            elements.append(
                {
                    "ui_type": "message_footer",
                    "data": "metadata.usage_service_tier",
                    "template": "tier: {{data}}",
                    "condition": {
                        "any": [
                            {"path": "metadata.usage_service_tier", "eq": "flex"},
                            {
                                "path": "metadata.usage_service_tier",
                                "eq": "priority",
                            },
                        ]
                    },
                }
            )
        if includes("mode"):
            elements.append(
                {
                    "ui_type": "message_footer",
                    "data": "metadata.usage_reasoning_mode",
                    "template": "mode: {{data}}",
                    "condition": {
                        "path": "metadata.usage_reasoning_mode",
                        "eq": "pro",
                    },
                }
            )
        if includes("cost"):
            elements.extend(
                [
                    {
                        "ui_type": "message_footer",
                        "data": "metadata.usage_total_cost_formatted",
                        "template": "estimated cost: {{data}}",
                        "condition": {
                            "path": "metadata.usage_effective_auth_mode",
                            "eq": "chatgpt",
                        },
                    },
                    {
                        "ui_type": "message_footer",
                        "data": "metadata.usage_total_cost_formatted",
                        "template": "cost: {{data}}",
                        "condition": {
                            "not": {
                                "path": "metadata.usage_effective_auth_mode",
                                "eq": "chatgpt",
                            }
                        },
                    },
                ]
            )
        if includes("turn_cost"):
            elements.extend(
                [
                    {
                        "ui_type": "message_footer",
                        "data": "metadata.usage_turn_cost_cumulative_formatted",
                        "template": "estimated turn: {{data}}",
                        "condition": {
                            "path": "metadata.usage_effective_auth_mode",
                            "eq": "chatgpt",
                        },
                    },
                    {
                        "ui_type": "message_footer",
                        "data": "metadata.usage_turn_cost_cumulative_formatted",
                        "template": "turn: {{data}}",
                        "condition": {
                            "not": {
                                "path": "metadata.usage_effective_auth_mode",
                                "eq": "chatgpt",
                            }
                        },
                    },
                ]
            )
        footer_fields = (
            (
                "turn_reasoning",
                "metadata.usage_turn_reasoning_tokens_cumulative_formatted",
                "reasoning: {{data}}",
            ),
            (
                "turn_input",
                "metadata.usage_turn_input_tokens_cumulative_formatted",
                "turn input: {{data}}",
            ),
            (
                "turn_cached",
                "metadata.usage_turn_cached_tokens_cumulative_formatted",
                "turn cached: {{data}}",
            ),
            (
                "turn_output",
                "metadata.usage_turn_output_tokens_cumulative_formatted",
                "turn output: {{data}}",
            ),
        )
        for field, data, template in footer_fields:
            if includes(field):
                elements.append(
                    {
                        "ui_type": "message_footer",
                        "data": data,
                        "template": template,
                    }
                )
        return elements

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        _ = (config, models)
        return ["ext:openai_responses_usage"]

    def required_tags(self) -> List[str]:
        return ["openai_responses"]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        _ = config
        return state

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        _ = messages
        return list(native_messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []

        for message in messages:
            if not isinstance(message, dict) or message.get("role") != "assistant":
                out.append(message)
                continue

            metadata_raw = message.get("metadata")
            metadata = dict(metadata_raw) if isinstance(metadata_raw, dict) else {}
            metadata, metadata_changed = self._sanitize_core_message_metadata(metadata)
            native_indices = metadata.get("native_indices")
            if not isinstance(native_indices, list):
                out.append(
                    {**message, "metadata": metadata} if metadata_changed else message
                )
                continue

            extra_md: Dict[str, Any] = {}
            for index in native_indices:
                if not isinstance(index, int) or not (
                    0 <= index < len(native_messages)
                ):
                    continue
                native_item = native_messages[index]
                if not isinstance(native_item, dict):
                    continue
                internal = native_item.get("_metadata")
                candidate = self._public_usage_metadata_from_internal(internal)
                if candidate:
                    extra_md = candidate

            if not extra_md:
                out.append(
                    {**message, "metadata": metadata} if metadata_changed else message
                )
                continue

            merged = dict(metadata)
            for key, value in extra_md.items():
                if key not in merged:
                    merged[key] = value

            out.append({**message, "metadata": merged})

        return out

    @staticmethod
    def _sanitize_core_message_metadata(
        metadata: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], bool]:
        updated = metadata
        changed = False

        usage = metadata.get("usage")
        if isinstance(usage, dict):
            sanitized_usage = project_usage_for_persistence(usage)
            if sanitized_usage is not usage:
                updated = {**updated, "usage": sanitized_usage}
                changed = True

        phase_messages = metadata.get("phase_messages")
        if isinstance(phase_messages, list):
            sanitized_phases: List[Any] = []
            phases_changed = False
            for phase_message in phase_messages:
                if not isinstance(phase_message, dict):
                    sanitized_phases.append(phase_message)
                    continue
                phase_metadata = phase_message.get("metadata")
                if not isinstance(phase_metadata, dict):
                    sanitized_phases.append(phase_message)
                    continue
                phase_usage = phase_metadata.get("usage")
                if not isinstance(phase_usage, dict):
                    sanitized_phases.append(phase_message)
                    continue
                sanitized_phase_usage = project_usage_for_persistence(phase_usage)
                if sanitized_phase_usage is phase_usage:
                    sanitized_phases.append(phase_message)
                    continue
                sanitized_phases.append(
                    {
                        **phase_message,
                        "metadata": {
                            **phase_metadata,
                            "usage": sanitized_phase_usage,
                        },
                    }
                )
                phases_changed = True
            if phases_changed:
                updated = {**updated, "phase_messages": sanitized_phases}
                changed = True

        return updated, changed

    @staticmethod
    def _usage_reasoning_tokens(usage: Dict[str, Any]) -> int:
        try:
            details = (
                usage.get("output_tokens_details")
                or usage.get("completion_tokens_details")
                or {}
            )
            if not isinstance(details, dict):
                return 0
            val = details.get("reasoning_tokens")
            if isinstance(val, (int, float)):
                return int(val)
        except Exception:
            return 0
        return 0

    @staticmethod
    def _effective_auth_mode(state: Dict[str, Any]) -> str:
        config = state.get("config") if isinstance(state, dict) else None
        if not isinstance(config, dict):
            return "api"
        raw = config.get("_openai_responses_effective_auth_mode")
        if isinstance(raw, str) and raw.strip().lower() in {"api", "chatgpt"}:
            return raw.strip().lower()
        requested = config.get("auth_mode")
        if not isinstance(requested, str):
            return "api"
        normalized = requested.strip().lower()
        if normalized == "api_key":
            return "api"
        if normalized == "chatgpt":
            return "chatgpt"
        return "api"

    @staticmethod
    def _effective_auth_mode_label(mode: str) -> str:
        if mode == "chatgpt":
            return "ChatGPT"
        return "API"

    @staticmethod
    def _usage_input_tokens(usage: Dict[str, Any]) -> Optional[int]:
        value = usage.get("input_tokens")
        if isinstance(value, (int, float)):
            return max(0, int(value))
        return None

    @staticmethod
    def _usage_cached_tokens(usage: Dict[str, Any]) -> Optional[int]:
        details = usage.get("input_tokens_details")
        if not isinstance(details, dict):
            return None
        value = details.get("cached_tokens")
        if isinstance(value, (int, float)):
            return max(0, int(value))
        return None

    @staticmethod
    def _usage_cache_write_tokens(usage: Dict[str, Any]) -> Optional[int]:
        details = usage.get("input_tokens_details")
        if not isinstance(details, dict):
            return None
        value = details.get("cache_write_tokens")
        if isinstance(value, (int, float)):
            return max(0, int(value))
        return None

    @classmethod
    def _effective_cached_tokens_from_internal(cls, internal: Any) -> Optional[int]:
        if not isinstance(internal, dict):
            return None
        estimated = internal.get("usage_estimated_cached_tokens")
        if isinstance(estimated, (int, float)) and not isinstance(estimated, bool):
            return max(0, int(estimated))
        usage = cls._public_usage_from_internal(internal)
        if isinstance(usage, dict):
            return cls._usage_cached_tokens(usage)
        return None

    @classmethod
    def _effective_cache_write_tokens_from_internal(
        cls, internal: Any
    ) -> Optional[int]:
        if not isinstance(internal, dict):
            return None
        usage = cls._public_usage_from_internal(internal)
        if isinstance(usage, dict):
            return cls._usage_cache_write_tokens(usage)
        return None

    @staticmethod
    def _usage_output_tokens(usage: Dict[str, Any]) -> Optional[int]:
        value = usage.get("output_tokens")
        if isinstance(value, (int, float)):
            return max(0, int(value))
        return None

    @staticmethod
    def _format_token_count(value: Optional[int]) -> Optional[str]:
        if not isinstance(value, int):
            return None
        return f"{value:,}"

    @staticmethod
    def _public_usage_from_internal(internal: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(internal, dict):
            return None
        usage = internal.get("usage")
        if isinstance(usage, dict) and usage:
            return usage
        usage = internal.get(_RAW_USAGE_METADATA_KEY)
        if isinstance(usage, dict) and usage:
            return usage
        return None

    @staticmethod
    def _existing_total_cost_from_internal(internal: Any) -> Optional[float]:
        if not isinstance(internal, dict):
            return None
        raw_total = internal.get("usage_total_cost")
        if isinstance(raw_total, (int, float)):
            return float(raw_total)
        return None

    @classmethod
    def _public_usage_metadata_from_internal(cls, internal: Any) -> Dict[str, Any]:
        if not isinstance(internal, dict):
            return {}

        out: Dict[str, Any] = {}
        usage = cls._public_usage_from_internal(internal)
        if isinstance(usage, dict) and usage:
            out["usage"] = project_usage_for_persistence(usage)

        has_tool_calls = internal.get("has_tool_calls")
        if isinstance(has_tool_calls, bool):
            out["has_tool_calls"] = has_tool_calls

        for key in _PUBLIC_USAGE_METADATA_KEYS:
            if key in internal:
                out[key] = internal[key]

        return out

    @classmethod
    def _item_usage_for_estimation(cls, item: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(item, dict):
            return None
        internal = item.get("_metadata")
        return cls._public_usage_from_internal(internal)

    @classmethod
    def _is_reduced_history_user_item(cls, item: Any) -> bool:
        return (
            isinstance(item, dict)
            and item.get("type") == "message"
            and item.get("role") == "user"
        )

    @classmethod
    def _is_reduced_history_tool_result_item(cls, item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        if item.get("type") == "function_call_output":
            return True
        return item.get("type") == "message" and item.get("role") == "tool"

    @classmethod
    def _is_reduced_history_usage_item(cls, item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        if cls._is_reduced_history_tool_result_item(item):
            return False
        usage = cls._item_usage_for_estimation(item)
        if not isinstance(usage, dict):
            return False
        if cls._usage_input_tokens(usage) is None:
            return False
        item_type = item.get("type")
        if item_type == "message":
            return item.get("role") == "assistant"
        return item_type in {"function_call", "custom_tool_call"}

    @classmethod
    def _reduced_history_markers(
        cls, native_items: List[Dict[str, Any]]
    ) -> List[Tuple[str, int]]:
        reduced: List[Tuple[str, int]] = []
        for item in native_items:
            if cls._is_reduced_history_user_item(item):
                reduced.append(("user", 0))
                continue
            if cls._is_reduced_history_usage_item(item):
                usage = cls._item_usage_for_estimation(item) or {}
                input_tokens = cls._usage_input_tokens(usage)
                if input_tokens is not None:
                    reduced.append(("usage", input_tokens))
        return reduced

    @classmethod
    def _estimated_cached_tokens_from_markers(
        cls, markers: List[Tuple[str, int]]
    ) -> List[int]:
        estimates: List[int] = []
        previous_turn_first_usage_input: Optional[int] = None
        previous_turn_last_usage_input: Optional[int] = None
        current_turn_first_usage_input: Optional[int] = None
        current_turn_last_usage_input: Optional[int] = None

        for kind, input_tokens in markers:
            if kind == "user":
                if current_turn_first_usage_input is not None:
                    previous_turn_first_usage_input = current_turn_first_usage_input
                    previous_turn_last_usage_input = current_turn_last_usage_input
                current_turn_first_usage_input = None
                current_turn_last_usage_input = None
                continue

            if current_turn_last_usage_input is not None:
                estimated = (
                    current_turn_last_usage_input
                    if current_turn_last_usage_input <= input_tokens
                    else 0
                )
            elif previous_turn_first_usage_input is not None:
                if (
                    previous_turn_last_usage_input is not None
                    and input_tokens > previous_turn_last_usage_input
                ):
                    estimated = previous_turn_last_usage_input
                elif previous_turn_first_usage_input <= input_tokens:
                    estimated = previous_turn_first_usage_input
                else:
                    estimated = 0
            else:
                estimated = 0

            estimates.append(estimated)
            if current_turn_first_usage_input is None:
                current_turn_first_usage_input = input_tokens
            current_turn_last_usage_input = input_tokens

        return estimates

    @classmethod
    def _estimated_cached_tokens_for_current(
        cls,
        base_native: List[Dict[str, Any]],
        usage: Dict[str, Any],
    ) -> Optional[int]:
        input_tokens = cls._usage_input_tokens(usage)
        if input_tokens is None:
            return None
        markers = cls._reduced_history_markers(base_native)
        markers.append(("usage", input_tokens))
        estimates = cls._estimated_cached_tokens_from_markers(markers)
        if not estimates:
            return None
        return estimates[-1]

    @staticmethod
    def _service_tier_from_items(items: List[Dict[str, Any]]) -> Optional[str]:
        for item in items:
            if not isinstance(item, dict):
                continue
            internal = item.get("_metadata")
            if not isinstance(internal, dict):
                continue
            service_tier = internal.get(_RAW_SERVICE_TIER_METADATA_KEY)
            if isinstance(service_tier, str) and service_tier:
                return service_tier
        return None

    @staticmethod
    def _reasoning_mode_from_items(items: List[Dict[str, Any]]) -> Optional[str]:
        for item in items:
            if not isinstance(item, dict):
                continue
            internal = item.get("_metadata")
            if not isinstance(internal, dict):
                continue
            reasoning_mode = internal.get(_RAW_REASONING_MODE_METADATA_KEY)
            if isinstance(reasoning_mode, str) and reasoning_mode:
                return reasoning_mode
        return None

    @staticmethod
    def _attach_internal_md(
        item: Dict[str, Any], extra: Dict[str, Any]
    ) -> Dict[str, Any]:
        base = item.get("_metadata")
        base_md = base if isinstance(base, dict) else {}
        cleaned = {k: v for k, v in base_md.items() if k != _RAW_USAGE_METADATA_KEY}
        return {**item, "_metadata": {**cleaned, **extra}}

    @staticmethod
    def _assistant_message_candidate_indices(items: List[Dict[str, Any]]) -> List[int]:
        indices: List[int] = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            role = item.get("role")
            if role is None or role == "assistant":
                indices.append(idx)
        return indices

    def _select_attach_index(self, items: List[Dict[str, Any]]) -> Optional[int]:
        candidates = self._assistant_message_candidate_indices(items)
        if candidates:
            attach_idx = candidates[-1]
            for idx in reversed(candidates):
                item = items[idx]
                if isinstance(item, dict) and item.get("phase") == "final_answer":
                    return idx
            return attach_idx
        if items:
            return len(items) - 1
        return None

    @classmethod
    def _item_turn_has_tool_calls(cls, item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        internal = item.get("_metadata")
        if isinstance(internal, dict):
            turn = internal.get("turn")
            if isinstance(turn, dict) and isinstance(turn.get("has_tool_calls"), bool):
                return bool(turn.get("has_tool_calls"))
            has_tool_calls = internal.get("has_tool_calls")
            if isinstance(has_tool_calls, bool):
                return has_tool_calls
        item_type = item.get("type")
        if item_type in {"function_call", "custom_tool_call"}:
            return True
        return False

    @classmethod
    def _item_is_turn_usage_boundary(cls, item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        if item.get("type") == "message" and item.get("role") in ("user", "system"):
            return True
        internal = item.get("_metadata")
        usage = cls._public_usage_from_internal(internal)
        if not isinstance(usage, dict):
            return False
        return not cls._item_turn_has_tool_calls(item)

    @staticmethod
    def _item_turn_id(item: Any) -> Optional[int]:
        if not isinstance(item, dict):
            return None
        internal = item.get("_metadata")
        if not isinstance(internal, dict):
            return None
        turn = internal.get("turn")
        if not isinstance(turn, dict):
            return None
        value = turn.get("id")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return int(value)

    @classmethod
    def _current_turn_id(cls, native_items: List[Dict[str, Any]]) -> int:
        last_assigned = 0
        max_seen_turn_id = 0
        current_open: Optional[int] = None

        for item in native_items:
            existing_turn_id = cls._item_turn_id(item)
            if existing_turn_id is not None:
                max_seen_turn_id = max(max_seen_turn_id, existing_turn_id)

            if cls._item_is_turn_usage_boundary(item) and item.get("role") in (
                "user",
                "system",
            ):
                current_open = None
                continue
            usage = cls._item_usage_for_estimation(item)
            if not isinstance(usage, dict):
                continue

            if existing_turn_id is not None:
                if current_open is None:
                    current_open = existing_turn_id
                last_assigned = max(last_assigned, existing_turn_id)
            elif current_open is None:
                current_open = max(last_assigned, max_seen_turn_id) + 1

            if not cls._item_turn_has_tool_calls(item):
                current_open = None

        if current_open is not None:
            return current_open
        return max(last_assigned, max_seen_turn_id) + 1

    def _build_usage_metadata(
        self,
        usage: Dict[str, Any],
        base_native: List[Dict[str, Any]],
        current_items: List[Dict[str, Any]],
        state: Dict[str, Any],
        response_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        prompt_tokens_str = None
        cached_tokens_str = None
        cache_write_tokens_str = None
        estimated_cached_tokens = None
        estimated_cached_tokens_str = None
        completion_tokens_str = None
        cost_str = None
        total_cost = None

        config = state.get("config") if isinstance(state, dict) else None
        model = config.get("model") if isinstance(config, dict) else None
        snapshot_path = (
            config.get("pricing_snapshot_path") if isinstance(config, dict) else None
        )
        manual_pricing = self._manual_model_pricing()
        service_tier = self._service_tier_from_items(current_items)
        reasoning_mode = self._reasoning_mode_from_items(current_items)
        effective_auth_mode = self._effective_auth_mode(state)

        input_tokens = usage.get("input_tokens")
        if isinstance(input_tokens, (int, float)):
            prompt_tokens_str = f"{int(input_tokens):,}"

        reported_cached = None
        try:
            reported_cached = (usage.get("input_tokens_details") or {}).get(
                "cached_tokens"
            )
        except Exception:
            reported_cached = None
        if isinstance(reported_cached, (int, float)):
            cached_tokens_str = f"{int(reported_cached):,}"

        reported_cache_write = self._usage_cache_write_tokens(usage)
        if isinstance(reported_cache_write, int):
            cache_write_tokens_str = f"{reported_cache_write:,}"

        effective_usage = usage
        if effective_auth_mode == "chatgpt":
            estimated_cached_tokens = self._estimated_cached_tokens_for_current(
                base_native, usage
            )
            if isinstance(estimated_cached_tokens, int):
                estimated_cached_tokens_str = f"{estimated_cached_tokens:,}"
        if effective_auth_mode == "chatgpt" and isinstance(
            estimated_cached_tokens, int
        ):
            # Preserve the existing ChatGPT cached-read estimation logic: replace
            # ``cached_tokens`` with the turn-aware estimate. Do NOT synthesize
            # ``cache_write_tokens`` from the estimate; preserve any backend-
            # reported write counter so the estimator can price it at the
            # cache-write rate when present.
            details = (
                dict(usage.get("input_tokens_details"))
                if isinstance(usage.get("input_tokens_details"), dict)
                else {}
            )
            details["cached_tokens"] = estimated_cached_tokens
            effective_usage = {**usage, "input_tokens_details": details}

        output_tokens = usage.get("output_tokens")
        if isinstance(output_tokens, (int, float)):
            completion_tokens_str = f"{int(output_tokens):,}"

        cost_breakdown: Optional[Dict[str, Any]] = None
        if isinstance(model, str) and model:
            try:
                total_cost = estimate_usage_cost(
                    effective_usage,
                    model=model,
                    service_tier=service_tier,
                    snapshot_path=(
                        snapshot_path if isinstance(snapshot_path, str) else None
                    ),
                    manual_entries=manual_pricing,
                )
                cost_breakdown = estimate_usage_cost_breakdown(
                    effective_usage,
                    model=model,
                    service_tier=service_tier,
                    snapshot_path=(
                        snapshot_path if isinstance(snapshot_path, str) else None
                    ),
                    manual_entries=manual_pricing,
                )
                if not isinstance(cost_breakdown, dict) or not cost_breakdown:
                    cost_breakdown = None
            except Exception:
                total_cost = None
                cost_breakdown = None

        if isinstance(total_cost, (int, float)):
            total_cost = float(total_cost)
            cost_str = f"${total_cost:.6f}"

        base_total = 0.0
        base_total_turn = 0.0
        base_total_turn_input = 0
        base_total_turn_cached = 0
        base_total_turn_cache_write = 0
        base_total_turn_output = 0
        base_total_turn_reasoning = 0

        for item in base_native:
            if not isinstance(item, dict):
                continue
            internal_prev = item.get("_metadata")
            previous_cost = self._existing_total_cost_from_internal(internal_prev)
            if previous_cost is None:
                continue
            base_total += previous_cost

        current_turn_id = self._current_turn_id(base_native)

        for item in base_native:
            if not isinstance(item, dict):
                continue
            internal_prev = item.get("_metadata")
            if not isinstance(internal_prev, dict):
                continue
            turn = internal_prev.get("turn")
            if not isinstance(turn, dict) or turn.get("id") != current_turn_id:
                continue
            previous_cost = self._existing_total_cost_from_internal(internal_prev)
            usage_prev = self._public_usage_from_internal(internal_prev)
            if previous_cost is not None:
                base_total_turn += previous_cost
            if isinstance(usage_prev, dict):
                input_tokens = self._usage_input_tokens(usage_prev)
                if isinstance(input_tokens, int):
                    base_total_turn_input += input_tokens
                cached_tokens = self._effective_cached_tokens_from_internal(
                    internal_prev
                )
                if isinstance(cached_tokens, int):
                    base_total_turn_cached += cached_tokens
                cache_write_tokens = self._effective_cache_write_tokens_from_internal(
                    internal_prev
                )
                if isinstance(cache_write_tokens, int):
                    base_total_turn_cache_write += cache_write_tokens
                output_tokens = self._usage_output_tokens(usage_prev)
                if isinstance(output_tokens, int):
                    base_total_turn_output += output_tokens
                base_total_turn_reasoning += self._usage_reasoning_tokens(usage_prev)

        effective_total_cost = (
            float(total_cost) if isinstance(total_cost, (int, float)) else 0.0
        )
        cumulative_cost = base_total + effective_total_cost
        usage_turn_cumulative = base_total_turn + effective_total_cost
        current_input = self._usage_input_tokens(usage) or 0
        current_cached = (
            estimated_cached_tokens
            if isinstance(estimated_cached_tokens, int)
            else self._usage_cached_tokens(usage) or 0
        )
        current_cache_write = self._usage_cache_write_tokens(usage) or 0
        current_output = self._usage_output_tokens(usage) or 0
        usage_turn_input_cumulative = base_total_turn_input + current_input
        usage_turn_cached_cumulative = base_total_turn_cached + current_cached
        usage_turn_cache_write_cumulative = (
            base_total_turn_cache_write + current_cache_write
        )
        usage_turn_output_cumulative = base_total_turn_output + current_output
        current_reasoning = self._usage_reasoning_tokens(usage)
        usage_turn_reasoning_cumulative = base_total_turn_reasoning + current_reasoning

        has_tool_calls = any(
            isinstance(it, dict)
            and it.get("type") in ("function_call", "custom_tool_call")
            for it in current_items
        )

        extra_md: Dict[str, Any] = {
            "usage": project_usage_for_persistence(usage),
            "has_tool_calls": has_tool_calls,
            "turn": {
                "id": current_turn_id,
                "has_tool_calls": has_tool_calls,
                "is_terminal": not has_tool_calls,
            },
            "usage_effective_auth_mode": effective_auth_mode,
            "usage_effective_auth_mode_label": self._effective_auth_mode_label(
                effective_auth_mode
            ),
            "usage_bucket": resolve_cost_bucket(
                state.get("config") if isinstance(state, dict) else None,
                effective_auth_mode,
            ),
            "usage_total_cost": effective_total_cost,
            "usage_total_cost_cumulative": cumulative_cost,
            "usage_total_cost_cumulative_formatted": f"${cumulative_cost:.6f}",
            "usage_turn_cost_cumulative": usage_turn_cumulative,
            "usage_turn_cost_cumulative_formatted": f"${usage_turn_cumulative:.6f}",
            "usage_turn_input_tokens_cumulative": usage_turn_input_cumulative,
            "usage_turn_input_tokens_cumulative_formatted": self._format_token_count(
                usage_turn_input_cumulative
            ),
            "usage_turn_cached_tokens_cumulative": usage_turn_cached_cumulative,
            "usage_turn_cached_tokens_cumulative_formatted": self._format_token_count(
                usage_turn_cached_cumulative
            ),
            "usage_turn_cache_write_tokens_cumulative": usage_turn_cache_write_cumulative,
            "usage_turn_cache_write_tokens_cumulative_formatted": self._format_token_count(
                usage_turn_cache_write_cumulative
            ),
            "usage_turn_output_tokens_cumulative": usage_turn_output_cumulative,
            "usage_turn_output_tokens_cumulative_formatted": self._format_token_count(
                usage_turn_output_cumulative
            ),
            "usage_turn_reasoning_tokens_cumulative": usage_turn_reasoning_cumulative,
            "usage_turn_reasoning_tokens_cumulative_formatted": (
                f"{int(usage_turn_reasoning_cumulative):,}"
            ),
        }

        if isinstance(service_tier, str) and service_tier:
            extra_md["usage_service_tier"] = service_tier

        if isinstance(cost_breakdown, dict) and cost_breakdown:
            # Per-item cost components for the generic cost tracking plugin
            # (input / cached / cache_write / output); items without data are
            # omitted by the estimator.
            extra_md["usage_cost_breakdown"] = cost_breakdown

        if isinstance(reasoning_mode, str) and reasoning_mode:
            extra_md["usage_reasoning_mode"] = reasoning_mode

        if prompt_tokens_str is not None:
            extra_md["usage_prompt_tokens_formatted"] = prompt_tokens_str
        if cached_tokens_str is not None and effective_auth_mode != "chatgpt":
            extra_md["usage_cached_tokens_formatted"] = cached_tokens_str
        if (
            cache_write_tokens_str is not None
            and reported_cache_write is not None
            and reported_cache_write > 0
        ):
            extra_md["usage_cache_write_tokens_formatted"] = cache_write_tokens_str
        if estimated_cached_tokens is not None:
            extra_md["usage_estimated_cached_tokens"] = estimated_cached_tokens
        if estimated_cached_tokens_str is not None:
            extra_md["usage_estimated_cached_tokens_formatted"] = (
                estimated_cached_tokens_str
            )
        if completion_tokens_str is not None:
            extra_md["usage_completion_tokens_formatted"] = completion_tokens_str
        if cost_str is not None and effective_total_cost != 0.0:
            extra_md["usage_total_cost_formatted"] = cost_str

        if effective_auth_mode == "chatgpt":
            self._append_chatgpt_usage_journal_record(
                usage=usage,
                state=state,
                config=config if isinstance(config, dict) else {},
                response_id=response_id,
                model=model,
                service_tier=service_tier,
                reasoning_mode=reasoning_mode,
                estimated_cached_tokens=estimated_cached_tokens,
                input_tokens=current_input,
                cached_tokens=current_cached,
                cache_write_tokens=current_cache_write,
                output_tokens=current_output,
                reasoning_tokens=current_reasoning,
                estimated_cost=effective_total_cost,
            )

        return extra_md

    @staticmethod
    def _chatgpt_rate_limits_for_journal(
        state: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Return the rate-limit snapshot payload for the journal record.

        Prefers the exact snapshot stashed in shared provider state for the
        current response; falls back to the latest persisted rate-limits
        state file.
        """

        stash = (
            state.get(_CHATGPT_RATE_LIMIT_SNAPSHOTS_STATE_KEY)
            if isinstance(state, dict)
            else None
        )
        if (
            isinstance(stash, dict)
            and isinstance(stash.get("snapshots"), list)
            and stash["snapshots"]
        ):
            return stash
        try:
            rate_limits_state = load_rate_limits_state(resolve_rate_limits_path(config))
        except Exception:
            return None
        if (
            isinstance(rate_limits_state, dict)
            and isinstance(rate_limits_state.get("snapshots"), list)
            and rate_limits_state["snapshots"]
        ):
            return rate_limits_state
        return None

    def _append_chatgpt_usage_journal_record(
        self,
        *,
        usage: Dict[str, Any],
        state: Dict[str, Any],
        config: Dict[str, Any],
        response_id: Optional[str],
        model: Any,
        service_tier: Any,
        reasoning_mode: Any,
        estimated_cached_tokens: Optional[int],
        input_tokens: int,
        cached_tokens: int,
        cache_write_tokens: int,
        output_tokens: int,
        reasoning_tokens: int,
        estimated_cost: float,
    ) -> None:
        """Append one request_usage record to the ChatGPT usage journal.

        Best-effort by contract: journaling failures are swallowed so they
        can never break the request pipeline.
        """

        if config.get("track_chatgpt_usage_journal") is False:
            return
        try:
            journal_path = resolve_usage_journal_path(config)
            # Re-finalize and rebuild paths can present the same response
            # again (for example when a session is re-rendered); journal each
            # response id at most once so rebuilds never duplicate records.
            if isinstance(response_id, str) and response_id:
                for record in iter_journal_records(journal_path):
                    if (
                        record.get("type") == "request_usage"
                        and record.get("response_id") == response_id
                    ):
                        return
            append_request_usage(
                journal_path,
                input_tokens=input_tokens,
                cached_tokens=cached_tokens,
                cache_write_tokens=cache_write_tokens,
                output_tokens=output_tokens,
                reasoning_tokens=reasoning_tokens,
                estimated_cached_tokens=estimated_cached_tokens,
                estimated_cost=estimated_cost,
                model=model,
                response_id=response_id,
                service_tier=service_tier,
                reasoning_mode=reasoning_mode,
                usage=project_usage_for_persistence(usage),
                rate_limits=self._chatgpt_rate_limits_for_journal(state, config),
                session_id=session_id_from_state(state),
                working_directory=resolve_working_directory(config),
                config=config,
            )
        except Exception:
            return

    @staticmethod
    def _manual_model_pricing() -> Dict[str, Any] | None:
        pricing = _load_manual_chatgpt_model_pricing_shared()
        return pricing or None

    def _extract_stream_usage(
        self, native_chunk: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(native_chunk, dict):
            return None
        if native_chunk.get("type") == "response.completed":
            response = native_chunk.get("response")
            if isinstance(response, dict):
                usage = response.get("usage")
                if isinstance(usage, dict) and usage:
                    return usage
        usage = native_chunk.get("usage")
        if isinstance(usage, dict) and usage:
            return usage
        return None

    def _extract_stream_response_id(
        self, native_chunk: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        if not isinstance(native_chunk, dict):
            return None
        if native_chunk.get("type") == "response.completed":
            response = native_chunk.get("response")
            if isinstance(response, dict):
                response_id = response.get("id")
                if isinstance(response_id, str) and response_id:
                    return response_id
        response_id = native_chunk.get("response_id")
        if isinstance(response_id, str) and response_id:
            return response_id
        return None

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        usage = self._extract_stream_usage(native_chunk)
        if not isinstance(usage, dict) or not usage or not final_messages:
            return partial_messages, final_messages, native_messages, state

        base_native = list(native_messages)
        try:
            base_native = base_native[: -len(final_messages)]
        except Exception:
            base_native = list(native_messages)

        extra_md = self._build_usage_metadata(
            usage,
            base_native,
            final_messages,
            state,
            response_id=self._extract_stream_response_id(native_chunk),
        )
        attach_idx = self._select_attach_index(final_messages)
        if attach_idx is None:
            return partial_messages, final_messages, native_messages, state

        new_finals: List[Dict[str, Any]] = []
        for idx, item in enumerate(final_messages):
            if idx == attach_idx and isinstance(item, dict):
                new_finals.append(self._attach_internal_md(item, extra_md))
            elif isinstance(item, dict):
                new_finals.append(self._attach_internal_md(item, {}))
            else:
                new_finals.append(item)

        new_native = list(native_messages)
        if len(new_native) >= len(final_messages):
            start = len(new_native) - len(final_messages)
            for rel_idx in range(len(final_messages)):
                native_item = new_native[start + rel_idx]
                if not isinstance(native_item, dict):
                    continue
                if rel_idx == attach_idx:
                    new_native[start + rel_idx] = self._attach_internal_md(
                        native_item, extra_md
                    )
                else:
                    new_native[start + rel_idx] = self._attach_internal_md(
                        native_item, {}
                    )

        return partial_messages, new_finals, new_native, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if final_messages:
            return final_messages, native_messages, state

        current_response_id: Optional[str] = None
        current_usage: Optional[Dict[str, Any]] = None

        for item in reversed(native_messages):
            if not isinstance(item, dict):
                continue
            internal = item.get("_metadata")
            if not isinstance(internal, dict):
                continue
            usage = internal.get(_RAW_USAGE_METADATA_KEY)
            response_id = internal.get("response_id")
            if isinstance(usage, dict) and usage:
                current_usage = usage
                if isinstance(response_id, str) and response_id:
                    current_response_id = response_id
                break

        if not isinstance(current_usage, dict) or not current_usage:
            return final_messages, native_messages, state

        response_indices: List[int] = []
        if isinstance(current_response_id, str) and current_response_id:
            for idx, item in enumerate(native_messages):
                if not isinstance(item, dict):
                    continue
                internal = item.get("_metadata")
                if not isinstance(internal, dict):
                    continue
                if internal.get("response_id") == current_response_id:
                    response_indices.append(idx)
        else:
            for idx, item in enumerate(native_messages):
                if not isinstance(item, dict):
                    continue
                internal = item.get("_metadata")
                if isinstance(internal, dict) and isinstance(
                    internal.get(_RAW_USAGE_METADATA_KEY), dict
                ):
                    response_indices.append(idx)

        if not response_indices:
            return final_messages, native_messages, state

        current_items = [
            native_messages[idx]
            for idx in response_indices
            if isinstance(native_messages[idx], dict)
        ]
        if not current_items:
            return final_messages, native_messages, state

        response_index_set = set(response_indices)
        base_native = [
            item
            for idx, item in enumerate(native_messages)
            if idx not in response_index_set and isinstance(item, dict)
        ]
        extra_md = self._build_usage_metadata(
            current_usage,
            base_native,
            current_items,
            state,
            response_id=current_response_id,
        )
        attach_rel_idx = self._select_attach_index(current_items)
        if attach_rel_idx is None:
            return final_messages, native_messages, state

        attach_abs_idx = response_indices[attach_rel_idx]

        for abs_idx in response_indices:
            item = native_messages[abs_idx]
            if not isinstance(item, dict):
                continue
            updated = self._attach_internal_md(
                item, extra_md if abs_idx == attach_abs_idx else {}
            )
            item.clear()
            item.update(updated)

        return final_messages, native_messages, state
