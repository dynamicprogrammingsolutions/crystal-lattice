from __future__ import annotations

import json

from agent_eval.crystal_lattice import (
    project_effective_config_view,
    project_session_review,
)
from agent_eval.result_packages import (
    availability,
    restore_replacements,
)

WORKSPACE = "/private/tmp/runs/abc/workspace"
REPLACEMENTS = {WORKSPACE: "<workspace>"}


def _glm_session() -> dict[str, object]:
    return {
        "session_id": "s-glm",
        "messages": [
            {
                "role": "system",
                "content": "short",
                "metadata": {
                    "compiled_content": (
                        "You are the agent.\n\nWork in "
                        f"{WORKSPACE} carefully."
                    )
                },
            },
            {"role": "user", "content": "Please create the task.", "metadata": {}},
            {
                "role": "assistant",
                "content": "I will inspect first.",
                "metadata": {
                    "reasoning": {"encrypted": "AAAAB3NzaC9l"},
                    "tool_calls": [
                        {
                            "function": {
                                "name": "Bash",
                                "arguments": json.dumps(
                                    {"command": f"ls {WORKSPACE}"}
                                ),
                            }
                        }
                    ],
                },
            },
            {
                "role": "tool",
                "content": "file-a.md\nfile-b.md\n",
                "metadata": {"tool_name": "Bash"},
            },
            {
                "role": "tool",
                "content": "cat: missing.md: No such file or directory",
                "metadata": {"tool_name": "Bash"},
            },
            {
                "role": "assistant",
                "content": "Done. Created the task.",
                "metadata": {},
            },
        ],
        "metadata": {},
    }


def _gpt_session() -> dict[str, object]:
    return {
        "session_id": "s-gpt",
        "messages": [
            {"role": "user", "content": "Please create the task.", "metadata": {}},
            {
                "role": "assistant",
                "content": "Inspecting.",
                "metadata": {
                    "usage": {
                        "input_tokens": 1000,
                        "output_tokens": 50,
                        "input_tokens_details": {
                            "cached_tokens": 0,
                            "cache_write_tokens": 100,
                        },
                        "output_tokens_details": {"reasoning_tokens": 10},
                    },
                    "usage_estimated_cached_tokens": 200,
                    "usage_total_cost": 0.001145,
                    "usage_total_cost_cumulative": 0.001145,
                },
            },
            {
                "role": "assistant",
                "content": "Created.",
                "metadata": {
                    "usage": {
                        "input_tokens": 500,
                        "output_tokens": 20,
                        "input_tokens_details": {"cached_tokens": 60},
                        "output_tokens_details": {"reasoning_tokens": 5},
                    },
                    "usage_total_cost": 0.00049,
                    "usage_total_cost_cumulative": 0.001635,
                },
            },
        ],
        "metadata": {},
    }


def test_review_keeps_compiled_instructions_and_lean_activity() -> None:
    review = project_session_review(_glm_session(), path_replacements=REPLACEMENTS)

    instructions = review["instructions"]
    assert instructions["availability"]["state"] == "captured"
    assert instructions["source"] == "session.compiled_content"
    assert WORKSPACE not in instructions["text"]
    assert "<workspace>" in instructions["text"]
    original = (
        "You are the agent.\n\nWork in " f"{WORKSPACE} carefully."
    )
    assert instructions["original_sha256"] == _sha(original)
    assert restore_replacements(
        instructions["text"], review["path_normalization"]["replacements"]
    ) == original

    roles = [entry["role"] for entry in review["conversation"]]
    assert roles == ["user", "assistant", "tool", "tool", "assistant"]
    assistant = review["conversation"][1]
    assert assistant["content"] == "I will inspect first."
    assert assistant["tool_calls"][0]["name"] == "Bash"
    assert WORKSPACE not in assistant["tool_calls"][0]["arguments"]
    assert assistant["reasoning_present"] is True
    assert "reasoning" not in assistant
    assert "AAAAB3NzaC9l" not in json.dumps(review)

    ok_tool = review["conversation"][2]
    assert ok_tool["tool_name"] == "Bash"
    assert "content" not in ok_tool
    assert "failure_excerpt" not in ok_tool
    failed_tool = review["conversation"][3]
    assert "No such file or directory" in failed_tool["failure_excerpt"]

    usage = review["usage"]
    assert usage["availability"]["state"] == "unavailable"
    assert usage["input_tokens"] is None

    assert review["execution"]["tool_call_count"] == 1
    assert review["execution"]["tool_result_count"] == 2
    assert review["execution"]["message_count"] == 6
    assert "full tool-result content" in review["omitted"]


