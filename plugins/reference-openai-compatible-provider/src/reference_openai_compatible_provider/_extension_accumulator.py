from __future__ import annotations

from typing import Any, Iterable


def _merged_override_value(current: dict[str, Any], delta: dict[str, Any], key: str) -> Any:
    value = delta.get(key)
    if value is None:
        return current.get(key, "")
    if isinstance(value, str) and not value:
        existing = current.get(key)
        if isinstance(existing, str) and existing:
            return existing
    return value


def _merge_delta_content(
    current: dict[str, Any],
    delta: dict[str, Any],
    *,
    override: Iterable[str] = (),
    accumulate: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        **current,
        **{k: _merged_override_value(current, delta, k) for k in override},
        **{k: (current.get(k) or "") + (delta.get(k) or "") for k in accumulate},
    }


class AccumulatorExtensionMixin:
    """Generic process_chunk that delegates extract_delta + process_delta."""

    def extract_delta(
        self, native_chunk: dict[str, Any]
    ) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def process_delta(
        self,
        delta: dict[str, Any],
        accumulated: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError

    def process_chunk(
        self,
        native_chunk: dict[str, Any] | None,
        partial_messages: list[dict[str, Any]],
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ):
        delta = self.extract_delta(native_chunk or {})
        accumulated = (
            state.get("partial") if isinstance(state.get("partial"), dict) else {}
        )
        patch, new_acc = self.process_delta(delta, accumulated)

        new_partials = partial_messages
        if isinstance(patch, dict) and patch:
            if partial_messages:
                new_partials = [*partial_messages[:-1], {**partial_messages[-1], **patch}]

        return (
            new_partials,
            final_messages,
            list(native_messages),
            {**state, "partial": new_acc},
        )
