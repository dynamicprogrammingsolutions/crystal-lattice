from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_run_profile(profiles_root: Path, profile: str | None) -> Dict[str, Any]:
    if not isinstance(profile, str) or not profile.strip():
        return {}

    raw = profile.strip()
    candidate = Path(raw).expanduser()
    if candidate.is_file():
        path = candidate
    else:
        path = profiles_root / f"{raw}.json"

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Run profile must be a JSON object: {path}")
    return payload
