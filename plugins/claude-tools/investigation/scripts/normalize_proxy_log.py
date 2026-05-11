#!/usr/bin/env python3
"""Normalize Claude Code proxy logs into implementation fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


BODY_MARKER = "Body:"
LONG_TEXT_HEADER = "--- Long Text Fields ---"


def _extract_balanced_json(text: str, start_index: int) -> tuple[dict[str, Any], int]:
    decoder = json.JSONDecoder()
    obj, end = decoder.raw_decode(text[start_index:])
    if not isinstance(obj, dict):
        raise ValueError("expected JSON object")
    return obj, start_index + end


def _parse_long_texts(block: str) -> dict[str, str]:
    long_texts: dict[str, str] = {}
    header_pattern = re.compile(r"LONG_TEXT_(?P<number>\d+) - (?P<path>.*?) \((?P<length>\d+) chars\):\n---\n")
    matches = list(header_pattern.finditer(block))
    for index, match in enumerate(matches):
        content_start = match.end()
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        content_block = block[content_start:next_start]
        delimiter_index = content_block.rfind("\n---")
        if delimiter_index >= 0:
            content = content_block[:delimiter_index]
        else:
            content = content_block
        long_texts[f"[LONG_TEXT_{match.group('number')}]"] = content
    return long_texts


def _restore_long_texts(value: Any, long_texts: dict[str, str]) -> Any:
    if isinstance(value, str):
        return long_texts.get(value, value)
    if isinstance(value, list):
        return [_restore_long_texts(item, long_texts) for item in value]
    if isinstance(value, dict):
        return {key: _restore_long_texts(item, long_texts) for key, item in value.items()}
    return value


def parse_proxy_log(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    requests: list[dict[str, Any]] = []
    for chunk in text.split("=== Incoming Request ==="):
        if BODY_MARKER not in chunk:
            continue
        method_match = re.search(r"Method:\s*(\S+)", chunk)
        url_match = re.search(r"Original URL:\s*(\S+)", chunk)
        body_index = chunk.find(BODY_MARKER)
        json_start = chunk.find("{", body_index)
        if json_start < 0:
            continue
        body, json_end = _extract_balanced_json(chunk, json_start)
        tail = chunk[json_end:]
        long_texts = _parse_long_texts(tail if LONG_TEXT_HEADER in tail else chunk)
        body = _restore_long_texts(body, long_texts)
        requests.append(
            {
                "method": method_match.group(1) if method_match else None,
                "url": url_match.group(1) if url_match else None,
                "body": body,
            }
        )
    return requests


def _normalize_string(value: str, replacements: dict[str, str]) -> str:
    for original, replacement in replacements.items():
        if original:
            value = value.replace(original, replacement)
    value = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "<UUID>",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\bcall_[A-Za-z0-9_-]+\b", "<TOOL_CALL_ID>", value)
    value = re.sub(r"\breq_[A-Za-z0-9_-]+\b", "<REQUEST_ID>", value)
    value = re.sub(r'"device_id":"[^"]+"', '"device_id":"<DEVICE_ID>"', value)
    return value


def normalize_value(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        return _normalize_string(value, replacements)
    if isinstance(value, list):
        return [normalize_value(item, replacements) for item in value]
    if isinstance(value, dict):
        source = value.get("source")
        if (
            value.get("type") == "image"
            and isinstance(source, dict)
            and isinstance(source.get("data"), str)
            and len(source["data"]) > 2000
        ):
            data = source["data"]
            return {
                **{key: normalize_value(item, replacements) for key, item in value.items() if key != "source"},
                "source": {
                    **{
                        key: normalize_value(item, replacements)
                        for key, item in source.items()
                        if key != "data"
                    },
                    "data": f"<BASE64 sha256={hashlib.sha256(data.encode('ascii')).hexdigest()} length={len(data)}>",
                },
            }
        return {key: normalize_value(item, replacements) for key, item in value.items()}
    return value


def _find_read_schema(requests: list[dict[str, Any]]) -> dict[str, Any] | None:
    for request in requests:
        for tool in request.get("body", {}).get("tools", []) or []:
            if isinstance(tool, dict) and tool.get("name") == "Read":
                return tool
    return None


def _find_tool_use(requests: list[dict[str, Any]]) -> dict[str, Any] | None:
    for request in requests:
        for message in request.get("body", {}).get("messages", []) or []:
            for block in message.get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Read":
                    return block
    return None


def _find_tool_result_message(requests: list[dict[str, Any]]) -> dict[str, Any] | None:
    for request in requests:
        for message in request.get("body", {}).get("messages", []) or []:
            for block in message.get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    return message
    return None


def build_fixture(
    *,
    case_name: str,
    proxy_log: Path,
    stdout_jsonl: Path | None,
    replacements: dict[str, str],
) -> dict[str, Any]:
    requests = parse_proxy_log(proxy_log)
    normalized_requests = normalize_value(requests, replacements)
    fixture: dict[str, Any] = {
        "case": case_name,
        "request_count": len(normalized_requests),
        "request_urls": [request.get("url") for request in normalized_requests],
        "tool_schema": _find_read_schema(normalized_requests),
        "assistant_tool_use": _find_tool_use(normalized_requests),
        "tool_result_message": _find_tool_result_message(normalized_requests),
        "final_result": None,
    }

    if stdout_jsonl and stdout_jsonl.exists():
        for line in stdout_jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "result":
                fixture["final_result"] = normalize_value(event.get("result"), replacements)

    return fixture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--proxy-log", type=Path, required=True)
    parser.add_argument("--stdout-jsonl", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replace", action="append", default=[], help="literal=replacement")
    args = parser.parse_args()

    replacements: dict[str, str] = {}
    for item in args.replace:
        original, separator, replacement = item.partition("=")
        if not separator:
            raise SystemExit(f"invalid --replace value: {item!r}")
        replacements[original] = replacement

    fixture = build_fixture(
        case_name=args.case,
        proxy_log=args.proxy_log,
        stdout_jsonl=args.stdout_jsonl,
        replacements=replacements,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
