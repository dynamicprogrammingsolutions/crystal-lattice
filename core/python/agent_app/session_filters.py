"""Declarative session-list filter normalization and evaluation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .session_listing import (
    SessionListDiagnostic,
    SessionListFilterEvaluation,
    resolve_session_list_path,
)


_OPTION_TONES = frozenset({"primary", "highlight", "warning", "success", "danger", "muted"})


def _is_record(value: Any) -> bool:
    return isinstance(value, Mapping)


def _is_option_value(value: Any) -> bool:
    return isinstance(value, (str, bool))


def _typed_value_key(value: Any) -> Tuple[str, Any]:
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, str):
        return ("string", value)
    return (type(value).__name__, value)


def _typed_equal(left: Any, right: Any) -> bool:
    return _typed_value_key(left) == _typed_value_key(right)


@dataclass(frozen=True)
class SessionListFilterOption:
    value: str | bool
    label: str
    icon: Optional[str] = None
    tone: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "value": self.value,
            "label": self.label,
        }
        if self.icon is not None:
            result["icon"] = self.icon
        if self.tone is not None:
            result["tone"] = self.tone
        return result


@dataclass(frozen=True)
class SessionListFilter:
    element_id: str
    plugin_id: Optional[str]
    label: str
    icon: Optional[str]
    order: float
    data_paths: Tuple[str, ...]
    filter_type: str
    match: str
    multiple: bool
    case_sensitive: bool
    has_missing_value: bool
    missing_value: Any
    default: Any
    options: Tuple[SessionListFilterOption, ...]
    main_search: bool
    declaration_index: int

    @property
    def inactive_value(self) -> Any:
        if self.filter_type == "text":
            return ""
        if self.filter_type == "select" and self.multiple:
            return []
        return None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "ui_type": "session_list_filter",
            "id": self.element_id,
            "label": self.label,
            "order": self.order,
            "data": (self.data_paths[0] if len(self.data_paths) == 1 else list(self.data_paths)),
            "type": self.filter_type,
            "match": self.match,
            "default": self.default,
            "main_search": self.main_search,
        }
        if self.plugin_id is not None:
            result["plugin"] = self.plugin_id
        if self.icon is not None:
            result["icon"] = self.icon
        if self.filter_type == "text":
            result["case_sensitive"] = self.case_sensitive
        if self.filter_type == "select":
            result["multiple"] = self.multiple
        if self.options:
            result["options"] = [option.to_dict() for option in self.options]
        if self.has_missing_value:
            result["missing_value"] = self.missing_value
        return result


@dataclass(frozen=True)
class SessionListFilterSchema:
    filters: Tuple[SessionListFilter, ...]
    main_search_id: Optional[str]
    identity: str
    diagnostics: Tuple[SessionListDiagnostic, ...]
    main_search_conflict: bool = False

    @property
    def main_search(self) -> Optional[SessionListFilter]:
        if self.main_search_id is None:
            return None
        for declaration in self.filters:
            if declaration.element_id == self.main_search_id:
                return declaration
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filters": [declaration.to_dict() for declaration in self.filters],
            "main_search_id": self.main_search_id,
            "identity": self.identity,
            "main_search_conflict": self.main_search_conflict,
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }


def _diagnostic(
    code: str,
    message: str,
    *,
    raw: Any = None,
    element_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> SessionListDiagnostic:
    plugin_id: Optional[str] = None
    if isinstance(raw, Mapping):
        raw_plugin = raw.get("plugin")
        if isinstance(raw_plugin, str) and raw_plugin:
            plugin_id = raw_plugin
        if element_id is None:
            raw_id = raw.get("id")
            if isinstance(raw_id, str) and raw_id:
                element_id = raw_id
    return SessionListDiagnostic(
        code=code,
        message=message,
        plugin_id=plugin_id,
        element_id=element_id,
        details=details,
    )


def _normalize_options(
    raw: Any,
    *,
    element: Mapping[str, Any],
    boolean_filter: bool,
) -> Tuple[Tuple[SessionListFilterOption, ...], Optional[SessionListDiagnostic]]:
    if raw is None and boolean_filter:
        return (), None
    if not isinstance(raw, list) or (not boolean_filter and not raw):
        return (), _diagnostic(
            "invalid_session_list_filter",
            (
                "session_list_filter.options must be a non-empty list."
                if not boolean_filter
                else "session_list_filter.options must be a list when provided."
            ),
            raw=element,
        )

    options: List[SessionListFilterOption] = []
    seen: set[Tuple[str, Any]] = set()
    for raw_option in raw:
        if not isinstance(raw_option, Mapping):
            return (), _diagnostic(
                "invalid_session_list_filter",
                "Every session_list_filter option must be an object.",
                raw=element,
            )
        value = raw_option.get("value")
        if not _is_option_value(value) or (boolean_filter and not isinstance(value, bool)):
            return (), _diagnostic(
                "invalid_session_list_filter",
                (
                    "Boolean filter option values must be booleans."
                    if boolean_filter
                    else "Select option values must be strings or booleans."
                ),
                raw=element,
            )
        if not boolean_filter and isinstance(value, str) and value.lower() == "any":
            return (), _diagnostic(
                "invalid_session_list_filter",
                "Select option value 'any' is reserved for the inactive value.",
                raw=element,
            )
        label = raw_option.get("label")
        if not isinstance(label, str) or not label:
            return (), _diagnostic(
                "invalid_session_list_filter",
                "Every session_list_filter option requires a non-empty label.",
                raw=element,
            )
        icon = raw_option.get("icon")
        if icon is not None and not isinstance(icon, str):
            return (), _diagnostic(
                "invalid_session_list_filter",
                "session_list_filter option icons must be strings.",
                raw=element,
            )
        tone = raw_option.get("tone")
        if tone is not None and tone not in _OPTION_TONES:
            return (), _diagnostic(
                "invalid_session_list_filter",
                "session_list_filter option tone is not supported.",
                raw=element,
            )
        key = _typed_value_key(value)
        if key in seen:
            return (), _diagnostic(
                "invalid_session_list_filter",
                "session_list_filter option values must be unique by type and value.",
                raw=element,
            )
        seen.add(key)
        options.append(
            SessionListFilterOption(
                value=value,
                label=label,
                icon=icon,
                tone=tone,
            )
        )
    return tuple(options), None


def _value_is_declared(
    value: Any,
    options: Sequence[SessionListFilterOption],
) -> bool:
    return any(_typed_equal(value, option.value) for option in options)


def _normalize_filter(
    raw: Mapping[str, Any],
    declaration_index: int,
) -> Tuple[Optional[SessionListFilter], List[SessionListDiagnostic]]:
    def fail(message: str) -> Tuple[None, List[SessionListDiagnostic]]:
        return None, [_diagnostic("invalid_session_list_filter", message, raw=raw)]

    element_id = raw.get("id")
    if not isinstance(element_id, str) or not element_id:
        return fail("session_list_filter.id must be a non-empty string.")
    label = raw.get("label")
    if not isinstance(label, str) or not label:
        return fail("session_list_filter.label must be a non-empty string.")
    icon = raw.get("icon")
    if icon is not None and not isinstance(icon, str):
        return fail("session_list_filter.icon must be a string.")
    order = raw.get("order", 0)
    if (
        isinstance(order, bool)
        or not isinstance(order, (int, float))
        or not math.isfinite(float(order))
    ):
        return fail("session_list_filter.order must be a finite number.")

    raw_data = raw.get("data")
    if isinstance(raw_data, str) and raw_data:
        data_paths = (raw_data,)
    elif (
        isinstance(raw_data, list)
        and raw_data
        and all(isinstance(path, str) and path for path in raw_data)
    ):
        data_paths = tuple(raw_data)
    else:
        return fail("session_list_filter.data must be a non-empty path or path list.")

    filter_type = raw.get("type")
    match = raw.get("match")
    if filter_type == "text":
        if match not in {"contains", "equals"}:
            return fail("Text filters support contains or equals.")
        if "multiple" in raw:
            return fail("session_list_filter.multiple is valid only for select filters.")
        if "options" in raw:
            return fail("Text filters do not support options.")
        case_sensitive = raw.get("case_sensitive", False)
        if not isinstance(case_sensitive, bool):
            return fail("Text filter case_sensitive must be a boolean.")
        multiple = False
        options: Tuple[SessionListFilterOption, ...] = ()
        default = raw.get("default", "")
        if not isinstance(default, str):
            return fail("Text filter default must be a string.")
    elif filter_type == "boolean":
        if match != "equals":
            return fail("Boolean filters support equals only.")
        if "multiple" in raw:
            return fail("session_list_filter.multiple is valid only for select filters.")
        if "case_sensitive" in raw:
            return fail("case_sensitive is valid only for text filters.")
        options, option_error = _normalize_options(
            raw.get("options"),
            element=raw,
            boolean_filter=True,
        )
        if option_error is not None:
            return None, [option_error]
        case_sensitive = False
        multiple = False
        default = raw.get("default")
        if default is not None and not isinstance(default, bool):
            return fail("Boolean filter default must be null, true, or false.")
    elif filter_type == "select":
        if "case_sensitive" in raw:
            return fail("case_sensitive is valid only for text filters.")
        raw_multiple = raw.get("multiple", False)
        if not isinstance(raw_multiple, bool):
            return fail("Select filter multiple must be a boolean.")
        multiple = raw_multiple
        expected_match = "one_of" if multiple else "equals"
        if match != expected_match:
            return fail(
                f"{'Multiple' if multiple else 'Single'} select filters require "
                f"{expected_match}."
            )
        options, option_error = _normalize_options(
            raw.get("options"),
            element=raw,
            boolean_filter=False,
        )
        if option_error is not None:
            return None, [option_error]
        case_sensitive = False
        default = raw.get("default", [] if multiple else None)
        if multiple:
            if not isinstance(default, list):
                return fail("Multiple-select filter default must be a list.")
            seen_defaults: set[Tuple[str, Any]] = set()
            for value in default:
                key = _typed_value_key(value)
                if not _value_is_declared(value, options) or key in seen_defaults:
                    return fail("Multiple-select defaults must be unique declared option values.")
                seen_defaults.add(key)
            default = list(default)
        elif default is not None and not _value_is_declared(default, options):
            return fail("Single-select default must be null or a declared option value.")
    else:
        return fail("session_list_filter.type must be text, boolean, or select.")

    raw_main_search = raw.get("main_search", False)
    if not isinstance(raw_main_search, bool):
        return fail("session_list_filter.main_search must be a boolean.")
    if raw_main_search and filter_type != "text":
        return fail("main_search is valid only for text filters.")
    if "missing_value" in raw:
        try:
            json.dumps(raw.get("missing_value"), allow_nan=False)
        except (TypeError, ValueError):
            return fail("session_list_filter.missing_value must be JSON-serializable.")

    plugin_id = raw.get("plugin")
    if not isinstance(plugin_id, str) or not plugin_id:
        plugin_id = None

    return (
        SessionListFilter(
            element_id=element_id,
            plugin_id=plugin_id,
            label=label,
            icon=icon,
            order=float(order),
            data_paths=data_paths,
            filter_type=filter_type,
            match=match,
            multiple=multiple,
            case_sensitive=case_sensitive,
            has_missing_value="missing_value" in raw,
            missing_value=raw.get("missing_value"),
            default=default,
            options=options,
            main_search=raw_main_search,
            declaration_index=declaration_index,
        ),
        [],
    )


def normalize_session_list_filter_schema(
    ui_elements: Sequence[Mapping[str, Any]],
) -> SessionListFilterSchema:
    diagnostics: List[SessionListDiagnostic] = []
    normalized: List[SessionListFilter] = []
    for declaration_index, raw in enumerate(ui_elements):
        if not isinstance(raw, Mapping) or raw.get("ui_type") != "session_list_filter":
            continue
        declaration, element_diagnostics = _normalize_filter(raw, declaration_index)
        diagnostics.extend(element_diagnostics)
        if declaration is not None:
            normalized.append(declaration)

    declared_main_searches = [declaration for declaration in normalized if declaration.main_search]
    by_id: Dict[str, List[SessionListFilter]] = {}
    for declaration in normalized:
        by_id.setdefault(declaration.element_id, []).append(declaration)
    duplicate_ids = {
        element_id for element_id, declarations in by_id.items() if len(declarations) > 1
    }
    for element_id in sorted(duplicate_ids):
        declarations = by_id[element_id]
        diagnostics.append(
            SessionListDiagnostic(
                code="duplicate_session_list_filter_id",
                message=(
                    f"Multiple session-list filters declare id {element_id!r}; "
                    "all declarations with that id were ignored."
                ),
                element_id=element_id,
                details={"plugins": [declaration.plugin_id for declaration in declarations]},
            )
        )
    normalized = [
        declaration for declaration in normalized if declaration.element_id not in duplicate_ids
    ]

    main_searches = [declaration for declaration in normalized if declaration.main_search]
    main_search_conflict = len(declared_main_searches) > 1
    if main_search_conflict:
        conflicting_ids = [declaration.element_id for declaration in declared_main_searches]
        diagnostics.append(
            SessionListDiagnostic(
                code="ambiguous_session_list_main_search",
                message=(
                    "Multiple valid session-list filters declare main_search; " "none was selected."
                ),
                details={"filter_ids": conflicting_ids},
            )
        )
        normalized = [declaration for declaration in normalized if not declaration.main_search]
        main_search_id = None
    else:
        main_search_id = main_searches[0].element_id if main_searches else None

    normalized.sort(
        key=lambda declaration: (
            declaration.order,
            declaration.declaration_index,
        )
    )
    identity_payload = [declaration.to_dict() for declaration in normalized]
    identity_payload.append(
        {
            "main_search_id": main_search_id,
            "main_search_conflict": main_search_conflict,
        }
    )
    identity = hashlib.sha256(
        json.dumps(
            identity_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()

    return SessionListFilterSchema(
        filters=tuple(normalized),
        main_search_id=main_search_id,
        identity=identity,
        diagnostics=tuple(diagnostics),
        main_search_conflict=main_search_conflict,
    )


def validate_session_list_filter_value(
    declaration: SessionListFilter,
    value: Any,
) -> Optional[str]:
    if declaration.filter_type == "text":
        return None if isinstance(value, str) else "must be a string"
    if declaration.filter_type == "boolean":
        return None if value is None or isinstance(value, bool) else "must be null, true, or false"
    if declaration.multiple:
        if not isinstance(value, list):
            return "must be a list of declared option values"
        seen: set[Tuple[str, Any]] = set()
        for selected in value:
            key = _typed_value_key(selected)
            if not _value_is_declared(selected, declaration.options) or key in seen:
                return "must contain unique declared option values"
            seen.add(key)
        return None
    if value is None or _value_is_declared(value, declaration.options):
        return None
    return "must be null or a declared option value"


def _normalize_runtime_values(
    schema: SessionListFilterSchema,
    filter_values: Optional[Mapping[str, object]],
    *,
    apply_filter_defaults: bool,
) -> Tuple[Dict[str, Any], List[SessionListDiagnostic]]:
    values = {
        declaration.element_id: (
            declaration.default if apply_filter_defaults else declaration.inactive_value
        )
        for declaration in schema.filters
    }
    diagnostics: List[SessionListDiagnostic] = []
    if filter_values is None:
        return values, diagnostics
    if not isinstance(filter_values, Mapping):
        diagnostics.append(
            SessionListDiagnostic(
                code="invalid_session_list_filter_values",
                message="Session-list filter values must be an object.",
            )
        )
        return values, diagnostics

    by_id = {declaration.element_id: declaration for declaration in schema.filters}
    for element_id, value in filter_values.items():
        declaration = by_id.get(element_id)
        if declaration is None:
            diagnostics.append(
                SessionListDiagnostic(
                    code="unknown_session_list_filter",
                    message=f"Unknown session-list filter {element_id!r}.",
                    element_id=element_id,
                )
            )
            continue
        error = validate_session_list_filter_value(declaration, value)
        if error is not None:
            diagnostics.append(
                SessionListDiagnostic(
                    code="invalid_session_list_filter_value",
                    message=(f"Value for session-list filter {element_id!r} {error}."),
                    plugin_id=declaration.plugin_id,
                    element_id=element_id,
                )
            )
            values[element_id] = declaration.inactive_value
            continue
        values[element_id] = value
    return values, diagnostics


def is_session_list_filter_active(
    declaration: SessionListFilter,
    value: Any,
) -> bool:
    if declaration.filter_type == "text":
        return isinstance(value, str) and value != ""
    if declaration.filter_type == "select" and declaration.multiple:
        return isinstance(value, list) and len(value) > 0
    return value is not None


def _resolved_value_matches(
    declaration: SessionListFilter,
    resolved_value: Any,
    runtime_value: Any,
) -> bool:
    if declaration.filter_type == "text":
        if not isinstance(resolved_value, str) or not isinstance(runtime_value, str):
            return False
        candidate = resolved_value
        query = runtime_value
        if not declaration.case_sensitive:
            candidate = candidate.lower()
            query = query.lower()
        if declaration.match == "equals":
            return candidate == query
        return query in candidate
    if declaration.filter_type == "boolean":
        return isinstance(resolved_value, bool) and _typed_equal(resolved_value, runtime_value)
    if declaration.multiple:
        return any(_typed_equal(resolved_value, selected) for selected in runtime_value)
    return _typed_equal(resolved_value, runtime_value)


def evaluate_session_list_filters(
    summaries: List[Dict[str, Any]],
    *,
    schema: SessionListFilterSchema,
    filter_values: Optional[Mapping[str, object]] = None,
    apply_filter_defaults: bool = False,
) -> SessionListFilterEvaluation:
    runtime_values, value_diagnostics = _normalize_runtime_values(
        schema,
        filter_values,
        apply_filter_defaults=apply_filter_defaults,
    )
    active = [
        (declaration, runtime_values[declaration.element_id])
        for declaration in schema.filters
        if is_session_list_filter_active(declaration, runtime_values[declaration.element_id])
    ]
    if not active:
        return SessionListFilterEvaluation(
            summaries=summaries,
            diagnostics=tuple(schema.diagnostics) + tuple(value_diagnostics),
        )

    filtered: List[Dict[str, Any]] = []
    for summary in summaries:
        include = True
        for declaration, runtime_value in active:
            path_match = False
            for path in declaration.data_paths:
                resolved = resolve_session_list_path(summary, path)
                if resolved.found:
                    candidate = resolved.value
                elif declaration.has_missing_value:
                    candidate = declaration.missing_value
                else:
                    continue
                if _resolved_value_matches(declaration, candidate, runtime_value):
                    path_match = True
                    break
            if not path_match:
                include = False
                break
        if include:
            filtered.append(summary)

    return SessionListFilterEvaluation(
        summaries=filtered,
        diagnostics=tuple(schema.diagnostics) + tuple(value_diagnostics),
    )


def _coerce_option_token(
    declaration: SessionListFilter,
    token: str,
) -> str | bool:
    matches: List[str | bool] = []
    for option in declaration.options:
        if isinstance(option.value, str) and option.value == token:
            matches.append(option.value)
        elif isinstance(option.value, bool) and token.lower() == str(option.value).lower():
            matches.append(option.value)
    unique = {_typed_value_key(value): value for value in matches}
    if len(unique) == 1:
        return next(iter(unique.values()))
    if len(unique) > 1:
        raise ValueError(f"filter {declaration.element_id!r} has ambiguous option value {token!r}")
    raise ValueError(f"invalid value {token!r} for filter {declaration.element_id!r}")


def coerce_session_list_filter_input(
    declaration: SessionListFilter,
    raw_value: str | Sequence[str],
) -> Any:
    """Coerce terminal-style strings using one normalized declaration."""

    if declaration.filter_type == "text":
        if not isinstance(raw_value, str):
            raise ValueError(f"text filter {declaration.element_id!r} requires one string")
        return raw_value

    tokens = [raw_value] if isinstance(raw_value, str) else list(raw_value)
    if declaration.filter_type == "boolean":
        if len(tokens) != 1:
            raise ValueError(f"boolean filter {declaration.element_id!r} requires one value")
        lowered = tokens[0].lower()
        if lowered == "any":
            return None
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        raise ValueError(f"boolean filter {declaration.element_id!r} accepts any, true, or false")

    if len(tokens) == 1 and tokens[0].lower() == "any":
        return [] if declaration.multiple else None
    if any(token.lower() == "any" for token in tokens):
        raise ValueError("'any' cannot be combined with selected option values")
    selected = [_coerce_option_token(declaration, token) for token in tokens]
    if declaration.multiple:
        if len({_typed_value_key(value) for value in selected}) != len(selected):
            raise ValueError(f"filter {declaration.element_id!r} contains duplicate values")
        return selected
    if len(selected) != 1:
        raise ValueError(f"single-select filter {declaration.element_id!r} requires one value")
    return selected[0]


class SessionListFilterEngine:
    """Application-owned interpreter for session-list filter declarations."""

    def schema(self, ui_elements: Sequence[Mapping[str, Any]]) -> SessionListFilterSchema:
        return normalize_session_list_filter_schema(ui_elements)

    def __call__(
        self,
        summaries: List[Dict[str, Any]],
        *,
        ui_elements: Sequence[Dict[str, Any]],
        filter_values: Optional[Dict[str, object]],
        apply_filter_defaults: bool,
    ) -> SessionListFilterEvaluation:
        schema = normalize_session_list_filter_schema(ui_elements)
        return evaluate_session_list_filters(
            summaries,
            schema=schema,
            filter_values=filter_values,
            apply_filter_defaults=apply_filter_defaults,
        )


__all__ = [
    "SessionListFilter",
    "SessionListFilterEngine",
    "SessionListFilterOption",
    "SessionListFilterSchema",
    "coerce_session_list_filter_input",
    "evaluate_session_list_filters",
    "is_session_list_filter_active",
    "normalize_session_list_filter_schema",
    "validate_session_list_filter_value",
]
