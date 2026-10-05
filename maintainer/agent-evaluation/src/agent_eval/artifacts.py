"""Canonical and raw run artifact rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .result import RunError
from .services import (
    ArtifactWriter,
    Evidence,
    EvidenceVisibility,
    jsonable,
)
from .workspace import WorkspaceObservation


def write_run_artifacts(
    writer: ArtifactWriter,
    *,
    run_id: str,
    name: str,
    status: str,
    cache_hit: bool,
    parent_run_id: str | None,
    environment_fingerprint: object,
    workspace: Path | None,
    workspace_fingerprint: object | None,
    snapshot_sha256: str | None,
    value: object,
    environment: object,
    error: RunError | None,
    evidence: tuple[Evidence, ...],
    workspace_observation: WorkspaceObservation,
) -> None:
    canonical_evidence = [
        item for item in evidence if item.visibility is EvidenceVisibility.CANONICAL
    ]
    persisted_evidence = [
        item for item in evidence if item.visibility is not EvidenceVisibility.INTERNAL
    ]
    payload = {
        "run_id": run_id,
        "name": name,
        "status": status,
        "cache_hit": cache_hit,
        "parent_run_id": parent_run_id,
        "environment_fingerprint": environment_fingerprint,
        "workspace": str(workspace) if workspace is not None else None,
        "workspace_fingerprint": workspace_fingerprint,
        "snapshot_sha256": snapshot_sha256,
        "changed_paths": workspace_observation.changed_paths,
        "value": value,
        "environment": environment,
        "error": error,
        "evidence": canonical_evidence,
    }
    writer.write_json("result.json", payload)
    writer.write_text("result.md", _render_markdown(payload))
    writer.write_json("raw/evidence.json", persisted_evidence)
    writer.write_text(
        "raw/workspace/git-status.txt",
        workspace_observation.git_status,
    )
    writer.write_bytes(
        "raw/workspace/git-diff.patch",
        workspace_observation.git_diff,
    )


def _render_markdown(payload: Mapping[str, object]) -> str:
    error = payload.get("error")
    lines = [
        f"# Evaluation run: {payload['name']}",
        "",
        f"- Run ID: `{payload['run_id']}`",
        f"- Status: **{payload['status']}**",
        f"- Cache hit: **{'yes' if payload['cache_hit'] else 'no'}**",
        f"- Parent run: `{payload['parent_run_id'] or 'none'}`",
        f"- Snapshot SHA-256: `{payload['snapshot_sha256'] or 'none'}`",
        f"- Workspace: `{payload['workspace'] or 'none'}`",
        "",
        "## Changed paths",
        "",
    ]
    changed = payload.get("changed_paths")
    if isinstance(changed, (list, tuple)) and changed:
        lines.extend(f"- `{path}`" for path in changed)
    else:
        lines.append("None.")

    lines.extend(
        [
            "",
            "## Program value",
            "",
            _json_block(payload.get("value")),
            "",
            "## Environment observation",
            "",
            _json_block(payload.get("environment")),
            "",
            "## Error",
            "",
        ]
    )
    if error is None:
        lines.append("None.")
    else:
        lines.append(_json_block(error))

    evidence = payload.get("evidence")
    lines.extend(
        [
            "",
            "## Canonical evidence",
            "",
            _json_block(evidence),
            "",
            (
                "Complete environment, workspace, and failure evidence is "
                "available under `raw/`."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _json_block(value: object) -> str:
    rendered = json.dumps(
        jsonable(value),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    if len(rendered) > 20_000:
        rendered = rendered[:20_000] + "\n... <truncated in canonical view>"
    return f"```json\n{rendered}\n```"
