#!/usr/bin/env python3
"""Run deterministic Claude Code investigations for the Read tool."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from normalize_proxy_log import build_fixture


REPO_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_ROOT = Path(__file__).resolve().parents[2]
PROXY_JS = REPO_ROOT.parent / "openai-proxy" / "proxy.js"
RAW_ROOT = PLUGIN_ROOT / "investigation" / "raw" / "read"
FIXTURE_ROOT = PLUGIN_ROOT / "investigation" / "fixtures" / "read"
DEFAULT_MODEL = "qwen3-coder-next:cloud"


@dataclass(frozen=True)
class CaseSpec:
    name: str
    prompt: str
    expected_fragment: str


CASES = {
    "success-small-file": CaseSpec(
        name="success-small-file",
        prompt=(
            "Use the Read tool to read the file at {small_file}. "
            "Then answer with exactly the first line from that file and nothing else."
        ),
        expected_fragment="CLAUDE_READ_SENTINEL first line",
    ),
    "success-offset-limit": CaseSpec(
        name="success-offset-limit",
        prompt=(
            "Use the Read tool to read the file at {range_file}, starting at offset 3 "
            "with limit 2. Then answer with exactly the text of the first returned line."
        ),
        expected_fragment="range-line-3",
    ),
    "missing-file-error": CaseSpec(
        name="missing-file-error",
        prompt=(
            "Use the Read tool to read the file at {missing_file}. "
            "Then briefly report the tool error."
        ),
        expected_fragment="",
    ),
    "large-file-truncation": CaseSpec(
        name="large-file-truncation",
        prompt=(
            "Use the Read tool to read the file at {large_file}. "
            "Then answer with exactly the first line from that file."
        ),
        expected_fragment="large-line-1",
    ),
    "empty-file": CaseSpec(
        name="empty-file",
        prompt=(
            "Use the Read tool to read the file at {empty_file}. "
            "Then briefly report exactly what the tool returned."
        ),
        expected_fragment="",
    ),
    "directory-path-error": CaseSpec(
        name="directory-path-error",
        prompt=(
            "Use the Read tool to read the path at {workspace}. "
            "Then briefly report the tool error."
        ),
        expected_fragment="",
    ),
    "small-image": CaseSpec(
        name="small-image",
        prompt=(
            "Use the Read tool to inspect the image at {image_file}. "
            "Then answer with a brief description of the image."
        ),
        expected_fragment="",
    ),
    "small-pdf": CaseSpec(
        name="small-pdf",
        prompt=(
            "Use the Read tool to read the PDF at {small_pdf}. "
            "Then answer with the first visible text from the PDF."
        ),
        expected_fragment="CLAUDE PDF SENTINEL",
    ),
    "large-pdf-requires-pages": CaseSpec(
        name="large-pdf-requires-pages",
        prompt=(
            "Use the Read tool to read the PDF at {large_pdf} without specifying pages. "
            "Then briefly report the tool result."
        ),
        expected_fragment="",
    ),
    "pdf-pages-range": CaseSpec(
        name="pdf-pages-range",
        prompt=(
            "Use the Read tool to read the PDF at {large_pdf} with pages set to \"2-3\". "
            "Then answer with the first visible text from the returned pages."
        ),
        expected_fragment="CLAUDE PDF PAGE 2",
    ),
    "notebook-simple": CaseSpec(
        name="notebook-simple",
        prompt=(
            "Use the Read tool to read the notebook at {notebook_file}. "
            "Then answer with the notebook sentinel text."
        ),
        expected_fragment="CLAUDE_NOTEBOOK_SENTINEL",
    ),
}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _require_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"required executable not found: {name}")


def _run(command: list[str], *, cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def _wait_for_proxy(port: int, timeout_seconds: float = 10.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        proc = _run(["curl", "-sS", f"http://localhost:{port}/health"], cwd=REPO_ROOT, timeout=5)
        if proc.returncode == 0:
            return
        time.sleep(0.2)
    raise RuntimeError(f"proxy did not become ready on port {port}")


def _prepare_workspace(root: Path) -> dict[str, Path]:
    workspace = root / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    small_file = workspace / "small-read.txt"
    small_file.write_text(
        "CLAUDE_READ_SENTINEL first line\nsecond line\nthird line\n",
        encoding="utf-8",
    )
    range_file = workspace / "range-read.txt"
    range_file.write_text(
        "\n".join(f"range-line-{index}" for index in range(1, 9)) + "\n",
        encoding="utf-8",
    )
    large_file = workspace / "large-read.txt"
    large_file.write_text(
        "\n".join(f"large-line-{index} " + ("x" * 120) for index in range(1, 5000)) + "\n",
        encoding="utf-8",
    )
    empty_file = workspace / "empty-read.txt"
    empty_file.write_text("", encoding="utf-8")
    image_file = workspace / "small.png"
    image_file.write_bytes(_one_by_one_png())
    small_pdf = workspace / "small.pdf"
    small_pdf.write_bytes(_minimal_pdf(["CLAUDE PDF SENTINEL one page"]))
    large_pdf = workspace / "large.pdf"
    large_pdf.write_bytes(_minimal_pdf([f"CLAUDE PDF PAGE {index}" for index in range(1, 13)]))
    notebook_file = workspace / "simple.ipynb"
    notebook_file.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": ["# CLAUDE_NOTEBOOK_SENTINEL\n", "Notebook markdown cell.\n"],
                    },
                    {
                        "cell_type": "code",
                        "execution_count": 1,
                        "metadata": {},
                        "outputs": [
                            {
                                "name": "stdout",
                                "output_type": "stream",
                                "text": ["CLAUDE_NOTEBOOK_OUTPUT\n"],
                            }
                        ],
                        "source": ["print('CLAUDE_NOTEBOOK_OUTPUT')\n"],
                    },
                ],
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3",
                        "language": "python",
                        "name": "python3",
                    },
                    "language_info": {"name": "python", "version": "3.11"},
                },
                "nbformat": 4,
                "nbformat_minor": 5,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "workspace": workspace,
        "small_file": small_file,
        "range_file": range_file,
        "large_file": large_file,
        "empty_file": empty_file,
        "image_file": image_file,
        "small_pdf": small_pdf,
        "large_pdf": large_pdf,
        "notebook_file": notebook_file,
        "missing_file": workspace / "missing-read.txt",
    }


def _one_by_one_png() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
    )


def _minimal_pdf(page_texts: list[str]) -> bytes:
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
    ]
    page_refs = " ".join(f"{3 + index * 2} 0 R" for index in range(len(page_texts)))
    objects.append(f"<< /Type /Pages /Kids [{page_refs}] /Count {len(page_texts)} >>".encode("ascii"))

    for index, text in enumerate(page_texts):
        page_obj = 3 + index * 2
        content_obj = page_obj + 1
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 18 Tf 72 720 Td ({escaped}) Tj ET".encode("ascii")
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> "
                f"/Contents {content_obj} 0 R >>"
            ).encode("ascii")
        )
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream")

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)


def _format_prompt(case: CaseSpec, paths: dict[str, Path]) -> str:
    return case.prompt.format(**{key: str(value) for key, value in paths.items()})


def _run_case(case: CaseSpec, *, model: str, keep_raw: bool) -> dict[str, object]:
    run_id = time.strftime("%Y%m%d-%H%M%S") + f"-{case.name}"
    if keep_raw:
        raw_dir = RAW_ROOT / run_id
        raw_dir.mkdir(parents=True, exist_ok=False)
        temp_context = None
    else:
        temp_context = tempfile.TemporaryDirectory(prefix=f"claude-read-{case.name}-")
        raw_dir = Path(temp_context.name)

    try:
        paths = _prepare_workspace(raw_dir)
        proxy_log = raw_dir / "proxy.log"
        stdout_jsonl = raw_dir / "claude_stdout.jsonl"
        stderr_log = raw_dir / "claude_stderr.log"
        debug_log = raw_dir / "claude_debug.log"
        port = _free_port()

        with proxy_log.open("w", encoding="utf-8") as proxy_out:
            proxy = subprocess.Popen(
                ["node", str(PROXY_JS), "http://localhost:11434/v1", str(port)],
                cwd=str(PROXY_JS.parent),
                stdout=proxy_out,
                stderr=subprocess.STDOUT,
                text=True,
            )
        try:
            _wait_for_proxy(port)
            base_url = f"http://localhost:{port}/api"
            env_settings = {
                "ANTHROPIC_BASE_URL": base_url,
                "ANTHROPIC_API_KEY": "ollama",
                "ANTHROPIC_AUTH_TOKEN": "ollama",
                "ANTHROPIC_SMALL_FAST_MODEL": model,
                "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
                "DISABLE_TELEMETRY": "1",
                "OTEL_METRICS_EXPORTER": "none",
                "OTEL_TRACES_EXPORTER": "none",
                "OTEL_LOGS_EXPORTER": "none",
            }
            prompt = _format_prompt(case, paths)
            command = [
                "claude",
                "-p",
                "--verbose",
                "--debug-file",
                str(debug_log),
                "--setting-sources",
                "project",
                "--settings",
                json.dumps({"env": env_settings}, separators=(",", ":")),
                "--no-session-persistence",
                "--model",
                model,
                "--tools",
                "Read",
                "--permission-mode",
                "bypassPermissions",
                "--output-format",
                "stream-json",
                prompt,
            ]
            env = {**os.environ, **env_settings}
            with stdout_jsonl.open("w", encoding="utf-8") as stdout_out, stderr_log.open(
                "w", encoding="utf-8"
            ) as stderr_out:
                completed = subprocess.run(
                    command,
                    cwd=str(paths["workspace"]),
                    env=env,
                    stdout=stdout_out,
                    stderr=stderr_out,
                    text=True,
                    timeout=150,
                    check=False,
                )
        finally:
            proxy.terminate()
            try:
                proxy.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proxy.kill()
                proxy.wait(timeout=5)

        replacements = {
            str(paths["workspace"]): "<WORKSPACE>",
            str(REPO_ROOT): "<REPO_ROOT>",
            str(raw_dir): "<RAW_DIR>",
        }
        fixture = build_fixture(
            case_name=case.name,
            proxy_log=proxy_log,
            stdout_jsonl=stdout_jsonl,
            replacements=replacements,
        )
        fixture["raw_artifact_dir"] = "<RAW_DIR>" if keep_raw else None
        fixture["claude_returncode"] = completed.returncode
        fixture_path = FIXTURE_ROOT / f"{case.name}.json"
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        return {
            "case": case.name,
            "returncode": completed.returncode,
            "fixture": str(fixture_path),
            "raw": str(raw_dir) if keep_raw else None,
            "schema_found": fixture.get("tool_schema") is not None,
            "tool_use_found": fixture.get("assistant_tool_use") is not None,
            "tool_result_found": fixture.get("tool_result_message") is not None,
            "final_result": fixture.get("final_result"),
        }
    finally:
        if temp_context is not None:
            temp_context.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=[*CASES.keys(), "all"],
        default="success-small-file",
        help="Read investigation case to run.",
    )
    parser.add_argument("--model", default=os.environ.get("CLAUDE_INVESTIGATION_MODEL", DEFAULT_MODEL))
    parser.add_argument(
        "--discard-raw",
        action="store_true",
        help="Use a temporary raw directory and keep only normalized fixtures.",
    )
    args = parser.parse_args()

    _require_executable("claude")
    _require_executable("node")
    _require_executable("curl")
    if not PROXY_JS.exists():
        raise SystemExit(f"proxy not found: {PROXY_JS}")
    ollama = _run(["curl", "-sS", "http://localhost:11434/api/tags"], cwd=REPO_ROOT, timeout=10)
    if ollama.returncode != 0:
        raise SystemExit("Ollama is not reachable at http://localhost:11434")

    selected = CASES.values() if args.case == "all" else [CASES[args.case]]
    summaries = [_run_case(case, model=args.model, keep_raw=not args.discard_raw) for case in selected]
    print(json.dumps(summaries, indent=2, sort_keys=True))
    failed = [
        item
        for item in summaries
        if not (item["schema_found"] and item["tool_use_found"] and item["tool_result_found"])
    ]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
