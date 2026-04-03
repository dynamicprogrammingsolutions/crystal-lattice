"""Feature plugin that annotates assistant tool-call previews.

The feature runs during the core-owned ``response_finalize`` lifecycle so it
can update both the in-flight final assistant messages and the persisted
provider-native history for rebuild-from-native flows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


_PREVIEWS_METADATA_KEY = "tool_call_previews"


class ToolCallPreviewFeature:
    name = "tool_call_preview"
    version = "0.1.0"
    priority = 100

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "annotate_tool_call_previews",
                "label": "Annotate tool call previews",
                "description": "Attach human-facing tool call previews to final assistant messages.",
                "inputs": {},
                "trigger": "response_finalize",
            }
        ]

    @staticmethod
    def _dedupe_previews(raw_previews: Any) -> List[Dict[str, Any]]:
        if not isinstance(raw_previews, list):
            return []
        deduped: List[Dict[str, Any]] = []
        seen: set[tuple[Any, Any]] = set()
        for item in raw_previews:
            if not isinstance(item, dict):
                continue
            key = (item.get("id"), item.get("preview"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def execute_action(
        self,
        action_id: str,
        session: Any,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = action_id, session, params, state
        if not isinstance(context, dict):
            return {"native_messages": list(native_messages)}

        core = context.get("core")
        config = context.get("config")
        final_messages = context.get("final_messages")
        if not isinstance(final_messages, list) or not isinstance(config, dict):
            return {"native_messages": list(native_messages)}
        if core is None or not hasattr(core, "format_tool_call_previews"):
            return {"native_messages": list(native_messages)}

        updated_native = list(native_messages)
        updated_finals: List[Dict[str, Any]] = []
        changed = False

        for msg in final_messages:
            if not isinstance(msg, dict) or msg.get("role") != "assistant":
                updated_finals.append(msg)
                continue

            metadata = msg.get("metadata")
            metadata_dict = dict(metadata) if isinstance(metadata, dict) else {}
            raw_tool_calls = metadata_dict.get("tool_calls")
            tool_calls = [call for call in raw_tool_calls if isinstance(call, dict)] if isinstance(raw_tool_calls, list) else []
            if not tool_calls:
                updated_finals.append(msg)
                continue

            previews = self._dedupe_previews(metadata_dict.get(_PREVIEWS_METADATA_KEY))
            if not previews:
                previews = self._dedupe_previews(core.format_tool_call_previews(tool_calls, config))
            if not previews:
                updated_finals.append(msg)
                continue

            metadata_dict[_PREVIEWS_METADATA_KEY] = previews
            updated_finals.append({**msg, "metadata": metadata_dict})
            changed = True

            native_indices = metadata_dict.get("native_indices")
            if isinstance(native_indices, list):
                updated_native = core.patch_native_internal_metadata(
                    updated_native,
                    [idx for idx in native_indices if isinstance(idx, int)],
                    {_PREVIEWS_METADATA_KEY: previews},
                )

        if not changed:
            return {"native_messages": list(native_messages)}

        return {
            "final_messages": updated_finals,
            "native_messages": updated_native,
        }

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state
        out: List[Dict[str, Any]] = []
        for msg in messages:
            if not isinstance(msg, dict) or msg.get("role") != "assistant":
                out.append(msg)
                continue

            metadata = msg.get("metadata")
            metadata_dict = dict(metadata) if isinstance(metadata, dict) else {}
            native_indices = metadata_dict.get("native_indices")
            if not isinstance(native_indices, list):
                out.append(msg)
                continue

            collected: List[Dict[str, Any]] = self._dedupe_previews(metadata_dict.get(_PREVIEWS_METADATA_KEY))
            if not collected:
                merged: List[Dict[str, Any]] = []
                for idx in native_indices:
                    if not isinstance(idx, int) or idx < 0 or idx >= len(native_messages):
                        continue
                    native = native_messages[idx]
                    if not isinstance(native, dict):
                        continue
                    internal = native.get("_metadata")
                    if not isinstance(internal, dict):
                        continue
                    merged.extend(self._dedupe_previews(internal.get(_PREVIEWS_METADATA_KEY)))
                collected = self._dedupe_previews(merged)

            if collected:
                metadata_dict[_PREVIEWS_METADATA_KEY] = collected
                out.append({**msg, "metadata": metadata_dict})
            else:
                out.append(msg)

        return out


__all__ = ["ToolCallPreviewFeature"]