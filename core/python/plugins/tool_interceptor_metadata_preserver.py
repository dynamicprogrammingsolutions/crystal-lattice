"""Persist tool interception metadata across provider-native history rebuilds.

``ToolLoopRunner`` stores ``interception_current`` / ``interception_phases`` on
assistant ``Message.metadata``. When ``session.metadata["native_messages"]`` is
used, :meth:`agent_core.AgentCore._rebuild_core_from_native` only restores
per-message fields that survive the provider-native ``_metadata`` convention.

This feature runs **after** :class:`EchoProviderMetadataPreserver` (default
priority 100 vs 110 here) so echo's narrow ``_metadata`` filter does not strip
interception keys before they are written for the wire snapshot.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core.types import FeaturePlugin

_KEYS = ("interception_current", "interception_phases")


class ToolInterceptorMetadataPreserver(FeaturePlugin):
    name = "tool_interceptor_metadata_preserver"
    version = "0.1.0"
    priority = 110

    @staticmethod
    def _select_interception_metadata(metadata: Any) -> Dict[str, Any]:
        if not isinstance(metadata, dict) or not metadata:
            return {}
        selected: Dict[str, Any] = {}
        current = metadata.get("interception_current")
        if isinstance(current, dict) and current:
            selected["interception_current"] = current
        phases = metadata.get("interception_phases")
        if isinstance(phases, list) and phases:
            selected["interception_phases"] = phases
        return selected

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Optional[Dict[str, Any]] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        updated = [dict(m) if isinstance(m, dict) else {} for m in native_messages]

        for idx, core_msg in enumerate(messages[: len(updated)]):
            if not isinstance(core_msg, dict):
                continue
            selected = self._select_interception_metadata(core_msg.get("metadata"))
            if not selected:
                continue

            existing = updated[idx].get("_metadata")
            base: Dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
            base.update(selected)
            updated[idx]["_metadata"] = base

        return updated

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Optional[Dict[str, Any]] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        updated = [dict(m) if isinstance(m, dict) else {} for m in messages]

        for idx, native_msg in enumerate(native_messages[: len(updated)]):
            if not isinstance(native_msg, dict):
                continue
            preserved = native_msg.get("_metadata")
            if not isinstance(preserved, dict) or not preserved:
                continue

            current_md = updated[idx].get("metadata")
            merged_md: Dict[str, Any] = (
                dict(current_md) if isinstance(current_md, dict) else {}
            )
            changed = False
            for key in _KEYS:
                if key not in preserved:
                    continue
                value = preserved[key]
                if key == "interception_current":
                    if not isinstance(value, dict) or not value:
                        continue
                elif key == "interception_phases":
                    if not isinstance(value, list) or not value:
                        continue
                if key not in merged_md:
                    merged_md[key] = value
                    changed = True

            if changed:
                updated[idx]["metadata"] = merged_md

        return updated
