"""OpenRouter `/responses` usage tracking extension.

This is the `/responses` counterpart to the chat-completions usage extension.
It expects usage to arrive primarily on the `response.completed` event
(`event["response"]["usage"]`).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agent_core.types import ProviderExtensionPlugin


class OpenRouterResponsesUsageExtension(ProviderExtensionPlugin):
    name: str = "openrouter_responses_usage"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if config.get("show_usage") is False:
            return []
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_prompt_tokens_formatted",
                "template": "input: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_cached_tokens_formatted",
                "template": "cached: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_completion_tokens_formatted",
                "template": "completion: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_total_cost_formatted",
                "template": "cost: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_turn_cost_cumulative_formatted",
                "template": "turn: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_turn_reasoning_tokens_cumulative_formatted",
                "template": "reasoning: {{data}}",
            },
            {
                "ui_type": "status_bar",
                "data": "metadata.usage_total_cost_cumulative_formatted",
                "template": "Total: {{data}}",
            },
        ]

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return ["ext:openrouter_responses_usage"]

    def required_tags(self) -> List[str]:
        return ["openrouter_responses"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Provider merges per-item internal "_metadata" into core message metadata.
        return messages

    @staticmethod
    def _usage_cost(usage: Dict[str, Any]) -> float:
        raw_cost = usage.get("cost")
        if isinstance(raw_cost, (int, float)) and float(raw_cost) != 0.0:
            return float(raw_cost)
        try:
            raw_cost = (usage.get("cost_details") or {}).get("upstream_inference_cost")
        except Exception:
            raw_cost = None
        if isinstance(raw_cost, (int, float)):
            return float(raw_cost)
        return 0.0

    @staticmethod
    def _usage_reasoning_tokens(usage: Dict[str, Any]) -> int:
        try:
            details = usage.get("output_tokens_details") or usage.get("completion_tokens_details") or {}
            if not isinstance(details, dict):
                return 0
            val = details.get("reasoning_tokens")
            if isinstance(val, (int, float)):
                return int(val)
        except Exception:
            return 0
        return 0

    @staticmethod
    def _attach_internal_md(item: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
        base = item.get("_metadata")
        base_md = base if isinstance(base, dict) else {}
        return {**item, "_metadata": {**base_md, **extra}}

    def process_chunk(
        self,
        native_chunk: Dict[str, Any] | None,
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:

        usage = None
        if isinstance(native_chunk, dict):
            if native_chunk.get("type") == "response.completed":
                resp = native_chunk.get("response")
                if isinstance(resp, dict):
                    usage = resp.get("usage")
            elif "usage" in native_chunk:
                usage = native_chunk.get("usage")

        if not isinstance(usage, dict) or not usage:
            return partial_messages, final_messages, native_messages, state

        prompt_tokens_str = None
        cached_tokens_str = None
        completion_tokens_str = None
        cost_str = None
        cumulative_cost = None
        cumulative_cost_str = None

        input_tokens = usage.get("input_tokens")
        if isinstance(input_tokens, (int, float)):
            try:
                prompt_tokens_str = f"{int(input_tokens):,}"
            except Exception:
                prompt_tokens_str = str(input_tokens)

        cached = None
        try:
            cached = (usage.get("input_tokens_details") or {}).get("cached_tokens")
        except Exception:
            cached = None
        if isinstance(cached, (int, float)):
            try:
                cached_tokens_str = f"{int(cached):,}"
            except Exception:
                cached_tokens_str = str(cached)

        output_tokens = usage.get("output_tokens")
        if isinstance(output_tokens, (int, float)):
            try:
                completion_tokens_str = f"{int(output_tokens):,}"
            except Exception:
                completion_tokens_str = str(output_tokens)

        current_cost = self._usage_cost(usage)
        cost_str = f"${current_cost:.6f}" if current_cost != 0.0 else None

        # Only attach derived usage metadata when we can associate it with final output items.
        if not final_messages:
            return partial_messages, final_messages, native_messages, state

        base_native = list(native_messages)
        try:
            base_native = base_native[: -len(final_messages)]
        except Exception:
            base_native = list(native_messages)

        base_total = 0.0
        base_total_turn = 0.0
        base_total_turn_reasoning = 0

        # Total cumulative across all prior responses (one usage block per response).
        for item in base_native:
            if not isinstance(item, dict):
                continue
            internal_prev = item.get("_metadata")
            if not isinstance(internal_prev, dict):
                continue
            usage_prev = internal_prev.get("usage")
            if not isinstance(usage_prev, dict):
                continue
            base_total += self._usage_cost(usage_prev)

        cumulative_cost = base_total + current_cost
        cumulative_cost_str = f"${cumulative_cost:.6f}"

        # Turn cumulative: sum costs since the last "separator".
        # Separator matches the legacy logic:
        # - any user/system message item
        # - any assistant response item (with usage) that did not include tool calls
        last_sep_idx = -1
        for idx, item in enumerate(base_native):
            if not isinstance(item, dict):
                continue
            if item.get("type") == "message" and item.get("role") in ("user", "system"):
                last_sep_idx = idx
                continue
            internal_prev = item.get("_metadata")
            if not isinstance(internal_prev, dict):
                continue
            usage_prev = internal_prev.get("usage")
            if not isinstance(usage_prev, dict):
                continue
            if internal_prev.get("has_tool_calls") is False:
                last_sep_idx = idx

        for idx, item in enumerate(base_native):
            if idx <= last_sep_idx or not isinstance(item, dict):
                continue
            internal_prev = item.get("_metadata")
            if not isinstance(internal_prev, dict):
                continue
            usage_prev = internal_prev.get("usage")
            if not isinstance(usage_prev, dict):
                continue
            base_total_turn += self._usage_cost(usage_prev)
            base_total_turn_reasoning += self._usage_reasoning_tokens(usage_prev)

        usage_turn_cumulative = base_total_turn + current_cost
        usage_turn_cumulative_str = f"${usage_turn_cumulative:.6f}"

        current_reasoning = self._usage_reasoning_tokens(usage)
        usage_turn_reasoning_cumulative = base_total_turn_reasoning + current_reasoning
        usage_turn_reasoning_cumulative_str = f"{int(usage_turn_reasoning_cumulative):,}"

        has_tool_calls = any(
            isinstance(it, dict) and it.get("type") == "function_call" for it in final_messages
        )

        extra_md: Dict[str, Any] = {"has_tool_calls": has_tool_calls}
        if prompt_tokens_str is not None:
            extra_md["usage_prompt_tokens_formatted"] = prompt_tokens_str
        if cached_tokens_str is not None:
            extra_md["usage_cached_tokens_formatted"] = cached_tokens_str
        if completion_tokens_str is not None:
            extra_md["usage_completion_tokens_formatted"] = completion_tokens_str
        if cost_str is not None:
            extra_md["usage_total_cost_formatted"] = cost_str
        extra_md["usage_total_cost_cumulative"] = cumulative_cost
        extra_md["usage_total_cost_cumulative_formatted"] = cumulative_cost_str
        extra_md["usage_turn_cost_cumulative"] = usage_turn_cumulative
        extra_md["usage_turn_cost_cumulative_formatted"] = usage_turn_cumulative_str
        extra_md["usage_turn_reasoning_tokens_cumulative"] = usage_turn_reasoning_cumulative
        extra_md["usage_turn_reasoning_tokens_cumulative_formatted"] = usage_turn_reasoning_cumulative_str

        # Attach to an assistant message item so metadata survives native->core conversion.
        def _is_assistant_message_item(item: Any) -> bool:
            if not isinstance(item, dict) or item.get("type") != "message":
                return False
            role = item.get("role")
            return role is None or role == "assistant"

        candidates = [idx for idx, item in enumerate(final_messages) if _is_assistant_message_item(item)]
        attach_idx: int
        if candidates:
            attach_idx = candidates[-1]
            for idx in reversed(candidates):
                item = final_messages[idx]
                if isinstance(item, dict) and item.get("phase") == "final_answer":
                    attach_idx = idx
                    break
        else:
            attach_idx = len(final_messages) - 1

        # Ensure usage is present on the chosen item if the provider didn't
        # attach it for some reason.
        if attach_idx is not None and isinstance(final_messages[attach_idx], dict):
            internal = final_messages[attach_idx].get("_metadata")
            if not (isinstance(internal, dict) and isinstance(internal.get("usage"), dict)):
                extra_md = {**extra_md, "usage": usage}

        new_finals: List[Dict[str, Any]] = []
        for idx, item in enumerate(final_messages):
            if idx == attach_idx and isinstance(item, dict):
                new_finals.append(self._attach_internal_md(item, extra_md))
            else:
                new_finals.append(item)

        # Update the corresponding item in the native history tail.
        if len(native_messages) >= len(final_messages):
            prefix = list(native_messages[: -len(final_messages)])
            tail = list(native_messages[-len(final_messages) :])
            try:
                native_target = tail[attach_idx]
                if isinstance(native_target, dict):
                    tail[attach_idx] = self._attach_internal_md(native_target, extra_md)
            except Exception:
                pass
            new_native = [*prefix, *tail]
        else:
            new_native = list(native_messages)

        return partial_messages, new_finals, new_native, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state
