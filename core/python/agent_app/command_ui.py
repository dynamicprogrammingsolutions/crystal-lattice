"""Normalization for action-backed command UI elements."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


COMMAND_UI_TYPES = frozenset({"cli_command", "slash_command"})
COMMAND_SCOPES = frozenset({"application", "session"})
_MAPPING_PREFIXES = (
    "$session.",
    "$message.",
    "$dialog.",
    "$form.",
    "$context.",
)


class CommandCatalogError(ValueError):
    """Raised when command UI declarations cannot form an unambiguous catalog."""


def _path(value: Any, *, field: str) -> tuple[str, ...]:
    if isinstance(value, str):
        parts = tuple(part for part in value.strip().split() if part)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        parts = tuple(value)
    else:
        parts = ()
    if not parts or any(
        not isinstance(part, str)
        or not part
        or part.startswith("/")
        or any(character.isspace() for character in part)
        for part in parts
    ):
        raise CommandCatalogError(
            f"{field} must be a non-empty token path without slash prefixes"
        )
    return parts


def normalize_command_element(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize one ``cli_command`` or ``slash_command`` element."""

    ui_type = raw.get("ui_type")
    if ui_type not in COMMAND_UI_TYPES:
        raise CommandCatalogError(
            "command ui_type must be 'cli_command' or 'slash_command'"
        )
    plugin = raw.get("plugin")
    element_id = raw.get("id")
    action_id = raw.get("action_id")
    if not isinstance(plugin, str) or not plugin:
        raise CommandCatalogError(f"{ui_type}.plugin must be a non-empty string")
    if not isinstance(element_id, str) or not element_id:
        raise CommandCatalogError(f"{ui_type}.id must be a non-empty string")
    if not isinstance(action_id, str) or not action_id:
        raise CommandCatalogError(f"{ui_type}.action_id must be a non-empty string")

    path = _path(raw.get("path"), field=f"{plugin}.{element_id}.path")
    raw_aliases = raw.get("aliases", [])
    if not isinstance(raw_aliases, list):
        raise CommandCatalogError(f"{plugin}.{element_id}.aliases must be a list")
    aliases: list[list[str]] = []
    seen = {path}
    for position, alias in enumerate(raw_aliases):
        normalized = _path(
            alias,
            field=f"{plugin}.{element_id}.aliases[{position}]",
        )
        if normalized in seen:
            continue
        seen.add(normalized)
        aliases.append(list(normalized))

    scope = raw.get("scope", "application")
    if scope not in COMMAND_SCOPES:
        raise CommandCatalogError(
            f"{plugin}.{element_id}.scope must be application or session"
        )
    order = raw.get("order")
    if not isinstance(order, (int, float)) or isinstance(order, bool):
        order = 0

    fixed_params = raw.get("fixed_params")
    if fixed_params is not None and not isinstance(fixed_params, Mapping):
        raise CommandCatalogError(
            f"{plugin}.{element_id}.fixed_params must be a mapping"
        )
    param_map = raw.get("param_map")
    if param_map is not None:
        if not isinstance(param_map, Mapping) or any(
            not isinstance(name, str)
            or not name
            or not isinstance(source, str)
            or not source.startswith(_MAPPING_PREFIXES)
            for name, source in param_map.items()
        ):
            raise CommandCatalogError(
                f"{plugin}.{element_id}.param_map contains an invalid mapping"
            )
    dialog = raw.get("dialog")
    if dialog is not None:
        if not isinstance(dialog, Mapping) or dialog.get("kind") not in {
            "none",
            "confirm",
            "form",
        }:
            raise CommandCatalogError(
                f"{plugin}.{element_id}.dialog must be none, confirm, or form"
            )
        inputs = dialog.get("inputs")
        if dialog.get("kind") == "form" and (
            inputs is not None
            and (
                not isinstance(inputs, list)
                or any(
                    not isinstance(field, Mapping)
                    or not isinstance(field.get("name"), str)
                    or not field.get("name")
                    for field in inputs
                )
            )
        ):
            raise CommandCatalogError(
                f"{plugin}.{element_id}.dialog.inputs contains an invalid field"
            )
    disabled = raw.get("disabled")
    if disabled is not None and not isinstance(disabled, bool):
        raise CommandCatalogError(f"{plugin}.{element_id}.disabled must be a boolean")
    if raw.get("disabled_reason") is not None and not isinstance(
        raw.get("disabled_reason"), str
    ):
        raise CommandCatalogError(
            f"{plugin}.{element_id}.disabled_reason must be a string"
        )
    foreground = raw.get("foreground")
    if foreground is not None:
        if not isinstance(foreground, Mapping):
            raise CommandCatalogError(
                f"{plugin}.{element_id}.foreground must be a mapping"
            )
        for field in ("attempt_id_path", "state_path"):
            if not isinstance(foreground.get(field), str) or not foreground.get(field):
                raise CommandCatalogError(
                    f"{plugin}.{element_id}.foreground.{field} must be a string"
                )
        for field in (
            "pending_states",
            "success_states",
            "failure_states",
            "cancelled_states",
            "expired_states",
        ):
            values = foreground.get(field)
            if not isinstance(values, list) or any(
                not isinstance(value, str) or not value for value in values
            ):
                raise CommandCatalogError(
                    f"{plugin}.{element_id}.foreground.{field} must be a string list"
                )
        interval = foreground.get("poll_interval_seconds")
        if (
            not isinstance(interval, (int, float))
            or isinstance(interval, bool)
            or interval < 0.1
            or interval > 60
        ):
            raise CommandCatalogError(
                f"{plugin}.{element_id}.foreground.poll_interval_seconds "
                "must be between 0.1 and 60"
            )
        for field in ("status", "cancel"):
            step = foreground.get(field)
            if (
                not isinstance(step, Mapping)
                or not isinstance(step.get("action_id"), str)
                or not step.get("action_id")
            ):
                raise CommandCatalogError(
                    f"{plugin}.{element_id}.foreground.{field} must bind an action"
                )
    browser = raw.get("browser")
    if browser is not None and (
        not isinstance(browser, Mapping) or browser.get("auto_open_local") is not True
    ):
        raise CommandCatalogError(
            f"{plugin}.{element_id}.browser must declare auto_open_local=true"
        )

    return {
        **raw,
        "ui_type": ui_type,
        "plugin": plugin,
        "id": element_id,
        "label": (
            raw["label"]
            if isinstance(raw.get("label"), str) and raw["label"]
            else " ".join(path)
        ),
        "description": (
            raw["description"] if isinstance(raw.get("description"), str) else ""
        ),
        "path": list(path),
        "aliases": aliases,
        "scope": scope,
        "order": order,
    }


