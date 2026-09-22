"""Generic cost tracking extension.

The extension is enabled by the ``cost_tracking`` capability tag that
cost-aware providers emit. It records one row per request into the SQLite
cost store and stamps the store-backed session total into message metadata so
the chat status bar can show a total aggregated by workspace + session id
instead of a stateless per-message cumulative sum.

The extension runs after the provider's usage extension (higher priority
number), so the finals and native messages already carry the usage metadata
(``usage``, ``usage_bucket``, ``usage_total_cost``, ``response_id``) stamped
by the provider plugin.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin

from . import cost_store


class CostTrackingExtension(ProviderExtensionPlugin):
    name: str = "cost_tracking"
    version: str = "0.1.0"
    priority: int = 70

    def required_tags(self) -> List[str]:
        return ["cost_tracking"]

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        _ = (config, models)
        return ["ext:cost_tracking"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "track_costs": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Record per-request cost rows for capability-emitting "
                    "providers in the SQLite cost store."
                ),
            },
            "cost_tracking_db_path": {
                "type": "string",
                "required": False,
                "description": (
                    "Optional path override for the cost store. Defaults to a "
                    "cost-tracking/cost-tracking.sqlite3 file under the "
                    "Crystal data directory."
                ),
            },
            "show_cost_status_total": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Show the store-backed session cost total in the chat "
                    "status bar."
                ),
            },
            "total_usage_breakdown": {
                "type": "string",
                "required": False,
                "default": "none",
                "label": "Total usage breakdown",
                "options": ["none", "totals", "averages"],
                "description": (
                    "Show the session cost breakdown as separate status "
                    "bar fields: 'none' keeps only the total footer, "
                    "'totals' shows per-item cost totals (input, cached "
                    "input, cache write, output) with the request count, "
                    "'averages' shows per-request average item costs. "
                    "Items without data are skipped. Both variants are "
                    "always stored in message metadata."
                ),
            },
            "track_cost_tracking_summary_csv": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Append per-request rows with rolling session and "
                    "reset-aware bucket totals to the summary CSV beside "
                    "the SQLite store."
                ),
            },
            "cost_tracking_summary_csv_path": {
                "type": "string",
                "required": False,
                "description": (
                    "Optional path override for the summary CSV. Defaults "
                    "to cost-tracking-summary.csv beside the cost store."
                ),
            },
        }

    @classmethod
    def _status_bar_element(cls, data_path: str, template: str) -> Dict[str, Any]:
        return {
            "ui_type": "status_bar",
            "data": data_path,
            "template": template,
            "condition": {"path": data_path, "exists": True},
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = context
        if isinstance(config, dict) and config.get("show_cost_status_total") is False:
            return []

        # The total footer element is unchanged and always first; the
        # platform renders status bar elements in this list order.
        elements: List[Dict[str, Any]] = [
            self._status_bar_element(
                "metadata.cost_session_total_formatted", "Total: {{data}}"
            )
        ]

        mode = config.get("total_usage_breakdown") if isinstance(config, dict) else None
        if mode not in ("totals", "averages"):
            return elements

        requests_element = self._status_bar_element(
            "metadata.cost_session_requests_formatted", "requests: {{data}}"
        )
        if mode == "totals":
            elements.extend(
                self._status_bar_element(
                    f"metadata.cost_session_{key}_cost_formatted",
                    f"{label}: {{{{data}}}}",
                )
                for key, label in self._BREAKDOWN_ITEM_LABELS
            )
            elements.append(requests_element)
        else:
            elements.append(requests_element)
            elements.append(
                self._status_bar_element(
                    "metadata.cost_session_average_cost_formatted",
                    "average: {{data}}",
                )
            )
            elements.extend(
                self._status_bar_element(
                    f"metadata.cost_session_{key}_cost_avg_formatted",
                    f"{label}: {{{{data}}}}",
                )
                for key, label in self._BREAKDOWN_ITEM_LABELS
            )
        return elements

    # ------------------------------------------------------------------
    # Request pipeline
    # ------------------------------------------------------------------

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
        _ = native_chunk
        if not final_messages:
            return partial_messages, final_messages, native_messages, state

        source = self._find_usage_metadata(
            [item for item in final_messages if isinstance(item, dict)]
        )
        if source is None:
            return partial_messages, final_messages, native_messages, state

        cost_md = self._record_and_build_metadata(source, state)
        if not cost_md:
            return partial_messages, final_messages, native_messages, state

        new_finals: List[Dict[str, Any]] = []
        for item in final_messages:
            if isinstance(item, dict):
                new_finals.append(self._attach_internal_md(item, cost_md))
            else:
                new_finals.append(item)

        new_native = list(native_messages)
        if len(new_native) >= len(final_messages):
            start = len(new_native) - len(final_messages)
            for rel_idx in range(len(final_messages)):
                native_item = new_native[start + rel_idx]
                if isinstance(native_item, dict):
                    new_native[start + rel_idx] = self._attach_internal_md(
                        native_item, cost_md
                    )

        return partial_messages, new_finals, new_native, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        _ = context
        if final_messages:
            # Streaming requests were already recorded and stamped in
            # ``process_chunk``; only record when the finals carry usage
            # metadata that has not been processed yet (non-stream providers
            # that return finals from their own finalize).
            if any(
                isinstance(item, dict)
                and isinstance(item.get("_metadata"), dict)
                and "cost_session_total" in item["_metadata"]
                for item in final_messages
            ):
                return final_messages, native_messages, state
            cost_md = self._metadata_from_finals(final_messages, state)
            if not cost_md:
                return final_messages, native_messages, state
            new_finals = [
                (
                    self._attach_internal_md(item, cost_md)
                    if isinstance(item, dict)
                    else item
                )
                for item in final_messages
            ]
            new_native = list(native_messages)
            if len(new_native) >= len(new_finals):
                start = len(new_native) - len(new_finals)
                for rel_idx in range(len(new_finals)):
                    native_item = new_native[start + rel_idx]
                    if isinstance(native_item, dict):
                        new_native[start + rel_idx] = self._attach_internal_md(
                            native_item, cost_md
                        )
            return new_finals, new_native, state

        # Non-stream path: the provider's finalize returned no finals and the
        # usage extension already stamped usage metadata onto the native tail.
        # Items already carrying a stamped session total were handled in the
        # streaming ``process_chunk`` path and must not record twice.
        for index in range(len(native_messages) - 1, -1, -1):
            item = native_messages[index]
            if not isinstance(item, dict):
                continue
            internal = item.get("_metadata")
            if not isinstance(internal, dict):
                continue
            if "cost_session_total" in internal:
                return final_messages, native_messages, state
            if not self._is_cost_record_source(internal):
                continue
            cost_md = self._record_and_build_metadata(internal, state)
            if cost_md:
                # Mutate in place (mirroring the usage extension's non-stream
                # attach) so history entries and finals that share the same
                # item object both pick up the stamped metadata.
                updated = self._attach_internal_md(item, cost_md)
                item.clear()
                item.update(updated)
                return final_messages, native_messages, state
            return final_messages, native_messages, state
        return final_messages, native_messages, state

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Optional[Dict[str, Any]] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Promote store-backed ``cost_*`` metadata to public message metadata.

        Mirrors the usage extension: assistant messages carry ``native_indices``
        pointing at their native items, and the stamped ``cost_*`` metadata is
        read from those items.
        """

        _ = (state, context)
        out: List[Dict[str, Any]] = []
        for message in messages:
            if not isinstance(message, dict) or message.get("role") != "assistant":
                out.append(message)
                continue

            metadata_raw = message.get("metadata")
            metadata = dict(metadata_raw) if isinstance(metadata_raw, dict) else {}
            native_indices = metadata.get("native_indices")
            if not isinstance(native_indices, list):
                out.append(message)
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
                if not isinstance(internal, dict):
                    continue
                candidate = {
                    key: value
                    for key, value in internal.items()
                    if isinstance(key, str) and key.startswith("cost_")
                }
                if candidate:
                    extra_md = candidate

            if not extra_md:
                out.append(message)
                continue

            merged = dict(metadata)
            for key, value in extra_md.items():
                if key not in merged:
                    merged[key] = value
            out.append({**message, "metadata": merged})

        return out

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_cost_record_source(internal: Dict[str, Any]) -> bool:
        bucket = internal.get("usage_bucket")
        usage = internal.get("usage")
        return isinstance(bucket, str) and bool(bucket) and isinstance(usage, dict)

    @classmethod
    def _find_usage_metadata(
        cls, items: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        for item in reversed(items):
            internal = item.get("_metadata")
            if isinstance(internal, dict) and cls._is_cost_record_source(internal):
                return internal
        return None

    def _metadata_from_finals(
        self, final_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        source = self._find_usage_metadata(
            [item for item in final_messages if isinstance(item, dict)]
        )
        if source is None:
            return {}
        return self._record_and_build_metadata(source, state)

    def _record_and_build_metadata(
        self, internal: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record one cost row (best-effort) and return the stamp metadata."""

        config = state.get("config") if isinstance(state, dict) else None
        if isinstance(config, dict) and config.get("track_costs") is False:
            return {}

        bucket = internal.get("usage_bucket")
        usage = internal.get("usage")
        if not (isinstance(bucket, str) and bucket) or not isinstance(usage, dict):
            return {}

        db_path = cost_store.resolve_cost_db_path(
            config if isinstance(config, dict) else None
        )
        working_directory = self._working_directory(config)
        session_id = self._session_id_from_state(state)
        model = (
            config.get("model")
            if isinstance(config, dict) and isinstance(config.get("model"), str)
            else None
        )

        actual_cost = self._actual_usage_cost(usage)
        estimated_cost = (
            internal.get("usage_total_cost") if actual_cost is None else None
        )
        cost_breakdown = internal.get("usage_cost_breakdown")
        if not isinstance(cost_breakdown, dict):
            cost_breakdown = None

        row_time = cost_store.utcnow_iso()
        recorded = False
        try:
            recorded = cost_store.record_request_usage(
                db_path,
                bucket=bucket,
                session_id=session_id,
                working_directory=working_directory,
                model=model,
                response_id=self._optional_str(internal.get("response_id")),
                input_tokens=self._usage_input_tokens(usage),
                cached_tokens=self._usage_cached_tokens(usage),
                cache_write_tokens=self._usage_cache_write_tokens(usage),
                output_tokens=self._usage_output_tokens(usage),
                reasoning_tokens=self._usage_reasoning_tokens(usage),
                estimated_cost=estimated_cost,
                actual_cost=actual_cost,
                cost_breakdown=cost_breakdown,
                time=row_time,
            )
        except Exception:
            # Best-effort by contract: cost tracking failures must never
            # break the request pipeline.
            return {}

        if recorded:
            try:
                cost_store.append_request_summary_csv(
                    db_path,
                    config if isinstance(config, dict) else None,
                    bucket=bucket,
                    session_id=session_id,
                    working_directory=working_directory,
                    model=model,
                    cost=actual_cost if actual_cost is not None else estimated_cost,
                    time=row_time,
                )
            except Exception:
                # Best-effort: the summary CSV must never break the request
                # pipeline either.
                pass

        if working_directory is None or session_id is None:
            return {}

        try:
            totals = cost_store.session_totals(
                db_path, working_directory=working_directory, session_id=session_id
            )
        except Exception:
            return {}

        total_cost = float(totals.get("total_cost") or 0.0)
        request_count = int(totals.get("request_count") or 0)
        metadata: Dict[str, Any] = {
            "cost_session_total": total_cost,
            "cost_session_total_formatted": f"${total_cost:.6f}",
            "cost_session_requests": request_count,
        }
        metadata.update(
            self._breakdown_metadata(
                totals,
                request_count=request_count,
                total_cost=total_cost,
            )
        )
        return metadata

    _BREAKDOWN_ITEM_LABELS = (
        ("input", "input"),
        ("cached", "cached input"),
        ("cache_write", "cache write"),
        ("output", "output"),
    )

    @classmethod
    def _breakdown_metadata(
        cls,
        totals: Dict[str, Any],
        *,
        request_count: int,
        total_cost: float,
    ) -> Dict[str, Any]:
        """Build the per-item cost stamps.

        Both totals and per-request averages are stamped as separate raw
        and formatted fields, always (the ``total_usage_breakdown`` config
        key only selects which UI elements display them). Every applicable
        item is included (input, cached input, cache write, output); items
        with no recorded data are skipped.
        """

        metadata: Dict[str, Any] = {}
        for key, _label in cls._BREAKDOWN_ITEM_LABELS:
            raw = totals.get(f"{key}_cost")
            if not isinstance(raw, (int, float)) or raw <= 0:
                continue
            value = float(raw)
            average = value / request_count if request_count else 0.0
            metadata[f"cost_session_{key}_cost"] = value
            metadata[f"cost_session_{key}_cost_formatted"] = f"${value:.6f}"
            metadata[f"cost_session_{key}_cost_avg"] = average
            metadata[f"cost_session_{key}_cost_avg_formatted"] = f"${average:.6f}"

        if request_count > 0:
            metadata["cost_session_requests_formatted"] = f"{request_count:,}"
            average_total = total_cost / request_count
            metadata["cost_session_average_cost"] = average_total
            metadata["cost_session_average_cost_formatted"] = f"${average_total:.6f}"
        return metadata

    @staticmethod
    def _attach_internal_md(
        item: Dict[str, Any], extra_md: Dict[str, Any]
    ) -> Dict[str, Any]:
        base_md = item.get("_metadata")
        merged: Dict[str, Any] = {}
        if isinstance(base_md, dict):
            merged.update(base_md)
        merged.update(extra_md)
        return {**item, "_metadata": merged}

    @staticmethod
    def _optional_str(value: Any) -> Optional[str]:
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _session_id_from_state(state: Optional[Dict[str, Any]]) -> Optional[str]:
        context = state.get("_request_context") if isinstance(state, dict) else None
        if isinstance(context, dict):
            value = context.get("session_id")
            if isinstance(value, str) and value:
                return value
        return None

    @staticmethod
    def _working_directory(config: Any) -> Optional[str]:
        if not isinstance(config, dict):
            return None
        raw = config.get("working_directory")
        if not isinstance(raw, str) or not raw.strip():
            return None
        return os.path.abspath(os.path.expanduser(raw))

    @staticmethod
    def _usage_int(value: Any) -> Optional[int]:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return max(0, int(value))

    @classmethod
    def _usage_input_tokens(cls, usage: Dict[str, Any]) -> Optional[int]:
        return cls._usage_int(usage.get("input_tokens", usage.get("prompt_tokens")))

    @classmethod
    def _usage_output_tokens(cls, usage: Dict[str, Any]) -> Optional[int]:
        return cls._usage_int(
            usage.get("output_tokens", usage.get("completion_tokens"))
        )

    @staticmethod
    def _detail_int(
        usage: Dict[str, Any], keys: Tuple[str, ...], key: str
    ) -> Optional[int]:
        for details_key in keys:
            details = usage.get(details_key)
            if isinstance(details, dict):
                value = details.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    return max(0, int(value))
        return None

    @classmethod
    def _usage_cached_tokens(cls, usage: Dict[str, Any]) -> Optional[int]:
        return cls._detail_int(
            usage, ("input_tokens_details", "prompt_tokens_details"), "cached_tokens"
        )

    @classmethod
    def _usage_cache_write_tokens(cls, usage: Dict[str, Any]) -> Optional[int]:
        return cls._detail_int(
            usage,
            ("input_tokens_details", "prompt_tokens_details"),
            "cache_write_tokens",
        )

    @classmethod
    def _usage_reasoning_tokens(cls, usage: Dict[str, Any]) -> Optional[int]:
        return cls._detail_int(
            usage,
            ("output_tokens_details", "completion_tokens_details"),
            "reasoning_tokens",
        )

    @staticmethod
    def _actual_usage_cost(usage: Dict[str, Any]) -> Optional[float]:
        for value in (
            usage.get("cost"),
            (usage.get("cost_details") or {}).get("upstream_inference_cost"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            return float(value)
        return None


__all__ = ["CostTrackingExtension"]
