"""OpenRouter usage tracking extension.

Captures token usage and cost information from OpenRouter streaming chunks
and exposes it on final assistant messages via metadata.

Behavior:
- During :meth:`process_chunk`, looks for a top-level ``usage`` object on
  the streaming chunk and, when present, attaches it to the provider's
  internal ``state["partial"]`` accumulator under its internal
  ``_metadata`` key.
- Adds two human-friendly, formatted fields for the total tokens and
  total cost to the same internal metadata so that UI layers can render
  them directly.
- During :meth:`from_native_messages`, mirrors the usage object and the
  formatted strings into core-message ``metadata``.

This extension is intended for the OpenRouter provider and relies on the
provider's use of ``state["partial"]`` as the final assistant message
for streaming responses.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin
from agent_core.constants import UIConfigKeys


class OpenRouterUsageExtension(ProviderExtensionPlugin):
    """Provider extension that surfaces OpenRouter usage metadata.

    Responsibilities:
    - Capture ``usage`` blocks from streaming chunks.
    - Attach the raw usage dict to provider-native assistant messages
      under ``_metadata["usage"]``.
    - Compute and attach formatted strings for total tokens and total
      cost for easier UI rendering.
    - Mirror these fields into core message metadata via
      :meth:`from_native_messages`.

    This extension also contributes UI metadata via
    :meth:`get_ui_elements`:

    - Two ``"message_footer"`` elements that expose
      ``metadata.usage_total_tokens_formatted`` and
      ``metadata.usage_total_cost_formatted`` for per-message footers.
    - One ``"status_bar"`` element that exposes
      ``metadata.usage_total_cost_cumulative_formatted`` so terminal UIs
      can display cumulative cost in the status bar.
    """

    name: str = "openrouter_usage"
    version: str = "0.1.0"

    # ---- Config / UI ----
    def get_config_schema(self) -> Dict[str, Any]:
        # No user-configurable options for now.
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        # Expose formatted usage information in the message footer,
        # similar to ClaudeCachingExtension's cached_tokens footer.
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

    def get_ui_elements_for_config(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return usage UI elements only when show_usage is not disabled in config."""
        if config.get(UIConfigKeys.SHOW_USAGE) is False:
            return []
        return self.get_ui_elements()

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        # Simple identification tag so other plugins/features can refer
        # to this extension if needed.
        return ["ext:openrouter_usage"]

    def required_tags(self) -> List[str]:
        # Only meaningful for the OpenRouter provider; the provider
        # already advertises the "openrouter" tag.
        return ["openrouter"]

    # ---- Stateless transforms ----
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # This extension operates during process_chunk/from_native only.
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Mirror usage data from provider-native metadata into core metadata.

        Usage information is attached under the following keys on the
        core message metadata when present on the provider-native
        message's internal ``_metadata``:

        - ``usage`` – the full usage object as returned by OpenRouter.
        - ``usage_prompt_tokens_formatted`` – human-friendly prompt (input) token count.
        - ``usage_cached_tokens_formatted`` – human-friendly cached token count.
        - ``usage_completion_tokens_formatted`` – human-friendly completion token count.
        - ``usage_total_cost_formatted`` – human-friendly cost string.
        """

        enhanced: List[Dict[str, Any]] = []

        if len(messages) == len(native_messages):
            for msg, native in zip(messages, native_messages):
                core_md = dict(msg.get("metadata") or {})
                internal_md = native.get("_metadata") or {}
                if isinstance(internal_md, dict) and "usage" in internal_md:
                    core_md["usage"] = internal_md.get("usage")
                    if "usage_prompt_tokens_formatted" in internal_md:
                        core_md["usage_prompt_tokens_formatted"] = internal_md[
                            "usage_prompt_tokens_formatted"
                        ]
                    if "usage_cached_tokens_formatted" in internal_md:
                        core_md["usage_cached_tokens_formatted"] = internal_md[
                            "usage_cached_tokens_formatted"
                        ]
                    if "usage_completion_tokens_formatted" in internal_md:
                        core_md["usage_completion_tokens_formatted"] = internal_md[
                            "usage_completion_tokens_formatted"
                        ]
                    if "usage_total_cost_formatted" in internal_md:
                        core_md["usage_total_cost_formatted"] = internal_md[
                            "usage_total_cost_formatted"
                        ]
                    if "usage_total_cost_cumulative" in internal_md:
                        core_md["usage_total_cost_cumulative"] = internal_md[
                            "usage_total_cost_cumulative"
                        ]
                    if "usage_total_cost_cumulative_formatted" in internal_md:
                        core_md["usage_total_cost_cumulative_formatted"] = internal_md[
                            "usage_total_cost_cumulative_formatted"
                        ]
                    # Only expose per-turn cost on assistant messages that
                    # do not include tool calls.
                    has_tool_calls = False
                    if isinstance(native, dict):
                        tcs = native.get("tool_calls")
                        if isinstance(tcs, list) and tcs:
                            has_tool_calls = True
                    if not has_tool_calls:
                        if "usage_turn_cost_cumulative" in internal_md:
                            core_md["usage_turn_cost_cumulative"] = internal_md[
                                "usage_turn_cost_cumulative"
                            ]
                        if "usage_turn_cost_cumulative_formatted" in internal_md:
                            core_md["usage_turn_cost_cumulative_formatted"] = internal_md[
                                "usage_turn_cost_cumulative_formatted"
                            ]
                        if "usage_turn_reasoning_tokens_cumulative" in internal_md:
                            core_md["usage_turn_reasoning_tokens_cumulative"] = internal_md[
                                "usage_turn_reasoning_tokens_cumulative"
                            ]
                        if "usage_turn_reasoning_tokens_cumulative_formatted" in internal_md:
                            core_md["usage_turn_reasoning_tokens_cumulative_formatted"] = internal_md[
                                "usage_turn_reasoning_tokens_cumulative_formatted"
                            ]
                enhanced.append({**msg, "metadata": core_md})
            return enhanced

        # When lengths differ (e.g. streaming combined finals), fall
        # back to copying only onto the last core message.
        enhanced.extend(messages)
        if native_messages and messages:
            native_last = native_messages[-1] if isinstance(native_messages[-1], dict) else {}
            internal_md = native_last.get("_metadata") or {}
            if isinstance(internal_md, dict) and "usage" in internal_md:
                last_msg = dict(messages[-1])
                core_md = dict(last_msg.get("metadata") or {})
                core_md["usage"] = internal_md.get("usage")
                if "usage_prompt_tokens_formatted" in internal_md:
                    core_md["usage_prompt_tokens_formatted"] = internal_md[
                        "usage_prompt_tokens_formatted"
                    ]
                if "usage_cached_tokens_formatted" in internal_md:
                    core_md["usage_cached_tokens_formatted"] = internal_md[
                        "usage_cached_tokens_formatted"
                    ]
                if "usage_completion_tokens_formatted" in internal_md:
                    core_md["usage_completion_tokens_formatted"] = internal_md[
                        "usage_completion_tokens_formatted"
                    ]
                if "usage_total_cost_formatted" in internal_md:
                    core_md["usage_total_cost_formatted"] = internal_md[
                        "usage_total_cost_formatted"
                    ]
                if "usage_total_cost_cumulative" in internal_md:
                    core_md["usage_total_cost_cumulative"] = internal_md[
                        "usage_total_cost_cumulative"
                    ]
                if "usage_total_cost_cumulative_formatted" in internal_md:
                    core_md["usage_total_cost_cumulative_formatted"] = internal_md[
                        "usage_total_cost_cumulative_formatted"
                    ]

                has_tool_calls = False
                tcs = native_last.get("tool_calls")
                if isinstance(tcs, list) and tcs:
                    has_tool_calls = True
                if not has_tool_calls:
                    if "usage_turn_cost_cumulative" in internal_md:
                        core_md["usage_turn_cost_cumulative"] = internal_md[
                            "usage_turn_cost_cumulative"
                        ]
                    if "usage_turn_cost_cumulative_formatted" in internal_md:
                        core_md["usage_turn_cost_cumulative_formatted"] = internal_md[
                            "usage_turn_cost_cumulative_formatted"
                        ]
                    if "usage_turn_reasoning_tokens_cumulative" in internal_md:
                        core_md["usage_turn_reasoning_tokens_cumulative"] = internal_md[
                            "usage_turn_reasoning_tokens_cumulative"
                        ]
                    if "usage_turn_reasoning_tokens_cumulative_formatted" in internal_md:
                        core_md["usage_turn_reasoning_tokens_cumulative_formatted"] = internal_md[
                            "usage_turn_reasoning_tokens_cumulative_formatted"
                        ]

                enhanced[-1] = {**last_msg, "metadata": core_md}

        return enhanced

    # ---- Lifecycle hooks ----
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        # No additional state is required; just pass existing state through.
        return state

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        # No request-shaping behavior; just forward messages unchanged.
        return list(native_messages), state

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        """Capture usage details from streaming chunks.

        The full ``usage`` object is attached to the provider-native
        assistant message stored in ``state["partial"]`` under its
        internal ``_metadata`` key. A formatted representation of the
        total tokens and total cost is also stored alongside it for
        better display in UIs.
        """

        if not isinstance(native_chunk, dict):
            return partial_messages, final_messages, native_messages, state

        usage = native_chunk.get("usage") or None
        if not isinstance(usage, dict):
            return partial_messages, final_messages, native_messages, state

        # Format totals for easier display. Keep this defensive so that
        # missing or malformed usage fields never break the provider.
        total_tokens = usage.get("total_tokens")
        total_cost = usage.get("cost") or usage.get("cost_details",{}).get("upstream_inference_cost",0)

        # Per-message token breakdown: prompt (input), cached, completion.
        prompt_tokens_str = None
        cached_tokens_str = None
        completion_tokens_str = None
        try:
            prompt_tokens = usage.get("prompt_tokens")
            if isinstance(prompt_tokens, (int, float)):
                try:
                    prompt_tokens_str = f"{int(prompt_tokens):,}"
                except Exception:
                    prompt_tokens_str = str(prompt_tokens)
        except Exception:
            prompt_tokens_str = None

        try:
            cached_tokens = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
            if isinstance(cached_tokens, (int, float)):
                try:
                    cached_tokens_str = f"{int(cached_tokens):,}"
                except Exception:
                    cached_tokens_str = str(cached_tokens)
        except Exception:
            cached_tokens_str = None

        try:
            completion_tokens = usage.get("completion_tokens")
            if isinstance(completion_tokens, (int, float)):
                try:
                    completion_tokens_str = f"{int(completion_tokens):,}"
                except Exception:
                    completion_tokens_str = str(completion_tokens)
        except Exception:
            completion_tokens_str = None

        cost_str = None
        cumulative_cost = None
        cumulative_cost_str = None
        if isinstance(total_cost, (int, float)):
            try:
                current_cost = float(total_cost)
            except Exception:
                current_cost = None
            if current_cost is not None:
                cost_str = f"${current_cost:.6f}"

                # Compute running total by summing costs from previous
                # assistant messages in the retained native history.
                base_total = 0.0
                try:
                    for msg in native_messages:
                        if not isinstance(msg, dict):
                            continue
                        if msg.get("role") != "assistant":
                            continue
                        md_prev = msg.get("_metadata") or {}
                        if not isinstance(md_prev, dict):
                            continue
                        usage_prev = md_prev.get("usage") or {}
                        if not isinstance(usage_prev, dict):
                            continue
                        prev_cost = usage_prev.get("cost") or usage_prev.get("cost_details", {}).get("upstream_inference_cost", 0)
                        if isinstance(prev_cost, (int, float)):
                            base_total += float(prev_cost)
                except Exception:
                    base_total = 0.0

                cumulative_cost = base_total + current_cost
                cumulative_cost_str = f"${cumulative_cost:.6f}"

                # Compute per-turn running total. The turn begins after the
                # last separator: either the most recent user/system message
                # or the most recent assistant message that had no tool calls.
                base_total_turn = 0.0
                base_total_turn_reasoning = 0
                try:
                    last_sep_idx = -1
                    for idx, msg in enumerate(native_messages):
                        if not isinstance(msg, dict):
                            continue
                        role = msg.get("role")
                        if role in ("user", "system"):
                            last_sep_idx = idx
                            continue
                        if role == "assistant":
                            has_tool_calls = False
                            tcs = msg.get("tool_calls")
                            if isinstance(tcs, list) and tcs:
                                has_tool_calls = True
                            else:
                                md_prev = msg.get("_metadata") or {}
                                if isinstance(md_prev, dict) and md_prev.get("tool_calls"):
                                    has_tool_calls = True
                            if not has_tool_calls:
                                last_sep_idx = idx

                    for idx, msg in enumerate(native_messages):
                        if not isinstance(msg, dict):
                            continue
                        if idx <= last_sep_idx:
                            continue
                        if msg.get("role") != "assistant":
                            continue
                        md_prev = msg.get("_metadata") or {}
                        if not isinstance(md_prev, dict):
                            continue
                        usage_prev = md_prev.get("usage") or {}
                        if not isinstance(usage_prev, dict):
                            continue
                        prev_cost = usage_prev.get("cost") or usage_prev.get("cost_details", {}).get("upstream_inference_cost", 0)
                        if isinstance(prev_cost, (int, float)):
                            base_total_turn += float(prev_cost)
                        # Sum reasoning tokens for per-turn reasoning total.
                        prev_reasoning = None
                        try:
                            prev_reasoning = (
                                usage_prev.get("completion_tokens_details") or {}
                            ).get("reasoning_tokens", None)
                        except Exception:
                            prev_reasoning = None
                        if isinstance(prev_reasoning, (int, float)):
                            try:
                                base_total_turn_reasoning += int(prev_reasoning)
                            except Exception:
                                pass
                except Exception:
                    base_total_turn = 0.0
                    base_total_turn_reasoning = 0

                usage_turn_cumulative = base_total_turn + current_cost
                usage_turn_cumulative_str = f"${usage_turn_cumulative:.6f}"

                # Compute per-turn reasoning tokens (if present in usage).
                usage_turn_reasoning_cumulative = None
                usage_turn_reasoning_cumulative_str = None
                try:
                    current_reasoning = (
                        usage.get("completion_tokens_details") or {}
                    ).get("reasoning_tokens", None)
                    if isinstance(current_reasoning, (int, float)):
                        try:
                            current_reasoning_int = int(current_reasoning)
                        except Exception:
                            current_reasoning_int = None
                        if current_reasoning_int is not None:
                            if "base_total_turn_reasoning" not in locals():
                                base_total_turn_reasoning = 0
                            usage_turn_reasoning_cumulative = base_total_turn_reasoning + current_reasoning_int
                            try:
                                usage_turn_reasoning_cumulative_str = f"{int(usage_turn_reasoning_cumulative):,}"
                            except Exception:
                                usage_turn_reasoning_cumulative_str = str(usage_turn_reasoning_cumulative)
                except Exception:
                    usage_turn_reasoning_cumulative = None
                    usage_turn_reasoning_cumulative_str = None

        accumulated = state.get("partial")
        if isinstance(accumulated, dict):
            internal_md = dict(accumulated.get("_metadata") or {})
            internal_md["usage"] = usage
            if prompt_tokens_str is not None:
                internal_md["usage_prompt_tokens_formatted"] = prompt_tokens_str
            if cached_tokens_str is not None:
                internal_md["usage_cached_tokens_formatted"] = cached_tokens_str
            if completion_tokens_str is not None:
                internal_md["usage_completion_tokens_formatted"] = completion_tokens_str
            if cost_str is not None:
                internal_md["usage_total_cost_formatted"] = cost_str
            if cumulative_cost is not None:
                internal_md["usage_total_cost_cumulative"] = cumulative_cost
            if cumulative_cost_str is not None:
                internal_md["usage_total_cost_cumulative_formatted"] = (
                    cumulative_cost_str
                )
            try:
                if "usage_turn_cumulative" in locals():
                    internal_md["usage_turn_cost_cumulative"] = usage_turn_cumulative
                if "usage_turn_cumulative_str" in locals():
                    internal_md["usage_turn_cost_cumulative_formatted"] = usage_turn_cumulative_str
                if "usage_turn_reasoning_cumulative" in locals() and usage_turn_reasoning_cumulative is not None:
                    internal_md["usage_turn_reasoning_tokens_cumulative"] = usage_turn_reasoning_cumulative
                if "usage_turn_reasoning_cumulative_str" in locals() and usage_turn_reasoning_cumulative_str is not None:
                    internal_md["usage_turn_reasoning_tokens_cumulative_formatted"] = (
                        usage_turn_reasoning_cumulative_str
                    )
            except Exception:
                pass
            accumulated = {**accumulated, "_metadata": internal_md}
            new_state: Dict[str, Any] = {**state, "partial": accumulated}
        else:
            new_state = state

        # Do not alter the provider's partial/final messages; we only
        # enrich the internal native accumulator so finalize() and
        # from_native_messages() can expose usage on the retained
        # history and final core messages.
        return partial_messages, final_messages, native_messages, new_state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # No additional finalization is required; usage is already
        # attached via process_chunk and cumulative cost is tracked in
        # shared state.
        return final_messages, native_messages, state
