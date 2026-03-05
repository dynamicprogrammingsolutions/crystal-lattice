from __future__ import annotations

"""Provider extension template (skeleton + reusable helpers).

Provider extensions run alongside the provider:

- Hot path: observe/transform per-chunk partials via `process_chunk`
- Cold path: observe/transform finals via `finalize`

This module intentionally includes reusable, provider-agnostic helpers that
mirror the accumulator streaming pattern used by provider plugins.

See also:

- `plugins/docs/provider-extensions.md`
- `plugins/template-python-provider/src/template_python_provider/provider.py`
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


def _merge_delta_content(
    current: Dict[str, Any],
    delta: Dict[str, Any],
    *,
    override: Iterable[str] = (),
    accumulate: Iterable[str] = (),
) -> Dict[str, Any]:
    """Merge a delta dict into an accumulator dict.

    This is the same style as the provider-side accumulator pattern:

    - Always preserves unknown keys already present in `current`.
    - `override` keys use the latest non-missing value.
    - `accumulate` keys concatenate string fragments.
    """

    return {
        **current,
        **{k: delta.get(k, current.get(k, "")) for k in override},
        **{k: ((current.get(k) or "") + (delta.get(k) or "")) for k in accumulate},
    }


class AccumulatorExtensionMixin:
    """Provider-style accumulator path for provider extensions.

    Implementations provide:

    - `extract_delta(native_chunk) -> dict`
    - `process_delta(delta, accumulated) -> (patch|None, new_accumulated)`

    The mixin provides a generic `process_chunk` that:

    - delegates delta parsing and accumulation
    - updates the shared accumulator at `state["partial"]`
    - optionally patches the provider's current partial message (last element
      of `partial_messages`) so streaming UIs can render extension fields
    """

    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def process_delta(
        self,
        delta: Dict[str, Any],
        accumulated: Dict[str, Any] | None,
    ) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        delta = self.extract_delta(native_chunk or {})
        acc = state.get("partial") if isinstance(state.get("partial"), dict) else {}
        patch, acc = self.process_delta(delta, acc)

        new_partials = partial_messages
        if isinstance(patch, dict) and patch and partial_messages:
            new_partials = [*partial_messages[:-1], {**partial_messages[-1], **patch}]

        return new_partials, final_messages, list(native_messages), {**state, "partial": acc}


def _merge_shallow(
    current: Dict[str, Any],
    delta: Dict[str, Any],
    *,
    exclude: Tuple[str, ...] = (),
) -> Dict[str, Any]:
    return {**current, **{k: v for k, v in delta.items() if k not in exclude}}


def _merge_tool_call(current: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    out = _merge_shallow(current, delta, exclude=("index", "function"))
    func_delta = delta.get("function")
    if isinstance(func_delta, dict):
        func_current = out.get("function")
        func_current = func_current if isinstance(func_current, dict) else {}
        out["function"] = _merge_delta_content(
            func_current,
            func_delta,
            override=("name",),
            accumulate=("arguments",),
        )
    return out


def _merge_tool_calls(
    existing: List[Dict[str, Any]],
    deltas: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Merge streaming tool_call deltas (OpenAI-style) into a list.

    Streaming tool calls are keyed by `index` and `function.arguments` commonly
    arrives as string fragments.
    """

    merged = [dict(tc) for tc in existing]
    for d in deltas:
        if not isinstance(d, dict):
            continue
        idx = d.get("index")
        i = idx if isinstance(idx, int) and idx >= 0 else len(merged)
        while len(merged) <= i:
            merged.append({})
        merged[i] = _merge_tool_call(merged[i], d)
    return merged


class TemplateProviderExtension(ProviderExtensionPlugin):
    name: str = "template_extension"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return []

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        # TODO: add tags advertised by this extension.
        return []

    def required_tags(self) -> List[str]:
        # TODO: return tags required for this extension to enable.
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), state

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return partial_messages, final_messages, native_messages, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state


__all__ = ["TemplateProviderExtension"]
