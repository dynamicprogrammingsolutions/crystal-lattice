from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CODEX_GITHUB_API_LATEST_COMMIT_URL = "https://api.github.com/repos/openai/codex/commits/main"
CODEX_RAW_MODELS_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/openai/codex/{commit}/codex-rs/models-manager/models.json"
)
CODEX_RAW_MAIN_MODELS_URL = (
    "https://raw.githubusercontent.com/openai/codex/main/codex-rs/models-manager/models.json"
)
_USER_AGENT = "openai-responses-codex-models/1.0"
_DEFAULT_MANUAL_MODELS_RELATIVE = "data/openai_chatgpt_manual_models.json"
_DEFAULT_SNAPSHOT_RELATIVE = "data/openai_codex_models.json"


def default_manual_models_path() -> Path:
    return Path(__file__).resolve().parent / _DEFAULT_MANUAL_MODELS_RELATIVE


def default_snapshot_path() -> Path:
    return Path(__file__).resolve().parent / _DEFAULT_SNAPSHOT_RELATIVE


@lru_cache(maxsize=1)
def load_manual_chatgpt_models(path: str | None = None) -> Dict[str, Any]:
    manual_path = Path(path) if path else default_manual_models_path()
    with manual_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError("invalid manual ChatGPT models payload")
    models = payload.get("models")
    if not isinstance(models, dict):
        raise RuntimeError("manual ChatGPT models payload missing models mapping")
    return payload


@lru_cache(maxsize=1)
def load_codex_models_snapshot(path: str | None = None) -> Dict[str, Any]:
    snapshot_path = Path(path) if path else default_snapshot_path()
    with snapshot_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError("invalid Codex models snapshot payload")
    models = payload.get("models")
    if not isinstance(models, dict):
        raise RuntimeError("Codex models snapshot missing models mapping")
    return payload


def clear_manual_chatgpt_models_cache() -> None:
    load_manual_chatgpt_models.cache_clear()


def clear_codex_models_snapshot_cache() -> None:
    load_codex_models_snapshot.cache_clear()


def _fetch_json(url: str, *, timeout: float) -> Any:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        },
    )
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        payload = response.read().decode(charset, errors="replace")
    return json.loads(payload)


def normalize_model_descriptor(item: Any) -> Dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    model_id = item.get("id") or item.get("slug")
    if not isinstance(model_id, str) or not model_id.strip():
        return None

    normalized: Dict[str, Any] = {"id": model_id.strip()}
    model_name = item.get("name") or item.get("display_name")
    if isinstance(model_name, str) and model_name.strip():
        normalized["name"] = model_name.strip()
    description = item.get("description")
    if isinstance(description, str) and description.strip():
        normalized["description"] = description.strip()
    return normalized


def normalize_models_payload(payload: Any) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        raise RuntimeError("Codex models payload must be a JSON object")

    raw_models = payload.get("models")
    if not isinstance(raw_models, list):
        raise RuntimeError("Codex models payload missing models list")

    normalized: List[Dict[str, Any]] = []
    for item in raw_models:
        descriptor = normalize_model_descriptor(item)
        if descriptor is not None:
            normalized.append(descriptor)
    return normalized


def _latest_commit_sha(*, timeout: float) -> str | None:
    commit_payload = _fetch_json(CODEX_GITHUB_API_LATEST_COMMIT_URL, timeout=timeout)
    sha = commit_payload.get("sha") if isinstance(commit_payload, dict) else None
    if not isinstance(sha, str) or not sha.strip():
        return None
    return sha.strip()


def fetch_codex_models(*, timeout: float) -> List[Dict[str, Any]]:
    latest_commit = None
    latest_commit_error: Exception | None = None

    try:
        latest_commit = _latest_commit_sha(timeout=timeout)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
        latest_commit_error = exc

    fetch_errors: List[str] = []
    urls: List[str] = []
    if latest_commit:
        urls.append(CODEX_RAW_MODELS_URL_TEMPLATE.format(commit=latest_commit))
    urls.append(CODEX_RAW_MAIN_MODELS_URL)

    for url in urls:
        try:
            payload = _fetch_json(url, timeout=timeout)
            return normalize_models_payload(payload)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            fetch_errors.append(f"{url}: {exc}")

    details = "; ".join(fetch_errors)
    if latest_commit_error is not None:
        details = f"commit lookup failed: {latest_commit_error}; {details}" if details else str(latest_commit_error)
    raise RuntimeError(f"failed to fetch Codex models catalog: {details}")


