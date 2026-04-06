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
    def _first_valid_native_index(raw_indices: Any, native_count: int) -> int | None:
        if not isinstance(raw_indices, list):
            return None
        for idx in raw_indices:
            if isinstance(idx, int) and 0 <= idx < native_count:
                return idx
        return None

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
            return {}

        core = context.get("core")
        config = context.get("config")
        final_messages = context.get("final_messages")
        if not isinstance(final_messages, list) or not isinstance(config, dict):
            return {}
        if core is None or not hasattr(core, "format_tool_call_previews"):
            return {}

        updated_native = native_messages
        updated_finals: List[Dict[str, Any]] = []
        finals_changed = False
        native_changed = False

        for msg in final_messages:
            if not isinstance(msg, dict) or msg.get("role") != "assistant":
                updated_finals.append(msg)
                continue

            metadata = msg.get("metadata")
            metadata_dict = dict(metadata) if isinstance(metadata, dict) else {}
            raw_tool_calls = metadata_dict.get("tool_calls")
            tool_calls = (
                [call for call in raw_tool_calls if isinstance(call, dict)]
                if isinstance(raw_tool_calls, list)
                else []
            )
            if not tool_calls:
                updated_finals.append(msg)
                continue

            previews = core.format_tool_call_previews(tool_calls, config)
            if not previews:
                updated_finals.append(msg)
                continue

            previous_previews = metadata_dict.get(_PREVIEWS_METADATA_KEY)
            metadata_dict[_PREVIEWS_METADATA_KEY] = previews
            if previous_previews == previews:
                updated_finals.append(msg)
            else:
                updated_finals.append({**msg, "metadata": metadata_dict})
                finals_changed = True

            anchor_idx = self._first_valid_native_index(
                metadata_dict.get("native_indices"),
                len(updated_native),
            )
            if anchor_idx is not None:
                patched_native = core.patch_native_internal_metadata(
                    updated_native,
                    [anchor_idx],
                    {_PREVIEWS_METADATA_KEY: previews},
                )
                if patched_native is not updated_native:
                    updated_native = patched_native
                    native_changed = True

        result: Dict[str, Any] = {}
        if finals_changed:
            result["final_messages"] = updated_finals
        if native_changed:
            result["native_messages"] = updated_native
        return result

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state
        out: List[Dict[str, Any]] = []
        consumed_native_indices: set[int] = set()
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

            replacement: List[Dict[str, Any]] | None = None
            replacement_idx: int | None = None
            for idx in native_indices:
                if not isinstance(idx, int) or idx < 0 or idx >= len(native_messages):
                    continue
                if idx in consumed_native_indices:
                    continue
                native = native_messages[idx]
                if not isinstance(native, dict):
                    continue
                internal = native.get("_metadata")
                if not isinstance(internal, dict):
                    continue
                raw_previews = internal.get(_PREVIEWS_METADATA_KEY)
                if not isinstance(raw_previews, list):
                    continue
                replacement = [item for item in raw_previews if isinstance(item, dict)]
                replacement_idx = idx
                break

            if replacement is not None:
                metadata_dict[_PREVIEWS_METADATA_KEY] = replacement
                if replacement_idx is not None:
                    consumed_native_indices.add(replacement_idx)
                out.append({**msg, "metadata": metadata_dict})
            else:
                out.append(msg)

        return out


__all__ = ["ToolCallPreviewFeature"]