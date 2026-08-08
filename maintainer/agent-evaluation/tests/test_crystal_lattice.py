from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from agent_app import AgentApplication
from agent_core import AgentCore, Session

from agent_eval import AgentEval
from agent_eval.crystal_lattice import (
    CrystalLatticeContext,
    CrystalLatticeEnvironment,
    CrystalLatticeSnapshot,
    CrystalRequestOutcome,
    application_session_snapshot,
)
from agent_eval.crystal_lattice.snapshots import restore_session


def write_config(
    tmp_path: Path,
    *,
    response_mode: str = "echo",
    response_text: str | None = None,
) -> Path:
    provider: dict[str, object] = {
        "provider": "agent_eval_test_provider",
        "model": "test-model",
        "response_mode": response_mode,
    }
    if response_text is not None:
        provider["response_text"] = response_text
    config = {
        "plugin_cache_dir": str(tmp_path / ".plugin-cache"),
        "providers": {"test": provider},
        "plugins": [
            "fixtures.crystal_plugins.EvaluationProvider",
            "fixtures.crystal_plugins.AddTool",
        ],
        "agents": {"default": {"provider": "test"}},
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def make_evaluation(
    tmp_path: Path,
    environment: CrystalLatticeEnvironment,
) -> AgentEval[CrystalLatticeContext]:
    return AgentEval(
        default_environment=environment,
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    )


def test_default_driver_crosses_real_application_and_core(
    tmp_path: Path,
) -> None:
    environment = CrystalLatticeEnvironment.from_config(write_config(tmp_path))
    with make_evaluation(tmp_path, environment) as evaluation:
        def program(context: CrystalLatticeContext):
            context.start("default")
            assert isinstance(context.application, AgentApplication)
            assert isinstance(context.core, AgentCore)
            assert isinstance(context.session, Session)
            context.add_message("user", "hello")
            outcome = context.request()
            return {
                "response": context.final_response(),
                "completed": outcome.completed,
                "events": len(outcome.events),
            }

        run = evaluation.run("crystal-default", program)

    run.raise_for_error()
    assert run.value["response"] == "Echo: hello"
    assert run.value["completed"] is True
    assert run.value["events"] > 0
    observation = cast(dict[str, object], run.environment)
    assert observation["request_count"] == 1
    assert run.artifact_dir.joinpath(
        "raw/environment/crystal-lattice-session.json"
    ).is_file()


def test_request_overrides_and_live_base_config_are_customizable(
    tmp_path: Path,
) -> None:
    config_path = write_config(tmp_path, response_text="base")
    environment = CrystalLatticeEnvironment.from_config(config_path)
    with make_evaluation(tmp_path, environment) as evaluation:
        def program(context: CrystalLatticeContext):
            context.start("default")
            context.config["response_text"] = "mutated base"
            context.add_message("user", "hello")
            base = context.request()
            context.add_message("user", "again")
            overridden = context.request(
                overrides={"response_text": "request override"}
            )
            return base.final_response, overridden.final_response

        run = evaluation.run("configuration", program)

    assert run.value == ("mutated base", "request override")


def test_custom_driver_can_bypass_application_request_loop(
    tmp_path: Path,
) -> None:
    environment = CrystalLatticeEnvironment.from_config(write_config(tmp_path))
    with make_evaluation(tmp_path, environment) as evaluation:
        def custom_driver(request):
            session = request.core.add_message(
                request.session,
                "assistant",
                "custom driver response",
            )
            session = request.context.application.save_session(session)
            return CrystalRequestOutcome(
                core=request.core,
                session=session,
                base_config=request.base_config,
                events=({"type": "custom"},),
                final_messages=(
                    {
                        "role": "assistant",
                        "content": "custom driver response",
                    },
                ),
                request_id=request.request_id,
                completed=True,
                cancelled=False,
                error_messages=(),
                tool_event_count=0,
                mutation_count=0,
                stop_reason=None,
                duration_seconds=0.0,
            )

        def program(context: CrystalLatticeContext):
            context.start("default")
            context.add_message("user", "hello")
            return context.request(driver=custom_driver).final_response

        run = evaluation.run("custom-driver", program)

    assert run.value == "custom driver response"


def test_real_tool_loop_observers_mutation_classifier_and_stop_condition(
    tmp_path: Path,
) -> None:
    environment = CrystalLatticeEnvironment.from_config(
        write_config(tmp_path, response_mode="tool_once")
    )
    observed: list[str] = []
    with make_evaluation(tmp_path, environment) as evaluation:
        def program(context: CrystalLatticeContext):
            context.start("default")
            context.add_message("user", "add numbers")
            return context.request(
                observers=(
                    lambda event: observed.append(str(event.get("type"))),
                ),
                mutation_classifier=lambda event: event.get("type")
                == "tool_results",
                stop_when=lambda progress: (
                    progress.mutation_count >= 1
                    and progress.event.get("type") == "session_checkpoint"
                ),
            )

        run = evaluation.run("tool-stop", program)

    run.raise_for_error()
    outcome = run.value
    assert outcome.stop_reason == "stop_condition"
    assert outcome.mutation_count == 1
    assert outcome.tool_event_count >= 2
    assert "tool_calls" in observed
    assert "tool_results" in observed
    assert any(message.role == "tool" for message in outcome.session.messages)


def test_real_tool_loop_runs_to_final_response(tmp_path: Path) -> None:
    environment = CrystalLatticeEnvironment.from_config(
        write_config(tmp_path, response_mode="tool_once")
    )
    with make_evaluation(tmp_path, environment) as evaluation:
        def program(context: CrystalLatticeContext):
            context.start("default")
            context.add_message("user", "add numbers")
            outcome = context.request()
            return outcome.final_response, outcome.tool_event_count

        run = evaluation.run("tool-complete", program)

    assert run.value[0] == "Tool completed: Result: 5"
    assert run.value[1] >= 2


def test_continuation_rebases_workspace_paths(tmp_path: Path) -> None:
    environment = CrystalLatticeEnvironment.from_config(write_config(tmp_path))

    def workspace_factory(staging: Path) -> Path:
        staging.mkdir(parents=True)
        return staging

    with make_evaluation(tmp_path, environment) as evaluation:
        def seed(context: CrystalLatticeContext):
            context.start("default")
            assert context.workspace is not None
            context.add_message(
                "user",
                f"Inspect {context.workspace / 'target.txt'}",
            )
            return str(context.workspace)

        parent = evaluation.run(
            "workspace-seed",
            seed,
            workspace=workspace_factory,
        )

        def continue_program(context: CrystalLatticeContext):
            content = str(context.session.messages[0].content)
            return str(context.workspace), content

        child = evaluation.run(
            "workspace-child",
            continue_program,
            continue_from=parent,
        )

    parent_workspace = parent.value
    child_workspace, restored_content = child.value
    assert parent_workspace != child_workspace
    assert child_workspace in restored_content
    assert parent_workspace not in restored_content


def test_rebased_snapshot_drops_stale_provider_native_history() -> None:
    old_root = "/tmp/evaluation-parent"
    new_root = "/tmp/evaluation-child"
    snapshot = CrystalLatticeSnapshot(
        schema=1,
        session={
            "session_id": "session-1",
            "messages": [
                {
                    "role": "user",
                    "content": f"Inspect {old_root}/target.txt",
                }
            ],
            "metadata": {
                "native_messages": [
                    {
                        "role": "user",
                        "content": f"Inspect {old_root}/target.txt",
                    }
                ],
                "native_messages_integrity": {
                    "message_count": 1,
                    "total_chars": len(f"Inspect {old_root}/target.txt"),
                },
                "agent_id": "default",
            },
        },
        workspace_root=old_root,
        request_defaults={},
    )

    restored = restore_session(snapshot, workspace_root=new_root)

    assert restored is not None
    assert restored.messages[0].content == f"Inspect {new_root}/target.txt"
    assert "native_messages" not in restored.metadata
    assert "native_messages_integrity" not in restored.metadata
    assert restored.metadata["agent_id"] == "default"


def test_snapshot_without_rebase_retains_provider_native_history() -> None:
    workspace = "/tmp/evaluation"
    snapshot = CrystalLatticeSnapshot(
        schema=1,
        session={
            "session_id": "session-1",
            "messages": [
                {
                    "role": "user",
                    "content": f"Inspect {workspace}/target.txt",
                }
            ],
            "metadata": {
                "native_messages": [
                    {
                        "role": "user",
                        "content": f"Inspect {workspace}/target.txt",
                    }
                ],
                "native_messages_integrity": {
                    "message_count": 1,
                    "total_chars": len(f"Inspect {workspace}/target.txt"),
                },
            },
        },
        workspace_root=workspace,
        request_defaults={},
    )

    restored = restore_session(snapshot, workspace_root=workspace)

    assert restored is not None
    assert "native_messages" in restored.metadata
    assert "native_messages_integrity" in restored.metadata


def test_named_snapshots_evaluation_projection_and_presentation(
    tmp_path: Path,
) -> None:
    environment = CrystalLatticeEnvironment.from_config(write_config(tmp_path))
    with make_evaluation(tmp_path, environment) as evaluation:
        def program(context: CrystalLatticeContext):
            context.start("default")
            context.add_message("user", "hello")
            context.request()
            default_snapshot = context.create_snapshot(
                "session",
                using=application_session_snapshot,
            )
            custom_snapshot = context.create_snapshot(
                "custom",
                using=lambda current: {
                    "response": current.final_response(),
                },
            )
            projected = context.evidence.project(
                "responses",
                using=lambda evidence: {
                    "summary": evidence.require(
                        "crystal_lattice.request_summary"
                    )
                },
            )
            score = context.evaluate(
                "length",
                context.final_response(),
                using=len,
            )
            created = context.present(
                "review",
                projected,
                using=lambda value, artifacts: artifacts.record(
                    "manual-review",
                    value,
                ),
            )
            return {
                "default_snapshot": type(default_snapshot).__name__,
                "custom_snapshot": custom_snapshot,
                "score": score,
                "created": created,
            }

        run = evaluation.run("evidence-and-presentation", program)

    assert run.value["default_snapshot"] == "CrystalLatticeSnapshot"
    assert run.value["custom_snapshot"] == {"response": "Echo: hello"}
    assert run.value["score"] == len("Echo: hello")
    assert "records/manual-review.json" in run.value["created"]
    assert run.artifact_dir.joinpath("records/manual-review.json").is_file()


def test_default_agent_starts_context_and_application_closes(
    tmp_path: Path,
) -> None:
    close_calls: list[str] = []

    def application_factory(*args, **kwargs):
        application = AgentApplication(*args, **kwargs)
        original_close = application.close

        def tracked_close() -> None:
            close_calls.append("closed")
            original_close()

        application.close = tracked_close  # type: ignore[method-assign]
        return application

    environment = CrystalLatticeEnvironment.from_config(
        write_config(tmp_path),
        default_agent="default",
        application_factory=application_factory,
    )
    with make_evaluation(tmp_path, environment) as evaluation:
        run = evaluation.run(
            "default-agent",
            lambda context: context.session.metadata["agent_id"],
        )

    assert run.value == "default"
    assert close_calls == ["closed"]


def test_environment_fingerprint_hashes_environment_values(
    tmp_path: Path,
) -> None:
    environment = CrystalLatticeEnvironment.from_config(
        write_config(tmp_path),
        environment={"SECRET_TOKEN": "sensitive-value"},
    )

    rendered = json.dumps(environment.fingerprint(), sort_keys=True)

    assert "SECRET_TOKEN" in rendered
    assert "sensitive-value" not in rendered


def test_environment_override_resolves_application_configuration(
    tmp_path: Path,
) -> None:
    config_path = write_config(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["providers"]["test"]["response_text"] = "${env:EVAL_RESPONSE}"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    environment = CrystalLatticeEnvironment.from_config(
        config_path,
        environment={"EVAL_RESPONSE": "resolved response"},
    )

    with make_evaluation(tmp_path, environment) as evaluation:
        def program(context: CrystalLatticeContext):
            context.start("default")
            context.add_message("user", "hello")
            return context.request().final_response

        run = evaluation.run("resolved-config", program)

    assert run.value == "resolved response"


def test_streaming_request_exposes_production_events_to_observers(
    tmp_path: Path,
) -> None:
    environment = CrystalLatticeEnvironment.from_config(write_config(tmp_path))
    observed: list[str] = []
    with make_evaluation(tmp_path, environment) as evaluation:
        def program(context: CrystalLatticeContext):
            context.start("default")
            context.add_message("user", "stream")
            outcome = context.request(
                stream=True,
                observers=(
                    lambda event: observed.append(str(event.get("type"))),
                ),
            )
            return outcome.final_response

        run = evaluation.run("streaming", program)

    assert run.value == "Echo: stream"
    assert "partial" in observed
    assert "final" in observed
    assert observed[-1] == "request_completed"


def test_crystal_lattice_cache_hit_and_continuation(
    tmp_path: Path,
) -> None:
    applications: list[AgentApplication] = []

    def application_factory(*args, **kwargs):
        application = AgentApplication(*args, **kwargs)
        applications.append(application)
        return application

    environment = CrystalLatticeEnvironment.from_config(
        write_config(tmp_path),
        application_factory=application_factory,
    )
    with make_evaluation(tmp_path, environment) as evaluation:
        def seed(context: CrystalLatticeContext):
            context.start("default")
            context.add_message("user", "seed")
            return context.request().final_response

        first = evaluation.run(
            "crystal-cache",
            seed,
            cache_key="crystal-cache-v1",
        )
        cached = evaluation.run(
            "crystal-cache",
            lambda context: "must not run",
            cache_key="crystal-cache-v1",
        )

        def continue_program(context: CrystalLatticeContext):
            context.add_message("user", "continued")
            outcome = context.request()
            return outcome.final_response, len(context.session.messages)

        child = evaluation.run(
            "crystal-child",
            continue_program,
            continue_from=cached,
        )

    assert first.value == "Echo: seed"
    assert cached.cache_hit is True
    assert cached.value == first.value
    assert len(applications) == 2
    assert child.value[0] == "Echo: continued"
    assert child.value[1] == 4