def fetch_codex_models_with_metadata(*, timeout: float) -> Tuple[List[Dict[str, Any]], str | None]:
    latest_commit = None
    latest_commit_error: Exception | None = None

    try:
        latest_commit = _latest_commit_sha(timeout=timeout)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
        latest_commit_error = exc

    fetch_errors: List[str] = []
    urls: List[Tuple[str, str | None]] = []
    if latest_commit:
        urls.append((CODEX_RAW_MODELS_URL_TEMPLATE.format(commit=latest_commit), latest_commit))
    urls.append((CODEX_RAW_MAIN_MODELS_URL, None))

    for url, commit in urls:
        try:
            payload = _fetch_json(url, timeout=timeout)
            return normalize_models_payload(payload), commit
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            fetch_errors.append(f"{url}: {exc}")

    details = "; ".join(fetch_errors)
    if latest_commit_error is not None:
        details = f"commit lookup failed: {latest_commit_error}; {details}" if details else str(latest_commit_error)
    raise RuntimeError(f"failed to fetch Codex models catalog: {details}")


def load_manual_chatgpt_model_descriptors(path: str | None = None) -> List[Dict[str, Any]]:
    payload = load_manual_chatgpt_models(path)
    models = payload.get("models")
    if not isinstance(models, dict):
        return []

    normalized: List[Dict[str, Any]] = []
    for item in models.values():
        descriptor = normalize_model_descriptor(item)
        if descriptor is not None:
            normalized.append(descriptor)
    return normalized


def load_snapshot_model_descriptors(path: str | None = None) -> List[Dict[str, Any]]:
    payload = load_codex_models_snapshot(path)
    models = payload.get("models")
    if not isinstance(models, dict):
        return []

    normalized: List[Dict[str, Any]] = []
    for item in models.values():
        descriptor = normalize_model_descriptor(item)
        if descriptor is not None:
            normalized.append(descriptor)
    return normalized


def load_manual_chatgpt_model_pricing(path: str | None = None) -> Dict[str, Dict[str, Any]]:
    payload = load_manual_chatgpt_models(path)
    models = payload.get("models")
    if not isinstance(models, dict):
        return {}

    normalized: Dict[str, Dict[str, Any]] = {}
    for model_id, item in models.items():
        if not isinstance(model_id, str) or not model_id.strip() or not isinstance(item, dict):
            continue
        pricing = item.get("pricing")
        if not isinstance(pricing, dict):
            continue
        normalized[model_id.strip()] = {
            "model": model_id.strip(),
            "pricing": pricing,
        }
    return normalized


def merge_model_descriptors(*descriptor_lists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged_by_id: Dict[str, Dict[str, Any]] = {}
    for descriptors in descriptor_lists:
        for item in descriptors:
            if not isinstance(item, dict):
                continue
            model_id = item.get("id")
            if not isinstance(model_id, str) or not model_id.strip():
                continue
            existing = merged_by_id.get(model_id.strip(), {})
            merged_by_id[model_id.strip()] = {**existing, **item, "id": model_id.strip()}
    return [merged_by_id[model_id] for model_id in sorted(merged_by_id)]


def build_snapshot_payload(
    *,
    fetched_at: str,
    model_entries: Iterable[Dict[str, Any]],
    source_commit: str | None = None,
) -> Dict[str, Any]:
    models: Dict[str, Dict[str, Any]] = {}
    for entry in model_entries:
        descriptor = normalize_model_descriptor(entry)
        if descriptor is None:
            continue
        models[descriptor["id"]] = descriptor

    payload: Dict[str, Any] = {
        "version": 1,
        "fetched_at": fetched_at,
        "source_base_url": "https://raw.githubusercontent.com/openai/codex",
        "models": dict(sorted(models.items())),
    }
    if isinstance(source_commit, str) and source_commit.strip():
        payload["source_commit"] = source_commit.strip()
    return payload


def build_live_snapshot_payload(*, timeout: float) -> Dict[str, Any]:
    model_entries, source_commit = fetch_codex_models_with_metadata(timeout=timeout)
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return build_snapshot_payload(
        fetched_at=fetched_at,
        model_entries=model_entries,
        source_commit=source_commit,
    )