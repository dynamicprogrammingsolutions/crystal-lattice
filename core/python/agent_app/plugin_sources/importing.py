from __future__ import annotations

import importlib
from typing import Any, Dict, Optional, Tuple


def import_dotted_class(entry: str) -> Tuple[Optional[type], Optional[Dict[str, Any]]]:
    module_path, sep, attr = entry.rpartition(".")
    if not sep:
        return None, {
            "type": "plugin_path_invalid",
            "detail": "Invalid entry: expected module.Class",
            "path": entry,
        }
    try:
        module = importlib.import_module(module_path)
        cls = getattr(module, attr)
        return cls, None
    except Exception as exc:
        return None, {
            "type": "plugin_import_error",
            "detail": str(exc),
            "path": entry,
        }
