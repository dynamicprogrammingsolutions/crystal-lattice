from __future__ import annotations

import copy
import json
import random
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Sequence


PROBE_CONTENT_PREFIX = "PROBE_CONTENT_"
_PROBE_ID_PATTERN = re.compile(r"PROBE_CONTENT_([0-9]{4}_[0-9a-f]{8})")
_REASONING_IGNORED_KEYS = frozenset(
    {
        "content",
        "encrypted_content",
        "signature",
        "summary",
    }
)

JsonPathSegment = str | int
JsonPath = tuple[JsonPathSegment, ...]
ProbeScope = Literal["session", "core", "native"]


@dataclass(frozen=True)
class ProbeMarker:
    marker_id: str
    key: str
    value: str
    response_path: str


@dataclass(frozen=True)
class ProbeMutationResult:
    payload: dict[str, Any]
    markers: tuple[ProbeMarker, ...]
    candidate_count: int
    selected_count: int
    seed: int

    @property
    def manifest(self) -> dict[str, ProbeMarker]:
        return {marker.marker_id: marker for marker in self.markers}


@dataclass(frozen=True)
class ProbeDetection:
    marker: ProbeMarker
    occurrences: int
    scope: ProbeScope


@dataclass(frozen=True)
class _Candidate:
    path: JsonPath
    target: dict[str, Any]


def _render_path(path: JsonPath) -> str:
    rendered = "$"
    for segment in path:
        if isinstance(segment, int):
            rendered += f"[{segment}]"
            continue
        if segment.isidentifier():
            rendered += f".{segment}"
            continue
        rendered += f"[{json.dumps(segment, ensure_ascii=False)}]"
    return rendered


def _discover_candidates(
    value: Any,
    *,
    max_depth: int,
) -> list[_Candidate]:
    candidates: list[_Candidate] = []

    def visit(current: Any, path: JsonPath, depth: int) -> None:
        if depth > max_depth:
            raise ValueError(
                f"probe response exceeds maximum discovery depth at {_render_path(path)}"
            )

        if isinstance(current, dict):
            if "_metadata" in path:
                return

            candidates.append(_Candidate(path=path, target=current))
            is_reasoning = current.get("type") == "reasoning"
            for key, child in current.items():
                if is_reasoning and key in _REASONING_IGNORED_KEYS:
                    continue
                visit(child, (*path, str(key)), depth + 1)
            return

        if isinstance(current, list):
            for index, child in enumerate(current):
                visit(child, (*path, index), depth + 1)

    visit(value, (), 0)
    return candidates


def mutate_response_objects(
    payload: Mapping[str, Any],
    *,
    seed: int,
    max_mutations: int = 100,
    max_depth: int = 64,
) -> ProbeMutationResult:
    if max_mutations <= 0:
        raise ValueError("max_mutations must be greater than zero")
    if max_depth <= 0:
        raise ValueError("max_depth must be greater than zero")

    mutated = copy.deepcopy(dict(payload))
    candidates = _discover_candidates(mutated, max_depth=max_depth)
    ordered = sorted(candidates, key=lambda candidate: _render_path(candidate.path))

    rng = random.Random(seed)
    if len(ordered) <= max_mutations:
        selected = ordered
    else:
        selected = sorted(
            rng.sample(ordered, max_mutations),
            key=lambda candidate: _render_path(candidate.path),
        )

    markers: list[ProbeMarker] = []
    used_ids: set[str] = set()
    for index, candidate in enumerate(selected, start=1):
        while True:
            marker_id = f"{index:04d}_{rng.getrandbits(32):08x}"
            key = f"__probe_{marker_id}"
            if marker_id not in used_ids and key not in candidate.target:
                used_ids.add(marker_id)
                break
        value = f"{PROBE_CONTENT_PREFIX}{marker_id}"
        candidate.target[key] = value
        markers.append(
            ProbeMarker(
                marker_id=marker_id,
                key=key,
                value=value,
                response_path=f"{_render_path(candidate.path)}.{key}",
            )
        )

    return ProbeMutationResult(
        payload=mutated,
        markers=tuple(markers),
        candidate_count=len(candidates),
        selected_count=len(selected),
        seed=seed,
    )


def detect_probe_markers_in_json(
    serialized: str,
    mutation: ProbeMutationResult,
    *,
    scope: ProbeScope = "session",
) -> list[ProbeDetection]:
    manifest = mutation.manifest
    counts: dict[str, int] = {}
    for match in _PROBE_ID_PATTERN.finditer(serialized):
        marker_id = match.group(1)
        if marker_id in manifest:
            counts[marker_id] = counts.get(marker_id, 0) + 1

    return [
        ProbeDetection(
            marker=manifest[marker_id],
            occurrences=counts[marker_id],
            scope=scope,
        )
        for marker_id in sorted(counts)
    ]


def detect_probe_markers_in_session_scope(
    session_payload: Mapping[str, Any],
    mutation: ProbeMutationResult,
    *,
    scope: ProbeScope,
) -> list[ProbeDetection]:
    if scope == "session":
        branch: Any = session_payload
    elif scope == "core":
        branch = session_payload.get("messages", [])
    elif scope == "native":
        metadata = session_payload.get("metadata")
        branch = (
            metadata.get("native_messages", []) if isinstance(metadata, Mapping) else []
        )
    else:
        raise ValueError(f"unsupported probe scope: {scope}")

    serialized = json.dumps(branch, ensure_ascii=False, separators=(",", ":"))
    return detect_probe_markers_in_json(serialized, mutation, scope=scope)


def format_probe_detections(
    detections: Sequence[ProbeDetection],
    mutation: ProbeMutationResult,
) -> str:
    lines = [
        (
            "provider response probe markers were retained: "
            f"seed={mutation.seed} candidates={mutation.candidate_count} "
            f"selected={mutation.selected_count}"
        )
    ]
    lines.extend(
        (
            f"{detection.marker.marker_id} "
            f"injected={detection.marker.response_path} "
            f"scope={detection.scope} "
            f"occurrences={detection.occurrences}"
        )
        for detection in detections
    )
    return "\n".join(lines)
