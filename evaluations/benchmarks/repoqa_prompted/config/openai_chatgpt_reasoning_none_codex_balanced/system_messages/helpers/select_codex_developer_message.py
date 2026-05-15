import re


def _selected_personality() -> str:
    value = CONFIG.get("codex_personality")
    if not isinstance(value, str) or not value:
        return "default"
    return value


def _developer_message_rows() -> list[dict]:
    rows = CONFIG.get("codex_developer_messages") or []
    return [row for row in rows if isinstance(row, dict)]


def _matches_model(model: str, pattern: str) -> bool:
    if not pattern:
        return False
    try:
        return re.search(pattern, model) is not None
    except re.error:
        return False


def _select_matching_text(model: str, personality: str | None) -> str:
    for row in _developer_message_rows():
        pattern = row.get("model_regex")
        if not isinstance(pattern, str) or not _matches_model(model, pattern):
            continue

        row_personality = row.get("personality")
        if personality is None:
            if row_personality not in (None, ""):
                continue
        elif row_personality != personality:
            continue

        text = row.get("text")
        if isinstance(text, str) and text:
            return text
    return ""


def select_codex_developer_message() -> str:
    model = str(CONFIG.get("model") or "")
    personality = _selected_personality()

    selected = _select_matching_text(model, personality)
    if selected:
        return selected

    fallback = _select_matching_text(model, None)
    if fallback:
        return fallback

    return ""


def get_ui_elements() -> list[dict]:
    return [
        {
            "ui_type": "config",
            "type": "select",
            "key": "codex_personality",
            "label": "Codex Personality",
            "default": _selected_personality(),
            "options": [
                {"value": "default", "label": "default"},
                {"value": "friendly", "label": "friendly"},
                {"value": "pragmatic", "label": "pragmatic"},
            ],
        }
    ]