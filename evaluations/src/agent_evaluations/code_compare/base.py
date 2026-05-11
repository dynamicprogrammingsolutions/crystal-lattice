from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class CodeComparisonResult:
    matched: bool
    method: str
    left_parse_ok: bool
    right_parse_ok: bool
    notes: Tuple[str, ...] = field(default_factory=tuple)
    normalized_left: str | None = None
    normalized_right: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched": self.matched,
            "method": self.method,
            "left_parse_ok": self.left_parse_ok,
            "right_parse_ok": self.right_parse_ok,
            "notes": list(self.notes),
            "normalized_left": self.normalized_left,
            "normalized_right": self.normalized_right,
        }