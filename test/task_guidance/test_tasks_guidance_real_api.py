from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
import requests


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from harness import (  # noqa: E402
    CREATE_TASK_PROMPT,
    TASK_PROMPT,
    ModelCase,
    assistant_text_after_last_user,
    assert_approval_response,
    assert_draft_execution_plan,
    assert_no_execution_approval,
    assert_no_execution_plan,
    assert_no_lifecycle_notes,
    assert_only_changed_paths,
    assert_task_prefix,
    chatgpt_credentials_path,
    environment_for_case,
    find_single_created_task,
    git_status,
    model_cases,
    mutation_call_limit,
    prepare_case,
    requirements_section,
    send_turn,
    start_agent,
    write_final_task_artifact,
    write_git_artifacts,
    write_turn_artifacts,
    current_run_id,
)


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_app.runtime_env import RuntimeEnvOverlay  # noqa: E402


pytestmark = [pytest.mark.integration, pytest.mark.manual_integration]
RUN_ID = current_run_id()


def _model_params() -> list[pytest.ParameterSet]:
    params: list[pytest.ParameterSet] = []
    for case in model_cases():
        marks = (
            [pytest.mark.api, pytest.mark.openai]
            if case.auth_mode == "chatgpt"
            else [pytest.mark.ollama]
        )
        params.append(pytest.param(case, id=case.case_id, marks=marks))
    return params


@pytest.fixture(autouse=True)
def _reset_runtime_overlay() -> None:
    yield
    RuntimeEnvOverlay._reset_for_tests()


@pytest.fixture
def require_real_model_eval(model_case: ModelCase) -> None:
    if os.getenv("RUN_TASK_GUIDANCE_REAL_MODEL_EVAL") != "1":
        pytest.skip("RUN_TASK_GUIDANCE_REAL_MODEL_EVAL != '1'")

    if model_case.auth_mode == "chatgpt":
        path = chatgpt_credentials_path()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            pytest.skip(f"saved ChatGPT credentials not found at {path}")
        if not isinstance(payload, dict) or not isinstance(
            payload.get("access_token"), str
        ):
            pytest.skip(f"saved ChatGPT credentials are invalid at {path}")
        return

    base_url = os.getenv("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1")
    try:
        response = requests.get(f"{base_url.rstrip('/')}/models", timeout=5)
    except Exception as exc:
        pytest.skip(f"Ollama endpoint is unavailable: {exc}")
    if not response.ok:
        pytest.skip(f"Ollama endpoint returned HTTP {response.status_code}")


def _activate_case_environment(
    monkeypatch: pytest.MonkeyPatch,
    *,
    prepared,
) -> None:
    monkeypatch.chdir(prepared.workspace)
    for key, value in environment_for_case(prepared).items():
        monkeypatch.setenv(key, value)


def _record_failure(prepared, exc: BaseException) -> None:
    prepared.case_dir.joinpath("failure.txt").write_text(
        f"{type(exc).__name__}: {exc}\n",
        encoding="utf-8",
    )
    write_git_artifacts(prepared)


@pytest.mark.parametrize("model_case", _model_params())
def test_create_task_file_after_prior_plan_uses_default_no_plan_case(
    model_case: ModelCase,
    require_real_model_eval: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = prepare_case(
        scenario="create-task-after-plan",
        model_case=model_case,
        run_id=RUN_ID,
        with_premade_task=False,
    )
    _activate_case_environment(monkeypatch, prepared=prepared)
    running = None

    try:
        running = start_agent(prepared)
        first = send_turn(running, prepared, prompt=TASK_PROMPT)
        write_turn_artifacts(
            prepared,
            turn_number=1,
            prompt=TASK_PROMPT,
            result=first,
            mutation_budget=running.mutation_budget,
        )
        first_turn_status = git_status(prepared.workspace)

        second = send_turn(
            running,
            prepared,
            prompt=CREATE_TASK_PROMPT,
            session=first.session,
        )
        write_turn_artifacts(
            prepared,
            turn_number=2,
            prompt=CREATE_TASK_PROMPT,
            result=second,
            mutation_budget=running.mutation_budget,
        )

        task_path = find_single_created_task(prepared.workspace)
        write_final_task_artifact(prepared, task_path)
        relative = task_path.relative_to(prepared.workspace).as_posix()
        assert_only_changed_paths(prepared.workspace, [relative])

        text = task_path.read_text(encoding="utf-8")
        assert_task_prefix(text)
        assert_no_execution_plan(text)
        assert_no_lifecycle_notes(text)
        assert_no_execution_approval(assistant_text_after_last_user(second.session))
        assert running.mutation_budget.calls, "expected a task-file mutation call"
        assert len(running.mutation_budget.calls) <= mutation_call_limit()
        assert second.response.strip()
        assert first_turn_status == [], (
            "planning-only first turn changed the repository: "
            f"{first_turn_status!r}"
        )
    except BaseException as exc:
        _record_failure(prepared, exc)
        raise
    finally:
        if running is not None:
            running.prompt_capture.uninstall()
            running.mutation_budget.uninstall()
            running.app.close()


@pytest.mark.parametrize("model_case", _model_params())
def test_existing_task_gets_draft_plan_before_approval_response(
    model_case: ModelCase,
    require_real_model_eval: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = prepare_case(
        scenario="plan-existing-task",
        model_case=model_case,
        run_id=RUN_ID,
        with_premade_task=True,
    )
    assert prepared.premade_task_path is not None
    task_path = prepared.premade_task_path
    original_requirements = requirements_section(
        task_path.read_text(encoding="utf-8")
    )

    _activate_case_environment(monkeypatch, prepared=prepared)
    running = None
    relative = task_path.relative_to(prepared.workspace).as_posix()
    prompt = f"Please prepare an execution plan for `{relative}`."

    try:
        running = start_agent(prepared)
        result = send_turn(running, prepared, prompt=prompt)
        write_turn_artifacts(
            prepared,
            turn_number=1,
            prompt=prompt,
            result=result,
            mutation_budget=running.mutation_budget,
        )
        write_final_task_artifact(prepared, task_path)

        assert_only_changed_paths(prepared.workspace, [relative])
        text = task_path.read_text(encoding="utf-8")
        assert_task_prefix(text)
        assert requirements_section(text) == original_requirements
        assert_draft_execution_plan(text)
        assert_approval_response(result.response)
        assert running.mutation_budget.calls, (
            "expected the plan to be written before the final response"
        )
        assert len(running.mutation_budget.calls) <= mutation_call_limit()
    except BaseException as exc:
        _record_failure(prepared, exc)
        raise
    finally:
        if running is not None:
            running.prompt_capture.uninstall()
            running.mutation_budget.uninstall()
            running.app.close()
