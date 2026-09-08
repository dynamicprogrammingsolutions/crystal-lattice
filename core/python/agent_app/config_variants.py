from __future__ import annotations

from typing import Any, Dict, List, Mapping
import re

from .config_merge import (
    DEFAULT_MAX_MERGE_DEPTH,
    MERGE_KEY,
    copy_config_value,
    merge_config,
    validate_merge_directives,
)


VARIANTS_KEY = "$variants"
WHEN_KEY = "$when"
MATCHES_KEY = "$matches"

_PROTECTED_ROOT_KEYS = {
    "provider",
    "plugins",
    "disabled_plugins",
    "enabled_plugins",
    "force_enabled_plugins",
    "mixin_refs",
    "mixin_merge",
    "mixin_policy",
}


def _error(
    errors: List[Dict[str, Any]],
    *,
    path: str,
    detail: str,
    error_type: str = "config_variant_invalid",
) -> None:
    errors.append(
        {
            "type": error_type,
            "path": path,
            "detail": detail,
        }
    )


def _validate_condition(
    condition: Any,
    *,
    path: str,
    errors: List[Dict[str, Any]],
) -> None:
    if not isinstance(condition, Mapping) or not condition:
        _error(
            errors,
            path=path,
            detail=f"{path!r} must be a non-empty mapping",
        )
        return

    for key, expected in condition.items():
        key_path = f"{path}.{key}"
        if not isinstance(key, str) or not key:
            _error(
                errors,
                path=key_path,
                detail="Condition field names must be non-empty strings",
            )
            continue
        if not isinstance(expected, Mapping):
            continue
        if set(expected.keys()) != {MATCHES_KEY}:
            unknown = sorted(str(value) for value in expected.keys())
            _error(
                errors,
                path=key_path,
                detail=(
                    "Condition mappings must contain only '$matches'; "
                    f"received {unknown!r}"
                ),
            )
            continue
        pattern = expected.get(MATCHES_KEY)
        if not isinstance(pattern, str):
            _error(
                errors,
                path=f"{key_path}.{MATCHES_KEY}",
                detail="'$matches' must be a string regular expression",
            )
            continue
        try:
            re.compile(pattern)
        except re.error as exc:
            _error(
                errors,
                path=f"{key_path}.{MATCHES_KEY}",
                detail=f"Invalid regular expression: {exc}",
            )


def _condition_matches(
    condition: Mapping[str, Any],
    selector: Mapping[str, Any],
) -> bool:
    for key, expected in condition.items():
        actual = selector.get(key)
        if isinstance(expected, Mapping):
            pattern = expected.get(MATCHES_KEY)
            if not isinstance(pattern, str) or not isinstance(actual, str):
                return False
            if re.search(pattern, actual) is None:
                return False
            continue
        if actual != expected:
            return False
    return True


def _validate_mapping(
    mapping: Mapping[str, Any],
    *,
    path: str,
    errors: List[Dict[str, Any]],
    root_scope: bool,
    depth: int,
    max_depth: int,
) -> None:
    if depth > max_depth:
        _error(
            errors,
            path=path or VARIANTS_KEY,
            detail=f"Configuration variants exceeded max_depth={max_depth}",
            error_type="config_variant_depth_exceeded",
        )
        return

    raw_variants = mapping.get(VARIANTS_KEY)
    if raw_variants is not None:
        variants_path = f"{path}.{VARIANTS_KEY}" if path else VARIANTS_KEY
        if not isinstance(raw_variants, list):
            _error(
                errors,
                path=variants_path,
                detail=f"{variants_path!r} must be a list",
            )
        else:
            for index, raw_variant in enumerate(raw_variants):
                variant_path = f"{variants_path}[{index}]"
                if not isinstance(raw_variant, Mapping):
                    _error(
                        errors,
                        path=variant_path,
                        detail="Variant entries must be mappings",
                    )
                    continue
                _validate_condition(
                    raw_variant.get(WHEN_KEY),
                    path=f"{variant_path}.{WHEN_KEY}",
                    errors=errors,
                )
                overlay = {
                    key: value for key, value in raw_variant.items() if key != WHEN_KEY
                }
                validate_merge_directives(
                    overlay,
                    path=variant_path,
                    errors=errors,
                    max_depth=max_depth,
                )
                if root_scope:
                    for protected_key in sorted(
                        _PROTECTED_ROOT_KEYS.intersection(overlay.keys())
                    ):
                        _error(
                            errors,
                            path=f"{variant_path}.{protected_key}",
                            detail=(
                                f"Variants cannot modify runtime topology key "
                                f"{protected_key!r}"
                            ),
                            error_type="config_variant_protected_key",
                        )
                _validate_mapping(
                    overlay,
                    path=variant_path,
                    errors=errors,
                    root_scope=root_scope,
                    depth=depth + 1,
                    max_depth=max_depth,
                )

    for key, child in mapping.items():
        if key in {VARIANTS_KEY, MERGE_KEY} or not isinstance(child, Mapping):
            continue
        child_path = f"{path}.{key}" if path else str(key)
        _validate_mapping(
            child,
            path=child_path,
            errors=errors,
            root_scope=False,
            depth=depth + 1,
            max_depth=max_depth,
        )


