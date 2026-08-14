from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from agent_eval import RunEnvironment, RunServices


@dataclass
class ReplayContext:
    services: RunServices
    responses: list[str]
    position: int = 0

    def next_response(self, prompt: str) -> str:
        self.services.record("replay.prompt", prompt)
        response = self.responses[self.position]
        self.position += 1
        self.services.record("replay.response", response)
        return response


@dataclass(frozen=True)
class ReplaySnapshot:
    position: int


class ReplayEnvironment(RunEnvironment[ReplayContext]):
    def __init__(
        self,
        responses: list[str],
        *,
        identity: str = "replay",
        snapshot_enabled: bool = True,
    ) -> None:
        self.responses = responses
        self.identity = identity
        self.snapshot_enabled = snapshot_enabled
        self.open_count = 0
        self.finalize_count = 0

    def fingerprint(self) -> object:
        return {
            "type": "replay",
            "identity": self.identity,
            "schema": 1,
            "responses": self.responses,
            "snapshot_enabled": self.snapshot_enabled,
        }

    @contextmanager
    def open(
        self,
        *,
        services: RunServices,
        workspace: Path | None,
        parent_snapshot: object | None,
    ) -> Iterator[ReplayContext]:
        self.open_count += 1
        position = (
            parent_snapshot.position
            if isinstance(parent_snapshot, ReplaySnapshot)
            else 0
        )
        yield ReplayContext(
            services=services,
            responses=list(self.responses),
            position=position,
        )

    def snapshot(self, context: ReplayContext) -> object | None:
        if not self.snapshot_enabled:
            return None
        return ReplaySnapshot(position=context.position)

    def finalize(self, context: ReplayContext) -> object:
        self.finalize_count += 1
        return {
            "responses_consumed": context.position,
            "responses_remaining": len(context.responses) - context.position,
        }