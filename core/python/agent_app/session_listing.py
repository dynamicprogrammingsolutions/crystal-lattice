"""Shared application-layer session-list construction and query service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import threading
from typing import Any, Callable, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple

from agent_core import Session

from .sessions import SessionStore, SessionStoreRecord


_RESERVED_SUMMARY_KEYS = frozenset(
    {
        "session_id",
        "modified",
        "preview",
        "metadata",
        "presentation",
    }
)
_EXCLUDED_METADATA_KEYS = frozenset({"native_messages"})


class SessionListFilterEvaluator(Protocol):
    """Cold-path filter seam implemented by the filter feature task."""

    def __call__(
        self,
        summaries: List[Dict[str, Any]],
        *,
        ui_elements: Sequence[Dict[str, Any]],
        filter_values: Optional[Dict[str, object]],
        apply_filter_defaults: bool,
    ) -> "SessionListFilterEvaluation | List[Dict[str, Any]]":  # pragma: no cover - protocol
        ...


@dataclass(frozen=True)
class SessionListFilterEvaluation:
    summaries: List[Dict[str, Any]]
    diagnostics: Tuple["SessionListDiagnostic", ...] = ()


def _identity_filter_evaluator(
    summaries: List[Dict[str, Any]],
    *,
    ui_elements: Sequence[Dict[str, Any]],
    filter_values: Optional[Dict[str, object]],
    apply_filter_defaults: bool,
) -> List[Dict[str, Any]]:
    _ = ui_elements, filter_values, apply_filter_defaults
    return summaries


@dataclass(frozen=True)
class SessionListDiagnostic:
    code: str
    message: str
    plugin_id: Optional[str] = None
    action_id: Optional[str] = None
    session_id: Optional[str] = None
    element_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.plugin_id is not None:
            result["plugin_id"] = self.plugin_id
        if self.action_id is not None:
            result["action_id"] = self.action_id
        if self.session_id is not None:
            result["session_id"] = self.session_id
        if self.element_id is not None:
            result["element_id"] = self.element_id
        if self.details is not None:
            result["details"] = self.details
        return result


@dataclass(frozen=True)
class ResolvedPath:
    found: bool
    value: Any = None


def resolve_session_list_path(root: Any, path: str) -> ResolvedPath:
    """Resolve a dotted path while preserving missing-versus-null semantics."""

    if not isinstance(path, str) or not path:
        return ResolvedPath(found=False)

    current = root
    for part in path.split("."):
        if isinstance(current, Mapping):
            if part not in current:
                return ResolvedPath(found=False)
            current = current[part]
            continue
        if isinstance(current, (list, tuple)):
            try:
                index = int(part)
            except (TypeError, ValueError):
                return ResolvedPath(found=False)
            if index < 0 or index >= len(current):
                return ResolvedPath(found=False)
            current = current[index]
            continue
        return ResolvedPath(found=False)
    return ResolvedPath(found=True, value=current)


@dataclass(frozen=True)
class _SessionListField:
    element_id: str
    plugin_id: Optional[str]
    role: str
    data: str
    template: str
    order: float
    metadata: Dict[str, Any]
    declaration_index: int


@dataclass(frozen=True)
class _TriggerAction:
    plugin_id: str
    action_id: str
    definition: Dict[str, Any]
    plugin_index: int
    action_index: int


@dataclass(frozen=True)
class _OrderSpec:
    key: str
    direction: str
    has_fallback: bool
    fallback: Any
    priority: int
    plugin_id: str
    action_id: str
    plugin_index: int
    action_index: int
    declaration_index: int

    @property
    def slot(self) -> Tuple[int, int, int]:
        return (self.plugin_index, self.action_index, self.declaration_index)

    def equivalent_contract(self, other: "_OrderSpec") -> bool:
        return (
            self.key == other.key
            and self.direction == other.direction
            and self.has_fallback == other.has_fallback
            and self.fallback == other.fallback
            and self.priority == other.priority
        )


@dataclass
class _CachedSummary:
    revision: object
    contract_token: str
    summary: Dict[str, Any]
    order_specs: Tuple[_OrderSpec, ...]
    diagnostics: Tuple[SessionListDiagnostic, ...]


ListActions = Callable[[], List[Dict[str, Any]]]
ListUiElements = Callable[[], List[Dict[str, Any]]]
ExecuteAction = Callable[
    [str, str, Dict[str, Any], Optional[Dict[str, Any]]],
    Dict[str, Any],
]


class SessionListService:
    """Build and query shared session summaries for all application consumers."""

    def __init__(
        self,
        *,
        store: SessionStore,
        list_actions: ListActions,
        list_ui_elements: ListUiElements,
        execute_action: ExecuteAction,
        logger: Any,
        filter_evaluator: Optional[SessionListFilterEvaluator] = None,
    ) -> None:
        self._store = store
        self._list_actions = list_actions
        self._list_ui_elements = list_ui_elements
        self._execute_action = execute_action
        self._logger = logger
        self._filter_evaluator: SessionListFilterEvaluator = (
            filter_evaluator or _identity_filter_evaluator
        )
        self._cache: Dict[str, _CachedSummary] = {}
        self._last_diagnostics: Tuple[SessionListDiagnostic, ...] = ()
        self._lock = threading.RLock()

    def set_filter_evaluator(self, evaluator: SessionListFilterEvaluator) -> None:
        """Install the filter evaluator supplied by the filter feature layer."""

        if not callable(evaluator):
            raise TypeError("evaluator must be callable")
        with self._lock:
            self._filter_evaluator = evaluator

    def invalidate(self, session_id: Optional[str] = None) -> None:
        with self._lock:
            if session_id is None:
                self._cache.clear()
            else:
                self._cache.pop(session_id, None)

    def get_last_diagnostics(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [diagnostic.to_dict() for diagnostic in self._last_diagnostics]

    def list_session_summaries(
        self,
        *,
        filter_values: Optional[Dict[str, object]] = None,
        apply_filter_defaults: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            diagnostics: List[SessionListDiagnostic] = []
            actions, ui_elements, fields, contract_token = self._load_contract(diagnostics)
            records = self._store.list_records()
            seen_ids = {record.session_id for record in records}
            for cached_id in tuple(self._cache):
                if cached_id not in seen_ids:
                    self._cache.pop(cached_id, None)

            summaries: List[Dict[str, Any]] = []
            all_specs: List[_OrderSpec] = []
            for record in records:
                summary, specs, entry_diagnostics = self._summary_for_record(
                    record=record,
                    actions=actions,
                    fields=fields,
                    contract_token=contract_token,
                )
                summaries.append(summary)
                all_specs.extend(specs)
                diagnostics.extend(entry_diagnostics)

            ordered = self._apply_ordering(summaries, all_specs, diagnostics)
            filter_evaluation = self._filter_evaluator(
                ordered,
                ui_elements=ui_elements,
                filter_values=filter_values,
                apply_filter_defaults=apply_filter_defaults,
            )
            if isinstance(filter_evaluation, SessionListFilterEvaluation):
                filtered = filter_evaluation.summaries
                diagnostics.extend(filter_evaluation.diagnostics)
            else:
                filtered = filter_evaluation
            if limit is not None and isinstance(limit, int) and not isinstance(limit, bool):
                if limit >= 0:
                    filtered = filtered[:limit]

            self._publish_diagnostics(diagnostics)
            return filtered

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        with self._lock:
            diagnostics: List[SessionListDiagnostic] = []
            actions, _ui_elements, fields, contract_token = self._load_contract(diagnostics)
            record = self._store.get_record(session_id)
            if record is None:
                self._cache.pop(session_id, None)
                raise KeyError(f"Session {session_id!r} not found")
            summary, _specs, entry_diagnostics = self._summary_for_record(
                record=record,
                actions=actions,
                fields=fields,
                contract_token=contract_token,
            )
            diagnostics.extend(entry_diagnostics)
            self._publish_diagnostics(diagnostics)
            return summary

    def _publish_diagnostics(self, diagnostics: Sequence[SessionListDiagnostic]) -> None:
        self._last_diagnostics = tuple(diagnostics)
        for diagnostic in diagnostics:
            log = getattr(self._logger, "warning", None)
            if callable(log):
                log(
                    "session list contract diagnostic",
                    **diagnostic.to_dict(),
                )

    @staticmethod
    def _contract_token(
        actions: Sequence[_TriggerAction],
        fields: Sequence[_SessionListField],
    ) -> str:
        payload = {
            "actions": [action.definition for action in actions],
            "fields": [
                {
                    "id": field.element_id,
                    "plugin": field.plugin_id,
                    "role": field.role,
                    "data": field.data,
                    "template": field.template,
                    "order": field.order,
                    "metadata": field.metadata,
                }
                for field in fields
            ],
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=repr,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _load_contract(
        self,
        diagnostics: List[SessionListDiagnostic],
    ) -> Tuple[
        List[_TriggerAction],
        List[Dict[str, Any]],
        List[_SessionListField],
        str,
    ]:
        try:
            raw_actions = self._list_actions()
        except Exception as exc:
            diagnostics.append(
                SessionListDiagnostic(
                    code="session_list_actions_unavailable",
                    message="Could not load application action definitions.",
                    details={"error": str(exc)},
                )
            )
            raw_actions = []

        try:
            raw_ui_elements = self._list_ui_elements()
        except Exception as exc:
            diagnostics.append(
                SessionListDiagnostic(
                    code="session_list_ui_unavailable",
                    message="Could not load application UI definitions.",
                    details={"error": str(exc)},
                )
            )
            raw_ui_elements = []

        ui_elements = [element for element in raw_ui_elements if isinstance(element, dict)]
        actions = self._collect_trigger_actions(raw_actions)
        fields = self._normalize_fields(ui_elements, diagnostics)
        return actions, ui_elements, fields, self._contract_token(actions, fields)

    @staticmethod
    def _collect_trigger_actions(
        raw_actions: Sequence[Dict[str, Any]],
    ) -> List[_TriggerAction]:
        plugin_indices: Dict[str, int] = {}
        action_indices: Dict[str, int] = {}
        actions: List[_TriggerAction] = []

        for raw_action in raw_actions:
            if not isinstance(raw_action, dict):
                continue
            plugin_id = raw_action.get("plugin")
            action_id = raw_action.get("id")
            if not isinstance(plugin_id, str) or not plugin_id:
                continue
            action_index = action_indices.get(plugin_id, 0)
            action_indices[plugin_id] = action_index + 1
            plugin_index = plugin_indices.setdefault(plugin_id, len(plugin_indices))

            trigger = raw_action.get("trigger")
            matches = trigger == "session_list" or (
                isinstance(trigger, list) and "session_list" in trigger
            )
            if not matches or not isinstance(action_id, str) or not action_id:
                continue
            actions.append(
                _TriggerAction(
                    plugin_id=plugin_id,
                    action_id=action_id,
                    definition=raw_action,
                    plugin_index=plugin_index,
                    action_index=action_index,
                )
            )
        return actions

    @staticmethod
    def _normalize_fields(
        ui_elements: Sequence[Dict[str, Any]],
        diagnostics: List[SessionListDiagnostic],
    ) -> List[_SessionListField]:
        fields: List[_SessionListField] = []
        for declaration_index, element in enumerate(ui_elements):
            if element.get("ui_type") != "session_list_field":
                continue
            element_id = element.get("id")
            plugin_id = element.get("plugin")
            role = element.get("role")
            data = element.get("data")
            template = element.get("template", "{{data}}")
            raw_order = element.get("order", 0)
            raw_metadata = element.get("metadata", {})

            invalid_reason: Optional[str] = None
            if not isinstance(element_id, str) or not element_id:
                invalid_reason = "id must be a non-empty string"
            elif role not in {"title", "subtitle", "meta"}:
                invalid_reason = "role must be title, subtitle, or meta"
            elif not isinstance(data, str) or not data:
                invalid_reason = "data must be a non-empty dotted path"
            elif not isinstance(template, str):
                invalid_reason = "template must be a string"
            elif (
                not isinstance(raw_order, (int, float))
                or isinstance(raw_order, bool)
                or not math.isfinite(float(raw_order))
            ):
                invalid_reason = "order must be a finite number"
            elif not isinstance(raw_metadata, dict):
                invalid_reason = "metadata must be an object"

            if invalid_reason is not None:
                diagnostics.append(
                    SessionListDiagnostic(
                        code="invalid_session_list_field",
                        message=f"Ignoring invalid session_list_field: {invalid_reason}.",
                        plugin_id=plugin_id if isinstance(plugin_id, str) else None,
                        element_id=(element_id if isinstance(element_id, str) else None),
                    )
                )
                continue

            fields.append(
                _SessionListField(
                    element_id=element_id,
                    plugin_id=plugin_id if isinstance(plugin_id, str) else None,
                    role=role,
                    data=data,
                    template=template,
                    order=float(raw_order),
                    metadata=raw_metadata,
                    declaration_index=declaration_index,
                )
            )
        return fields

    def _summary_for_record(
        self,
        *,
        record: SessionStoreRecord,
        actions: Sequence[_TriggerAction],
        fields: Sequence[_SessionListField],
        contract_token: str,
    ) -> Tuple[
        Dict[str, Any],
        Tuple[_OrderSpec, ...],
        Tuple[SessionListDiagnostic, ...],
    ]:
        cached = self._cache.get(record.session_id)
        if (
            cached is not None
            and cached.revision == record.revision
            and cached.contract_token == contract_token
        ):
            return cached.summary, cached.order_specs, cached.diagnostics

        diagnostics: List[SessionListDiagnostic] = []
        session: Optional[Session]
        try:
            session = self._store.load(record.session_id)
        except Exception as exc:
            session = None
            diagnostics.append(
                SessionListDiagnostic(
                    code="session_summary_load_failed",
                    message="Stored session could not be loaded; using summary fallbacks.",
                    session_id=record.session_id,
                    details={"error": str(exc)},
                )
            )

        summary = self._build_base_summary(record, session)
        order_specs: List[_OrderSpec] = []
        cacheable = True
        for action in actions:
            action_diagnostics, action_specs, succeeded = self._run_trigger_action(
                action=action,
                record=record,
                session=session,
                summary=summary,
            )
            diagnostics.extend(action_diagnostics)
            order_specs.extend(action_specs)
            cacheable = cacheable and succeeded

        summary["presentation"] = derive_session_list_presentation(summary, fields)
        result_specs = tuple(order_specs)
        result_diagnostics = tuple(diagnostics)
        if cacheable:
            self._cache[record.session_id] = _CachedSummary(
                revision=record.revision,
                contract_token=contract_token,
                summary=summary,
                order_specs=result_specs,
                diagnostics=result_diagnostics,
            )
        else:
            self._cache.pop(record.session_id, None)
        return summary, result_specs, result_diagnostics

    @staticmethod
    def _build_base_summary(
        record: SessionStoreRecord,
        session: Optional[Session],
    ) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {}
        preview = ""
        if session is not None:
            raw_metadata = session.metadata
            if isinstance(raw_metadata, dict):
                metadata = {
                    key: value
                    for key, value in raw_metadata.items()
                    if key not in _EXCLUDED_METADATA_KEYS
                }
            for message in session.messages:
                if message.role != "user":
                    continue
                content = message.content
                if not isinstance(content, str) or not content:
                    continue
                single_line = " ".join(content.split())
                preview = single_line[:77] + "..." if len(single_line) > 80 else single_line
                break
        return {
            "session_id": record.session_id,
            "modified": record.modified,
            "preview": preview,
            "metadata": metadata,
        }

    def _run_trigger_action(
        self,
        *,
        action: _TriggerAction,
        record: SessionStoreRecord,
        session: Optional[Session],
        summary: Dict[str, Any],
    ) -> Tuple[List[SessionListDiagnostic], List[_OrderSpec], bool]:
        diagnostics: List[SessionListDiagnostic] = []
        params: Dict[str, Any] = {}
        inputs = action.definition.get("inputs")
        if not isinstance(inputs, dict):
            inputs = {}
        if "session_id" in inputs:
            params["session_id"] = record.session_id
        if "session_summary" in inputs:
            params["session_summary"] = summary
        if "session" in inputs:
            if session is None:
                diagnostics.append(
                    SessionListDiagnostic(
                        code="session_list_action_session_unavailable",
                        message="List-trigger action requires a loadable session.",
                        plugin_id=action.plugin_id,
                        action_id=action.action_id,
                        session_id=record.session_id,
                    )
                )
                return diagnostics, [], True
            params["session"] = session

        try:
            result = self._execute_action(
                action.plugin_id,
                action.action_id,
                params,
                {
                    "lifecycle": "session_list",
                    "trigger_source": "application",
                    "session_id": record.session_id,
                },
            )
        except Exception as exc:
            diagnostics.append(
                SessionListDiagnostic(
                    code="session_list_action_failed",
                    message="List-trigger action failed and was ignored.",
                    plugin_id=action.plugin_id,
                    action_id=action.action_id,
                    session_id=record.session_id,
                    details={"error": str(exc)},
                )
            )
            return diagnostics, [], False

        fields = result.get("session_list_fields")
        if fields is not None and not isinstance(fields, dict):
            diagnostics.append(
                SessionListDiagnostic(
                    code="invalid_session_list_fields_result",
                    message="session_list_fields must be an object.",
                    plugin_id=action.plugin_id,
                    action_id=action.action_id,
                    session_id=record.session_id,
                )
            )
        elif isinstance(fields, dict):
            for key, value in fields.items():
                if not isinstance(key, str) or not key or key in _RESERVED_SUMMARY_KEYS:
                    diagnostics.append(
                        SessionListDiagnostic(
                            code="invalid_session_list_field_result",
                            message="Ignoring a contributed field with an invalid or reserved key.",
                            plugin_id=action.plugin_id,
                            action_id=action.action_id,
                            session_id=record.session_id,
                            details={"key": repr(key)},
                        )
                    )
                    continue
                try:
                    json.dumps(value, allow_nan=False)
                except (TypeError, ValueError):
                    diagnostics.append(
                        SessionListDiagnostic(
                            code="non_serializable_session_list_field",
                            message="Ignoring a contributed field that is not JSON-serializable.",
                            plugin_id=action.plugin_id,
                            action_id=action.action_id,
                            session_id=record.session_id,
                            details={"key": key},
                        )
                    )
                    continue
                summary[key] = value

        specs = self._normalize_order_specs(
            result.get("session_list_order"),
            action=action,
            session_id=record.session_id,
            diagnostics=diagnostics,
        )
        return diagnostics, specs, True

    @staticmethod
    def _normalize_order_specs(
        raw_specs: Any,
        *,
        action: _TriggerAction,
        session_id: str,
        diagnostics: List[SessionListDiagnostic],
    ) -> List[_OrderSpec]:
        if raw_specs is None:
            return []
        if isinstance(raw_specs, dict):
            candidates = [raw_specs]
        elif isinstance(raw_specs, list):
            candidates = raw_specs
        else:
            diagnostics.append(
                SessionListDiagnostic(
                    code="invalid_session_list_order_result",
                    message="session_list_order must be an object or list.",
                    plugin_id=action.plugin_id,
                    action_id=action.action_id,
                    session_id=session_id,
                )
            )
            return []

        specs: List[_OrderSpec] = []
        for declaration_index, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                diagnostics.append(
                    SessionListDiagnostic(
                        code="invalid_session_list_order_spec",
                        message="Ignoring a non-object session-list order specification.",
                        plugin_id=action.plugin_id,
                        action_id=action.action_id,
                        session_id=session_id,
                    )
                )
                continue
            key = candidate.get("key")
            direction = candidate.get("direction")
            raw_priority = candidate.get("priority", 100)
            invalid_reason: Optional[str] = None
            if not isinstance(key, str) or not key:
                invalid_reason = "key must be a non-empty dotted path"
            elif direction not in {"asc", "desc"}:
                invalid_reason = "direction must be asc or desc"
            elif not isinstance(raw_priority, int) or isinstance(raw_priority, bool):
                invalid_reason = "priority must be an integer"

            if invalid_reason is not None:
                diagnostics.append(
                    SessionListDiagnostic(
                        code="invalid_session_list_order_spec",
                        message=f"Ignoring order specification: {invalid_reason}.",
                        plugin_id=action.plugin_id,
                        action_id=action.action_id,
                        session_id=session_id,
                        details={"spec": candidate},
                    )
                )
                continue

            specs.append(
                _OrderSpec(
                    key=key,
                    direction=direction,
                    has_fallback="fallback" in candidate,
                    fallback=candidate.get("fallback"),
                    priority=raw_priority,
                    plugin_id=action.plugin_id,
                    action_id=action.action_id,
                    plugin_index=action.plugin_index,
                    action_index=action.action_index,
                    declaration_index=declaration_index,
                )
            )
        return specs

    @staticmethod
    def _apply_ordering(
        summaries: List[Dict[str, Any]],
        raw_specs: Sequence[_OrderSpec],
        diagnostics: List[SessionListDiagnostic],
    ) -> List[Dict[str, Any]]:
        ordered = sorted(
            summaries,
            key=lambda summary: _numeric_modified(summary.get("modified")),
            reverse=True,
        )
        if not ordered or not raw_specs:
            return ordered

        specs_by_slot: Dict[Tuple[int, int, int], _OrderSpec] = {}
        for spec in raw_specs:
            existing = specs_by_slot.get(spec.slot)
            if existing is None:
                specs_by_slot[spec.slot] = spec
                continue
            if existing.equivalent_contract(spec):
                continue
            diagnostics.append(
                SessionListDiagnostic(
                    code="conflicting_session_list_order_spec",
                    message="Conflicting order declarations occupied the same plugin slot; the first was used.",
                    plugin_id=spec.plugin_id,
                    action_id=spec.action_id,
                    details={"key": spec.key},
                )
            )

        candidates = sorted(
            specs_by_slot.values(),
            key=lambda spec: (
                spec.priority,
                spec.plugin_index,
                spec.action_index,
                spec.declaration_index,
            ),
        )
        valid: List[Tuple[_OrderSpec, Dict[str, Any]]] = []
        for spec in candidates:
            values_by_session: Dict[str, Any] = {}
            categories: set[str] = set()
            invalid = False
            for summary in ordered:
                resolved = resolve_session_list_path(summary, spec.key)
                if not resolved.found:
                    if not spec.has_fallback:
                        diagnostics.append(
                            SessionListDiagnostic(
                                code="session_list_order_missing_fallback",
                                message="Ignoring order specification because a key is missing and no fallback was declared.",
                                plugin_id=spec.plugin_id,
                                action_id=spec.action_id,
                                details={"key": spec.key},
                            )
                        )
                        invalid = True
                        break
                    value = spec.fallback
                else:
                    value = resolved.value
                category = _sortable_category(value)
                if category is None:
                    diagnostics.append(
                        SessionListDiagnostic(
                            code="session_list_order_value_not_sortable",
                            message="Ignoring order specification with a non-sortable value.",
                            plugin_id=spec.plugin_id,
                            action_id=spec.action_id,
                            details={"key": spec.key},
                        )
                    )
                    invalid = True
                    break
                categories.add(category)
                values_by_session[str(summary.get("session_id") or "")] = value
            if invalid:
                continue
            if len(categories) > 1:
                diagnostics.append(
                    SessionListDiagnostic(
                        code="session_list_order_values_incomparable",
                        message="Ignoring order specification whose values have incompatible types.",
                        plugin_id=spec.plugin_id,
                        action_id=spec.action_id,
                        details={"key": spec.key},
                    )
                )
                continue
            valid.append((spec, values_by_session))

        for spec, values_by_session in reversed(valid):
            ordered.sort(
                key=lambda summary: _sortable_key(
                    values_by_session[str(summary.get("session_id") or "")]
                ),
                reverse=spec.direction == "desc",
            )
        return ordered


def _numeric_modified(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return 0.0


def _sortable_category(value: Any) -> Optional[str]:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return "number"
    if isinstance(value, str):
        return "string"
    return None


def _sortable_key(value: Any) -> Any:
    if value is None:
        return 0
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return value


def _stringify_template_value(value: Any) -> str:
    if value is None:
        return ""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _render_template(template: str, value: Any) -> str:
    text = _stringify_template_value(value)
    return template.replace("{{data}}", text, 1).replace("{{ data }}", text, 1)


def _format_datetime(value: Any) -> Any:
    parsed: Optional[datetime] = None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            parsed = datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return value
    elif isinstance(value, str) and value:
        try:
            normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return value
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        parsed = parsed.astimezone(timezone.utc)
    if parsed is None:
        return value
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def _format_field_value(field: _SessionListField, value: Any) -> Any:
    if field.metadata.get("format") == "datetime":
        return _format_datetime(value)
    return value


def derive_session_list_presentation(
    summary: Dict[str, Any],
    fields: Sequence[_SessionListField],
) -> Dict[str, Any]:
    """Derive title, subtitle, and meta presentation from normalized fields."""

    grouped = {
        "title": sorted(
            (field for field in fields if field.role == "title"),
            key=lambda field: (field.order, field.declaration_index),
        ),
        "subtitle": sorted(
            (field for field in fields if field.role == "subtitle"),
            key=lambda field: (field.order, field.declaration_index),
        ),
        "meta": sorted(
            (field for field in fields if field.role == "meta"),
            key=lambda field: (field.order, field.declaration_index),
        ),
    }

    def first_value(role: str) -> Optional[str]:
        for field in grouped[role]:
            resolved = resolve_session_list_path(summary, field.data)
            if not resolved.found or resolved.value is None or resolved.value == "":
                continue
            text = _render_template(
                field.template,
                _format_field_value(field, resolved.value),
            )
            if text:
                return text
        return None

    title = first_value("title")
    if title is None:
        preview = summary.get("preview")
        if isinstance(preview, str) and preview.strip():
            title = preview
        else:
            session_id = summary.get("session_id")
            prefix = session_id[:8] if isinstance(session_id, str) else ""
            title = f"Session {prefix}"

    meta_parts: List[str] = []
    for field in grouped["meta"]:
        resolved = resolve_session_list_path(summary, field.data)
        if not resolved.found or resolved.value is None or resolved.value == "":
            continue
        text = _render_template(
            field.template,
            _format_field_value(field, resolved.value),
        )
        if text:
            meta_parts.append(text)

    return {
        "title": title,
        "subtitle": first_value("subtitle"),
        "meta": " · ".join(meta_parts) if meta_parts else None,
    }


__all__ = [
    "ResolvedPath",
    "SessionListDiagnostic",
    "SessionListFilterEvaluation",
    "SessionListFilterEvaluator",
    "SessionListService",
    "derive_session_list_presentation",
    "resolve_session_list_path",
]
