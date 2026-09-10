from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "application" / "python" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import boot_smoke  # type: ignore[import-not-found]  # noqa: E402
from progress import (  # type: ignore[import-not-found]  # noqa: E402
    StepLogger,
    format_command,
)


def test_step_logger_matches_release_progress_format(capsys) -> None:
    progress = StepLogger(total_steps=2)

    progress.step("Preparing")
    progress.detail("workspace: /tmp/example")
    progress.step("Running")
    progress.command(["python", "example.py", "--name", "two words"])

    assert capsys.readouterr().out.splitlines() == [
        "[1/2] Preparing",
        "      workspace: /tmp/example",
        "[2/2] Running",
        "      $ " + format_command(["python", "example.py", "--name", "two words"]),
    ]


def test_visible_subprocess_output_is_not_delayed(
    tmp_path: Path,
    capfd,
) -> None:
    progress = StepLogger(total_steps=1)
    progress.step("Running child")

    progress.run_visible(
        [sys.executable, "-c", "print('child-visible', flush=True)"],
        cwd=tmp_path,
    )

    output = capfd.readouterr().out
    assert output.index("[1/1] Running child") < output.index("child-visible")


def test_boot_wait_reports_periodic_progress(monkeypatch) -> None:
    monotonic_values = iter((0.0, 0.5, 1.2, 1.3))
    request_count = 0
    messages: list[str] = []

    class RunningProcess:
        @staticmethod
        def poll() -> None:
            return None

    def fake_request(_url: str, *, timeout: float) -> dict[str, str]:
        nonlocal request_count
        assert timeout == 2
        request_count += 1
        if request_count == 1:
            raise OSError("not ready")
        return {"status": "ok"}

    monkeypatch.setattr(boot_smoke.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(boot_smoke.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(boot_smoke, "_json_request", fake_request)

    boot_smoke._wait_for_server(
        "http://127.0.0.1:1234",
        RunningProcess(),  # type: ignore[arg-type]
        timeout_seconds=10,
        progress=messages.append,
        progress_interval_seconds=1,
    )

    assert messages == ["still waiting for CLI readiness after 1 seconds"]
