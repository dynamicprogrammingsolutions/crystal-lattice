from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

from agent_terminal_app.terminal import _run_terminal


class _HarnessAgentApplication:
    def get_application_config(self) -> Dict[str, Any]:
        return {
            "terminal_startup_help": "hint",
            "tool_output_live_one_line": False,
        }


class TerminalProgressHarnessApplication:
    """Minimal deterministic event source for the production prompt loop."""

    def __init__(self, event_path: Path) -> None:
        self._event_path = event_path
        self._event_offset = 0
        self._session_id = "terminal-progress-harness"
        self.agent_app = _HarnessAgentApplication()

    @property
    def session_id(self) -> str:
        return self._session_id

    def available_agents(self) -> List[str]:
        return ["default"]

    def start_new_session(
        self,
        agent_id: str | None = None,
        *,
        persist: bool = False,
    ) -> SimpleNamespace:
        _ = agent_id, persist
        return SimpleNamespace(session_id=self._session_id)

    def current_agent_id(self) -> str:
        return "default"

    def get_last_assistant_message(self) -> None:
        return None

    def status_bar_elements(self) -> List[Dict[str, Any]]:
        return []

    def message_footer_elements(self) -> List[Dict[str, Any]]:
        return []

    def poll_new_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        _ = limit
        if not self._event_path.exists():
            return []
        lines = self._event_path.read_text(encoding="utf-8").splitlines()
        pending = lines[self._event_offset :]
        self._event_offset = len(lines)
        events: List[Dict[str, Any]] = []
        for line in pending:
            if not line.strip():
                continue
            value = json.loads(line)
            if isinstance(value, dict):
                events.append(value)
        return events


def main() -> None:
    event_path = Path(os.environ["TERMINAL_PROGRESS_EVENT_FILE"])
    asyncio.run(_run_terminal(TerminalProgressHarnessApplication(event_path)))


if __name__ == "__main__":
    main()
