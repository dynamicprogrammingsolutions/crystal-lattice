"""
Evaluate UI element conditions against a message/context dict.

Used for ``message_footer`` and ``status_bar`` elements that carry an optional
``condition``. When present, the element is only shown when the condition
evaluates to true against the current message (footer) or last assistant
message (status bar).

Condition shape (minimal spec, shared with TypeScript):

- Leaf operators (object with ``path`` and one of):
  - ``eq``: value at path must equal the given value (strict).
  - ``exists``: value at path must exist (true) or be missing (false).
  - ``empty``: value at path must be empty (true) or non-empty (false).
    Empty = None, "", [], {}.
- Composition:
  - ``all``: list of conditions, all must be true.
  - ``any``: list of conditions, at least one must be true.
  - ``not``: single condition, must be false.

Example::

    {"condition": {"all": [
        {"path": "role", "eq": "assistant"},
        {"path": "metadata.tool_calls", "empty": True}
    ]}}
"""

from __future__ import annotations

from typing import Any, Dict


def _get_value_by_path(obj: Any, path: str) -> Any:
    """Resolve a dot-separated path into obj. Returns None if path is missing."""
    if not isinstance(path, str) or not path:
        return None
    current: Any = obj
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        elif isinstance(current, list):
            try:
                idx = int(part)
            except (ValueError, TypeError):
                return None
            if idx < 0 or idx >= len(current):
                return None
            current = current[idx]
        else:
            return None
    return current


def _is_empty(value: Any) -> bool:
    """True if value is None, "", [], or {}."""
    if value is None:
        return True
    if isinstance(value, str) and value == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def evaluate_condition(condition: Any, context: Dict[str, Any]) -> bool:
    """Evaluate a condition object against the context (e.g. message dict).

    Returns True if the condition is satisfied or if condition is missing/falsy
    (so elements without a condition are shown).
    """
    if not condition or not isinstance(condition, dict):
        return True

    if "all" in condition:
        sub = condition["all"]
        if not isinstance(sub, list):
            return True
        return all(
            evaluate_condition(c, context) for c in sub
        )

    if "any" in condition:
        sub = condition["any"]
        if not isinstance(sub, list):
            return True
        return any(
            evaluate_condition(c, context) for c in sub
        )

    if "not" in condition:
        return not evaluate_condition(condition["not"], context)

    path = condition.get("path")
    if not isinstance(path, str) or not path:
        return True
    value = _get_value_by_path(context, path)

    if "eq" in condition:
        return value == condition["eq"]

    if "exists" in condition:
        want = condition["exists"]
        # "exists: true" -> path must resolve to something (we treat None as missing)
        if want is True:
            return value is not None
        if want is False:
            return value is None
        return True

    if "empty" in condition:
        want = condition["empty"]
        return _is_empty(value) is want

    return True
