from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Mapping


MergeMode = Literal["shallow", "deep"]
MERGE_KEY = "$merge"
DEFAULT_MAX_MERGE_DEPTH = 16
_VALID_MODES = {"shallow", "deep"}


@dataclass(frozen=True)
class MergePolicy:
    default: MergeMode
    key_modes: Mapping[str, MergeMode]


def copy_config_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: copy_config_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [copy_config_value(item) for item in value]
    return value


def _error(
    errors: List[Dict[str, Any]],
    *,
    path: str,
    detail: str,
    error_type: str = "config_merge_invalid",
) -> None:
    errors.append(
        {
            "type": error_type,
            "path": path,
            "detail": detail,
        }
    )


def coerce_merge_mode(
    raw_value: Any,
    *,
    path: str,
    errors: List[Dict[str, Any]],
    default: MergeMode,
) -> MergeMode:
    if raw_value is None:
        return default
    if raw_value in _VALID_MODES:
        return raw_value
    _error(
        errors,
        path=path,
        detail=f"{path!r} must be 'shallow' or 'deep'",
    )
    return default


def parse_merge_policy(
    raw_value: Any,
    *,
    path: str,
    errors: List[Dict[str, Any]],
    inherited_mode: MergeMode,
) -> MergePolicy:
    if raw_value is None:
        return MergePolicy(default=inherited_mode, key_modes={})

    if isinstance(raw_value, str):
        return MergePolicy(
            default=coerce_merge_mode(
                raw_value,
                path=path,
                errors=errors,
                default=inherited_mode,
            ),
            key_modes={},
        )

    if not isinstance(raw_value, Mapping):
        _error(
            errors,
            path=path,
            detail=(
                f"{path!r} must be 'shallow', 'deep', or a mapping with "
                "'default', 'shallow', and 'deep'"
            ),
        )
        return MergePolicy(default=inherited_mode, key_modes={})

    unknown_keys = sorted(
        str(key)
        for key in raw_value.keys()
        if not isinstance(key, str) or key not in {"default", "shallow", "deep"}
    )
    for key in unknown_keys:
        _error(
            errors,
            path=f"{path}.{key}",
            detail=f"Unknown merge-policy key {key!r}",
        )

    default_mode = coerce_merge_mode(
        raw_value.get("default"),
        path=f"{path}.default",
        errors=errors,
        default=inherited_mode,
    )
    key_modes: Dict[str, MergeMode] = {}

    for mode in ("shallow", "deep"):
        raw_keys = raw_value.get(mode)
        if raw_keys is None:
            continue
        if not isinstance(raw_keys, list):
            _error(
                errors,
                path=f"{path}.{mode}",
                detail=f"{path}.{mode} must be a list of non-empty strings",
            )
            continue
        for index, key in enumerate(raw_keys):
            key_path = f"{path}.{mode}[{index}]"
            if not isinstance(key, str) or not key:
                _error(
                    errors,
                    path=key_path,
                    detail="Merge-policy key names must be non-empty strings",
                )
                continue
            previous = key_modes.get(key)
            if previous is not None and previous != mode:
                _error(
                    errors,
                    path=key_path,
                    detail=(
                        f"Merge-policy key {key!r} is assigned to both "
                        f"{previous!r} and {mode!r}"
                    ),
                )
                continue
            key_modes[key] = mode

    return MergePolicy(default=default_mode, key_modes=key_modes)


def _resolved_overlay_value(
    value: Any,
    *,
    inherited_mode: MergeMode,
    default_mode: MergeMode,
    path: str,
    errors: List[Dict[str, Any]],
    depth: int,
    max_depth: int,
    preserve_directives: bool,
) -> Any:
    if isinstance(value, Mapping):
        return merge_config(
            {},
            value,
            default_mode=default_mode,
            inherited_mode=inherited_mode,
            path=path,
            errors=errors,
            depth=depth,
            max_depth=max_depth,
            preserve_directives=preserve_directives,
        )
    # Arrays are intentionally opaque to configuration-language traversal.
    return copy_config_value(value)


