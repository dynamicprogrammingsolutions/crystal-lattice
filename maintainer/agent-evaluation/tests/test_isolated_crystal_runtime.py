"""Isolated (fork-worker) Crystal Lattice execution.

Process isolation moves each run's application lifecycle into a forked
worker so the process-global runtime environment overlay can never
collide between sibling runs — the failure mode behind the runner's
``--max-concurrent 1`` cap. These tests cover the mechanism at its
public boundary: the full kernel path (cache, records, artifacts,
evidence) through ``AgentEval``, sibling concurrency that would
conflict in-process, and worker failure capture.
"""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from agent_eval import AgentEval
from agent_eval.crystal_lattice.context import CrystalLatticeContext
from agent_eval.crystal_lattice.environment import CrystalLatticeEnvironment
from agent_eval.runner import RunModel
from agent_eval.services import ArtifactWriter, EvidenceJournal, RunServices

from fixtures.crystal_mini_scenario import (
    ECHO_AGENT,
    ECHO_SCENARIO,
    MINI_AGENTS,
    MINI_GUIDANCE,
    SCENARIO_PROMPTS,
    mini_environment_values,
    mini_workspace_factory,
    write_mini_config,
)


def _isolated_environment(root: Path, *, name: str) -> CrystalLatticeEnvironment:
    # Each environment gets its own config DIRECTORY: the runtime
    # overlay installs CONFIG_DIR (the config file's parent), so
    # sibling roots must differ by directory, not just file name.
    config_path = root / name / "config.json"
    write_mini_config(config_path, agents=(ECHO_AGENT,))
    return CrystalLatticeEnvironment.from_config(
        config_path,
        environment=mini_environment_values(include_ollama=False),
        isolated=True,
    )


def _echo_program(context: CrystalLatticeContext) -> dict[str, object]:
    context.start(ECHO_AGENT)
    context.config.update(
        {
            "model": MINI_AGENTS[ECHO_AGENT].model,
            "guidance_file": str(context.workspace / "AGENTS.md"),
            "response_mode": "echo",
        }
    )
    context.add_message("user", SCENARIO_PROMPTS[ECHO_SCENARIO])
    outcome = context.request()
    return {
        "response": outcome.final_response,
        "completed": outcome.completed,
        "errors": tuple(outcome.error_messages),
    }


def test_isolated_run_executes_program_in_worker(tmp_path: Path) -> None:
    environment = _isolated_environment(tmp_path, name="iso")
    evaluation = AgentEval(
        default_environment=environment,
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    )
    model = RunModel(evaluation, label="iso-batch")

    def workspace_factory(staging: Path) -> Path:
        return mini_workspace_factory(staging, guidance=MINI_GUIDANCE)

    run = model.run(
        "iso-echo",
        _echo_program,
        identity="iso:v1",
        workspace=workspace_factory,
    )
    run.raise_for_error()

    assert run.value["response"] == f"Echo: {SCENARIO_PROMPTS[ECHO_SCENARIO]}"
    assert run.value["completed"] is True
    assert run.cache_hit is False

    # Worker-side lifecycle artifacts land in the shared run directory
    # and worker-emitted evidence is merged into the parent journal.
    observation = json.loads(
        (
            run.artifact_dir
            / "raw"
            / "environment"
            / "crystal-lattice-observation.json"
        ).read_text(encoding="utf-8")
    )
    assert observation["request_count"] == 1
    evidence = json.loads(
        (run.artifact_dir / "raw" / "evidence.json").read_text(encoding="utf-8")
    )
    kinds = {item["kind"] for item in evidence}
    assert "crystal_lattice.agent_started" in kinds
    assert "crystal_lattice.request_summary" in kinds

    # The pickled value round-trips through the execution cache.
    replay = model.run(
        "iso-echo",
        _echo_program,
        identity="iso:v1",
        workspace=workspace_factory,
    )
    replay.raise_for_error()
    assert replay.cache_hit is True
    assert replay.value["response"] == run.value["response"]

    evaluation.close()


