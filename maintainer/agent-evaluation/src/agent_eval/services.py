"""Run-owned artifact and evidence services."""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, TypeVar


ProjectionT = TypeVar("ProjectionT")

_SENSITIVE_KEY = re.compile(
    r"(?:^|[_-])(auth|credentials?|password|secret|token|api[_-]?key)(?:$|[_-])",
    re.IGNORECASE,
)


def jsonable(value: Any) -> Any:
    """Convert common values to deterministic JSON-compatible data."""

    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            rendered_key = str(key)
            if _SENSITIVE_KEY.search(rendered_key):
                result[rendered_key] = "<redacted>"
            else:
                result[rendered_key] = jsonable(item)
        return result
    if isinstance(value, (list, tuple, set, frozenset)):
        return [jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "to_dict"):
        try:
            return jsonable(value.to_dict())
        except Exception:
            pass
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: jsonable(getattr(value, field.name))
            for field in fields(value)
        }
    return repr(value)


class EvidenceVisibility(str, Enum):
    """Default destination for an evidence item."""

    CANONICAL = "canonical"
    RAW = "raw"
    INTERNAL = "internal"


@dataclass(frozen=True)
class EvidenceReference:
    """Stable in-run reference to one evidence item."""

    index: int
    kind: str


@dataclass(frozen=True)
class Evidence:
    """One append-only observation."""

    kind: str
    source: str
    value: object
    metadata: Mapping[str, object]
    timestamp: str
    visibility: EvidenceVisibility


class EvidenceJournal:
    """Thread-safe append-only journal with explicit projections."""

    def __init__(self) -> None:
        self._items: list[Evidence] = []
        self._lock = threading.Lock()

    def emit(
        self,
        kind: str,
        value: object,
        *,
        source: str,
        metadata: Mapping[str, object] | None = None,
        visibility: EvidenceVisibility = EvidenceVisibility.CANONICAL,
    ) -> EvidenceReference:
        item = Evidence(
            kind=kind,
            source=source,
            value=value,
            metadata=dict(metadata or {}),
            timestamp=datetime.now(timezone.utc).isoformat(),
            visibility=visibility,
        )
        with self._lock:
            index = len(self._items)
            self._items.append(item)
        return EvidenceReference(index=index, kind=kind)

    def items(self) -> tuple[Evidence, ...]:
        with self._lock:
            return tuple(self._items)

    def extend(self, items: tuple[Evidence, ...]) -> None:
        with self._lock:
            self._items.extend(items)

    def select(
        self,
        predicate: Callable[[Evidence], bool],
    ) -> tuple[Evidence, ...]:
        return tuple(item for item in self.items() if predicate(item))

    def values(self, kind: str) -> tuple[object, ...]:
        return tuple(item.value for item in self.items() if item.kind == kind)

    def require(self, kind: str) -> object:
        values = self.values(kind)
        if not values:
            raise KeyError(f"no evidence recorded for {kind!r}")
        return values[-1]

    def project(
        self,
        name: str,
        *,
        using: Callable[["EvidenceJournal"], ProjectionT],
    ) -> ProjectionT:
        result = using(self)
        self.emit(
            f"projection.{name}",
            result,
            source="evidence",
            visibility=EvidenceVisibility.RAW,
        )
        return result


class ArtifactWriter:
    """Write run artifacts while preventing path escape and redacting JSON."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, relative: str | Path) -> Path:
        target = (self.root / relative).resolve()
        if target != self.root and self.root not in target.parents:
            raise ValueError(f"artifact path escapes root: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def write_text(self, relative: str | Path, content: str) -> Path:
        target = self.path(relative)
        target.write_text(content, encoding="utf-8")
        return target

    def write_bytes(self, relative: str | Path, content: bytes) -> Path:
        target = self.path(relative)
        target.write_bytes(content)
        return target

    def write_json(self, relative: str | Path, value: object) -> Path:
        return self.write_text(
            relative,
            json.dumps(
                jsonable(value),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n",
        )

    def record(self, name: str, value: object) -> Path:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-")
        if not safe_name:
            raise ValueError("record name must contain an alphanumeric character")
        if isinstance(value, str):
            suffix = "" if "." in safe_name else ".md"
            return self.write_text(f"records/{safe_name}{suffix}", value.rstrip() + "\n")
        suffix = "" if safe_name.endswith(".json") else ".json"
        return self.write_json(f"records/{safe_name}{suffix}", value)


@dataclass(frozen=True)
class RunServices:
    """Environment-independent services supplied to one run context."""

    run_id: str
    name: str
    artifact_dir: Path
    workspace: Path | None
    parent: object | None
    evidence: EvidenceJournal
    artifacts: ArtifactWriter

    def record(
        self,
        kind: str,
        value: object,
        *,
        metadata: Mapping[str, object] | None = None,
        visibility: EvidenceVisibility = EvidenceVisibility.CANONICAL,
    ) -> EvidenceReference:
        return self.evidence.emit(
            kind,
            value,
            source="program",
            metadata=metadata,
            visibility=visibility,
        )

    def record_artifact(self, name: str, value: object) -> Path:
        return self.artifacts.record(name, value)