def legacy_command_element(
    raw: Mapping[str, Any],
    *,
    plugin: str,
    position: int,
) -> dict[str, Any]:
    """Adapt one legacy ``get_commands`` declaration to CLI compatibility."""

    name = raw.get("name")
    action_id = raw.get("action_id")
    if not isinstance(name, str) or not name:
        raise CommandCatalogError(
            f"legacy command from {plugin!r} is missing a non-empty name"
        )
    if not isinstance(action_id, str) or not action_id:
        raise CommandCatalogError(
            f"legacy command {plugin}.{name} is missing a non-empty action_id"
        )
    return normalize_command_element(
        {
            **raw,
            "ui_type": "cli_command",
            "plugin": plugin,
            "id": f"legacy:{name}",
            "label": raw.get("description") or name,
            "path": [name],
            "aliases": [],
            "scope": "application",
            "order": 100000 + position,
            "legacy": True,
        }
    )


def build_command_catalog(
    elements: Iterable[Mapping[str, Any]],
    *,
    ui_type: str,
    reserved_paths: Iterable[Sequence[str]] = (),
) -> list[dict[str, Any]]:
    """Return a normalized, collision-free catalog in declaration order."""

    if ui_type not in COMMAND_UI_TYPES:
        raise ValueError(f"unsupported command ui_type {ui_type!r}")
    normalized = [
        normalize_command_element(element)
        for element in elements
        if element.get("ui_type") == ui_type
    ]

    reserved = [tuple(path) for path in reserved_paths if path]
    owners: dict[tuple[str, ...], list[str]] = {path: ["built-in"] for path in reserved}
    for element in normalized:
        identity = f"{element['plugin']}.{element['id']}"
        routes = [element["path"], *element.get("aliases", [])]
        for route in routes:
            route_path = tuple(route)
            owners.setdefault(route_path, []).append(identity)
            if any(
                reserved_path != route_path
                and (
                    route_path[: len(reserved_path)] == reserved_path
                    or reserved_path[: len(route_path)] == route_path
                )
                for reserved_path in reserved
            ):
                owners[route_path].append("built-in")

    conflicts = [
        (path, identities) for path, identities in owners.items() if len(identities) > 1
    ]
    if conflicts:
        details = "; ".join(
            f"{' '.join(path)}: {', '.join(sorted(identities))}"
            for path, identities in sorted(conflicts, key=lambda item: item[0])
        )
        raise CommandCatalogError(f"command route collisions: {details}")

    return sorted(
        normalized,
        key=lambda element: (
            element.get("order", 0),
            tuple(element["path"]),
            element["plugin"],
            element["id"],
        ),
    )


def match_command_path(
    catalog: Iterable[Mapping[str, Any]],
    tokens: Sequence[str],
) -> tuple[dict[str, Any] | None, list[str]]:
    """Resolve the longest canonical or alias path from ``tokens``."""

    candidates: list[tuple[int, dict[str, Any]]] = []
    for raw in catalog:
        element = dict(raw)
        for route in [element.get("path"), *(element.get("aliases") or [])]:
            if not isinstance(route, list):
                continue
            if list(tokens[: len(route)]) == route:
                candidates.append((len(route), element))
    if not candidates:
        return None, list(tokens)
    length, element = max(candidates, key=lambda item: item[0])
    return element, list(tokens[length:])


__all__ = [
    "COMMAND_UI_TYPES",
    "CommandCatalogError",
    "build_command_catalog",
    "legacy_command_element",
    "match_command_path",
    "normalize_command_element",
]