def test_review_does_not_flag_successful_exit_codes() -> None:
    session = {
        "session_id": "s-exit",
        "messages": [
            {
                "role": "tool",
                "content": "Exit code: 0\nWall time: 0.1 seconds\nfile-a.md\n",
                "metadata": {"tool_name": "shell"},
            },
            {
                "role": "tool",
                "content": "Exit code: 1\nWall time: 0.2 seconds\nboom",
                "metadata": {"tool_name": "shell"},
            },
        ],
        "metadata": {},
    }

    review = project_session_review(session)

    ok_entry, failed_entry = review["conversation"]
    assert "failure_excerpt" not in ok_entry
    assert "Exit code: 1" in failed_entry["failure_excerpt"]


def test_review_uses_supplied_reconstructed_instructions() -> None:
    text = "You are the agent.\n\nWork in /private/tmp/runs/abc/workspace."
    review = project_session_review(
        _gpt_session(),
        supplied_instructions={
            "text": text,
            "source": "recompiled-from-saved-sources",
            "availability": availability("reconstructed", verified=True),
            "detail": "SHA-256 matches the recorded delivery hash",
        },
        path_replacements=REPLACEMENTS,
    )

    instructions = review["instructions"]
    assert instructions["availability"] == {
        "state": "reconstructed",
        "verified": True,
        "detail": "SHA-256 matches the recorded delivery hash",
    }
    assert instructions["source"] == "recompiled-from-saved-sources"
    assert instructions["original_sha256"] == _sha(text)
    assert WORKSPACE not in instructions["text"]


def test_review_reports_missing_instructions() -> None:
    review = project_session_review(_gpt_session())

    instructions = review["instructions"]
    assert instructions["text"] is None
    assert instructions["availability"]["state"] == "unavailable"
    assert "no system or developer message" in instructions["availability"]["detail"]


def test_review_extracts_usage_with_estimated_cached_tokens() -> None:
    review = project_session_review(_gpt_session())

    usage = review["usage"]
    assert usage["availability"]["state"] == "captured"
    assert usage["input_tokens"] == 1500
    assert usage["output_tokens"] == 70
    assert usage["reasoning_tokens"] == 15
    assert usage["cache_write_tokens"] == 100
    assert usage["cached_input_tokens"] == 260
    assert usage["cached_input_estimated"] is True
    assert abs(usage["provider_reported_cost"] - 0.001635) < 1e-9
    assert abs(usage["provider_reported_cost_cumulative"] - 0.001635) < 1e-9


def test_review_bounds_inherited_continuation_prefix() -> None:
    parent_messages = _glm_session()["messages"]
    continued = {
        "session_id": "s-cont",
        "messages": [
            *parent_messages,
            {"role": "user", "content": "Now plan.", "metadata": {}},
            {
                "role": "assistant",
                "content": "Planning.",
                "metadata": {
                    "usage": {
                        "input_tokens": 900,
                        "output_tokens": 30,
                        "input_tokens_details": {"cached_tokens": 700},
                        "output_tokens_details": {"reasoning_tokens": 3},
                    },
                    "usage_total_cost": 0.0003,
                    "usage_total_cost_cumulative": 0.0003,
                },
            },
        ],
        "metadata": {},
    }

    review = project_session_review(
        continued,
        inherited_prefix={"length": len(parent_messages)},
    )

    prefix = review["inherited_prefix"]
    assert prefix["length"] == len(parent_messages)
    assert prefix["availability"]["state"] == "captured"
    inherited_entries = [
        entry for entry in review["conversation"] if entry.get("inherited")
    ]
    assert len(inherited_entries) == len(parent_messages)
    assert all("content" not in entry for entry in inherited_entries)
    usage = review["usage"]
    assert usage["input_tokens"] == 900
    assert usage["cached_input_tokens"] == 700
    assert usage["cached_input_estimated"] is False
    assert usage["provider_reported_cost"] == 0.0003


def test_review_marks_unknown_prefix_as_unbounded_usage() -> None:
    review = project_session_review(
        _gpt_session(),
        inherited_prefix={"length": None},
    )

    assert review["inherited_prefix"]["length"] is None
    assert review["inherited_prefix"]["availability"]["state"] == "unavailable"
    assert review["usage"]["availability"]["state"] == "unavailable"
    assert "cannot be bounded" in review["usage"]["availability"]["detail"]


