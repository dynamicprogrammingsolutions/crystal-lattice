def include_tasks() -> bool:
    return bool(CONFIG.get("include_tasks", False))


def get_ui_elements() -> list[dict]:
    return [
        {
            "ui_type": "config",
            "type": "checkbox",
            "key": "include_tasks",
            "label": "Include TASKS Guidance",
            "default": include_tasks(),
        }
    ]