def merge_config(
    base: Mapping[str, Any],
    overlay: Mapping[str, Any],
    *,
    default_mode: MergeMode,
    inherited_mode: MergeMode | None = None,
    path: str = "",
    errors: List[Dict[str, Any]] | None = None,
    depth: int = 0,
    max_depth: int = DEFAULT_MAX_MERGE_DEPTH,
    preserve_directives: bool = False,
) -> Dict[str, Any]:
    """Merge two config mappings using recursive parent-scoped policies.

    A mapping's ``$merge`` value controls how its ordinary sibling keys merge.
    ``shallow`` replaces a colliding direct value. ``deep`` recursively merges
    colliding mappings. Arrays and scalars replace in either mode.
    """

    collected_errors = errors if errors is not None else []
    if depth > max_depth:
        _error(
            collected_errors,
            path=path or MERGE_KEY,
            detail=f"Configuration merge exceeded max_depth={max_depth}",
            error_type="config_merge_depth_exceeded",
        )
        return {
            key: copy_config_value(value)
            for key, value in overlay.items()
            if key != MERGE_KEY
        }

    effective_inherited = inherited_mode or default_mode
    merge_path = f"{path}.{MERGE_KEY}" if path else MERGE_KEY
    policy = parse_merge_policy(
        overlay.get(MERGE_KEY),
        path=merge_path,
        errors=collected_errors,
        inherited_mode=effective_inherited,
    )

    base_directive = base.get(MERGE_KEY)
    overlay_directive = overlay.get(MERGE_KEY)
    merged: Dict[str, Any] = {
        key: copy_config_value(value) for key, value in base.items() if key != MERGE_KEY
    }

    for key, overlay_value in overlay.items():
        if key == MERGE_KEY:
            continue
        key_path = f"{path}.{key}" if path else str(key)
        mode = policy.key_modes.get(key, policy.default)
        base_value = merged.get(key)

        if (
            mode == "deep"
            and isinstance(base_value, Mapping)
            and isinstance(overlay_value, Mapping)
        ):
            merged[key] = merge_config(
                base_value,
                overlay_value,
                default_mode=default_mode,
                inherited_mode=mode,
                path=key_path,
                errors=collected_errors,
                depth=depth + 1,
                max_depth=max_depth,
                preserve_directives=preserve_directives,
            )
            continue

        merged[key] = _resolved_overlay_value(
            overlay_value,
            inherited_mode=mode,
            default_mode=default_mode,
            path=key_path,
            errors=collected_errors,
            depth=depth + 1,
            max_depth=max_depth,
            preserve_directives=preserve_directives,
        )

    if preserve_directives:
        directive = (
            overlay_directive if overlay_directive is not None else base_directive
        )
        if directive is not None:
            merged[MERGE_KEY] = copy_config_value(directive)

    return merged


def validate_merge_directives(
    value: Any,
    *,
    path: str = "",
    errors: List[Dict[str, Any]] | None = None,
    inherited_mode: MergeMode = "deep",
    depth: int = 0,
    max_depth: int = DEFAULT_MAX_MERGE_DEPTH,
) -> List[Dict[str, Any]]:
    """Validate merge directives in mappings without traversing arrays."""

    collected_errors = errors if errors is not None else []
    if not isinstance(value, Mapping):
        return collected_errors
    if depth > max_depth:
        _error(
            collected_errors,
            path=path or MERGE_KEY,
            detail=f"Configuration merge exceeded max_depth={max_depth}",
            error_type="config_merge_depth_exceeded",
        )
        return collected_errors

    merge_path = f"{path}.{MERGE_KEY}" if path else MERGE_KEY
    policy = parse_merge_policy(
        value.get(MERGE_KEY),
        path=merge_path,
        errors=collected_errors,
        inherited_mode=inherited_mode,
    )
    for key, child in value.items():
        if key == MERGE_KEY or not isinstance(child, Mapping):
            continue
        child_path = f"{path}.{key}" if path else str(key)
        validate_merge_directives(
            child,
            path=child_path,
            errors=collected_errors,
            inherited_mode=policy.key_modes.get(key, policy.default),
            depth=depth + 1,
            max_depth=max_depth,
        )
    return collected_errors