def test_review_includes_observation_execution_counts() -> None:
    review = project_session_review(
        _glm_session(),
        observation={
            "request_count": 1,
            "tool_event_count": 2,
            "mutation_count": 0,
            "error_count": 0,
        },
    )

    execution = review["execution"]
    assert execution["request_count"] == 1
    assert execution["tool_event_count"] == 2
    assert execution["mutation_count"] == 0
    assert execution["error_count"] == 0


def test_effective_config_view_redacts_and_normalizes() -> None:
    config = {
        "model": "gpt-test",
        "working_directory": WORKSPACE,
        "api_key": "secret-value",
        "nested": {"auth_token": "secret-value", "keep": WORKSPACE},
    }

    view = project_effective_config_view(config, path_replacements=REPLACEMENTS)

    assert view["model"] == "gpt-test"
    assert view["working_directory"] == "<workspace>"
    assert view["api_key"] == "<redacted>"
    assert view["nested"]["auth_token"] == "<redacted>"
    assert view["nested"]["keep"] == "<workspace>"
    assert "secret-value" not in json.dumps(view)


def _sha(text: str) -> str:
    from agent_eval.result_packages import sha256_text

    return sha256_text(text)

def test_render_session_markdown_shows_full_transcript() -> None:
    from agent_eval.crystal_lattice import render_session_markdown

    review = project_session_review(_glm_session(), path_replacements=REPLACEMENTS)
    markdown = render_session_markdown(
        review,
        title="tg-01 task-creation glm max",
        context={
            "Run": "`run-1`",
            "Model": "glm-test (effort max)",
            "Delivered instructions": (
                "[glm-max](../../../shared/system-messages/glm-max.md)"
                " — captured (original SHA-256 `abc123…`)"
            ),
        },
    )

    assert "# Session — tg-01 task-creation glm max" in markdown
    assert "- Run: `run-1`" in markdown
    assert "- Activity: 6 messages · 1 tool calls · 2 tool results" in markdown
    assert "- Usage: unknown — saved session contains no provider usage metadata" in markdown
    assert "**User**" in markdown
    assert "Please create the task." in markdown
    assert "**Assistant** *(reasoning present)*" in markdown
    assert "- `Bash` {\"command\": \"ls <workspace>\"}" in markdown
    assert "**Tool `Bash`** — *(result omitted)*" in markdown
    assert "**Tool `Bash`** — failed" in markdown
    assert "> cat: missing.md: No such file or directory" in markdown
    assert "AAAAB3NzaC9l" not in markdown


def test_render_session_markdown_truncates_long_tool_arguments() -> None:
    from agent_eval.crystal_lattice import render_session_markdown

    session = {
        "session_id": "s-long",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "metadata": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "shell",
                                "arguments": json.dumps(
                                    {"command": "x" * 500}
                                ),
                            }
                        }
                    ]
                },
            }
        ],
        "metadata": {},
    }
    review = project_session_review(session)
    markdown = render_session_markdown(review, title="long")

    argument_line = next(
        line for line in markdown.splitlines() if line.startswith("- `shell`")
    )
    assert len(argument_line) < 200
    assert argument_line.endswith("…")


def test_render_session_markdown_reports_captured_usage() -> None:
    from agent_eval.crystal_lattice import render_session_markdown

    review = project_session_review(_gpt_session())
    markdown = render_session_markdown(review, title="gpt")

    assert (
        "- Usage: 1,500 input · 260 cached (estimated) · 100 cache write"
        " · 70 output · provider cost $0.0016350" in markdown
    )


def test_review_keeps_model_text_verbatim_but_normalizes_projection() -> None:
    session = {
        "session_id": "s-verbatim",
        "messages": [
            {
                "role": "user",
                "content": f"Plan in {WORKSPACE}.",
                "metadata": {},
            },
            {
                "role": "assistant",
                "content": f"Created the plan in {WORKSPACE}/tasks/plan.md.",
                "metadata": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "Bash",
                                "arguments": json.dumps(
                                    {"command": f"ls {WORKSPACE}"}
                                ),
                            }
                        }
                    ]
                },
            },
        ],
        "metadata": {},
    }

    review = project_session_review(session, path_replacements=REPLACEMENTS)

    user_entry = review["conversation"][0]
    assistant_entry = review["conversation"][1]
    assert user_entry["content"] == f"Plan in {WORKSPACE}."
    assert (
        assistant_entry["content"]
        == f"Created the plan in {WORKSPACE}/tasks/plan.md."
    )
    assert WORKSPACE not in assistant_entry["tool_calls"][0]["arguments"]
