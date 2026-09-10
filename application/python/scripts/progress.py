#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import shlex
import subprocess
from typing import Mapping, Sequence


CommandPart = str | os.PathLike[str]


def format_command(command: Sequence[CommandPart]) -> str:
    parts = [str(part) for part in command]
    if os.name == "nt":
        return subprocess.list2cmdline(parts)
    return shlex.join(parts)


@dataclass
class StepLogger:
    total_steps: int
    _step_index: int = field(default=0, init=False)

    def step(self, message: str) -> None:
        self._step_index += 1
        print(
            f"[{self._step_index}/{self.total_steps}] {message}",
            flush=True,
        )

    def detail(self, message: str) -> None:
        print(f"      {message}", flush=True)

    def command(self, command: Sequence[CommandPart]) -> None:
        self.detail(f"$ {format_command(command)}")

    def run_visible(
        self,
        command: Sequence[CommandPart],
        *,
        cwd: Path,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[bytes]:
        normalized = [str(part) for part in command]
        self.command(normalized)
        return subprocess.run(
            normalized,
            cwd=str(cwd),
            env=None if env is None else dict(env),
            timeout=timeout,
            check=check,
        )

    def run_capture(
        self,
        command: Sequence[CommandPart],
        *,
        cwd: Path,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        normalized = [str(part) for part in command]
        self.command(normalized)
        return subprocess.run(
            normalized,
            cwd=str(cwd),
            env=None if env is None else dict(env),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=check,
        )


__all__ = ["StepLogger", "format_command"]
