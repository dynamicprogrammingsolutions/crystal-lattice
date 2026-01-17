from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import json


@dataclass(frozen=True)
class PluginDescriptor:
    entries: List[str]
    subdirectory: Optional[str]
    kinds: Dict[str, str]


def read_descriptor(path: Path) -> Tuple[Optional[PluginDescriptor], Optional[Dict[str, Any]]]:
    desc_path = path / "agent_plugin.json"
    if not desc_path.is_file():
        return None, {
            "type": "plugin_descriptor_missing",
            "detail": "Missing agent_plugin.json",
            "path": str(desc_path),
        }
    try:
        raw = json.loads(desc_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, {
            "type": "plugin_descriptor_invalid",
            "detail": f"Could not parse agent_plugin.json: {exc}",
            "path": str(desc_path),
        }
    if not isinstance(raw, dict):
        return None, {
            "type": "plugin_descriptor_invalid",
            "detail": "agent_plugin.json must be a JSON object",
            "path": str(desc_path),
        }
    entries = [e for e in (raw.get("entries") or []) if isinstance(e, str) and e.strip()]
    if not entries:
        return None, {
            "type": "plugin_descriptor_invalid",
            "detail": "agent_plugin.json must include a non-empty 'entries' list",
            "path": str(desc_path),
        }
    subdirectory = raw.get("subdirectory")
    subdir_val = subdirectory.strip() if isinstance(subdirectory, str) and subdirectory.strip() else None

    kinds_map = raw.get("kinds")
    kinds: Dict[str, str] = {}
    if isinstance(kinds_map, dict):
        for k, v in kinds_map.items():
            if isinstance(k, str) and isinstance(v, str) and k.strip() and v.strip():
                kinds[k] = v

    return PluginDescriptor(entries=entries, subdirectory=subdir_val, kinds=kinds), None
