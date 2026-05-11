from __future__ import annotations

from dataclasses import dataclass
import gzip
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, Optional
from urllib.request import urlopen

from agent_core import Session
from agent_evaluations.code_compare import compare_code
from agent_evaluations.config_dir import EvaluationEnvironment
from agent_evaluations.utils import isoformat_utc


DEFAULT_REPOQA_RELEASE = "2024-06-23"
REPOQA_RELEASE_URL_TEMPLATE = (
    "https://github.com/evalplus/repoqa_release/releases/download/{release}/"
    "repoqa-{release}.json.gz"
)


@dataclass(frozen=True)
class RepoQATask:
    task_id: str
    language: str
    repo_index: int
    needle_index: int
    repo_name: str
    commit_sha: str
    path: str
    symbol: str
    description: str
    start_line: int
    end_line: int
    ground_truth_code: str

    def to_manifest_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "language": self.language,
            "repo_index": self.repo_index,
            "needle_index": self.needle_index,
            "repo_name": self.repo_name,
            "commit_sha": self.commit_sha,
            "path": self.path,
            "symbol": self.symbol,
            "description": self.description,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "ground_truth_code": self.ground_truth_code,
        }


def repoqa_release_url(release: str) -> str:
    return REPOQA_RELEASE_URL_TEMPLATE.format(release=release)


def repoqa_cache_path(env: EvaluationEnvironment, release: str) -> Any:
    return env.paths.cache_root / "repoqa" / "releases" / f"repoqa-{release}.json.gz"


def download_repoqa_release(
    env: EvaluationEnvironment,
    *,
    release: str,
    force: bool = False,
) -> Any:
    destination = repoqa_cache_path(env, release)
    if destination.exists() and not force:
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(repoqa_release_url(release), timeout=60) as response:
        payload = response.read()
    destination.write_bytes(payload)
    return destination


def load_repoqa_dataset(env: EvaluationEnvironment, *, release: str) -> Dict[str, Any]:
    path = repoqa_cache_path(env, release)
    raw = gzip.decompress(path.read_bytes())
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("RepoQA dataset payload must be a JSON object")
    return payload


def _normalize_repoqa_path(text: str) -> str:
    normalized = text.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.startswith("/"):
        normalized = normalized[1:]
    if normalized.startswith("repo/"):
        normalized = normalized[len("repo/") :]
    try:
        return str(PurePosixPath(normalized))
    except Exception:
        return normalized

def _extract_ground_truth_code(repo_entry: Dict[str, Any], needle: Dict[str, Any]) -> str:
    path = needle.get("path")
    start_line = needle.get("start_line")
    end_line = needle.get("end_line")
    content_map = repo_entry.get("content")
    if (
        not isinstance(path, str)
        or not isinstance(start_line, int)
        or not isinstance(end_line, int)
        or not isinstance(content_map, dict)
    ):
        raise ValueError("RepoQA entry missing code extraction fields")
    file_text = content_map.get(path)
    if not isinstance(file_text, str):
        raise ValueError(f"RepoQA content missing file {path!r}")
    lines = file_text.splitlines()
    snippet = "\n".join(lines[start_line - 1 : end_line])
    return snippet.strip("\n") + "\n"


def iter_repoqa_tasks(
    dataset: Dict[str, Any],
    *,
    language: str,
) -> Iterable[RepoQATask]:
    repos = dataset.get(language)
    if not isinstance(repos, list):
        raise KeyError(f"RepoQA dataset does not contain language {language!r}")

    for repo_index, repo_entry in enumerate(repos):
        if not isinstance(repo_entry, dict):
            continue
        needles = repo_entry.get("needles")
        if not isinstance(needles, list):
            continue
        for needle_index, needle in enumerate(needles):
            if not isinstance(needle, dict):
                continue
            path = needle.get("path")
            symbol = needle.get("name")
            start_line = needle.get("start_line")
            end_line = needle.get("end_line")
            description = needle.get("description")
            repo_name = repo_entry.get("repo")
            commit_sha = repo_entry.get("commit_sha")
            if not all(
                [
                    isinstance(path, str),
                    isinstance(symbol, str),
                    isinstance(start_line, int),
                    isinstance(end_line, int),
                    isinstance(description, str),
                    isinstance(repo_name, str),
                    isinstance(commit_sha, str),
                ]
            ):
                continue
            task_id_source = f"{language}|{repo_name}|{path}|{symbol}|{start_line}|{end_line}"
            task_id = hashlib.sha1(task_id_source.encode("utf-8")).hexdigest()[:16]
            yield RepoQATask(
                task_id=task_id,
                language=language,
                repo_index=repo_index,
                needle_index=needle_index,
                repo_name=repo_name,
                commit_sha=commit_sha,
                path=path,
                symbol=symbol,
                description=description.strip(),
                start_line=start_line,
                end_line=end_line,
                ground_truth_code=_extract_ground_truth_code(repo_entry, needle),
            )


def score_repoqa_answer(task: RepoQATask, answer: Optional[Dict[str, str]]) -> Dict[str, Any]:
    if answer is None:
        return {
            "matched": False,
            "path_match": False,
            "symbol_match": False,
            "code_match": False,
            "comparison_method": None,
            "code_comparison": None,
            "score": 0.0,
        }

    path_match = _normalize_repoqa_path(answer.get("path", "")) == _normalize_repoqa_path(task.path)
    symbol_match = answer.get("symbol") == task.symbol
    code_comparison = compare_code(
        task.language,
        answer.get("code", ""),
        task.ground_truth_code,
    )
    code_match = code_comparison.matched
    matched = path_match and symbol_match and code_match
    return {
        "matched": matched,
        "path_match": path_match,
        "symbol_match": symbol_match,
        "code_match": code_match,
        "comparison_method": code_comparison.method,
        "code_comparison": code_comparison.to_dict(),
        "score": 1.0 if matched else 0.0,
    }


def count_tool_calls(session: Session) -> int:
    total = 0
    for message in session.messages:
        metadata = message.metadata if isinstance(message.metadata, dict) else {}
        tool_calls = metadata.get("tool_calls")
        if isinstance(tool_calls, list):
            total += len(tool_calls)
    return total


def extract_final_assistant_text(events: list[Dict[str, Any]]) -> str:
    for event in reversed(events):
        if event.get("type") != "final":
            continue
        messages = event.get("messages")
        if not isinstance(messages, list):
            continue
        for message in reversed(messages):
            if not isinstance(message, dict):
                continue
            if message.get("role") != "assistant":
                continue
            content = message.get("content")
            if isinstance(content, str):
                return content
    return ""