def validate_config_variants(
    mapping: Mapping[str, Any],
    *,
    path: str = "",
    root_scope: bool = True,
    max_depth: int = DEFAULT_MAX_MERGE_DEPTH,
) -> List[Dict[str, Any]]:
    errors = validate_merge_directives(
        mapping,
        path=path,
        max_depth=max_depth,
    )
    _validate_mapping(
        mapping,
        path=path,
        errors=errors,
        root_scope=root_scope,
        depth=0,
        max_depth=max_depth,
    )
    return errors


def _resolve_overlay(
    mapping: Mapping[str, Any],
    *,
    selector: Mapping[str, Any],
    path: str,
    errors: List[Dict[str, Any]],
    root_scope: bool,
    depth: int,
    max_depth: int,
) -> Dict[str, Any]:
    raw_merge = mapping.get(MERGE_KEY)
    body = {key: value for key, value in mapping.items() if key != MERGE_KEY}
    resolved = _resolve_mapping(
        body,
        selector=selector,
        path=path,
        errors=errors,
        root_scope=root_scope,
        depth=depth,
        max_depth=max_depth,
    )
    if raw_merge is not None:
        resolved[MERGE_KEY] = copy_config_value(raw_merge)
    return resolved


def _resolve_mapping(
    mapping: Mapping[str, Any],
    *,
    selector: Mapping[str, Any],
    path: str,
    errors: List[Dict[str, Any]],
    root_scope: bool,
    depth: int,
    max_depth: int,
) -> Dict[str, Any]:
    if depth > max_depth:
        _error(
            errors,
            path=path or VARIANTS_KEY,
            detail=f"Configuration variants exceeded max_depth={max_depth}",
            error_type="config_variant_depth_exceeded",
        )
        return {}

    resolved: Dict[str, Any] = {}
    for key, value in mapping.items():
        if key in {VARIANTS_KEY, MERGE_KEY}:
            continue
        key_path = f"{path}.{key}" if path else str(key)
        if isinstance(value, Mapping):
            resolved[key] = _resolve_mapping(
                value,
                selector=selector,
                path=key_path,
                errors=errors,
                root_scope=False,
                depth=depth + 1,
                max_depth=max_depth,
            )
        else:
            # Arrays are copied but not traversed for configuration controls.
            resolved[key] = copy_config_value(value)

    raw_variants = mapping.get(VARIANTS_KEY)
    if not isinstance(raw_variants, list):
        return resolved

    variants_path = f"{path}.{VARIANTS_KEY}" if path else VARIANTS_KEY
    for index, raw_variant in enumerate(raw_variants):
        if not isinstance(raw_variant, Mapping):
            continue
        condition = raw_variant.get(WHEN_KEY)
        if not isinstance(condition, Mapping) or not _condition_matches(
            condition, selector
        ):
            continue
        variant_path = f"{variants_path}[{index}]"
        overlay = _resolve_overlay(
            {key: value for key, value in raw_variant.items() if key != WHEN_KEY},
            selector=selector,
            path=variant_path,
            errors=errors,
            root_scope=root_scope,
            depth=depth + 1,
            max_depth=max_depth,
        )
        if root_scope:
            for protected_key in sorted(
                _PROTECTED_ROOT_KEYS.intersection(overlay.keys())
            ):
                _error(
                    errors,
                    path=f"{variant_path}.{protected_key}",
                    detail=(
                        f"Variants cannot modify runtime topology key "
                        f"{protected_key!r}"
                    ),
                    error_type="config_variant_protected_key",
                )
                overlay.pop(protected_key, None)
        resolved = merge_config(
            resolved,
            overlay,
            default_mode="deep",
            path=path,
            errors=errors,
            depth=depth,
            max_depth=max_depth,
        )

    return resolved


def resolve_config_variants(
    base_config: Mapping[str, Any],
    *,
    selector: Mapping[str, Any],
    path: str = "",
    max_depth: int = DEFAULT_MAX_MERGE_DEPTH,
) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    errors = validate_config_variants(
        base_config,
        path=path,
        root_scope=True,
        max_depth=max_depth,
    )
    if errors:
        return {}, errors
    resolved = _resolve_mapping(
        base_config,
        selector=selector,
        path=path,
        errors=errors,
        root_scope=True,
        depth=0,
        max_depth=max_depth,
    )
    return resolved, errors