def test_isolated_siblings_with_different_roots_run_concurrently(
    tmp_path: Path,
) -> None:
    """Two live runs with different config roots coexist in one process.

    The control (inline execution) demonstrates the real collision:
    overlapping ``open()`` calls install different ``CONFIG_DIR``
    values into the process-global overlay and raise. The isolated
    environments run the same programs concurrently and both succeed.
    """

    environment_a = _isolated_environment(tmp_path, name="sibling-a")
    environment_b = _isolated_environment(tmp_path, name="sibling-b")

    def run_isolated(environment: CrystalLatticeEnvironment, tag: str) -> dict:
        run_dir = tmp_path / f"run-{tag}"
        run_dir.mkdir(parents=True, exist_ok=True)
        services = RunServices(
            run_id=f"iso-{tag}",
            name=f"iso-{tag}",
            artifact_dir=run_dir,
            workspace=run_dir / "workspace",
            parent=None,
            evidence=EvidenceJournal(),
            artifacts=ArtifactWriter(run_dir),
        )
        (run_dir / "workspace").mkdir(exist_ok=True)
        (run_dir / "workspace" / "AGENTS.md").write_text(
            MINI_GUIDANCE, encoding="utf-8"
        )
        outcome = environment.isolated_execute(
            services=services,
            workspace=services.workspace,
            parent_snapshot=None,
            program=_echo_program,
            writer=services.artifacts,
        )
        assert outcome.error is None, outcome.error
        return outcome.value  # type: ignore[return-value]

    # Align the two executions so both applications are constructed
    # while the sibling is live — the exact window that conflicts
    # in-process.
    barrier = threading.Barrier(2)

    def coordinated(environment, tag):  # type: ignore[no-untyped-def]
        barrier.wait(timeout=60)
        return run_isolated(environment, tag)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(coordinated, environment_a, "a")
        second = pool.submit(coordinated, environment_b, "b")
        values = [first.result(timeout=120), second.result(timeout=120)]

    assert all(value["completed"] is True for value in values)
    assert len({value["response"] for value in values}) == 1

    # Control: the same environments without isolation conflict.
    inline_a = CrystalLatticeEnvironment.from_config(
        tmp_path / "sibling-a" / "config.json"
    )
    inline_b = CrystalLatticeEnvironment.from_config(
        tmp_path / "sibling-b" / "config.json"
    )

    live = threading.Event()
    release = threading.Event()
    conflict: list[BaseException] = []

    def hold_open() -> None:
        services = _inline_services(tmp_path, "control-a")
        try:
            with inline_a.open(
                services=services,
                workspace=services.workspace,
                parent_snapshot=None,
            ):
                live.set()
                release.wait(timeout=60)
        except BaseException as exc:  # noqa: BLE001 - recorded for assertion
            conflict.append(exc)
        finally:
            live.set()

    def collide() -> None:
        live.wait(timeout=60)
        services = _inline_services(tmp_path, "control-b")
        try:
            with inline_b.open(
                services=services,
                workspace=services.workspace,
                parent_snapshot=None,
            ):
                pass
        except BaseException as exc:  # noqa: BLE001 - recorded for assertion
            conflict.append(exc)
        finally:
            release.set()

    holder = threading.Thread(target=hold_open)
    collider = threading.Thread(target=collide)
    holder.start()
    collider.start()
    holder.join(timeout=120)
    collider.join(timeout=120)

    assert any(
        "Conflicting runtime environment overlay" in str(exc) for exc in conflict
    ), conflict


def _inline_services(root: Path, name: str) -> RunServices:
    run_dir = root / name
    run_dir.mkdir(parents=True, exist_ok=True)
    workspace = run_dir / "workspace"
    workspace.mkdir(exist_ok=True)
    (workspace / "AGENTS.md").write_text(MINI_GUIDANCE, encoding="utf-8")
    return RunServices(
        run_id=name,
        name=name,
        artifact_dir=run_dir,
        workspace=workspace,
        parent=None,
        evidence=EvidenceJournal(),
        artifacts=ArtifactWriter(run_dir),
    )


def test_isolated_worker_program_failure_is_captured(tmp_path: Path) -> None:
    environment = _isolated_environment(tmp_path, name="iso-failure")
    evaluation = AgentEval(
        default_environment=environment,
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    )
    model = RunModel(evaluation, label="iso-failure")

    def failing_program(context: CrystalLatticeContext) -> dict[str, object]:
        raise ValueError("worker program exploded")

    run = model.run(
        "iso-failure",
        failing_program,
        identity="iso-failure:v1",
        workspace=lambda staging: mini_workspace_factory(
            staging, guidance=MINI_GUIDANCE
        ),
    )
    assert run.error is not None
    print("ERR:", run.error.type, run.error.message[:300])
    assert run.error.phase == "program"
    assert run.error.type == "ValueError"
    traceback_text = (run.artifact_dir / "raw" / "errors" / "program.txt").read_text(
        encoding="utf-8"
    )
    assert "worker program exploded" in traceback_text
    evaluation.close()
